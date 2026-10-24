"""Delete the first one/two training types from frozen natural dictionaries."""
import argparse
from dataclasses import asdict,replace
import json
from pathlib import Path
from time import perf_counter
from benchmarks import natural_training_vocabulary as base
from benchmarks.l3_conflict import verify
from voynich_smt.data.corpus import digest,write_json
from voynich_smt.language.dictionary import WordDictionary
from voynich_smt.experiments.hidden import HiddenRecoveryRequest
from voynich_smt.solver.observed_codes import recover_observed_codes

OUT=Path('experiments/results/training-vocabulary-ablation')
COUNTS=(1,2)


def build(source,previous):
    if not previous['complete'] or previous['prepared_sha256']!=digest(source):raise ValueError('Unmatched baseline')
    cases=[]
    for original in source['cases']:
        positive=original if original['kind']=='positive' else next(c for c in source['cases'] if c['id']==original['positive_id'])
        types=list(dict.fromkeys(tuple(w) for w in positive['truth']['plaintext']['words']))
        old=next(r for r in previous['cases'] if r['id']==original['id'])
        if old['request_sha256']!=digest(original['request']):raise ValueError('Unmatched baseline request')
        for count in COUNTS:
            removed=types[:count]
            if len(removed)!=count:raise ValueError('Insufficient distinct training types')
            q=HiddenRecoveryRequest.from_dict(original['request'])
            members=q.dictionary.words
            if not set(removed)<=set(members):raise ValueError('Missing baseline training entries')
            q=replace(q,dictionary=WordDictionary(tuple(w for w in members if w not in removed)))
            case=dict(original,id=f"{original['id']}-delete-{count}",original_id=original['id'],request=asdict(q),
                      previous_256=old,removed_words=removed,removed_type_count=count,
                      removed_training_occurrences=sum(tuple(w) in removed for w in positive['truth']['plaintext']['words']),
                      training_type_count=len(types))
            if case['kind']=='positive':
                verify(HiddenRecoveryRequest.from_dict(original['request']),case['truth'])
                assert not set(removed)&set(q.dictionary.words)
                case['heldout_coverage']=[dict(c,in_dictionary=tuple(w) in set(q.dictionary.words)) for c,w in zip(original['heldout_coverage'],case['holdout_plaintext']['words'])]
            cases.append(case)
    return cases


def prepare():
    source=base.prepare();previous=json.loads((base.OUT/'report.json').read_text())
    paths=(Path(__file__),Path(base.__file__),Path('benchmarks/l3_conflict.py'),Path('benchmarks/natural_passage_replication.py'),
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
    protocol={'identity':identity,'planned_fits':len(cases),'removed_type_counts':COUNTS,'timeout_ms':5000,
        'selection':'First one and first two distinct true training word types in passage occurrence order. Delete those exact entries from each paired dictionary; no replacements or corpus refilling. Dictionary sizes 255/254; deletion sets nested. No length/frequency/solver/heldout-based selection, retries or longer budgets.',
        'scope':'Eight real-encryption fixtures and eight paired shuffles, each at two deletion levels. Only dictionary changes. Removed training types exclude the generating explanation; ablated real fixtures are not guaranteed SAT and UNSAT is permitted. SAT could be an alternative interpretation, not recovery of the full original plaintext. Frozen positive exact/novel and included/excluded predictions; control compatibility only. Source training assistance, structural holdout selection and same-source/profile correlations remain. UNKNOWN unresolved; UNSAT solver-reported without proof certificates. No manuscript-language inference.'}
    p={'identity':identity,'protocol':protocol,'cases':cases};write_json(OUT/'protocol.json',protocol);write_json(path,p);return p


def run():
    p=prepare();path=OUT/'report.json'
    r=json.loads(path.read_text()) if path.exists() else {'prepared_sha256':digest(p),'cases':[],'complete':False}
    if r['prepared_sha256']!=digest(p):raise ValueError('Checkpoint changed')
    for case in p['cases']:
        if any(a['id']==case['id'] for a in r['cases']):continue
        q=HiddenRecoveryRequest.from_dict(case['request']);print(case['id'],'timeout=5000ms',flush=True)
        start=perf_counter();result=asdict(recover_observed_codes(q));wall=perf_counter()-start;verify(q,result)
        row={'id':case['id'],'request_sha256':digest(asdict(q)),'result':result,'fit_wall_seconds':wall}
        if case['kind']=='positive' and result['status']=='SAT':
            row['training_exact_words']=sum(tuple(w)==tuple(t) for w,t in zip(result['plaintext']['words'],case['truth']['plaintext']['words']))
        row.update(base.evaluation(case,q,result));r['cases'].append(row);write_json(path,r)
        print(result['status'],f"solver={result['runtime_seconds']:.3f}s exact={row.get('exact_words')}",flush=True)
    r['complete']=True;write_json(path,r);return r


def validate():
    p=prepare();r=json.loads((OUT/'report.json').read_text());source=base.prepare();previous=json.loads((base.OUT/'report.json').read_text())
    cases=build(source,previous);assert digest(cases)==digest(p['cases'])
    assert r['complete'] and r['prepared_sha256']==digest(p) and len(r['cases'])==len(cases)
    assert len({a['id'] for a in r['cases']})==len(cases)
    for case in cases:
        original=next(c for c in source['cases'] if c['id']==case['original_id'])
        before=dict(original['request']);after=dict(case['request']);before.pop('dictionary');after.pop('dictionary')
        assert digest(before)==digest(after) and case['holdout']==original['holdout']
        q=HiddenRecoveryRequest.from_dict(case['request']);assert len(q.dictionary.words)==256-case['removed_type_count']
        assert not set(map(tuple,case['removed_words']))&set(q.dictionary.words)
        row=next(a for a in r['cases'] if a['id']==case['id']);assert row['request_sha256']==digest(asdict(q));verify(q,row['result'])
        if case['kind']=='positive' and row['result']['status']=='SAT':
            hits=sum(tuple(w)==tuple(t) for w,t in zip(row['result']['plaintext']['words'],case['truth']['plaintext']['words']))
            assert row['training_exact_words']==hits and hits<=24-case['removed_training_occurrences']
        assert all(digest(row[k])==digest(v) for k,v in base.evaluation(case,q,row['result']).items())
    write_json(OUT/'validation.json',{'verified':True,'cases':len(cases),'checks':['hashes/baseline matching','predetermined nested deletion','generating explanation excluded','dictionary-only changes','SAT witnesses','frozen scoring'], 'limitation':'UNSAT solver-reported; UNKNOWN unresolved.'})
    print('Validated training vocabulary ablation')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');parser.add_argument('--validate',action='store_true');a=parser.parse_args()
    if a.validate:validate()
    elif a.run:run()
    else:prepare();print('Frozen 32 ablated requests')
