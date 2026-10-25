"""Independent omission, fit, probability and paired-change audit."""
from benchmarks.grammar_training_sensitivity_iteration148 import *

def run():
    hc=pc=mc=0
    for name in ['design-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    for iteration in ['iteration142','iteration144']:
        for p,h in load(ROOT/iteration/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    split=load(ROOT/'iteration116/type-split.json');train=split['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];targets=set(load(ROOT/'iteration93/types.json')['candidates']);assert not set(train)&targets
    f=load(ROOT/'iteration142/training-features.json');lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};models=load(OUT/'models.json');assert set(models)=={'full',*train};assert models['full']==load(ROOT/'iteration142/models.json')['joint']['final']
    for omitted,m in models.items():
        if omitted=='full':continue
        tr=[w for w in train if w!=omitted];assert m['training']==tr and omitted not in tr;assert m['columns']==COLS
        x=np.array([[f[lookup[w]][c] for c in COLS] for w in tr]);assert np.allclose(x.mean(0),m['mean'],atol=1e-12) and np.allclose(x.std(0),m['scale'],atol=1e-12)
        re=fit_vector(f,tr,lookup,anchors,COLS);assert abs(re['loss']-m['loss'])<1e-8;assert np.allclose(re['weights'],m['weights'],atol=1e-6)
    pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');features=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json')
    for work,views in pred.items():
        assert views['full']==old[work+'/full']['joint']
        baseline={r['type']:r for r in views['full']}
        for name,rows in views.items():
            m=models[name];coef=np.array(m['weights'])[:,1]-np.array(m['weights'])[:,0];assert {r['type'] for r in rows}==set(baseline);flips=goodbad=badgood=0;movement=[]
            for r in rows:
                b=baseline[r['type']];assert all(r[k]==b[k] for k in ['type','opaque','n','sentences','supported']);x=np.array([features[work+'/full'][r['opaque']][c] for c in COLS]);x=(x-np.array(m['mean']))/np.array(m['scale']);p=1/(1+math.exp(-float(coef[0]+x@coef[1:])));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1;q=b['probabilities']['raw'];movement.append(abs(p-q))
                if (p>.5)!=(q>.5):
                    flips+=1;before=(q>.5)==(anchors[r['type']]=='CCONJ');goodbad+=int(before);badgood+=int(not before)
            s=summary[work][name];assert len(s['decision_flips'])==flips and s['correct_to_wrong']==goodbad and s['wrong_to_correct']==badgood;assert abs(s['mean_absolute_probability_change']-np.mean(movement))<1e-12;assert abs(s['maximum_absolute_probability_change']-max(movement))<1e-12
            q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);mm=s['metrics'];assert mm['n']==len(rows) and mm['correct']==int(((q>.5)==y).sum());assert abs(mm['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert mm['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
        print('audited',work,flush=True)
    assert summary==evaluate(pred,anchors,anchors)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,prior_manifests_verified=2,omission_models_retrained=13,probabilities_independently_replayed=pc,metric_groups_independently_checked=mc,full_baselines_matched=7,strict_target_exclusion=True,paired_changes_verified=True))
if __name__=='__main__':run()
