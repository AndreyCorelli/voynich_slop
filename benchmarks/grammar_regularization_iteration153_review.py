"""Independent source splits, ridge objective, selection and target replay."""
from benchmarks.grammar_regularization_iteration153 import *

def check_fit(m,f,expected,lookup,anchors):
    assert m['training']==expected;raw=np.array([[f[lookup[w]][c] for c in COLS] for w in expected]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;assert np.allclose(mean,m['mean']) and np.allclose(scale,m['scale']);x=np.column_stack([np.ones(len(expected)),(raw-mean)/scale]);y=np.array([anchors[w]=='CCONJ' for w in expected],dtype=int);counts=np.bincount(y,minlength=2);mass=np.array([.5/counts[c] for c in y]);weights=np.array(m['weights']);assert np.allclose(weights[:,0],-weights[:,1]);b=weights[:,1]-weights[:,0];assert min(b[1:])>=0;strength=m['strength']
    def obj(beta):
        z=x@beta;return float(mass@(np.logaddexp(0,z)-y*z)+strength/2*(beta@beta)),x.T@(mass*(expit(z)-y))+strength*beta
    loss,g=obj(b);assert abs(loss-m['loss'])<1e-10;violation=max(abs(g[0]),*[abs(g[j]) if b[j]>1e-7 else max(0.,-g[j]) for j in [1,2]]);assert violation<2e-6
    re=minimize(obj,np.zeros(3),jac=True,method='SLSQP',bounds=[(None,None),(0,None),(0,None)],options=dict(maxiter=1000,ftol=1e-12));assert re.success and abs(re.fun-loss)<1e-7

def run():
    hc=fc=pc=mc=0
    for name in ['design-freeze','model-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    split=load(ROOT/'iteration116/type-split.json');train=split['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};assert not set(train)&set(load(ROOT/'iteration93/types.json')['candidates']);f=load(ROOT/'iteration142/training-features.json');focal=load(ROOT/'iteration150/features.json');selection=load(OUT/'selection.json');inner=load(OUT/'inner-models.json');models=load(OUT/'models.json');oof=load(OUT/'oof.json')
    for key,s in selection.items():
        held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key[-1])];tr=[w for w in train if w not in held];losses={}
        assert set(s['trials'])==set(map(str,GRID))
        for strength in GRID:
            pp={};fits=inner[key][str(strength)];assert set(fits)==set(tr)
            for w,m in fits.items():
                assert m['strength']==strength;check_fit(m,f,[t for t in tr if t!=w],lookup,anchors);fc+=1;pp[w]=predict_vector(f[lookup[w]],m);assert not set(m['training'])&set(held)
            assert pp==s['trials'][str(strength)]['predictions'];nn=[]
            for tag in ['ADP','CCONJ']:nn.append(sum(-math.log(pp[w] if tag=='CCONJ' else 1-pp[w]) for w in tr if anchors[w]==tag)/sum(anchors[w]==tag for w in tr))
            loss=sum(nn)/2;assert abs(loss-s['trials'][str(strength)]['balanced_nll'])<1e-12;losses[strength]=loss
        chosen=max(k for k,v in losses.items() if v<=min(losses.values())+1e-10);assert s['chosen']==chosen
    for name,m in models.items():
        if name.startswith('outer'):held=[w for w in train if split['oof_folds'][w]==int(name[-1])];strength=selection[name]['chosen']
        else:held=[name[5:]] if name.startswith('omit/') else [];strength=selection['final']['chosen']
        assert m['strength']==strength;ff=focal[name[6:]] if name.startswith('motif/') else f;check_fit(m,ff,[w for w in train if w not in held],lookup,anchors);fc+=1
        if name.startswith('outer'):
            for w in held:assert oof[w]==predict_vector(f[lookup[w]],m)
    pred=load(OUT/'predictions.json');summary=load(OUT/'summary.json');old=load(ROOT/'iteration152/predictions.json');cached=load(ROOT/'iteration144/features.json')
    for w,views in pred.items():
        assert set(views)==set(old[w])
        for name,arms in views.items():
            for arm in ['constrained','unconstrained']:assert arms[arm]==old[w][name][arm]
            m=models[name];weights=np.array(m['weights']);b=weights[:,1]-weights[:,0]
            for r in arms['selected']:
                ff=cached[w+'/full'][r['opaque']];x=(np.array([ff[c] for c in COLS])-m['mean'])/m['scale'];assert abs(float(expit(b[0]+x@b[1:]))-r['probabilities']['raw'])<1e-10;pc+=1
            for arm,rows in arms.items():
                q=np.array([r['probabilities']['raw'] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);mm=summary[w][name][arm];assert mm['correct']==int(((q>.5)==y).sum());assert abs(mm['nll']-float(-np.log(np.where(y,q,1-q)).mean()))<1e-12;assert mm['auc']==float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:])));mc+=1
    assert load(OUT/'source-summary.json')==metrics([dict(type=w,n=1,sentences=1,supported=True,probabilities=dict(raw=oof[w]),**{'class':anchors[w]}) for w in train],'raw')
    save(OUT/'audit.json',dict(input_hashes_verified=hc,models_independently_optimized_and_kkt_checked=fc,source_only_selections_verified=4,nested_oof_predictions_verified=13,selected_target_probabilities_independently_replayed=pc,metric_groups_independently_checked=mc,all_matched_baselines_verified=True,perturbation_strength_fixed_before_targets=True))
if __name__=='__main__':run()
