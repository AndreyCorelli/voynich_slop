"""Independent hybrid identity, refit and exact attribution audit."""
from benchmarks.grammar_siue_attribution_iteration151 import *

def run():
    hc=pc=mc=0
    for name in ['design-freeze','hybrids-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    for p,h in load(ROOT/'iteration150/verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    train=load(ROOT/'iteration116/type-split.json')['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};source=load(ROOT/'iteration150/features.json');hybrids=load(OUT/'hybrids.json');models=load(OUT/'models.json');siue=lookup['siue'];changed=[w for w in train if source['full'][lookup[w]]!=source['2'][lookup[w]]];assert changed==['siue'];assert not set(train)&set(load(ROOT/'iteration93/types.json')['candidates'])
    for name in ['focal_only','others_only']:
        for w,i in lookup.items():
            use_changed=(w=='siue') if name=='focal_only' else (w!='siue');assert hybrids[name][i]==source['2' if use_changed else 'full'][i]
        re=fit_vector(hybrids[name],train,lookup,anchors,COLS);assert re==models[name]
    assert models['focal_only']==models['middle_perturbed'];assert models['others_only']==models['full'];pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');cached=load(ROOT/'iteration144/features.json')
    for w,views in pred.items():
        assert views['focal_only']==views['middle_perturbed'] and views['others_only']==views['full']
        for name,rows in views.items():
            m=models[name];coef=np.array(m['weights'])[:,1]-np.array(m['weights'])[:,0]
            for r in rows:
                f=cached[w+'/full'][r['opaque']];x=(np.array([f[c] for c in COLS])-np.array(m['mean']))/np.array(m['scale']);p=1/(1+math.exp(-float(coef[0]+x@coef[1:])));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
            q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);s=summary[w][name]['metrics'];assert s['correct']==int(((q>.5)==y).sum());assert abs(s['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert s['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
    assert summary==evaluate(pred,anchors,{name:'feature_intervention' for name in models})
    save(OUT/'audit.json',dict(input_hashes_verified=hc,prior_manifest_verified=True,hybrid_models_retrained=2,training_vectors_checked=13,changed_training_vectors=['siue'],exact_hybrid_model_identities=True,probabilities_independently_replayed=pc,metric_groups_independently_checked=mc,exact_probability_attribution_all7texts=True))
if __name__=='__main__':run()
