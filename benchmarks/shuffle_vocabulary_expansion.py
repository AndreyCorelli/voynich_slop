"""Same twelve randomized controls with only dictionary enlarged to 256 words."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter

from benchmarks import varied_length_shuffle_controls as shuffles
from benchmarks import varied_length_vocabulary_ladder as ladder
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/shuffle-vocabulary-expansion')


def prepare():
    source=shuffles.prepare();previous=json.loads((shuffles.OUT/'report.json').read_text())
    original,vocabulary=ladder.prepare();positives=json.loads((ladder.OUT/'report.json').read_text())
    if not previous['complete'] or previous['prepared_sha256']!=digest(source):raise ValueError('Unmatched shuffle baseline')
    if not positives['complete'] or positives['prepared_sha256']!=digest(vocabulary):raise ValueError('Unmatched positive ladder')
    identity={'source_sha256':digest(source),'previous_report_sha256':digest(previous),'ladder_sha256':digest(vocabulary),'positive_report_sha256':digest(positives),
        'code_sha256':{str(p):digest(p.read_text()) for p in
            (Path(__file__),Path('benchmarks/varied_length_shuffle_controls.py'),Path('src/voynich_smt/language/dictionary.py'),
             Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('src/voynich_smt/solver/recovery.py'),
             Path('src/voynich_smt/solver/observed_codes.py'),Path('benchmarks/frozen_key_holdout.py'))}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen sources or code changed')
        return p
    dictionary=WordDictionary(tuple(tuple(w) for w in vocabulary['dictionaries']['256']['words']))
    cases=[]
    for control in source['controls']:
        base=HiddenRecoveryRequest.from_dict(control['request']);q=replace(base,dictionary=dictionary)
        old=next(c for c in previous['controls'] if c['id']==control['id'])
        if old['request_sha256']!=digest(asdict(base)):raise ValueError('Unmatched 64-word control')
        positive64=next(c for c in vocabulary['cases'] if c['id']==control['positive_id'])
        positive256=next(c for c in positives['cases'] if c['source_case']==positive64['source_case'] and c['vocabulary_size']==256)
        cases.append(dict(control,id=control['id']+'-vocab-256',original_control_id=control['id'],
            request=asdict(q),previous_64=old,positive_256=positive256))
    protocol={'identity':identity,'planned_fits':len(cases),'vocabulary_size':256,'timeout_ms_per_fit':5000,
        'scope':'Exact same twelve shuffled training and held-out ciphertexts and seeds; only dictionary changes to the frozen 256-word ladder. Same alphabets, H1 L1-3, free selection, flat observed-domain recovery and timeout. Previous control and positive rows reused after hash/request checks. No reshuffling, oracle, score tuning or retries. SAT means compatibility; UNKNOWN unresolved; UNSAT solver-reported. SAT control keys frozen-scored on same shuffled continuation without generating-plaintext accuracy claims.'}
    p={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(c['id']==case['id'] for c in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request'])
        print(case['id'],'timeout=5000ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(q));wall=perf_counter()-start;verify(q,result)
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        row.update(shuffles.prediction(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s",f"holdout_dictionary={row.get('prediction',{}).get('dictionary_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text())
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==len(p['cases'])
    source=shuffles.prepare();old=json.loads((shuffles.OUT/'report.json').read_text())
    original,vocabulary=ladder.prepare();positives=json.loads((ladder.OUT/'report.json').read_text())
    for case in p['cases']:
        previous=next(c for c in source['controls'] if c['id']==case['original_control_id'])
        before=dict(previous['request']);after=dict(case['request']);before.pop('dictionary');after.pop('dictionary');assert before==after
        assert case['holdout']==previous['holdout'] and case['seed']==previous['seed'] and case['construction']==previous['construction']
        assert case['request']['dictionary']==vocabulary['dictionaries']['256']
        assert case['previous_64']==next(c for c in old['controls'] if c['id']==previous['id'])
        positive64=next(c for c in vocabulary['cases'] if c['id']==previous['positive_id'])
        assert case['positive_256']==next(c for c in positives['cases'] if c['source_case']==positive64['source_case'] and c['vocabulary_size']==256)
        q=HiddenRecoveryRequest.from_dict(case['request']);row=next(c for c in r['cases'] if c['id']==case['id'])
        assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
        assert not row['result']['capacity'].get('oracle_word_lengths',False)
        assert all(digest(row[k])==digest(v) for k,v in shuffles.prediction(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':len(r['cases']),'checks':['hashes','dictionary-only changes','unchanged control/holdout/seed','matched cached controls/positives','SAT witness verification','frozen continuation scoring'], 'limitation':'UNSAT solver-reported without independent proof certificates; UNKNOWN remains unresolved.'})
    print('Validated unchanged shuffles at 256 words')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Prepared unchanged controls at 256 words')
