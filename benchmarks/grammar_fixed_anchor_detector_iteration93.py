"""Single masked-type class model and source-calibrated anchor-error detection."""
from benchmarks.grammar_masked_anchor_class_iteration92 import *
from voynich_smt.fixed_anchor_detector import predict_records,ARMS as DETECTOR_ARMS
OUT=ROOT/'iteration93'

def train93(sentences,anchors,words):
    public,lookup=inputs92(sentences,anchors,words,'fit93');bytype={w:cap_rows(masked_type_features(public,set(),lookup[w])) for w in words};xx=[r['features'] for w in words for r in bytype[w]];labels={w:BINARY_CLASSES.index(anchors[w]) for w in words};y=[labels[w] for w in words for r in bytype[w]];models=dict(context=ag.fit(xx,y,list(BINARY_CLASSES)),prior=[(y.count(k)+.5)/(len(y)+1) for k in range(2)]);shuffles={}
    for seed in range(3):
        rng=np.random.default_rng(9300+seed);shuffles[str(seed)]=dict(zip(words,rng.permutation([labels[w] for w in words]).tolist()));models['shuffle'+str(seed)]=ag.fit(xx,[shuffles[str(seed)][w] for w in words for r in bytype[w]],list(BINARY_CLASSES))
    return models,dict(sampled_rows={w:[[r['sid'],r['index']] for r in rows] for w,rows in bytype.items()},shuffled_type_labels=shuffles)

def prepare93(sentences,anchors,words,replacements,salt,models):
    public=ag.public_sentences(sentences,anchors,salt);lookup={t['anchor']:t['id'] for s in public for t in s['tokens'] if t['anchor'] in words};changed=perturb(public,replacements,anchors);candidates={lookup[w]:anchors[replacements.get(w,w)] for w in words if w in lookup};results=predict_records(changed,candidates,models);inverse={opaque:w for w,opaque in lookup.items()}
    for rows in results.values():
        for r in rows:r['class_wrong']=r['proposed']!=anchors[inverse[r['anchor_id']]]
    return dict(records=results,identities=inverse)

def run():
    assert not OUT.exists();OUT.mkdir()
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]];cat=load(ROOT/'iteration85/anchor-budgets.json');anchors=cat['195'];trainwords=sorted(w for w,p in anchors.items() if p in BINARY_CLASSES);candidates=sorted(w for w,p in cat['20'].items() if p in BINARY_CLASSES);patterns=load(ROOT/'iteration90/patterns.json');save(OUT/'patterns.json',patterns);save(OUT/'types.json',dict(training=trainwords,candidates=candidates));(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/fixed_anchor_detector.py'),Path('src/voynich_smt/masked_anchor_class.py'),Path('src/voynich_smt/anchor_class_audit.py'),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration92/verification-manifest.json',ROOT/'iteration91/evaluation.json',CACHE,DECLARATION,OUT/'patterns.json',OUT/'types.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Onefixedbinarycontextmodel, all29sourceFITADP/CCONJtypes withwholeowntypemasked, remaininganchorsvisible. Max20occurrencespertype deterministiccap92. Samefeatures/L2/solver. No fold routing, no opaqueIDfeatures;IDonlygroup/mask. Sameprior+3fixedtype-labelpermutationcontrols seeds9300..9302, frozenbeforecal. Detectorcandidates16common20ADP/CCONJ as91; logopposite/proposed meanprobability, support>=5occ3sentences (binaryclassmass1, no13classmassgate). Calibrate eacharmONLYsourcecal clean/knownin-etswap using91grid0,.5,1,2,3,4,8,OFF; cleantypeFP<=1 andcleanflaggedocc<=5%candidateocc; maximizeknownswapTP thenmincorruptFP,cleanflaggedtokens,higherthreshold. Freezeall5policiesbeforeANYsourcetest/authorevaluation. All8patterns90, source/CachedJerome/Caesar, falsealarms/unsupportederrors reported. Original91frozenPOSOFFcontrol retained. Sameclassswaps classcorrect, classlabelsoriginalsourceMAPsimulationonly attachedAFTERpublicscores, nottargetgoldPOS. Nopair-specificretraining, thresholdrelaxation, detectorcorrection, PPintegration, newqueries,reserve/sealedtest. Training nowincludescandidate typeclasses; sentence-disjointcal/test, nottypeheldout;92separatetypeCVfinding preserved.'))
    models,provenance=train93(source('fit'),anchors,trainwords);save(OUT/'models.json',models);save(OUT/'training-provenance.json',provenance);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'models.json',OUT/'training-provenance.json')}));print('trained fixed models',flush=True)
    cal={}
    for pattern in ('correct','rehearsed_in_et'):
        prediction=prepare93(source('calibration'),anchors,candidates,patterns[pattern],'cal93',models);save(OUT/('calibration-'+pattern+'.json'),prediction);cal[pattern]=prediction['records']
    policies={}
    for arm in DETECTOR_ARMS:
        selected,curve=choose_threshold(cal['correct'][arm],cal['rehearsed_in_et'][arm]);policies[arm]=selected;save(OUT/('calibration-curve-'+arm+'.json'),curve);print('policy',arm,selected,flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json']+list(OUT.glob('calibration-*.json'))}))
    cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        for pattern,replacements in patterns.items():
            folder=OUT/(name.lower()+'-'+pattern);folder.mkdir();prediction=prepare93(sentences,anchors,candidates,replacements,'eval93-'+name,models);save(folder/'predictions.json',prediction);save(folder/'prediction-freeze.json',dict(inputs={str(folder/'predictions.json'):digest(folder/'predictions.json')}));result={arm:metrics(rows,float('inf') if policies[arm]['threshold'] is None else policies[arm]['threshold']) for arm,rows in prediction['records'].items()};result['frozen91']=load(ROOT/'iteration91/evaluation.json')[name+'/'+pattern];save(folder/'evaluation.json',result);summary[name+'/'+pattern]=result
        print('evaluated',name,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
