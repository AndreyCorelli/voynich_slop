"""Nested source-only regularization selection for monotonic joint classes."""
from benchmarks.grammar_monotone_joint_iteration152 import *
from scipy.special import expit
OUT=ROOT/'iteration153';GRID=[.0005,.005,.05,.5]

def fit_strength(features,train,lookup,anchors,strength):
    raw=np.array([[features[lookup[w]][c] for c in COLS] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([anchors[w]=='CCONJ' for w in train],dtype=int);counts=np.bincount(y,minlength=2);assert min(counts)>0;mass=np.array([.5/counts[c] for c in y])
    def objective(beta):
        z=x@beta;return float(mass@(np.logaddexp(0,z)-y*z)+strength*.5*(beta@beta)),x.T@(mass*(expit(z)-y))+strength*beta
    r=minimize(objective,np.zeros(3),jac=True,method='L-BFGS-B',bounds=[(None,None),(0,None),(0,None)],options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(columns=COLS,mean=mean.tolist(),scale=scale.tolist(),weights=np.column_stack([-r.x/2,r.x/2]).tolist(),loss=float(r.fun),training=train,strength=strength)

def select(features,train,lookup,anchors):
    trials={};fits={}
    for strength in GRID:
        key=str(strength);pp={};fits[key]={}
        for held in train:
            m=fit_strength(features,[w for w in train if w!=held],lookup,anchors,strength);fits[key][held]=m;pp[held]=predict_vector(features[lookup[held]],m)
        loss=sum(np.mean([-math.log(max(1e-300,pp[w] if tag=='CCONJ' else 1-pp[w])) for w in train if anchors[w]==tag]) for tag in ['ADP','CCONJ'])/2;trials[key]=dict(balanced_nll=float(loss),predictions=pp)
    best=min(r['balanced_nll'] for r in trials.values());chosen=max(v for v in GRID if trials[str(v)]['balanced_nll']<=best+1e-10);return dict(chosen=chosen,trials=trials),fits

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration152/verification-manifest.json',ROOT/'iteration152/predictions.json',ROOT/'iteration152/source-summary.json',ROOT/'iteration142/training-features.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration150/features.json',ROOT/'iteration116/type-split.json',ROOT/'iteration85/anchor-budgets.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Monotonic2feature model, exactly4ridge strengths .0005,.005,.05,.5 in originaltwoclasspenalty units: binarypenalty strength/2*||beta||² includingintercept. SOURCEONLY innerleave-one-type-out classbalancedNLL selects minimum, strongesttie within1e-10; outer existing3folds for honestnestedOOF, no targetlabels for selection. Innerfeaturestandardization fittypesonly; cachedfullsource unsupervisedfeatures sameas152. Finalstrength selectedLOOonall13, freeze beforetargets; SAMEstrengthfixed for all13omissionfits and7motifsubstitutionfits, NOperturbation/authorreselection. Raw>.5, sameclassbalancedloss/optimizer. Compare all7texts to frozen152constrainedfixedridge and itsmatched unconstrainedbaselines; source nestedOOF vs152fixedstrength. Report allaccuracy/NLL/AUC, sourcegridresults, allperturbations notindependentreplications. No newannotations/reserve/sealedworks/nuclei/generalPOS/default. Ifstrongestboundarychosen reportlimit notexpandgrid aftertargets.'))
    split=load(ROOT/'iteration116/type-split.json');train=split['training'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];lookup={w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in train};assert not set(train)&set(load(ROOT/'iteration93/types.json')['candidates']);f=load(ROOT/'iteration142/training-features.json');selection={};inner={};models={};oof={}
    for fold in range(3):
        key='outer'+str(fold);held=[w for w in train if split['oof_folds'][w]==fold];tr=[w for w in train if w not in held];selection[key],inner[key]=select(f,tr,lookup,anchors);m=fit_strength(f,tr,lookup,anchors,selection[key]['chosen']);models[key]=m;oof.update({w:predict_vector(f[lookup[w]],m) for w in held})
    selection['final'],inner['final']=select(f,train,lookup,anchors);strength=selection['final']['chosen'];models['full']=fit_strength(f,train,lookup,anchors,strength)
    for w in train:models['omit/'+w]=fit_strength(f,[t for t in train if t!=w],lookup,anchors,strength)
    focal=load(ROOT/'iteration150/features.json')
    for mask in range(1,8):models['motif/'+str(mask)]=fit_strength(focal[str(mask)],train,lookup,anchors,strength)
    for n,x in [('selection',selection),('inner-models',inner),('models',models),('oof',oof)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['selection','inner-models','models','oof']}));cached=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration152/predictions.json');pred={}
    for w,views in old.items():
        pred[w]={}
        for name,arms in views.items():pred[w][name]={**arms,'selected':[dict(r,probabilities=dict(raw=predict_vector(cached[w+'/full'][r['opaque']],models[name]))) for r in arms['constrained']]}
    save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));summary={w:{name:{arm:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw') for arm,rows in arms.items()} for name,arms in views.items()} for w,views in pred.items()};save(OUT/'summary.json',summary);source=metrics([dict(type=w,n=1,sentences=1,supported=True,probabilities=dict(raw=oof[w]),**{'class':anchors[w]}) for w in train],'raw');save(OUT/'source-summary.json',source);print('SELECTION',{k:{'chosen':v['chosen'],'losses':{a:b['balanced_nll'] for a,b in v['trials'].items()}} for k,v in selection.items()},flush=True);print('SOURCE',source,flush=True)
    for w,views in summary.items():print(w,{name:{arm:(r['correct'],r['nll'],r['auc']) for arm,r in arms.items()} for name,arms in views.items() if name in ['full','omit/siue','motif/2']},flush=True)
if __name__=='__main__':run()
