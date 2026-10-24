"""Independent count reconstruction, probability, null and plan-chain checks."""
from collections import Counter,defaultdict
import json
import math
from statistics import mean
from benchmarks import long_range_calibration as m
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
        p=(globalcounts[target]+.5)/(sum(globalcounts.values())+2)
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
    strongest={}
    for name,c in cases.items():
        checked+=independent(c['train'],c['heldout'],c['score'])
        if 'renamed_score' in c:
            checked+=independent(m.transform(c['train']),m.transform(c['heldout']),c['renamed_score'])
            assert abs(c['score']['gain']-c['renamed_score']['gain'])<1e-12
        strongest[name]=max(c['score']['lag_gains'],key=c['score']['lag_gains'].get)
        result=stages[5]['cases'][name]
        for seed,null in zip(m.NULLS,result['nulls'],strict=True):
            pair=[]
            for split in ('train','heldout'):
                original=c[split]; shuffled=m.null_rows(original,f'{seed}:{split}')
                assert [(r['pos'],r['previous'],r['target']) for r in original]==[(r['pos'],r['previous'],r['target']) for r in shuffled]
                for d in m.LAGS:
                    assert Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in original)==Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in shuffled)
                pair.append(shuffled)
            checked+=independent(*pair,null)
            assert [r['baseline'] for r in null['rows']]==[r['baseline'] for r in c['score']['rows']]
        assert abs(result['excess']-(c['score']['gain']-mean(n['gain'] for n in result['nulls'])))<1e-12
    for kind in m.KINDS:
        expected={'gains':[cases[f'{kind}-{seed}']['score']['gain'] for seed in m.SEEDS],'excesses':[stages[5]['cases'][f'{kind}-{seed}']['excess'] for seed in m.SEEDS]}
        assert stages[6]['grouped'][kind]==expected
        assert stages[6]['weak'][kind]==stages[5]['cases'][f'weak-{kind}']['excess']
    report={'status':'passed','active_cases':len(cases),'refitted_null_cases':len(cases)*3,'independent_target_probability_checks':checked,'strongest_lags':strongest,'scope':'Independent tuple-count reconstruction of all baseline/lag/mixture losses; conditional null inventory and baseline invariance; alphabet relabeling; digests and summary. Does not establish power on historical corpora.'}
    write_json(m.OUT/'validation.json',report); print(report,flush=True)

if __name__=='__main__': validate()
