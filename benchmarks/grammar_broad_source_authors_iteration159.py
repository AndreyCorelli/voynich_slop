"""Frozen broad-class models on source-author sentences outside training."""
from benchmarks.grammar_no_purity_iteration157 import *
OUT=ROOT/'iteration159';AUTHORS=['Cicero','Palladius'];POSITIVE={'ADP','AUX','CCONJ','DET','PART','PRON','SCONJ'}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration157/verification-manifest.json',ROOT/'iteration157/models.json',ROOT/'iteration44/annotations-truth.json',ROOT/'iteration158/verification-manifest.json',ROOT/'iteration49/manifest.json',Path('experiments/holdouts/grammar-construction-next.json'),Path('src/voynich_smt/opaque_context_overlap.py'),Path('src/voynich_smt/opaque_context_roles.py')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen1573models, source44cachedcompletePOS/words, EXACT49partition0calibration+test IDorder groupedCicero/Palladius, excludingfit andallreservedIDs beforewordprojection. Theseauthorsseeninsourcefit, setsalreadyusedindevelopment; NOTindependentnewauthorconfirmation. No fitting/annotations/sealedworks. Same158wordonlyflatopaquegraph, occurrence>=5alltypeseligible no purity/sourcevocabulary/16cataloguefilter at inference. Primaryrawlog1p(n); fixedlengthcontrol log1p(n*31884/N), allmodels/allarms reported no chooseauthor. Freezeinputs/selectionbeforefeatures andallpredictions beforemodalreferences/metrics. Same7POSunion/modallexicalties; alltop5,10,20,50 withactualnifsmall, precision/recall/AP/AUC/NLL, tie-robustshortlistbounds inaudit. Comparefourtextdatasets158Caesar/Jerome andthese2separately notpooledindependence; exactidentitiesnotinferred/coarseclassnotgeneralPOS. No sourcefit/reserve/newrawannotations or thresholdsselected.'))
    truth={sid:r['tokens'] for sid,r in load(ROOT/'iteration44/annotations-truth.json').items()};data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];reserved={r['sent_id'] for rows in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rows};source=set(part['fit']);streams={};selection={}
    for author in AUTHORS:
        sids=[sid for sid in part['calibration']+part['test'] if data[sid]['author']==author and sid not in reserved];assert sids and not set(sids)&(source|reserved);tokens=[t['word'] for sid in sids for t in truth[sid]];counts=Counter(tokens);words=sorted(w for w,n in counts.items() if n>=5);lookup={w:hashlib.sha256(('author159-'+author+'|'+w).encode()).hexdigest() for w in set(tokens)};streams[author]=[lookup[w] for w in tokens];selection[author]=dict(sent_ids=sids,tokens=len(tokens),word_types=len(counts),eligible={w:dict(opaque=lookup[w],n=counts[w]) for w in words})
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
