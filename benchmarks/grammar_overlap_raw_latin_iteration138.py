"""Frozen sentence-free overlap inference on already inspected raw Latin works."""
from benchmarks.grammar_context_overlap_iteration135 import *
OUT=ROOT/'iteration138';NULL_SEEDS=list(range(13800,13816))
CORPUS=Path('experiments/results/scalable-latin-corpus-morphology/v2/corpus/evaluation-only')
WORKS=['gellius-1','livy-1']

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration135/models.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration137/verification-manifest.json',ROOT/'iteration137/contrasts.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration93/types.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('experiments/results/scalable-latin-trigram/v1/confirmation-design.json'),Path('experiments/results/scalable-latin-trigram/v1/confirmation-comparison.json')]+[CORPUS/(w+suffix) for w in WORKS for suffix in ['.txt','.json']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen135anchor-free/SENTENCE-FREE overlapclassifier, no fit/PP. EXACTalreadyinspectednormalizedGelliusI9670tokens andLivyI16983tokens. Livymetadatahistoricallysealed-test BUTpriortrigramconfirmation-design/comparisonprovealreadyopened; doNOTreadstillsealedAmmianus/Quintilian. No rawnewcorpus/annotation/decodingtruth/recoveryquery. UseexistingwordstreamsUNCHANGEDlowercaseu/v/i/j normalization, no sentenceboundaries/resegmentation/encliticsplitting/initialrepair. 16sourcecataloguetypes allpresent retained/missingreported; sourceMODALclassreference notnewtokenPOS, potentialcinitial/queclitic mismatchreported notdropped orrelabeled. Fixedcandidate membershipstillgiven. HashwordsintosaltedopaqueIDs, inferencefeaturesONLYIDs. Eachoriginalstream+16globalwordshuffles seeds13800..15 exactcountspreserved. Freezeallstreams/transforms BEFOREstatistics, predictions BEFOREreferences/metrics. PRIMARYcorrected,raw/frequencycontrolsallreportedneverpickauthorarm/cutoff. Fixed>.5; allpresent metrics/supportoccurrence>=5reportonly,sentence-supportUNAVAILABLE. Afterfreeze attachOLDsourceMAPreferences, notnewannotations. Combined4textsummaryincludes137concatJerome/Caesar, no poolingindependentgeneralaccuracy. No model/default/nucleiclaim orVoynich application. Rawversustreebanksegmentation isconfound notcontrolledlanguageeffect.'))
    models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');words=load(ROOT/'iteration93/types.json')['candidates'];streams={};selection={};transforms={}
    for work in WORKS:
        path=CORPUS/(work+'.txt');tokens=path.read_text().split();meta=load(CORPUS/(work+'.json'));assert len(tokens)==meta['tokens'];assert digest(path)==meta['normalized_sha256'];assert all(w==w.lower() and 'v' not in w and 'j' not in w for w in tokens);salt='raw138-'+work;lookup={w:hashlib.sha256((salt+'|'+w).encode()).hexdigest() for w in words};seq=[hashlib.sha256((salt+'|'+w).encode()).hexdigest() for w in tokens];counts=Counter(tokens);streams[work]=seq;selection[work]=dict(tokens=len(tokens),types=len(counts),lookup=lookup,candidate_counts={w:counts[w] for w in words},missing_types=sorted(w for w in words if not counts[w]),standalone_c_count=counts['c'],standalone_que_count=counts['que'],sentence_support_available=False,normalization_unchanged=True);transforms[work]={'original':None,**{'word'+str(seed):np.random.default_rng(seed).permutation(len(seq)).tolist() for seed in NULL_SEEDS}}
    save(OUT/'streams.json',streams);save(OUT/'selection.json',selection);save(OUT/'transforms.json',transforms);save(OUT/'input-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['streams.json','selection.json','transforms.json']}));allstats={};predictions={}
    for work,seq in streams.items():
        lookup=selection[work]['lookup'];allstats[work]={};predictions[work]={}
        for name,indices in transforms[work].items():
            stream=seq if indices is None else [seq[i] for i in indices];assert Counter(stream)==Counter(seq);st=statistics([dict(tokens=[dict(id=i) for i in stream])],set(lookup.values()));allstats[work][name]=st;predictions[work][name]={}
            for arm in ARMS:
                rows=[]
                for w,identity in sorted(lookup.items()):
                    if identity not in st:continue
                    raw=predict_scalar(st[identity][arm],models[arm]['final']);rows.append(dict(type=w,opaque=identity,n=st[identity]['n'],sentences=1,supported=st[identity]['n']>=5,support_kind='occurrence_only',statistic=st[identity][arm],probabilities=dict(raw=raw,new=float(apply_offset([raw],cal[arm])[0]),prior=.5)))
                predictions[work][name][arm]=rows
        print('predicted',work,flush=True)
    save(OUT/'statistics.json',allstats);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['statistics.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];summary={};contrast={}
    for work,tt in predictions.items():
        summary[work]={name:{arm:{p:metrics([dict(r,**{'class':anchors[r['type']]}) for r in rr],p) for p in ['new','raw','prior']} for arm,rr in arms.items()} for name,arms in tt.items()};contrast[work]={}
        for arm in ARMS:
            actual=summary[work]['original'][arm]['new'];null=[summary[work]['word'+str(seed)][arm]['new'] for seed in NULL_SEEDS];contrast[work][arm]=dict(actual=actual,null_mean={m:float(np.mean([r[m] for r in null])) for m in ['accuracy','nll','auc']},null_auc_range=[min(r['auc'] for r in null),max(r['auc'] for r in null)],null_auc_at_least_actual=sum(r['auc']>=actual['auc'] for r in null),null_accuracy_at_least_actual=sum(r['accuracy']>=actual['accuracy'] for r in null))
        print('RESULT',work,contrast[work],flush=True)
    previous=load(ROOT/'iteration137/contrasts.json');four={'Caesar':previous['Caesar-expanded']['corrected']['concat'],'Jerome':previous['Jerome-expanded']['corrected']['concat'],**{w:contrast[w]['corrected']['actual'] for w in WORKS}};save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrast);save(OUT/'four-text-summary.json',four)
if __name__=='__main__':run()
