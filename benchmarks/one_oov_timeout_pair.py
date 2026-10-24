"""Fixed 60-second replay pair from timed-out one-OOV natural cases."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter
from benchmarks import one_oov_calibration as source_benchmark
from benchmarks import natural_training_vocabulary as base
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.oov_recovery import recover_oov

OUT=Path('experiments/results/one-oov-60s-pair')
def verify_oov(q,result):
    if result['status']!='SAT':return
    words=tuple(tuple(w) for w in result['plaintext']['words'])
    missing=tuple(w for w in words if w not in q.dictionary.words)
    if len(missing)>1:raise RuntimeError('OOV budget exceeded')
    # Reuse independent cipher/selection verifier after explicitly checking budget.
    maximum=q.max_word_length or max(map(len,q.dictionary.words))
    verify(replace(q,dictionary=WordDictionary(q.dictionary.words+tuple(dict.fromkeys(missing))),max_word_length=maximum),result)


PAIR=('latin-2-fixed-two-delete-1','latin-2-fixed-two-shuffle-delete-1')


def build(source,previous):
    if not previous['complete'] or previous['prepared_sha256']!=digest(source):raise ValueError('Unmatched baseline')
    cases=[]
    for case_id in PAIR:
        original=next(c for c in source['cases'] if c['id']==case_id)
        old=next(r for r in previous['cases'] if r['id']==case_id)
        if old['result']['status']!='UNKNOWN' or old['request_sha256']!=digest(original['request']):raise ValueError('Expected matched timeout')
        q=replace(HiddenRecoveryRequest.from_dict(original['request']),timeout_ms=60000)
        cases.append(dict(original,request=asdict(q),previous_5s=old))
    return cases


def prepare():
    source=source_benchmark.prepare();previous=json.loads((source_benchmark.OUT/'report.json').read_text())
    paths=(Path(__file__),Path(source_benchmark.__file__),Path(base.__file__),Path('src/voynich_smt/solver/oov_recovery.py'),Path('benchmarks/l3_conflict.py'),Path('benchmarks/natural_passage_replication.py'),
           Path('benchmarks/public_length_calibration.py'),Path('benchmarks/frozen_key_holdout.py'),
           Path('src/voynich_smt/solver/recovery.py'),Path('src/voynich_smt/solver/observed_codes.py'),
           Path('src/voynich_smt/solver/dictionary_encoding.py'),Path('src/voynich_smt/language/dictionary.py'))
    identity={'source_sha256':digest(source),'baseline_report_sha256':digest(previous),'code_sha256':{str(p):digest(p.read_text()) for p in paths}}
    path=OUT/'prepared.json'
    if path.exists():
        p=json.loads(path.read_text())
        if p['identity']!=identity:raise ValueError('Frozen inputs or code changed')
        return p
    cases=build(source,previous)
    protocol={'identity':identity,'planned_fits':2,'timeout_ms':60000,'max_oov_word_occurrences':1,
        'selection':'Fixed Latin passage 2 fixed-two positive and paired shuffle, both previously UNKNOWN at 5 seconds. First timed-out positive in frozen source order. Only timeout changes to 60 seconds. No retries, replacement cases, new keys or tuning.',
        'scope':'Same public inputs, dictionary, one unknown occurrence, alphabets and encoding. Positive generating witness verified. First SAT key frozen-scored; shuffle compatibility only. Preserve UNKNOWN. This is a bounded performance check on one correlated pair, not population discrimination or manuscript inference.'}
    p={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(a['id']==case['id'] for a in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request']);print(case['id'],'timeout=60000ms',flush=True)
        start=perf_counter();result=asdict(recover_oov(q,1));wall=perf_counter()-start;verify_oov(q,result)
        if case['kind']=='positive' and result['status']=='UNSAT':raise RuntimeError('Relaxed generating positive UNSAT')
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        if case['kind']=='positive' and result['status']=='SAT':
            row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
        if result['status']=='SAT':row['oov_training_positions']=[i for i,w in enumerate(result['plaintext']['words']) if tuple(w) not in q.dictionary.words]
        row.update(base.evaluation(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text());source=source_benchmark.prepare();previous=json.loads((source_benchmark.OUT/'report.json').read_text())
    cases=build(source,previous);assert digest(cases)==digest(p['cases'])
    for case in cases:
        original=next(c for c in source['cases'] if c['id']==case['id'])
        before=dict(original['request']);after=dict(case['request'])
        assert before.pop('timeout_ms')==5000 and after.pop('timeout_ms')==60000
        assert digest(before)==digest(after) and case['holdout']==original['holdout']
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==len(cases)
    assert len({a['id'] for a in r['cases']})==len(cases)
    for case in cases:
        q=HiddenRecoveryRequest.from_dict(case['request'])
        row=next(a for a in r['cases'] if a['id']==case['id']);assert row['request_sha256']==digest(asdict(q));verify_oov(q,row['result'])
        if case['kind']=='positive':
            verify_oov(q,case['truth']);assert row['result']['status']!='UNSAT'
            if row['result']['status']=='SAT':
                assert row['training_exact_words']==sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
        if row['result']['status']=='SAT':
            assert row['oov_training_positions']==[i for i,w in enumerate(row['result']['plaintext']['words']) if tuple(w) not in q.dictionary.words]
        assert all(digest(row[k])==digest(v) for k,v in base.evaluation(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':len(cases),'checks':['hashes/baseline matching','unchanged ablated requests','generating explanation restored','one actual OOV occurrence','SAT witnesses','frozen scoring'], 'limitation':'UNSAT solver-reported; UNKNOWN unresolved.'})
    print('Validated one-OOV 60-second pair')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen 60-second replay pair')
