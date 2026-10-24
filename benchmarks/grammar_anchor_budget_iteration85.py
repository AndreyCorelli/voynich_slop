"""Fixed anchor budget curve with strict pooling and source-only precision policies."""
from benchmarks.grammar_anchor_only_iteration84 import *
from benchmarks.grammar_anchor_only_iteration84_pool_control import fold_pool
from voynich_smt.anchor_budget import budgets,conservative_policy
OUT=ROOT/'iteration85';PREVIOUS=ROOT/'iteration84'
ARMS=('pooled_pos','left','prior')

def infer85(rows,models):
    xx=[r['features'] for r in rows];q=ag.anchor_override(rows,np.mean([ag.predict(xx,m) for m in models['pos'].values()],axis=0),models['pos_classes']);pq=ag.pool(rows,q);p=np.mean([ag.predict(xx,m,pq) for m in models['pp'].values()],axis=0)[:,4:].sum(axis=1)
    return [dict(sid=r['sid'],index=r['index'],word=r['word'],visible=r['anchor_tag']!='X',labels=r['labels'],scores={'pooled_pos':{'pp':float(p[i])},'left':{'pp':proximity83(r,'left')},'prior':{'pp':models['prior']}}) for i,r in enumerate(rows)]

def evaluate85(rows,pol):
    return {a:dict(f1=counts(rows,'pp',a,p['standard']['f1']['threshold']),empirical90=counts(rows,'pp',a,p['standard']['precision90']['threshold']) if p['standard']['precision90'] else None,conservative90=counts(rows,'pp',a,p['conservative']['threshold']) if p['conservative'] else None) for a,p in pol.items()}

def train_budget(fits,classes):
    xx=[r['features'] for r in fits];q=np.zeros((len(fits),len(classes)));pos={};prov={}
    for f in range(3):
        ids=[i for i,r in enumerate(fits) if fold(r['sid'])!=f];held=[i for i,r in enumerate(fits) if fold(r['sid'])==f];pos[str(f)]=ag.fit([xx[i] for i in ids],[fits[i]['pos_gold'] for i in ids],classes);q[held]=ag.predict([xx[i] for i in held],pos[str(f)]);prov[str(f)]=dict(train_sids=sorted({fits[i]['sid'] for i in ids}),train_n=len(ids))
    q=ag.anchor_override(fits,q,classes);pq=fold_pool(fits,q);pp={}
    for f in range(3):
        ids=[i for i,r in enumerate(fits) if fold(r['sid'])!=f];pp[str(f)]=ag.fit([xx[i] for i in ids],[fits[i]['structure_gold'] for i in ids],list(CLASSES),pq[ids])
    return dict(pos=pos,pp=pp,pos_classes=classes,prior=(sum(r['labels']['pp'] for r in fits)+.5)/(len(fits)+1)),dict(provenance=prov,probabilities=q.tolist())

def run():
    assert not OUT.exists();OUT.mkdir()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    paths=[Path(__file__),Path('src/voynich_smt/anchor_budget.py'),Path('src/voynich_smt/anchor_grammar.py'),Path('benchmarks/grammar_anchor_only_iteration84.py'),Path('benchmarks/grammar_anchor_only_iteration84_pool_control.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration84/models.json',ROOT/'iteration84/anchors.json',ROOT/'iteration84/fold-local-pool/models.json',PREVIOUS/'verification-manifest.json',Path('experiments/holdouts/grammar-construction-next.json')]
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Samealltoken/source49splits and84opaqueinputs. Freeze0/5/10/20/ALLeligibleADP+CCONJ+SCONJanchors, rankedsourceFITfrequency withlexicalties; ALLcount41. Include195full84anchorupperreference withfrozenPOS/strictpoolPPmodels, norefit. Trainotherbudgets samecontextPOS3fold andPP3ensembles, strictfoldlocalfitpooling; no changinghyperparams. Publicanchors exactsuppliedmapping/sourceMAPtag, allotherformsopaqueequalitynohiddenlookup. Fit/cal models/policies ALLbudgets beforeANY testpredictions; reportentirecurve, no testpickedbudget. Perarm pooledPOS/nearestleft/prior sourcecal F1andempirical90same77rule. Additionalconservativecaldiagnostic one-sidedClopperPearsonlowerbound atalpha=.05/101foreachfixedgridpoint, require>=.9and20predictions10types, selectmaxsourceTP. Tokenindependence andstationarity assumptions notestablished; notformal90%transferguarantee. Authors/hiddenvsanchorreporting. Reusedsourceonly, noCaesar/reserve/sealedtest/newtargetqueries/search.'))
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0']
    def source(split):return [dict(sent_id=sid,**data[sid]) for sid in part[split]]
    inventory=ag.anchor_inventory(source('fit'));catalogue=budgets(source('fit'),inventory);assert len(catalogue['41'])==41;catalogue['195']=inventory;save(OUT/'anchor-budgets.json',catalogue);save(OUT/'anchor-freeze.json',dict(catalogue=digest(OUT/'anchor-budgets.json')));classes=load(ROOT/'iteration84/models.json')['pos_classes']
    for budget,anchors in catalogue.items():
        folder=OUT/('budget-'+budget);folder.mkdir()
        if budget=='195':
            old=load(ROOT/'iteration84/models.json');models=dict(pos=old['pos'],pp=load(ROOT/'iteration84/fold-local-pool/models.json'),pos_classes=classes,prior=old['prior']);oof=None
        else:
            _,fits=prepare84(source('fit'),anchors,'fit85',classes);models,oof=train_budget(fits,classes)
        save(folder/'models.json',models)
        if oof is not None:save(folder/'oof.json',oof)
        save(folder/'model-freeze.json',dict(inputs={str(p):digest(p) for p in folder.glob('*.json')}))
        _,calq=prepare84(source('calibration'),anchors,'cal85',classes);cal=infer85(calq,models);save(folder/'calibration-predictions.json',cal);pol={a:dict(standard=select_policy(cal,'pp',a),conservative=conservative_policy(cal,a)) for a in ARMS};save(folder/'policies.json',pol);save(folder/'calibration-freeze.json',dict(inputs={str(p):digest(p) for p in (folder/'calibration-predictions.json',folder/'policies.json')}));print('Fit/calibrated anchor budget',budget,flush=True)
    save(OUT/'all-calibration-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('budget-*/calibration-freeze.json')}))
    result={}
    for budget,anchors in catalogue.items():
        folder=OUT/('budget-'+budget);models=load(folder/'models.json');pol=load(folder/'policies.json');_,queries=prepare84(source('test'),anchors,'test85',classes);rows=infer85(queries,models);save(folder/'predictions.json',rows);save(folder/'prediction-freeze.json',dict(predictions=digest(folder/'predictions.json')));result[budget]=dict(visible_tokens=sum(r['visible'] for r in rows),metrics=evaluate85(rows,pol));save(folder/'evaluation.json',result[budget]);print('Evaluated budget',budget,json.dumps(result[budget]),flush=True)
    save(OUT/'evaluation.json',result)
if __name__=='__main__':run()
