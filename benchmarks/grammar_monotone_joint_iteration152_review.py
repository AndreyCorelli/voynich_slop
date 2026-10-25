"""Independent binary objective/KKT checks and all fixed-panel replay."""
from benchmarks.grammar_monotone_joint_iteration152 import *
from scipy.special import expit

def run():
    hc=pc=mc=0
    for name in ['design-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    split=load(ROOT/'iteration116/type-split.json');train=split['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};assert not set(train)&set(load(ROOT/'iteration93/types.json')['candidates']);original=load(ROOT/'iteration142/training-features.json');focal=load(ROOT/'iteration150/features.json');models=load(OUT/'models.json');oof=load(OUT/'oof.json');maxloss=0.;maxkkt=0.
    assert set(models)=={'full',*[f'oof{k}' for k in range(3)],*['omit/'+w for w in train],*['motif/'+str(k) for k in range(1,8)]}
    for name,m in models.items():
        held=[w for w in train if split['oof_folds'][w]==int(name[-1])] if name.startswith('oof') else [name[5:]] if name.startswith('omit/') else [];tr=[w for w in train if w not in held];assert m['training']==tr;f=focal[name[6:]] if name.startswith('motif/') else original;raw=np.array([[f[lookup[w]][c] for c in COLS] for w in tr]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;assert np.allclose(mean,m['mean']) and np.allclose(scale,m['scale']);x=np.column_stack([np.ones(len(tr)),(raw-mean)/scale]);y=np.array([anchors[w]=='CCONJ' for w in tr],dtype=int);counts=np.bincount(y,minlength=2);mass=np.array([.5/counts[v] for v in y]);ww=np.array(m['weights']);assert np.allclose(ww[:,0],-ww[:,1]);beta=ww[:,1]-ww[:,0];assert np.all(beta[1:]>=0)
        def objective(b):
            z=x@b;return float(mass@(np.logaddexp(0,z)-y*z)+.00025*(b@b)),x.T@(mass*(expit(z)-y))+.0005*b
        loss,g=objective(beta);assert abs(loss-m['loss'])<1e-10;viol=max(abs(g[0]),*[abs(g[j]) if beta[j]>1e-7 else max(0.,-g[j]) for j in [1,2]]);maxkkt=max(maxkkt,viol);assert viol<2e-6
        re=minimize(objective,np.zeros(3),jac=True,method='SLSQP',bounds=[(None,None),(0,None),(0,None)],options=dict(maxiter=1000,ftol=1e-12));assert re.success;maxloss=max(maxloss,abs(re.fun-loss));assert abs(re.fun-loss)<1e-7
        for w in held if name.startswith('oof') else []:assert abs(predict_vector(f[lookup[w]],m)-oof[w])<1e-12
    pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');om=load(ROOT/'iteration148/predictions.json');fp=load(ROOT/'iteration150/predictions.json')
    for w,views in pred.items():
        assert len(views)==21
        for name,arms in views.items():
            expected=old[w+'/full']['joint'] if name=='full' else om[w][name[5:]] if name.startswith('omit/') else fp[w][name[6:]];assert arms['unconstrained']==expected;m=models[name];ww=np.array(m['weights']);beta=ww[:,1]-ww[:,0]
            for arm,rows in arms.items():
                if arm=='constrained':
                    for r in rows:
                        f=cached[w+'/full'][r['opaque']];x=(np.array([f[c] for c in COLS])-m['mean'])/m['scale'];p=float(expit(beta[0]+x@beta[1:]));assert abs(p-r['probabilities']['raw'])<1e-10;pc+=1
                q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);mm=summary[w][name][arm];assert mm['correct']==int(((q>.5)==y).sum());assert abs(mm['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert mm['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
    source=load(OUT/'source-summary.json')
    for name,rr in [('constrained',oof),('unconstrained',load(ROOT/'iteration142/oof-probabilities.json')['joint'])]:assert source[name]==metrics([dict(type=w,n=1,sentences=1,supported=True,probabilities=dict(raw=rr[w]),**{'class':anchors[w]}) for w in train],'raw')
    save(OUT/'audit.json',dict(input_hashes_verified=hc,models_independently_optimized=24,maximum_independent_loss_difference=maxloss,maximum_kkt_violation=maxkkt,oof_predictions_checked=13,constrained_probabilities_independently_replayed=pc,metric_groups_independently_checked=mc,all_matched_unconstrained_references_verified=True,source_summaries_replayed=True))
if __name__=='__main__':run()
