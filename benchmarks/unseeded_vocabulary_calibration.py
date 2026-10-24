"""Independent prefix dictionaries on new natural passages, one-OOV recovery."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter
from benchmarks import natural_passage_replication as natural
from benchmarks.one_oov_calibration import verify_oov
from benchmarks.l3_conflict import verify
from voynich_smt.cipher.base import Bounds
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.models.alphabet import Alphabet
from voynich_smt.models.text import Text
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.oov_recovery import recover_oov

OUT=Path('experiments/results/unseeded-vocabulary-calibration')


def dictionary_from_prefix(records,alphabet,allowed,size=256):
    words=[];provenance=[];seen=set()
    for i,r in enumerate(records[:len(records)//2]):
        w=tuple(r['tokens'])
        if r.get('excluded_reason') is not None or not w or w not in allowed or not set(w)<=set(alphabet.symbols) or w in seen:continue
        seen.add(w);words.append(w);provenance.append({'record_index':i,'word':w})
        if len(words)==size:return WordDictionary(tuple(words)),provenance
    raise ValueError('Insufficient prefix vocabulary; no broadening')


def coverage(plain,held,dictionary):
    members=set(dictionary.words);maximum=max(map(len,dictionary.words))
    missing=[i for i,w in enumerate(plain.words) if w not in members]
    length_fail=[i for i,w in enumerate(plain.words) if not 1<=len(w)<=maximum]
    return {'missing_training_positions':missing,'missing_training_types':sorted({plain.words[i] for i in missing}),
            'training_words':len(plain.words),'missing_training_occurrences':len(missing),
            'outside_public_length_positions':length_fail,'generating_explanation_admitted':len(missing)<=1 and not length_fail,
            'heldout_dictionary_members':[w in members for w in held.words]}


def build(records,templates):
    passages={};cases=[]
    for lang,stream in records.items():
        template=templates[lang]['request'];alphabet=Alphabet(tuple(template['plaintext_alphabet']['symbols']))
        allowed=set(map(tuple,template['dictionary']['words']))
        dictionary,provenance=dictionary_from_prefix(stream,alphabet,allowed)
        prior=natural.selections(stream,allowed)[-1][0]
        start,plain,held_plain,block=natural.select_passage(stream,allowed,prior+natural.TRAIN+natural.HELD)
        audit=coverage(plain,held_plain,dictionary)
        passages[lang]={'record_start':start,'record_end_exclusive':start+30,'source_records':block,
            'plaintext':asdict(plain),'holdout_plaintext':asdict(held_plain),'dictionary':asdict(dictionary),
            'alphabet':asdict(alphabet),'dictionary_provenance':provenance,'coverage':audit}
        for profile in natural.PROFILES:
            encoder=natural.key(alphabet.symbols,tuple('uvwxyz'),profile,natural.KEY_SEED)
            train=encoder.encode(plain,(0,)*plain.size);held=encoder.encode(held_plain,(0,)*held_plain.size)
            q=HiddenRecoveryRequest(train,alphabet,Alphabet(tuple('uvwxyz')),Bounds('verbose',1,1,3),dictionary,timeout_ms=60000)
            truth={'status':'SAT','verified':True,'encoder':asdict(encoder),'plaintext':asdict(plain),'choices':[0]*plain.size,'nulls':[]}
            # Cipher correctness regardless of dictionary coverage; not a legal-model claim.
            extra=tuple(w for w in dict.fromkeys(plain.words) if w not in dictionary.words)
            verify(replace(q,dictionary=WordDictionary(dictionary.words+extra),max_word_length=max(max(map(len,dictionary.words)),max(map(len,plain.words)))),truth)
            if audit['generating_explanation_admitted']:verify_oov(q,truth)
            case_id=f'{lang}-{profile}'
            cases.append({'id':case_id,'kind':'positive','language':lang,'profile':profile,'request':asdict(q),
                'truth':truth,'holdout':asdict(held),'holdout_plaintext':asdict(held_plain),'coverage':audit})
            full=Text(train.words+held.words);shuffled,generation=natural.typewise_shuffle(full,natural.SHUFFLE_SEED)
            invariants=natural.diagnostics(full,shuffled)
            assert all(invariants[k] for k in ('word_length_sequence_preserved','glyph_counts_per_word_preserved','exact_repetition_partition_preserved'))
            if shuffled.words[:24]==train.words:raise ValueError('Unchanged training shuffle; stop')
            cq=replace(q,ciphertext=Text(shuffled.words[:24]))
            cases.append({'id':case_id+'-shuffle','kind':'shuffle','language':lang,'profile':profile,'request':asdict(cq),
                'holdout':asdict(Text(shuffled.words[24:])),'construction':generation,'invariants':invariants})
    return passages,cases


def prepare():
    records,templates,sources=natural.load_sources();prior=natural.prepare()
    paths=(Path(__file__),Path(natural.__file__),Path('benchmarks/one_oov_calibration.py'),Path('src/voynich_smt/solver/oov_recovery.py'),Path('benchmarks/l3_conflict.py'),Path('benchmarks/frozen_key_holdout.py'),Path('benchmarks/public_length_calibration.py'))
    identity={'sources':sources,'previous_passages_sha256':digest(prior),'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen source/code changed')
        return p
    passages,cases=build(records,templates)
    protocol={'identity':identity,'planned_fits':8,'timeout_ms':60000,'dictionary_size':256,'max_oov_occurrences':1,
        'selection':'Dictionary first 256 distinct corrected eligible source words in first-half record order, fixed source alphabet; no training or heldout word reservation. One next eligible contiguous 24+6 passage after each prior replication block, no coverage-based passage selection. Profiles fixed-two/mixed-one-two-three, key seed4501, shuffle4502. Freeze all requests/coverage before solving; no retries.',
        'scope':'Dictionary comes from disjoint earlier source portion but same source, not external genre validation. Source alphabet and corrected full-source inventory remain available; structural selection sees heldout plaintext for novelty/letter coverage. Missing occurrence and public length coverage audited separately. Inadmissible generating explanation is coverage failure; SAT may be alternative interpretation and UNSAT does not refute real encryption. Admitted explanation permits recovery evaluation. First keys frozen-scored, controls compatibility only. Correlated passages/profiles, UNKNOWN unresolved, UNSAT solver-reported; no manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'passages':passages,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def evaluation(case,q,result):
    return natural.evaluate_positive(case,q,result) if case['kind']=='positive' else natural.control_prediction(case,q,result)


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for c in p['cases']:
        if any(a['id']==c['id'] for a in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(c['request']);print(c['id'],'timeout=60000ms',flush=True)
        start=perf_counter();result=asdict(recover_oov(q,1));wall=perf_counter()-start;verify_oov(q,result)
        if c['kind']=='positive' and c['coverage']['generating_explanation_admitted'] and result['status']=='UNSAT':raise RuntimeError('Admitted generating positive UNSAT')
        row={'id':c['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        if c['kind']=='positive':
            row['coverage_status']='ADMITTED' if c['coverage']['generating_explanation_admitted'] else 'GENERATING_EXPLANATION_EXCLUDED'
            if result['status']=='SAT':row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],c['truth']['plaintext']['words']))
        row.update(evaluation(c,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text());records,templates,_=natural.load_sources()
    passages,cases=build(records,templates)
    assert digest(passages)==digest(p['passages']) and digest(cases)==digest(p['cases'])
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==len(cases) and len({a['id'] for a in r['cases']})==len(cases)
    for c in cases:
        q=HiddenRecoveryRequest.from_dict(c['request']);row=next(a for a in r['cases'] if a['id']==c['id'])
        assert row['request_sha256']==digest(asdict(q));verify_oov(q,row['result'])
        if c['kind']=='positive':
            assert row['coverage_status']==('ADMITTED' if c['coverage']['generating_explanation_admitted'] else 'GENERATING_EXPLANATION_EXCLUDED')
            if row['result']['status']=='SAT':assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],c['truth']['plaintext']['words']))
        assert all(digest(row[k])==digest(v) for k,v in evaluation(c,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':len(cases),'checks':['source/code hashes','independent prefix dictionaries','new contiguous passages','coverage audits','generating cipher checks','shuffle reconstruction','SAT witnesses','frozen scores'],'limitation':'Coverage failure not recovery failure; UNSAT solver-reported.'})
    print('Validated unseeded natural vocabulary calibration')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:
        p=prepare()
        for lang,passage in p['passages'].items():print(lang,passage['record_start'],passage['coverage'])
