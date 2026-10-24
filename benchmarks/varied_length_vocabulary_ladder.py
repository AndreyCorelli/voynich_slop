"""One-variable vocabulary scaling on frozen small varied-length H1 controls."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks import small_varied_length_controls as small
from benchmarks.public_length_calibration import evaluate
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/varied-length-vocabulary-ladder')
CORPUS=Path('data/processed/caesar-latin-v2.json')
SIZES=(64,256)


def vocabularies(base,alphabet,records,sizes=SIZES):
    if not sizes or tuple(sorted(set(sizes)))!=tuple(sizes) or any(type(n)is not int or n<len(base.words) for n in sizes):raise ValueError('Invalid ladder sizes')
    words=list(base.words);seen=set(words);allowed=set(alphabet.symbols);provenance=[]
    for index,record in enumerate(records):
        if len(words)>=max(sizes):break
        if record['excluded_reason'] is not None:continue
        word=tuple(record['tokens'])
        if not word or not set(word)<=allowed or word in seen:continue
        words.append(word);seen.add(word);provenance.append({'record_index':index,'word':word})
    if len(words)<max(sizes):raise ValueError('Insufficient eligible words; do not broaden')
    return {n:WordDictionary(tuple(words[:n])) for n in sizes},provenance


def prepare():
    source=small.prepare();baseline=json.loads((small.OUT/'report.json').read_text())
    if not baseline['complete'] or baseline['prepared_sha256']!=digest(source):raise ValueError('Unmatched small controls')
    corpus=json.loads(CORPUS.read_text())
    identity={'source_sha256':digest(source),'baseline_sha256':digest(baseline),'corpus_sha256':digest(corpus),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('src/voynich_smt/language/dictionary.py'),
             Path('src/voynich_smt/solver/recovery.py'),Path('src/voynich_smt/solver/observed_codes.py'),
             Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return source,p
    base=HiddenRecoveryRequest.from_dict(source['cases'][0]['request'])
    dictionaries,provenance=vocabularies(base.dictionary,base.plaintext_alphabet,corpus['records'])
    cases=[];reused=[]
    for case in source['cases']:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        if q.dictionary!=base.dictionary or q.plaintext_alphabet!=base.plaintext_alphabet:raise ValueError('Expected common vocabulary/alphabet')
        previous=next(a for a in baseline['arms'] if a['case']==case['id'] and a['arm']=='hidden-words')
        if previous['request_sha256']!=digest(asdict(q)):raise ValueError('Unmatched baseline request')
        reused.append(previous)
        for n,dictionary in dictionaries.items():
            expanded=replace(q,dictionary=dictionary);verify(expanded,case['truth'])
            cases.append({'id':f"{case['id']}-vocab-{n}",'source_case':case['id'],'vocabulary_size':n,'request':asdict(expanded)})
    protocol={'identity':identity,'sizes':[12,*SIZES],'new_fits':12,'reused_hidden_fits':6,'timeout_ms_per_fit':5000,
        'selection':'Retain original twelve dictionary entries/order, append first distinct normalized Caesar corpus words in record order using only the unchanged fourteen-letter alphabet. No outcome, frequency or length filter. Nested 64/256 dictionaries; original training and holdout words stay included.',
        'semantics':'Only dictionary changes. Same six generating keys, alphabets, observations, H1 L1-3, free selection, flat encoding/observed domains and hidden identities/lengths. No guidance, oracle word lengths, retries or longer timeout. Twelve new first-key fits; six saved hidden baselines reused after hash/request checks. Correct synthetic keys verify all positives. Compare exact frozen holdout predictions; dictionary-member counts use each arm dictionary and are not directly comparable. Engineered text, no negative controls or manuscript inference.',
        'prior_review':'Earlier reduced-vocabulary 64/128/256 study used another H2 fixture and ten-second budget; this freezes H1 varied generating codes and fourteen-letter alphabet.'}
    p={'identity':identity,'protocol':protocol,'dictionaries':{str(n):asdict(d) for n,d in dictionaries.items()},
        'added_word_provenance':provenance,'reused_baselines':reused,'cases':cases}
    write_json(OUT/'protocol.json',protocol);write_json(path,p);return source,p


def run():
    source,p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(c['id']==case['id'] for c in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        original=next(c for c in source['cases'] if c['id']==case['source_case'])
        print(case['id'],'hidden; timeout=5000ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(q));wall=perf_counter()-start;verify(q,result)
        if result['status']=='UNSAT':raise RuntimeError('Known positive returned UNSAT')
        row={'id':case['id'],'source_case':case['source_case'],'vocabulary_size':case['vocabulary_size'],
            'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        if result['status']=='SAT':row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],original['truth']['plaintext']['words']))
        row.update(evaluate(original,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    source,p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==12
    corpus=json.loads(CORPUS.read_text());base=HiddenRecoveryRequest.from_dict(source['cases'][0]['request'])
    dictionaries,provenance=vocabularies(base.dictionary,base.plaintext_alphabet,corpus['records'])
    assert digest(p['added_word_provenance'])==digest(provenance)
    assert all(digest(p['dictionaries'][str(n)])==digest(asdict(d)) for n,d in dictionaries.items())
    for case in p['cases']:
        original=next(c for c in source['cases'] if c['id']==case['source_case'])
        before=dict(original['request']);after=dict(case['request']);before.pop('dictionary');after.pop('dictionary');assert before==after
        q=HiddenRecoveryRequest.from_dict(case['request']);verify(q,original['truth'])
        row=next(c for c in r['cases'] if c['id']==case['id']);assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
        assert not row['result']['capacity'].get('oracle_word_lengths',False)
        if row['result']['status']=='SAT':assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],original['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in evaluate(original,q,row['result']).items())
    baseline=json.loads((small.OUT/'report.json').read_text())
    assert digest(p['reused_baselines'])==digest([a for a in baseline['arms'] if a['arm']=='hidden-words'])
    write_json(OUT/'validation.json',{'verified':True,'new_fits':12,'reused':6,'checks':['hashes','corpus selection and nested dictionaries','only dictionary field changes','unchanged generating witnesses','matched recovered witnesses','no oracle lengths','frozen scoring','exact baseline reuse']})
    print('Validated twelve expansion fits and six reused baselines')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared twelve dictionary-expansion fits; six baselines reused')
