"""PP-governed membership with opaque content and explicit function anchors."""
from benchmarks.grammar_pp_privileges_iteration83 import *
from voynich_smt import anchor_grammar as ag
from voynich_smt.coarse_government import CLASSES,fold
OUT=ROOT/'iteration84';PREVIOUS=ROOT/'iteration83'
ARMS=('anchors','context_pos','pooled_pos','left','either','prior')

def prepare84(sentences,anchors,salt,pos_classes):
    public=ag.public_sentences(sentences,anchors,salt);rows=ag.public_features(public);lookup={(s['sent_id'],i):(s['tokens'],t) for s in sentences for i,t in enumerate(s['tokens'])}
    for r in rows:
        ts,t=lookup[r['sid'],r['index']];pp,_=bundles(ts,[t['pos'] for t in ts],r['index']);h=t.get('head');p=ts[h]['pos'] if h is not None else None;head='ROOT' if h is None else 'VERBAL' if p in ('VERB','AUX') else 'NOMINAL' if p in ('NOUN','PROPN','ADJ','PRON') else 'OTHER';r['structure_gold']=CLASSES.index(('oraclePP:present=True' in pp,head));r['pos_gold']=pos_classes.index(t['pos']);r['labels']={'pp':r['structure_gold']>=4};r['masked_center']=r['features']
    return public,rows

def infer84(rows,models):
    xx=[r['features'] for r in rows];q=ag.anchor_override(rows,np.mean([ag.predict(xx,m) for m in models['pos'].values()],axis=0),models['pos_classes']);pq=ag.pool(rows,q);softs={'anchors':None,'context_pos':q,'pooled_pos':pq};values={}
    for a,soft in softs.items():values[a]=np.mean([ag.predict(xx,m,soft) for m in models['pp'][a].values()],axis=0)[:,4:].sum(axis=1)
    return [dict(sid=r['sid'],index=r['index'],word=r['word'],pos_gold=r['pos_gold'],labels=r['labels'],scores={a:{'pp':float(values[a][i]) if a in values else float(models['prior']) if a=='prior' else proximity83(r,a)} for a in ARMS},pos_probabilities=q[i].tolist(),pooled_pos_probabilities=pq[i].tolist()) for i,r in enumerate(rows)]

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/anchor_grammar.py'),Path('src/voynich_smt/coarse_government.py'),Path('src/voynich_smt/government_context.py'),Path('src/voynich_smt/government_oracle.py'),ROOT/'iteration49/manifest.json',ROOT/'iteration44/annotations-truth.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Same49sourceonlyallstoredtoken splits. Build suppliedfunctionanchor inventory SOURCEFITONLY:word frequency>=5 andmodalUPOS ADP/CCONJ/SCONJ/PRON/DET/PART. Revealexactidentity andsource-modalPOSoftheseanchors; hideEVERYotherform inclunrecognizedfunctionwords asopaqueequalityIDs withsplit-specificsalt. No hidden-form lexical/POS/dictionary/suffix/length/finite lookups; no49morphology/71wordPOSmodels loaded. Publicfeatureinterfaceonlyid/anchor/tag. Features governmentcontext withopaqueXandallfinite0, centerknownanchor tag/identity, anchoridentity±4; IDs never classifierfeatures. ContextPOSsoftmax sourcefitgoldUPOS supervision, 3sentenceblockedfolds as82; OOFfitPOSprobabilities, knownanchorPOSoverridden tosourceMAP. Pool acrossopaqueequality withinSPLIT, no goldtype labels. Train3PP/head8classensembles:anchors only, +continuouscontextPOS, +pooledPOS. Fit usesOOFPOS, cal/testensemblePOS; no PPgoldatprediction. Structuralheadcategory sourcegoldPOS labels(privatesupervision), PPscope same83. SourcecalF1/precision90samegrid/support frozenbeforetest. Allarms run; primarypooledPOS, controlsanchors/contextPOS/nearestleft/either/prior. Sourceauthors/seenanchorcoverage/hiddenPOSdiagnostics; no Caesar/reserve/sealedtest/newtargetqueries/search. Readablefunctionanchors remainexplicitprivilege, not discoveredVoynichmapping.'))
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0']
    def source(split):return [dict(sent_id=sid,**data[sid]) for sid in part[split]]
    fit_source=source('fit');anchors=ag.anchor_inventory(fit_source);pos_classes=sorted({t['pos'] for s in fit_source for t in s['tokens']}|set(anchors.values()));save(OUT/'anchors.json',anchors);save(OUT/'anchor-freeze.json',dict(anchors=digest(OUT/'anchors.json'),selection='sourcefitonly; allotherformsopaque'))
    pub,rows=prepare84(fit_source,anchors,'fit84',pos_classes);save(OUT/'fit-public.json',pub);xx=[r['features'] for r in rows];q=np.zeros((len(rows),len(pos_classes)));pos_models={};provenance={}
    for f in range(3):
        train=[i for i,r in enumerate(rows) if fold(r['sid'])!=f];held=[i for i,r in enumerate(rows) if fold(r['sid'])==f];pos_models[str(f)]=ag.fit([xx[i] for i in train],[rows[i]['pos_gold'] for i in train],pos_classes);q[held]=ag.predict([xx[i] for i in held],pos_models[str(f)]);provenance[str(f)]=dict(training_sids=sorted({rows[i]['sid'] for i in train}),train_n=len(train))
    q=ag.anchor_override(rows,q,pos_classes);pq=ag.pool(rows,q);pp_models={}
    for a,soft in [('anchors',None),('context_pos',q),('pooled_pos',pq)]:
        pp_models[a]={}
        for f in range(3):
            ids=[i for i,r in enumerate(rows) if fold(r['sid'])!=f];pp_models[a][str(f)]=ag.fit([xx[i] for i in ids],[rows[i]['structure_gold'] for i in ids],list(CLASSES),None if soft is None else soft[ids])
        print('Fitted',a,flush=True)
    models=dict(pos=pos_models,pp=pp_models,pos_classes=pos_classes,prior=(sum(r['labels']['pp'] for r in rows)+.5)/(len(rows)+1));save(OUT/'models.json',models);save(OUT/'oof.json',dict(provenance=provenance,probabilities=q.tolist()));save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'models.json',OUT/'oof.json',OUT/'fit-public.json')}))
    pub,calq=prepare84(source('calibration'),anchors,'cal84',pos_classes);save(OUT/'calibration-public.json',pub);cal=infer84(calq,models);save(OUT/'calibration-predictions.json',cal);pol={a:select_policy(cal,'pp',a) for a in ARMS};save(OUT/'policies.json',pol);save(OUT/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'policies.json',OUT/'calibration-predictions.json',OUT/'calibration-public.json')}))
    pub,testq=prepare84(source('test'),anchors,'test84',pos_classes);save(OUT/'test-public.json',pub);test=infer84(testq,models);save(OUT/'predictions.json',test);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'predictions.json',OUT/'test-public.json')}));result=evaluate83(test,pol);save(OUT/'evaluation.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':run()
