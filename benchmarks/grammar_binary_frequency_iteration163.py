"""Normalized count information in full-source anonymous binary classification."""
from benchmarks.grammar_full_source_iteration162 import *
OUT=ROOT/'iteration163';GRID=[.0005,.005,.05,.5];ARMS={'structural':['corrected','role_similarity'],'frequency':['frequency'],'combined':['corrected','role_similarity','frequency']}

def fit_arm(f,train,lookup,labels,columns,strength):
    raw=np.array([[f[lookup[w]][c] for c in columns] for w in train]);mean=raw.mean(0);scale=raw.std(0);scale[scale<1e-12]=1.;x=np.column_stack([np.ones(len(train)),(raw-mean)/scale]);y=np.array([labels[w]=='CCONJ' for w in train],dtype=int);counts=np.bincount(y,minlength=2);mass=np.array([.5/counts[c] for c in y]);bounds=[(None,None)]+[(None,None) if c=='frequency' else (0,None) for c in columns]
    def obj(b):
        z=x@b;return float(mass@(np.logaddexp(0,z)-y*z)+strength/2*(b@b)),x.T@(mass*(expit(z)-y))+strength*b
    r=minimize(obj,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',bounds=bounds,options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),loss=float(r.fun),strength=strength,training=train)

def probability(f,m):return float(expit(m['beta'][0]+((np.array([f[c] for c in m['columns']])-m['mean'])/m['scale'])@np.array(m['beta'][1:])))

def select_arm(f,train,lookup,labels,cols,salt):
    folds={}
    for tag in ['ADP','CCONJ']:
        ww=sorted([w for w in train if labels[w]==tag],key=lambda w:hashlib.sha256((salt+'|'+w).encode()).hexdigest());folds.update({w:j%3 for j,w in enumerate(ww)})
    trials={};fits={}
    for strength in GRID:
        pp={};fits[str(strength)]={}
        for k in range(3):
            held=[w for w in train if folds[w]==k];m=fit_arm(f,[w for w in train if w not in held],lookup,labels,cols,strength);fits[str(strength)][str(k)]=m;pp.update({w:probability(f[lookup[w]],m) for w in held})
        loss=sum(np.mean([-math.log(max(1e-300,pp[w] if tag=='CCONJ' else 1-pp[w])) for w in train if labels[w]==tag]) for tag in ['ADP','CCONJ'])/2;trials[str(strength)]=dict(balanced_nll=float(loss),predictions=pp)
    best=min(r['balanced_nll'] for r in trials.values());return dict(folds=folds,trials=trials,chosen=max(v for v in GRID if trials[str(v)]['balanced_nll']<=best+1e-10)),fits

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration162/verification-manifest.json',ROOT/'iteration162/eligibility.json',ROOT/'iteration162/features.json',ROOT/'iteration144/selection.json',ROOT/'iteration144/features.json',ROOT/'iteration144/predictions.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration147/audit.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Same162SOURCE29/outerfolds/anonymousauthortransfer, explicitrelaxed16wordtypeholdout; suppliedcandidatecatalogue remains. Fixed3arms:2structuralnonnegative, frequencyonlyunconstrainedslope, combinedstructuralnonnegative/frequencyunconstrained. Feature frequency=log1p(n*31884/Nstream), so source unchangedlog1p(n), normalizedtargets exact144fullstreamtokenN. Source-onlynested3innerfolds stratifiedSHA(inner163-outer{k}|word)/final163, same4ridgegrid balancedNLL strongesttie1e-10; preserve162outerfolds honestOOF. Freezeallsourcefeatures/models/selections beforetargetpredictions/allpredictions beforemodalmetrics. Finalsource-selectedstrength FIXEDperarm forfull/all29omissions/all7existingmotifperturbations, noauthor/reselection/outcome-pickedarm. Source perturbationNunchanged31884, countsfrom162featuremetadata. All7alreadyinspectedfulltexts, raw>.5 cutoff, reportaccuracyNLLAUC/perturbationranges allarms. No newannotations/reserve/sealedworks/names/mappings/generalPOS/nuclei/default. Testmissingfrequencyinformation notassumedimprovement.'))
    e=load(ROOT/'iteration162/eligibility.json');train=e['training'];lookup=e['lookup'];labels={w:r['label'] for w,r in e['records'].items()};folds=e['folds'];features=load(ROOT/'iteration162/features.json');assert load(ROOT/'iteration147/audit.json')['source_fit_tokens']==31884
    for f in features.values():
        for r in f.values():r['frequency']=math.log1p(r['n'])
    models={};inner={};selection={};oof={}
    for arm,cols in ARMS.items():
        models[arm]={};inner[arm]={};selection[arm]={};oof[arm]={}
        for k in range(3):
            key=str(k);held=[w for w in train if folds[w]==k];tr=[w for w in train if w not in held];selection[arm][key],inner[arm][key]=select_arm(features['full'],tr,lookup,labels,cols,'inner163-outer'+key);m=fit_arm(features['full'],tr,lookup,labels,cols,selection[arm][key]['chosen']);models[arm]['oof'+key]=m;oof[arm].update({w:probability(features['full'][lookup[w]],m) for w in held})
        selection[arm]['final'],inner[arm]['final']=select_arm(features['full'],train,lookup,labels,cols,'final163');strength=selection[arm]['final']['chosen'];models[arm]['full']=fit_arm(features['full'],train,lookup,labels,cols,strength)
        for w in train:models[arm]['omit/'+w]=fit_arm(features['full'],[t for t in train if t!=w],lookup,labels,cols,strength)
        for mask in range(1,8):models[arm]['motif/'+str(mask)]=fit_arm(features['motif/'+str(mask)],train,lookup,labels,cols,strength)
    for n,x in [('source-features',features),('models',models),('inner-models',inner),('selection',selection),('oof',oof)]:save(OUT/(n+'.json'),x)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['source-features','models','inner-models','selection','oof']}));tf=load(ROOT/'iteration144/features.json');old=load(ROOT/'iteration144/predictions.json');windows=load(ROOT/'iteration144/selection.json');pred={};targetfeatures={}
    for key,configs in old.items():
        if not key.endswith('/full'):continue
        w=key[:-5];N=windows[key]['stop']-windows[key]['start'];targetfeatures[w]={i:dict(r,frequency=math.log1p(r['n']*31884/N)) for i,r in tf[key].items()};pred[w]={arm:{name:[dict(r,probabilities=dict(raw=probability(targetfeatures[w][r['opaque']],m))) for r in configs['joint']] for name,m in mm.items() if not name.startswith('oof')} for arm,mm in models.items()}
    save(OUT/'target-features.json',targetfeatures);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['target-features.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];summary={w:{arm:{name:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rows],'raw') for name,rows in vv.items()} for arm,vv in arms.items()} for w,arms in pred.items()};source={arm:metrics_for(pp,labels) for arm,pp in oof.items()};save(OUT/'summary.json',summary);save(OUT/'source-summary.json',source);print('SOURCE',source,flush=True);print('SELECTED',{a:{k:r['chosen'] for k,r in ss.items()} for a,ss in selection.items()},flush=True)
    for w,arms in summary.items():print(w,{a:{n:(r['correct'],r['n'],r['auc'],r['nll']) for n,r in vv.items() if n in ['full','omit/siue','motif/2']} for a,vv in arms.items()},flush=True)
if __name__=='__main__':run()
