"""Held-out-type detection of seven explicitly defined grammatical POS classes."""
from benchmarks.grammar_joint_token_budget_iteration144 import *
from scipy.special import expit
OUT=ROOT/'iteration157';GRID=[.0005,.005,.05,.5];DETECTORS={'structural':['corrected','role_similarity'],'frequency':['frequency'],'combined':['corrected','role_similarity','frequency']}

def fit_detector(f,train,lookup,labels,columns,strength):
    raw=np.array([[f[lookup[w]][c] for c in columns] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([labels[w] for w in train]);count=np.bincount(y,minlength=2);mass=np.array([.5/count[c] for c in y])
    def objective(b):
        z=x@b;return float(mass@(np.logaddexp(0,z)-y*z)+strength/2*(b@b)),x.T@(mass*(expit(z)-y))+strength*b
    r=minimize(objective,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),loss=float(r.fun),strength=strength,training=train)

def probability(f,m):return float(expit(m['beta'][0]+((np.array([f[c] for c in m['columns']])-m['mean'])/m['scale'])@np.array(m['beta'][1:])))

def fold_map(words,labels,salt):
    out={}
    for label in [0,1]:
        ordered=sorted([w for w in words if labels[w]==label],key=lambda w:hashlib.sha256((salt+'|'+w).encode()).hexdigest())
        out.update({w:k%3 for k,w in enumerate(ordered)})
    return out

def select(f,train,lookup,labels,cols,salt):
    folds=fold_map(train,labels,salt);trials={};fits={}
    for strength in GRID:
        pp={};fits[str(strength)]={}
        for k in range(3):
            held=[w for w in train if folds[w]==k];m=fit_detector(f,[w for w in train if w not in held],lookup,labels,cols,strength);fits[str(strength)][str(k)]=m;pp.update({w:probability(f[lookup[w]],m) for w in held})
        loss=sum(np.mean([-math.log(max(1e-300,pp[w] if label else 1-pp[w])) for w in train if labels[w]==label]) for label in [0,1])/2;trials[str(strength)]=dict(balanced_nll=float(loss),predictions=pp)
    best=min(r['balanced_nll'] for r in trials.values());chosen=max(v for v in GRID if trials[str(v)]['balanced_nll']<=best+1e-10);return dict(folds=folds,trials=trials,chosen=chosen),fits

def detection_metrics(pp,labels):
    words=sorted(pp,key=lambda w:(-pp[w],w));positive=sum(labels[w] for w in words);negative=len(words)-positive;tp=fp=ap=0.;groups={}
    for w in words:groups.setdefault(pp[w],[]).append(w)
    for score,ww in sorted(groups.items(),reverse=True):
        hits=sum(labels[w] for w in ww);tp+=hits;fp+=len(ww)-hits;ap+=hits/positive*tp/(tp+fp)
    q=np.array([pp[w] for w in words]);y=np.array([labels[w] for w in words],dtype=bool);a=q>.5;tp=int((a&y).sum());fp=int((a&~y).sum());fn=int((~a&y).sum());tn=int((~a&~y).sum())
    return dict(n=len(words),positives=positive,prevalence=positive/len(words),tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/positive,accuracy=(tp+tn)/len(words),average_precision=ap,auc=float(np.mean((q[y,None]>q[~y][None,:])+.5*(q[y,None]==q[~y][None,:]))),nll=float(-np.log(np.maximum(1e-300,np.where(y,q,1-q))).mean()),top={str(k):dict(n=min(k,len(words)),correct=sum(labels[w] for w in words[:k]),types=words[:k]) for k in [5,10,20,50]})

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json',ROOT/'iteration116/type-split.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py'),Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCEFITONLY sevenPOSunion156 unchanged, ALLtypes>=5occurrences scored irrespective purity. Purity>=.8 used ONLY to select sourceTRAININGtypes in each fit; mixed heldouttypes remain primaryevaluation. Entire16catalogueexcluded everyfit. Allsupportednon-targettypes outerstratifiedSHA(candidate157|word)roundrobin3; source inner3folds ONLYpureoutertrainingtypes, same3arms/grid/balancedNLLselection/strongesttie; no mixed-type outcome selection. Fixedfoldstandardization/transductiveunlabeledgraph. Freeze eligibility/folds beforefeatures, allmodels beforepredictions, predictions beforemetrics. Primaryall-supportedtype precision/recall/AP/AUC/NLL/top5,10,20,50; pure/mixedsecondary allreported, no favorablebudget. Finalmodelsfitallpurenon-targettypes, withheld16targetrecallonly. Labelmodal tieslexical, labelpurity retainedmetadataONLY not inferencefilter; no newannotations/reserve/sealedworks/nuclei/generalPOSclaim. Frequencyonlycomparator/combinedstructuralfixed, no attributingfrequencygain tostructure.'))
    public,lookup,anchors,split,targets,allowed=training_inputs();fit=load(ROOT/'iteration49/manifest.json')['partitions']['0']['fit'];data=load(ROOT/'iteration44/annotations-truth.json');counts={}
    for sid in fit:
        for t in data[sid]['tokens']:counts.setdefault(t['word'],Counter())[t['pos']]+=1
    records={}
    for w,c in sorted(counts.items()):
        tag,n=sorted(c.items(),key=lambda x:(-x[1],x[0]))[0];total=sum(c.values())
        if total>=5:records[w]=dict(n=total,modal=tag,purity=n/total,label=int(tag in ['ADP','AUX','CCONJ','DET','PART','PRON','SCONJ']))
    labels={w:r['label'] for w,r in records.items()};train=sorted(set(records)-set(targets));folds=fold_map(train,labels,'candidate157');lookup.update({w:hashlib.sha256(('fit116|'+w).encode()).hexdigest() for w in records});save(OUT/'eligibility.json',dict(records=records,training=train,folds=folds,targets=sorted(set(records)&set(targets)),lookup={w:lookup[w] for w in records}));save(OUT/'eligibility-freeze.json',dict(inputs={str(OUT/'eligibility.json'):digest(OUT/'eligibility.json')}));ids=[t['id'] for s in public for t in s['tokens']];features=features_for(ids,{lookup[w] for w in records})
    for f in features.values():f['frequency']=math.log1p(f['n'])
    models={};selections={};inner={};oof={}
    for name,cols in DETECTORS.items():
        models[name]={};selections[name]={};inner[name]={};oof[name]={}
        for k in range(3):
            key=str(k);held=[w for w in train if folds[w]==k];tr=[w for w in train if w not in held and records[w]['purity']>=.8];selections[name][key],inner[name][key]=select(features,tr,lookup,labels,cols,'inner157-outer'+key);m=fit_detector(features,tr,lookup,labels,cols,selections[name][key]['chosen']);models[name][key]=m;oof[name].update({w:probability(features[lookup[w]],m) for w in held})
        selections[name]['final'],inner[name]['final']=select(features,[w for w in train if records[w]['purity']>=.8],lookup,labels,cols,'final157');models[name]['final']=fit_detector(features,[w for w in train if records[w]['purity']>=.8],lookup,labels,cols,selections[name]['final']['chosen'])
    for n,x in [('features',features),('models',models),('selection',selections),('inner-models',inner)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['features','models','selection','inner-models']}));pred=dict(oof=oof,targets={name:{w:probability(features[lookup[w]],mm['final']) for w in set(records)&set(targets)} for name,mm in models.items()});save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));summary={name:{group:detection_metrics({w:p for w,p in pp.items() if group=='all' or (records[w]['purity']>=.8)==(group=='pure')},labels) for group in ['all','pure','mixed']} for name,pp in oof.items()};save(OUT/'summary.json',summary);save(OUT/'target-recall.json',{name:dict(n=len(pp),reference_positive=sum(labels[w] for w in pp),predicted_positive=sum(p>.5 for w,p in pp.items()),true_positive=sum(p>.5 and labels[w] for w,p in pp.items()),probabilities=pp) for name,pp in pred['targets'].items()});print('ELIGIBILITY',len(records),len(train),sum(labels[w] for w in train),flush=True)
    for name,r in summary.items():print(name,r,flush=True)
if __name__=='__main__':run()
