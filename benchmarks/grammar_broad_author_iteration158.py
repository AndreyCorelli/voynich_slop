"""Frozen broad-class models on two complete cached author annotation sets."""
from benchmarks.grammar_no_purity_iteration157 import *
OUT=ROOT/'iteration158';AUTHORS=['Caesar','Jerome'];POSITIVE={'ADP','AUX','CCONJ','DET','PART','PRON','SCONJ'}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration157/verification-manifest.json',ROOT/'iteration157/models.json',ROOT/'iteration40/manifest.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration49/manifest.json',Path('experiments/holdouts/grammar-construction-next.json'),Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen157final3models on EXACT40cached100Caesar/100Jerome completewordPOSrefs; no newPOSreading/annotations, no expandedunlabeledstreams/sealedworks/reserve. SourceN31884fixed fromsourcefit. Inputsword-onlyflatconcatenationopaqueID; noanchors/sentenceboundaries/sourcevocabularyor16catalogueexclusionsat inference. Everyauthortype>=5occurrences eligible, no purityfilter/unknownreferencesdropped. Primary frozen rawlog1p(n)frequency; predeclared lengthnormalizedcontrol log1p(n*31884/Nauthor), sameweights, all3models/allarmsreported no chooseauthorarm. Freezewordinputs/selectionbeforefeatures, allpredictions beforeauthor-modalreferencecounts. ReferencesmodalPOS fromexistingauthor100tokens tieslexical, sevenPOSunion same157; purityevaluationonly. Precisionrecallraw>.5/AP/AUC/NLL/top5,10,20,50 allbudgets with actualn ifpoolsmall; top10 primaryshortlist reporting butallbudgetsretained. Eachauthor separate, cacheddevelopment notfreshconfirmation, shorttext/segmentationprivileges. Unknownwordidentities remainunknown foralgorithm, noexactnuclei/generalPOSclaim. No retraining/thresholdselection.'))
    truth=load(ROOT/'iteration40/data-truth.json');manifest=load(ROOT/'iteration40/manifest.json');reserved={r['sent_id'] for rows in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rows};source={sid for rows in load(ROOT/'iteration49/manifest.json')['partitions']['0'].values() for sid in rows};streams={};selection={}
    for author in AUTHORS:
        sids=manifest['split_ids'][author];assert len(sids)==100 and not set(sids)&(source|reserved);tokens=[t['word'] for sid in sids for t in truth[sid]];counts=Counter(tokens);words=sorted(w for w,n in counts.items() if n>=5);lookup={w:hashlib.sha256(('author158-'+author+'|'+w).encode()).hexdigest() for w in set(tokens)};streams[author]=[lookup[w] for w in tokens];selection[author]=dict(sent_ids=sids,tokens=len(tokens),word_types=len(counts),eligible={w:dict(opaque=lookup[w],n=counts[w]) for w in words})
    save(OUT/'streams.json',streams);save(OUT/'selection.json',selection);save(OUT/'input-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['streams.json','selection.json']}));models=load(ROOT/'iteration157/models.json');features={};pred={}
    for author,seq in streams.items():
        lookup=selection[author]['eligible'];features[author]=features_for(seq,{r['opaque'] for r in lookup.values()});pred[author]={}
        for scale in ['raw','normalized']:
            pred[author][scale]={}
            for name,mm in models.items():
                rows={}
                for w,r in lookup.items():
                    f=dict(features[author][r['opaque']]);f['frequency']=math.log1p(f['n']*(1 if scale=='raw' else 31884/len(seq)));rows[w]=probability(f,mm['final'])
                pred[author][scale][name]=rows
    save(OUT/'features.json',features);save(OUT/'predictions.json',pred);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['features.json','predictions.json']}));references={};summary={}
    for author,s in selection.items():
        counts={}
        for sid in s['sent_ids']:
            for t in truth[sid]:counts.setdefault(t['word'],Counter())[t['pos']]+=1
        refs={}
        for w in s['eligible']:
            cc=counts[w];tag,n=sorted(cc.items(),key=lambda x:(-x[1],x[0]))[0];refs[w]=dict(modal=tag,n=sum(cc.values()),purity=n/sum(cc.values()),label=int(tag in POSITIVE),pos_counts=dict(cc))
        references[author]=refs;labels={w:r['label'] for w,r in refs.items()};summary[author]={scale:{name:detection_metrics(pp,labels) for name,pp in arms.items()} for scale,arms in pred[author].items()}
    save(OUT/'references.json',references);save(OUT/'summary.json',summary)
    for author,scales in summary.items():
        print(author,'TOKENS',selection[author]['tokens'],'TYPES',len(selection[author]['eligible']),flush=True)
        for scale,arms in scales.items():print(scale,{name:{k:r[k] for k in ['n','positives','precision','recall','average_precision','auc','top']} for name,r in arms.items()},flush=True)
if __name__=='__main__':run()
