"""Source-only class discrimination under whole-type masked validation."""
from benchmarks.grammar_anchor_class_audit_iteration91 import *
from voynich_smt.masked_anchor_class import CLASSES as BINARY_CLASSES,type_fold,masked_type_features,cap_rows,type_summary
OUT=ROOT/'iteration92';ARMS92=('context','prior','shuffle0','shuffle1','shuffle2')

def inputs92(sentences,anchors,words,salt):
    public=ag.public_sentences(sentences,anchors,salt);lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};return public,lookup

def fit92(sentences,anchors,words):
    public,lookup=inputs92(sentences,anchors,words,'fit92');models={};provenance={}
    for f in range(3):
        held=[w for w in words if type_fold(w)==f];train=[w for w in words if type_fold(w)!=f];held_ids={lookup[w] for w in held};bytype={w:cap_rows(masked_type_features(public,held_ids,lookup[w])) for w in train};xx=[r['features'] for w in train for r in bytype[w]];gold={w:BINARY_CLASSES.index(anchors[w]) for w in train};y=[gold[w] for w in train for r in bytype[w]];prior=[(y.count(k)+.5)/(len(y)+1) for k in range(2)];m=dict(context=ag.fit(xx,y,list(BINARY_CLASSES)),prior=prior);shuffles={}
        for seed in range(3):
            rng=np.random.default_rng(9200+100*f+seed);permuted=rng.permutation([gold[w] for w in train]).tolist();labels=dict(zip(train,permuted));shuffles[str(seed)]=labels;m['shuffle'+str(seed)]=ag.fit(xx,[labels[w] for w in train for r in bytype[w]],list(BINARY_CLASSES))
        models[str(f)]=m;provenance[str(f)]=dict(held_types=held,train_types=train,sampled_rows={w:[(r['sid'],r['index']) for r in rows] for w,rows in bytype.items()},shuffled_type_labels=shuffles);print('trained type fold',f,flush=True)
    return models,provenance

def predict92(sentences,anchors,words,models,salt):
    public,lookup=inputs92(sentences,anchors,words,salt);records=[]
    for w in words:
        if w not in lookup:continue
        f=type_fold(w);held_ids={lookup[v] for v in words if v in lookup and type_fold(v)==f};rows=masked_type_features(public,held_ids,lookup[w]);xx=[r['features'] for r in rows];m=models[str(f)];probs={a:(m['prior'] if a=='prior' else ag.predict(xx,m[a]).mean(axis=0).tolist()) for a in ARMS92}
        records.append(dict(type=w,fold=f,n=len(rows),sentences=len({r['sid'] for r in rows}),gold=BINARY_CLASSES.index(anchors[w]),probabilities=probs))
    return records

def run():
    assert not OUT.exists();OUT.mkdir()
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=sorted(w for w,p in anchors.items() if p in BINARY_CLASSES);save(OUT/'types.json',{w:dict(label=anchors[w],fold=type_fold(w)) for w in words});(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/masked_anchor_class.py'),Path('src/voynich_smt/anchor_grammar.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration91/verification-manifest.json',OUT/'types.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Stage1ONLYsourcefit/typeblocked sourcecal validation; no detectorcalibration, swap/authortests, sourcetest,reserve,sealedtest. All29source195ADP/CCONJtypeMAPclasses, deterministicSHAclass92word3typefolds. Eachfoldmodel excludesheldtypesfromfitlabels and hidesALLheldtypesfromALLpublicinputs. Pertrainingtype hideentireowntype aswell; sampleup20occurrences deterministicSIDs/indexhash, equalcap notoversamplingraretypes. Sameanchorpublicfeatures; no targettypeidentity/ID/POS inclassifierfeatures. BinaryADP/CCONJsoftmaxsameL2/solver. Controls per-foldsmoothedsampled-labelprior,3type-label permutations seeds9200+100fold+seed andidenticalfeatures. Freeze12models beforeanycalprediction. PrimarysourceCAL pooledtypeaccuracy/NLL(allpresent), secondarysupport>=5occ3sentences andfitOOFdiagnostic. Gateforfurtherwork: CALcontext accuracy>=prior+.10 and >=meanshuffle+.10 ANDNLL lowerthanbothprior/meanshuffle. No hyperparamselectionfromcal; whethergatepassorfail preservefullresults/provenance. This isofflineknown-source-typecrossvalidation, routingbyvalidationtype notclaimeddeployableopaqueanchorclassifier; futuredetectorneedsseparatelyfrozeninference. No PPintegration, nucleusrecovery, newannotations.'))
    models,prov=fit92(source('fit'),anchors,words);save(OUT/'models.json',models);save(OUT/'training-provenance.json',prov);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'models.json',OUT/'training-provenance.json')}))
    summary={}
    for split in ('fit','calibration'):
        rows=predict92(source(split),anchors,words,models,split+'92');save(OUT/(split+'-predictions.json'),rows);save(OUT/(split+'-prediction-freeze.json'),dict(inputs={str(OUT/(split+'-predictions.json')):digest(OUT/(split+'-predictions.json'))}));summary[split]={a:type_summary(rows,a) for a in ARMS92}
    c=summary['calibration'];context=c['context']['all'];prior=c['prior']['all'];sa=np.mean([c['shuffle'+str(i)]['all']['accuracy'] for i in range(3)]);sn=np.mean([c['shuffle'+str(i)]['all']['nll'] for i in range(3)]);summary['gate']=dict(passed=bool(context['accuracy']>=prior['accuracy']+.1 and context['accuracy']>=sa+.1 and context['nll']<prior['nll'] and context['nll']<sn),mean_shuffle_accuracy=float(sa),mean_shuffle_nll=float(sn));save(OUT/'evaluation.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
