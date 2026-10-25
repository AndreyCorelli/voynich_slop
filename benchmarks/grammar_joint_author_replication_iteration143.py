"""Frozen joint-model replication on three previously inspected raw Latin authors."""
from benchmarks.grammar_joint_scalars_iteration142 import *
OUT=ROOT/'iteration143';WORKS=['apuleius-1','curtius-3','suetonius-augustus'];NULL_SEEDS=list(range(14300,14316))
CORPUS=Path('experiments/results/scalable-latin-corpus-morphology/v2/corpus/evaluation-only')

def features_for(ids,wanted):
    a=statistics([dict(tokens=[dict(id=i) for i in ids])],wanted);b=role_statistics(ids,wanted)
    return {i:dict(n=a[i]['n'],corrected=a[i]['corrected'],role_similarity=b[i]['role_similarity']) for i in a}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration142/verification-manifest.json',ROOT/'iteration142/models.json',ROOT/'iteration142/summary.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py'),Path('experiments/results/scalable-latin-trigram/v1/design.json')]+[CORPUS/(w+s) for w in WORKS for s in ['.txt','.json']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen142PRIMARYjointRAW>.5, NOtraining/calibration/guardshift/PP. EXACT3previouslyinspectedRavidevelopmentworksApuleiusI/CurtiusIII/SuetoniusAugustus, fullcachednormalizedwordstreams unchanged. Priortrigramdesign+metadata development provealreadyinspected; no remainingsealedworks/reserve/newrawannotations. InferenceopaqueIDequality/orderonly, NOknownmappings/sentenceboundaries. Same16sourcefunctioncatalogue, allpresenttypes primary/missing+occ5supportreportonly, c/que initial/clitic compatibilityflags andsource-modalreferencesNOTtokenPOS. Compute2featuresin142frozenmodules, matched142singlefeaturesRAWcontrols retainedalltextsneverpickauthorarm. Eachoriginal+16globalwordnullsseeds14300..15, exacttoken/typecountpreservation. Freezeallopaqueinputs/nullindicesBEFOREfeatures, ALLpredictionsBEFOREreferences/metrics. Reportprimarytypeaccuracy/NLL/AUC/perclass/weighted plusnullmax/taildescriptive, fixedcommon14secondary defined139beforethisexperiment. Freeze142primarynotchoosebetweenraw/calibrated basednewtexts. Additional-authorDEVELOPMENTreplication notuntouchedcorpusconfirmation, lengthsunequal. No default/lexicalnuclei/Voynichtranslation claim, catalogue membershipstillgiven.'))
    words=load(ROOT/'iteration93/types.json')['candidates'];models=load(ROOT/'iteration142/models.json');prior=load('experiments/results/scalable-latin-trigram/v1/design.json');assert set(WORKS)<=set(prior['development']);streams={};selection={};transforms={}
    for work in WORKS:
        path=CORPUS/(work+'.txt');tokens=path.read_text().split();meta=load(CORPUS/(work+'.json'));assert meta['split']=='development' and len(tokens)==meta['tokens'] and digest(path)==meta['normalized_sha256'];assert all(t==t.lower() and 'v' not in t and 'j' not in t for t in tokens);salt='raw143-'+work;lookup={w:hashlib.sha256((salt+'|'+w).encode()).hexdigest() for w in words};seq=[hashlib.sha256((salt+'|'+w).encode()).hexdigest() for w in tokens];streams[work]=seq;counts=Counter(tokens);selection[work]=dict(tokens=len(tokens),types=len(counts),lookup=lookup,candidate_counts={w:counts[w] for w in words},missing_types=sorted(w for w in words if not counts[w]),standalone_c_count=counts['c'],standalone_que_count=counts['que']);transforms[work]={'original':None,**{'word'+str(seed):np.random.default_rng(seed).permutation(len(seq)).tolist() for seed in NULL_SEEDS}}
    for name,x in [('streams',streams),('selection',selection),('transforms',transforms)]:save(OUT/(name+'.json'),x)
    save(OUT/'input-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['streams','selection','transforms']}));allfeatures={};predictions={}
    for work,seq in streams.items():
        lookup=selection[work]['lookup'];allfeatures[work]={};predictions[work]={}
        for view,ix in transforms[work].items():
            ids=seq if ix is None else [seq[i] for i in ix];assert Counter(ids)==Counter(seq);f=features_for(ids,set(lookup.values()));allfeatures[work][view]=f;predictions[work][view]={}
            for name in CONFIGS:
                rows=[]
                for word,i in sorted(lookup.items()):
                    if i in f:rows.append(dict(type=word,opaque=i,n=f[i]['n'],sentences=1,supported=f[i]['n']>=5,probabilities=dict(raw=predict_vector(f[i],models[name]['final']),prior=.5)))
                predictions[work][view][name]=rows
        print('predicted',work,flush=True)
    save(OUT/'features.json',allfeatures);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=set(load(ROOT/'iteration139/common-core.json'));summary={};contrasts={}
    for work,views in predictions.items():
        summary[work]={}
        for view,configs in views.items():
            summary[work][view]={}
            for name,rows in configs.items():
                refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];summary[work][view][name]={g:{p:metrics(rr,p) for p in ['raw','prior']} for g,rr in [('all',refs),('supported',[r for r in refs if r['supported']]),('common14',[r for r in refs if r['type'] in core])]}
        contrasts[work]={}
        for name in CONFIGS:
            actual=summary[work]['original'][name]['all']['raw'];null=[summary[work]['word'+str(seed)][name]['all']['raw'] for seed in NULL_SEEDS];contrasts[work][name]=dict(actual=actual,null_mean_auc=float(np.mean([r['auc'] for r in null])),null_max_auc=max(r['auc'] for r in null),null_auc_at_least_actual=sum(r['auc']>=actual['auc'] for r in null))
        print('RESULT',work,selection[work],contrasts[work],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
