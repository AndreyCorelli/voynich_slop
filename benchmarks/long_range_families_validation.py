"""Independent frozen-estimator audit on new mechanism-family controls."""
from collections import Counter
import json
from statistics import mean
from benchmarks import long_range_families as m
from benchmarks.long_range_pooled_validation import independent
from voynich_smt.data.corpus import digest,write_json


def validate():
    p=m.prepare(); reports=[]; cases={}; checked=operations=0
    selection=json.loads((m.estimator.OUT/'iteration-2.json').read_text())
    assert p['spec']==selection['selected'] and p['selection_sha256']==digest(selection)
    assert not set(m.SEEDS)&(set(m.estimator.SEEDS)|set(m.estimator.CALIBRATION))
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(p) and r['plan']['selection'] is False
        assert r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None)
        reports.append(r)
        if 2<=i<=5: cases.update(r['cases'])
    for name,c in cases.items():
        key=c['mapping']; assert set(key)==set(m.estimator.prior.ALPHABET)==set(key.values())
        for split,blocks in zip(('train','heldout'),c['blocks']):
            rebuilt=[]
            for b in blocks:
                for i,w in enumerate(b['words']):
                    operation=b['operations'][i]
                    if operation.startswith('mapped'):
                        lag=int(operation[6:]); assert b['positions'][i]>=lag and b['lines'][i]==b['lines'][i-lag]
                        assert w[0]==key[b['words'][i-lag][-1]]; operations+=1
                    if b['positions'][i]<8: continue
                    assert all(b['lines'][i-d]==b['lines'][i] for d in m.estimator.prior.LAGS)
                    context=str(int(b['positions'][i]>=12))+':'+str(len(w))
                    if c.get('oracle')=='state': context+=':state'+str(b['states'][i])
                    if c.get('oracle')=='phase': context+=':phase'+str(b['phases'][i])
                    rebuilt.append({'pos':context,'previous':b['words'][i-1][-1],'target':w[0],'lags':{str(d):b['words'][i-d][-1] for d in m.estimator.prior.LAGS}})
            assert rebuilt==c[split]
        assert len(c['train'])==512 and len(c['heldout'])==1424
        checked+=independent(c['train'],c['heldout'],c['score'],p['spec'])
        result=reports[5]['cases'][name]
        for seed,record in zip(m.NULLS,result['nulls'],strict=True):
            pair=[]
            for split in ('train','heldout'):
                original=c[split]; shuffled=m.estimator.prior.prior.null_rows(original,f'{seed}:{split}')
                assert [(r['pos'],r['previous'],r['target']) for r in original]==[(r['pos'],r['previous'],r['target']) for r in shuffled]
                for d in m.estimator.prior.LAGS:
                    assert Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in original)==Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in shuffled)
                pair.append(shuffled)
            checked+=independent(*pair,record,p['spec'])
            assert [r['baseline'] for r in record['rows']]==[r['baseline'] for r in c['score']['rows']]
        assert abs(result['excess']-(c['score']['gain']-mean(n['gain'] for n in result['nulls'])))<1e-12
    nulls=reports[5]['cases']
    grouped={k:[nulls[f'{k}-{s}']['excess'] for s in m.SEEDS] for k in m.KINDS}
    oracle={k:[nulls[f'oracle-{k}-{s}']['excess'] for s in m.SEEDS] for k in ('persistent-state','template')}
    assert reports[6]['grouped']==grouped and reports[6]['oracle']==oracle
    minimum=min(grouped['weak-mapped-lag4']); maximum=max(v for k in ('independent','mapped-local','persistent-state','template') for v in grouped[k])
    assert reports[6]['criterion']=={'min_weak':minimum,'max_control':maximum,'separated':minimum>maximum}
    report={'status':'passed','active_cases':len(cases),'refitted_null_cases':len(cases)*3,'independent_probability_loss_checks':checked,'mapped_copy_events_checked':operations,'scope':'Independent hierarchical likelihood reconstruction, mapping operations, line/oracle features, null invariants, frozen selection and plan/summary chain. Generator and synthetic family assumptions reused.'}
    write_json(m.OUT/'validation.json',report); print(report,flush=True)

if __name__=='__main__': validate()
