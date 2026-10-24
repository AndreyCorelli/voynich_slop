"""Independent hierarchical likelihood reconstruction and training-selection audit."""
from collections import Counter,defaultdict
import json
import math
from statistics import mean
from benchmarks import long_range_pooled as m
from benchmarks.long_range_realistic_validation import independent as old_independent
from voynich_smt.data.corpus import digest,write_json


def independent(train,held,record,spec):
    strength,weight=spec; counts=defaultdict(Counter); pooled=defaultdict(Counter)
    for r in train:
        for key in ((),(r['pos'],),(r['pos'],r['previous'])): counts[key][r['target']]+=1
        for d,v in r['lags'].items():
            pooled[(d,v)][r['target']]+=1; counts[(d,r['pos'],r['previous'],v)][r['target']]+=1
    gains=[]; losses=[]; laggains=defaultdict(list); checked=0
    for r,stored in zip(held,record['rows'],strict=True):
        target=r['target']; c=counts[()]; p=(c[target]+.5)/(sum(c.values())+13)
        for key in ((r['pos'],),(r['pos'],r['previous'])):
            c=counts[key]; p=(c[target]+20*p)/(sum(c.values())+20)
        base=-math.log2(p); assert abs(base-stored['baseline'])<1e-12; checked+=1; values=[]
        for d,v in r['lags'].items():
            c=pooled[(d,v)]; pool=(c[target]+strength*p)/(sum(c.values())+strength)
            c=counts[(d,r['pos'],r['previous'],v)]; fine=(c[target]+strength*pool)/(sum(c.values())+strength)
            q=(1-weight)*p+weight*fine; loss=-math.log2(q)
            assert abs(loss-stored['lags'][d])<1e-12; values.append(q); laggains[d].append(base-loss); checked+=1
        loss=-math.log2(sum(values)/7); assert abs(loss-stored['mixture'])<1e-12
        gains.append(base-loss); losses.append(loss); checked+=1
    assert abs(mean(gains)-record['gain'])<1e-12 and abs(mean(losses)-record['loss'])<1e-12
    for d,values in laggains.items(): assert abs(mean(values)-record['lag_gains'][d])<1e-12
    return checked


def validate():
    prepared=m.prepare(); reports=[]; cases={}; checked=0
    assert not set(m.CALIBRATION)&set(m.SEEDS)
    assert not (set(m.CALIBRATION)|set(m.SEEDS))&set(m.prior.SEEDS)
    for i in range(1,8):
        r=json.loads((m.OUT/f'iteration-{i}.json').read_text())
        assert r['plan']==json.loads((m.OUT/f'plan-{i}.json').read_text())
        assert r['plan']['prepared_sha256']==digest(prepared)
        assert r['plan']['previous_sha256']==(digest(reports[-1]) if reports else None)
        reports.append(r)
        if 3<=i<=5: cases.update(r['cases'])
    calibration=reports[1]
    for name,c in calibration['calibration'].items():
        kind,seed=name.rsplit('-',1); blocks=m.prior.generate(int(seed),kind,'train')
        assert c['train']==m.prior.rows(blocks[:16]) and c['validation']==m.prior.rows(blocks[16:])
        for spec in m.CANDIDATES: checked+=independent(c['train'],c['validation'],c['scores'][f'{spec[0]}-{spec[1]}'],spec)
    losses={f'{s}-{w}':mean(c['scores'][f'{s}-{w}']['loss'] for c in calibration['calibration'].values()) for s,w in m.CANDIDATES}
    assert losses==calibration['cv_losses']
    spec=list(min(m.CANDIDATES,key=lambda s:(losses[f'{s[0]}-{s[1]}'],s)))
    assert spec==calibration['selected']==reports[6]['selected']
    for name,c in cases.items():
        for split,blocks in zip(('train','heldout'),c['blocks']):
            rebuilt=[]
            for b in blocks:
                for i,w in enumerate(b['words']):
                    if b['positions'][i]<8: continue
                    assert all(b['lines'][i-d]==b['lines'][i] for d in m.prior.LAGS)
                    rebuilt.append({'pos':str(int(b['positions'][i]>=12))+':'+str(len(w)),'previous':b['words'][i-1][-1],'target':w[0],'lags':{str(d):b['words'][i-d][-1] for d in m.prior.LAGS}})
            assert rebuilt==c[split]
        assert len(c['train'])==512 and len(c['heldout'])==1424
        checked+=independent(c['train'],c['heldout'],c['pooled'],spec)
        checked+=old_independent(c['train'],c['heldout'],c['old'])
        for seed,index in zip(m.NULLS,range(3)):
            pair=[]
            for split in ('train','heldout'):
                original=c[split]; shuffled=m.prior.prior.null_rows(original,f'{seed}:{split}')
                assert [(r['pos'],r['previous'],r['target']) for r in original]==[(r['pos'],r['previous'],r['target']) for r in shuffled]
                for d in m.prior.LAGS:
                    assert Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in original)==Counter((r['pos'],r['previous'],r['lags'][str(d)]) for r in shuffled)
                pair.append(shuffled)
            result=reports[5]['cases'][name]
            checked+=independent(*pair,result['pooled']['nulls'][index],spec)
            checked+=old_independent(*pair,result['old']['nulls'][index])
            for model in ('old','pooled'):
                assert [r['baseline'] for r in result[model]['nulls'][index]['rows']]==[r['baseline'] for r in c[model]['rows']]
        for model in ('old','pooled'):
            result=reports[5]['cases'][name][model]
            assert abs(result['excess']-(c[model]['gain']-mean(n['gain'] for n in result['nulls'])))<1e-12
    grouped={kind:{model:[reports[5]['cases'][f'{kind}-{seed}'][model]['excess'] for seed in m.SEEDS] for model in ('old','pooled')} for kind in m.prior.KINDS}
    assert grouped==reports[6]['grouped']
    weak=min(grouped['weak-lag4']['pooled']); control=max(v for kind in ('independent','local','state-iid','state-local') for v in grouped[kind]['pooled'])
    assert reports[6]['criterion']['min_weak']==weak and reports[6]['criterion']['max_control']==control
    assert reports[6]['criterion']['separated']==(weak>control)
    result={'status':'passed','evaluation_cases':len(cases),'model_evaluations_with_nulls':len(cases)*8,'calibration_candidate_scores':len(calibration['calibration'])*6,'independent_probability_loss_checks':checked,'training_only_selection':True,'scope':'Independent pooled and old likelihoods including calibration; selected-loss arithmetic, line features, conditional null inventories, baseline invariance and plan summaries. Generator reused; three evaluation seeds do not estimate power.'}
    write_json(m.OUT/'validation.json',result); print(result,flush=True)

if __name__=='__main__': validate()
