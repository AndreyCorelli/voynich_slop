"""Cipher-observable neighbor frequency/recurrence in strict sparse class inference."""
from benchmarks.grammar_sparse_training_iteration132 import *
from voynich_smt.opaque_neighbor_features import features as neighbor_features
OUT=ROOT/'iteration134';ARMS=['frequency','recurrence']

def feature_rows(public,arm):
    rows=ag.public_features(public);extra=neighbor_features(public,relational=arm=='recurrence');assert len(rows)==len(extra)
    return [dict(r,features=r['features']+e) for r,e in zip(rows,extra)]

def fit_rows(rows,train,lookup,anchors):
    selected={w:cap_rows([r for r in rows if r['word']==lookup[w]]) for w in train};rr=[r for w in train for r in selected[w]];xx=[r['features'] for r in rr];y=np.array([CLASSES.index(anchors[w]) for w in train for r in selected[w]]);v=ag.vocabulary(xx);x=ag.matrix(xx,v);counts=np.bincount(y,minlength=2);weights=np.array([1/(2*counts[c]) for c in y]);r=minimize(weighted_objective,np.zeros(x.shape[1]*2),args=(x,y,weights),jac=True,method='L-BFGS-B',options=dict(maxiter=300,ftol=1e-11,gtol=1e-7));assert r.success,r.message
    return dict(vocabulary=v,classes=CLASSES,weights=r.x.reshape(x.shape[1],2).tolist(),loss=float(r.fun),iterations=int(r.nit)),{w:[[r['sid'],r['index']] for r in rs] for w,rs in selected.items()}

def profiles_rows(rows,words,lookup,model):
    q=ag.predict([r['features'] for r in rows],model);out={}
    for w in words:
        ii=[i for i,r in enumerate(rows) if r['word']==lookup[w]]
        if ii:out[w]=dict(mean=float(q[ii,1].mean()),n=len(ii),sentences=len({rows[i]['sid'] for i in ii}))
    return out

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/opaque_neighbor_features.py'),Path('tests/test_opaque_neighbor_features.py'),ROOT/'iteration132/verification-manifest.json',ROOT/'iteration132/training-provenance.json',ROOT/'iteration132/predictions.json',ROOT/'iteration132/scores.json',ROOT/'iteration116/type-split.json',ROOT/'iteration129/anchor-ranking.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration118/public.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration120/cohorts.json',ROOT/'iteration130/cohorts.json',BASE/'models.json',BASE/'predictions.json',Path('experiments/holdouts/grammar-construction-next.json')]+[p for vv in INPUTS.values() for p in vv.values()]+list(LABELS.values())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLYtrained representation experiment, exact132fixed5anchors/13train/116folds/20rows/type/balancedloss/L2. 16targetlabels excluded entirely. 2PREDECLAREDarms: frequencycontroladdsrelativecenter+adjacentopaqueIDfrequencybins; PRIMARYrecurrenceaddsleft/righttypecontext diversity/normalizedentropy/concentration/pairshare/pairrepeated andflankequality. Featurefunction usesONLYopaqueIDequality andsentenceboundaries, no plaintextnames/tag/labels innewfeatures. Existing132anchorfeatures unchanged. Globalunsupervisedstatsfromeachadmittedcontextincludingheldtypes, noheldlabels; identityrenaming/poison invariance tests. Samefixedfrequencyboundaries .0001,.0005,.001,.0025,.005,.01,.025,.05; ratebinboundaries in frozenmodule, no selection. Trainbotharms3OOF+final, recalibratebalancedoffsetONLY13OOFmeans, freezebothBEFORE ANYsource/authorprediction. Exact132source+ALL4cachedauthorcontexts; allpresenttypes, supportreportonly; compare132matched old atidenticalinputs, frequencycontrol, recurrence, prior. Primarytypeaccuracy/NLL/AUC; recurrencevsfrequencydistinguishesrelationalsignalfromcounts. No testwinnerarmselection. PP85/.80 hardnewclasses only, authororiginal100positions, cachedlabels/cohorts fixed. Freezeallnewpredictions/PPviewsBEFOREPPscores andmetrics. Reuseddevelopment; no newannotations/reserve/sealedlexicaltest/default/nuclei; fiveknownmappings/catalogue/segmentation remainprivileges.'))
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);assert all(t['anchor'] is None or t['anchor'] in allowed for s in public for t in s['tokens']);models={};oof={};provenance={};calibrators={}
    for arm in ARMS:
        rows=feature_rows(public,arm);models[arm]={};oof[arm]={};provenance[arm]={}
        for fold in range(3):
            held=[w for w in train if split['oof_folds'][w]==fold];tr=[w for w in train if w not in held];models[arm][str(fold)],provenance[arm][str(fold)]=fit_rows(rows,tr,lookup,anchors);oof[arm].update(profiles_rows(rows,held,lookup,models[arm][str(fold)]))
        models[arm]['final'],provenance[arm]['final']=fit_rows(rows,train,lookup,anchors);calibrators[arm]=fit_offset([oof[arm][w]['mean'] for w in train],[int(anchors[w]=='CCONJ') for w in train],True);print('trained',arm,flush=True)
    for name,obj in [('models',models),('oof-profiles',oof),('training-provenance',provenance),('calibrators',calibrators)]:save(OUT/(name+'.json'),obj)
    save(OUT/'model-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['models','oof-profiles','training-provenance','calibrators']}));contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p) for a,vv in INPUTS.items() for v,p in vv.items()});old=load(ROOT/'iteration132/predictions.json');predictions={};views={}
    for key,context in contexts.items():
        lookup={r['type']:r['opaque'] for r in old[key]};targets=set(lookup.values());masked=mask_budget(context,targets,allowed);predictions[key]={};views[key]={};previous={r['type']:r for r in old[key]}
        for arm in ARMS:
            pr=profiles_rows(feature_rows(masked,arm),sorted(lookup),lookup,models[arm]['final']);rr=[dict(type=w,opaque=lookup[w],n=p['n'],sentences=p['sentences'],supported=p['n']>=5 and p['sentences']>=3,probabilities=dict(raw=p['mean'],new=float(apply_offset([p['mean']],calibrators[arm])[0]),previous=previous[w]['probabilities']['matched'],prior=.5)) for w,p in sorted(pr.items())];predictions[key][arm]=rr;tags={r['opaque']:('CCONJ' if r['probabilities']['new']>.5 else 'ADP') for r in rr};views[key][arm]=inject(masked if key=='source' else masked[:100],targets,tags);save(OUT/('public-'+key+'-'+arm+'.json'),views[key][arm])
    save(OUT/'predictions.json',predictions);save(OUT/'input-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'predictions.json']+list(OUT.glob('public-*.json'))}));labels={'source':load(BASE/'predictions.json')};labels.update({a+'-'+v:load(p) for a,p in LABELS.items() for v in ['base','expanded']});ppmodel=load(BASE/'models.json');scores={k:{a:[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(v,labels[k]),ppmodel)] for a,v in aa.items()} for k,aa in views.items()};save(OUT/'scores.json',scores);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/'scores.json'):digest(OUT/'scores.json')}));cohorts={'source':load(ROOT/'iteration120/cohorts.json')};cohorts.update({a+'-'+v:load(ROOT/'iteration130/cohorts.json')[a] for a in INPUTS for v in ['base','expanded']});oldpp=load(ROOT/'iteration132/scores.json');summary={};evaluation={}
    for key,arms in predictions.items():
        summary[key]={};evaluation[key]={}
        for arm,rr in arms.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rr];summary[key][arm]={a:metrics(refs,a) for a in ['raw','new','previous','prior']};evaluation[key][arm]={c:dict(metrics=confusion(labels[key],scores[key][arm],.8,ii),changes_from132=changes(labels[key],oldpp[key],scores[key][arm],.8,ii)) for c,ii in cohorts[key].items()};print('RESULT',key,arm,summary[key][arm]['new'],evaluation[key][arm]['all'],flush=True)
    save(OUT/'class-summary.json',summary);save(OUT/'evaluation.json',evaluation)
if __name__=='__main__':run()
