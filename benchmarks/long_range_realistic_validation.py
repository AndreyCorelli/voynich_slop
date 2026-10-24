"""Independent sparse-control likelihood, feature and source-boundary checks."""
from collections import Counter,defaultdict
import json
import math
from statistics import mean
from benchmarks import long_range_realistic as m
from voynich_smt.data.corpus import digest,write_json

def independent(train,held,record):
    # Tuple keys and independently rebuilt event counts.
    counts=defaultdict(Counter)
    for r in train:
        for key in ((),(r['pos'],),(r['pos'],r['previous'])):
            counts[key][r['target']]+=1
        for d,v in r['lags'].items(): counts[(d,r['pos'],r['previous'],v)][r['target']]+=1
    gains=[]; laggains=defaultdict(list); events=0
    for r,stored in zip(held,record['rows'],strict=True):
        target=r['target']; globalcounts=counts[()]
        p=(globalcounts[target]+.5)/(sum(globalcounts.values())+13)
        for key in ((r['pos'],),(r['pos'],r['previous'])):
            c=counts[key]; p=(c[target]+20*p)/(sum(c.values())+20)
        base=-math.log2(p); probabilities=[]
        assert abs(base-stored['baseline'])<1e-12; events+=1
        for d,v in r['lags'].items():
            c=counts[(d,r['pos'],r['previous'],v)]; q=(c[target]+20*p)/(sum(c.values())+20)
            loss=-math.log2(q); assert abs(loss-stored['lags'][d])<1e-12
            laggains[d].append(base-loss); probabilities.append(q); events+=1
        mixture=-math.log2(sum(probabilities)/7); assert abs(mixture-stored['mixture'])<1e-12
        gains.append(base-mixture); events+=1
    assert abs(mean(gains)-record['gain'])<1e-12
    for d,values in laggains.items(): assert abs(mean(values)-record['lag_gains'][d])<1e-12
    return events


def validate():
    prepared=m.prepare(); stages=[]; cases={}; checked=0
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(prepared)
        assert r['plan']['previous_sha256']==(digest(stages[-1]) if stages else None)
        stages.append(r)
        if 2<=i<=5: cases.update(r['cases'])
    for name,c in cases.items():
        oracle=name.startswith('oracle')
        for split,blocks in zip(('train','heldout'),c['blocks']):
            rebuilt=[]
            for b in blocks:
                assert len(b['words'])==32
                for i,w in enumerate(b['words']):
                    assert 3<=len(w)<=4 and set(w)<=set(m.ALPHABET)
                    if b['positions'][i]<8: continue
                    assert all(b['lines'][i-d]==b['lines'][i] for d in m.LAGS)
                    context=str(int(b['positions'][i]>=12))+':'+str(len(w))
                    if oracle: context+=':state'+str(b['states'][i])
                    rebuilt.append({'pos':context,'previous':b['words'][i-1][-1],'target':w[0],'lags':{str(d):b['words'][i-d][-1] for d in m.LAGS}})
            assert rebuilt==c[split]
        assert len(c['heldout'])==1424
        assert len(c['train'])==(2048 if name.startswith('large') else 512)
        checked+=independent(c['train'],c['heldout'],c['score'])
        result=stages[5]['cases'][name]
        for seed,null in zip(m.NULLS,result['nulls'],strict=True):
            pair=[]
            for split in ('train','heldout'):
                original=c[split]; shuffled=m.prior.null_rows(original,f'{seed}:{split}')
                assert [(r['pos'],r['previous'],r['target']) for r in original]==[(r['pos'],r['previous'],r['target']) for r in shuffled]
                for d in m.LAGS:
                    assert Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in original)==Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in shuffled)
                pair.append(shuffled)
            checked+=independent(*pair,null)
            assert [r['baseline'] for r in null['rows']]==[r['baseline'] for r in c['score']['rows']]
        assert abs(result['excess']-(c['score']['gain']-mean(n['gain'] for n in result['nulls'])))<1e-12
    nulls=stages[5]['cases']
    assert stages[6]['grouped']=={kind:[nulls[f'{kind}-{s}']['excess'] for s in m.SEEDS] for kind in m.KINDS}
    assert stages[6]['oracle']=={kind:[nulls[f'oracle-{kind}-{s}']['excess'] for s in m.SEEDS] for kind in ('state-iid','state-local')}
    assert stages[6]['large']=={kind:nulls[f'large-{kind}']['excess'] for kind in ('local','weak-lag4','state-local')}
    report={'status':'passed','active_cases':len(cases),'refitted_null_cases':len(cases)*3,'independent_probability_loss_checks':checked,'line_feature_reconstruction':True,'scope':'Independent tuple-count likelihoods, row reconstruction from words, null inventories/baseline invariance and digest/summary chain. Generator reused; no historical-source calibration.'}
    write_json(m.OUT/'validation.json',report); print(report,flush=True)

if __name__=='__main__': validate()
