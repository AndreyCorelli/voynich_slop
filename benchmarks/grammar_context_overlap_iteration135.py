"""One-statistic anchor-free directional-context class diagnostic."""
from benchmarks.grammar_sparse_training_iteration132 import *
from voynich_smt.opaque_context_overlap import statistics
OUT=ROOT/'iteration135';ARMS=['corrected','overlap','frequency']

def fit_scalar(stats,train,lookup,anchors,arm):
    raw=np.array([stats[lookup[w]][arm] for w in train]);mean=float(raw.mean());scale=float(raw.std()) or 1.;z=(raw-mean)/scale;y=np.array([int(anchors[w]=='CCONJ') for w in train]);x=np.column_stack([np.ones(len(train)),z]);counts=np.bincount(y,minlength=2);weight=np.array([1/(2*counts[c]) for c in y]);r=minimize(weighted_objective,np.zeros(4),args=(x,y,weight),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(weights=r.x.reshape(2,2).tolist(),mean=mean,scale=scale,loss=float(r.fun),types=train)

def predict_scalar(value,model):
    return float(softmax(np.array([1.,(value-model['mean'])/model['scale']])@np.array(model['weights']))[1])

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/opaque_context_overlap.py'),Path('tests/test_opaque_context_overlap.py'),ROOT/'iteration132/verification-manifest.json',ROOT/'iteration132/predictions.json',ROOT/'iteration116/type-split.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration118/public.json',ROOT/'iteration85/anchor-budgets.json',Path('experiments/holdouts/grammar-construction-next.json')]+[p for vv in INPUTS.values() for p in vv.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SmallANCHOR-FREEclassdiagnostic, NO PP. Features fromopaqueIDequality/sentenceboundariesONLY. Primarycorrected=sum_neighbor min(leftfreq,rightfreq) minus EXACTcountconditionednullmean: poolleft+rightneighbors, randomsplitpreservingL/Rsample sizes andcombinedneighborcounts; hypergeom marginal perneighbor, summingexpectedmin. Descriptivenullnotrealgrammarpvalue/independentobservations. Controlsrawoverlap andlog1poccurrencecount. Eacharm2parameterbinarylogistic(bias+onescalar),source13classbalancedloss/sameL2. StandardizationtrainfoldONLY,1163foldheldtypeOOF13, final13, fitbalancedscalaroffsetONLY13OOFprobs; freezeallmodelsbeforetargetstats. ALL16targettraininglabels excluded; no anchorfeatures/tags/identitynames used anymodel. Existingfitwordcache stats13only, contexts exact132source+all4cachedauthors; computeALLpresenttargets/missing/support flags, no filters/author-specificdirection/cutoff. Fixedq>.5CCONJ, primaryaccuracy/NLL/AUCvs132conditionalmodel andbalancedprior; showall3arms, doNOTpicktestwinner orfiton targetlabels. Freezepredictions beforemodalreferences. NoPPinference/newannotations/reserve/sealedlexicaltest/default/nuclei; catalogue/segmentation remain supplied, reuseddevelopmentnotfreshvalidation.'))
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);stats=statistics(public,{lookup[w] for w in train});models={};oof={};calibrators={}
    for arm in ARMS:
        models[arm]={};oof[arm]={}
        for fold in range(3):
            held=[w for w in train if split['oof_folds'][w]==fold];tr=[w for w in train if w not in held];m=fit_scalar(stats,tr,lookup,anchors,arm);models[arm][str(fold)]=m;oof[arm].update({w:predict_scalar(stats[lookup[w]][arm],m) for w in held})
        models[arm]['final']=fit_scalar(stats,train,lookup,anchors,arm);calibrators[arm]=fit_offset([oof[arm][w] for w in train],[int(anchors[w]=='CCONJ') for w in train],True)
    for name,obj in [('training-statistics',stats),('models',models),('oof-probabilities',oof),('calibrators',calibrators)]:save(OUT/(name+'.json'),obj)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['training-statistics','models','oof-probabilities','calibrators']}));contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p) for a,vv in INPUTS.items() for v,p in vv.items()});old=load(ROOT/'iteration132/predictions.json');predictions={};allstats={}
    for key,context in contexts.items():
        lookup={r['type']:r['opaque'] for r in old[key]};st=statistics(context,set(lookup.values()));allstats[key]=st;predictions[key]={}
        for arm in ARMS:
            rows=[]
            for r in old[key]:
                value=st[r['opaque']][arm];raw=predict_scalar(value,models[arm]['final']);rows.append(dict(type=r['type'],opaque=r['opaque'],n=r['n'],sentences=r['sentences'],supported=r['supported'],direction_supported=st[r['opaque']]['supported'],statistic=value,probabilities=dict(raw=raw,new=float(apply_offset([raw],calibrators[arm])[0]),previous=r['probabilities']['matched'],prior=.5)))
            predictions[key][arm]=rows
        print('predicted',key,flush=True)
    save(OUT/'statistics.json',allstats);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['statistics.json','predictions.json']}));summary={}
    for key,arms in predictions.items():
        summary[key]={}
        for arm,rows in arms.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];summary[key][arm]={a:metrics(refs,a) for a in ['raw','new','previous','prior']};print('RESULT',key,arm,summary[key][arm]['new'],flush=True)
    save(OUT/'class-summary.json',summary)
if __name__=='__main__':run()
