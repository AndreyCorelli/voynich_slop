"""Nonnegative symmetry slopes, fixed source validation and robustness panels."""
from benchmarks.grammar_training_sensitivity_iteration148 import *
OUT=ROOT/'iteration152'

def fit_monotone(features,train,lookup,anchors):
    raw=np.array([[features[lookup[w]][c] for c in COLS] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([int(anchors[w]=='CCONJ') for w in train]);counts=np.bincount(y,minlength=2);weight=np.array([1/(2*counts[c]) for c in y])
    def objective(beta):
        z=np.column_stack([-beta/2,beta/2]);loss,g=weighted_objective(z.ravel(),x,y,weight);g=g.reshape(-1,2);return loss,(g[:,1]-g[:,0])/2
    r=minimize(objective,np.zeros(3),jac=True,method='L-BFGS-B',bounds=[(None,None),(0,None),(0,None)],options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(columns=COLS,mean=mean.tolist(),scale=scale.tolist(),weights=np.column_stack([-r.x/2,r.x/2]).tolist(),loss=float(r.fun),training=train)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_scalars_iteration142.py'),Path('benchmarks/grammar_balanced_training_iteration124.py'),ROOT/'iteration142/training-features.json',ROOT/'iteration142/models.json',ROOT/'iteration142/oof-probabilities.json',ROOT/'iteration148/models.json',ROOT/'iteration148/predictions.json',ROOT/'iteration150/features.json',ROOT/'iteration150/models.json',ROOT/'iteration150/predictions.json',ROOT/'iteration150/verification-manifest.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration116/type-split.json',ROOT/'iteration85/anchor-budgets.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ONE modification: constrain both standardized CCONJ logit slopes>=0, biasfree; binarybeta equivalent antisymmetrictwoclass weights preserves exact .0005||W||² L2 and classbalancedloss142. Same13types/features/raw>.5/nooffset/tuning. Fit3sourceOOF plusfull, all13typeomissions onoriginalfeatures, all7fixed150focalsubstitutions; compare matched frozenunconstrained142/148/150 refs. No pickfavorablemodel/author/perturbation; sourceOOF all13samefolds botharms, metrics accuracy/NLL/AUC. Freeze allmodels before7targetpredictions and allpredictions before modalmetrics. Source/targetcaches only, no newannotations/reserve/sealedworks. Monotonic hypothesisnotuniversalgrammar. A constraint preventing reversals doesnot byitself demonstrate usefulrestoration; retain probability metrics and allbaseline decisions. No generalPOS/nuclei/confidenceclaim.'))
    split=load(ROOT/'iteration116/type-split.json');train=split['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};assert not set(train)&set(load(ROOT/'iteration93/types.json')['candidates']);f=load(ROOT/'iteration142/training-features.json');models={};oof={}
    for fold in range(3):
        held=[w for w in train if split['oof_folds'][w]==fold];m=fit_monotone(f,[w for w in train if w not in held],lookup,anchors);models['oof'+str(fold)]=m;oof.update({w:predict_vector(f[lookup[w]],m) for w in held})
    models['full']=fit_monotone(f,train,lookup,anchors)
    for w in train:models['omit/'+w]=fit_monotone(f,[t for t in train if t!=w],lookup,anchors)
    focal=load(ROOT/'iteration150/features.json')
    for mask in range(1,8):models['motif/'+str(mask)]=fit_monotone(focal[str(mask)],train,lookup,anchors)
    save(OUT/'models.json',models);save(OUT/'oof.json',oof);save(OUT/'model-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['models.json','oof.json']}));cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');om=load(ROOT/'iteration148/predictions.json');fp=load(ROOT/'iteration150/predictions.json');pred={}
    for key,configs in old.items():
        if not key.endswith('/full'):continue
        w=key[:-5];pred[w]={}
        for name,m in models.items():
            if name.startswith('oof'):continue
            baseline=configs['joint'] if name=='full' else om[w][name[5:]] if name.startswith('omit/') else fp[w][name[6:]]
            pred[w][name]={'constrained':[dict(r,probabilities=dict(raw=predict_vector(cached[key][r['opaque']],m))) for r in configs['joint']],'unconstrained':baseline}
    save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));summary={w:{name:{arm:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw') for arm,rows in arms.items()} for name,arms in views.items()} for w,views in pred.items()};save(OUT/'summary.json',summary);source={}
    for name,rr in [('constrained',oof),('unconstrained',load(ROOT/'iteration142/oof-probabilities.json')['joint'])]:source[name]=metrics([dict(type=w,n=1,sentences=1,supported=True,probabilities=dict(raw=rr[w]),**{'class':anchors[w]}) for w in train],'raw')
    save(OUT/'source-summary.json',source);print('SOURCE',source,flush=True)
    for w,views in summary.items():print(w,{name:{arm:(r['correct'],r['nll']) for arm,r in arms.items()} for name,arms in views.items() if name in ['full','omit/siue','motif/2']},flush=True)
if __name__=='__main__':run()
