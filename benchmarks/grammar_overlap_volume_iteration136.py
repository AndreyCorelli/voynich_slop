"""Frozen anchor-free overlap classification across author context mixtures."""
from benchmarks.grammar_context_overlap_iteration135 import *
OUT=ROOT/'iteration136';SEEDS=[13600,13601,13602]
SIZES={'Jerome':[100,200,400,800,829],'Caesar':[100,200,400,800,1600,2494]}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration135/verification-manifest.json',ROOT/'iteration135/models.json',ROOT/'iteration135/calibrators.json',ROOT/'iteration135/predictions.json',ROOT/'iteration135/statistics.json',ROOT/'iteration85/anchor-budgets.json',Path('src/voynich_smt/opaque_context_overlap.py'),Path('experiments/holdouts/grammar-construction-next.json')]+[p for vv in INPUTS.values() for p in vv.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen135PRIMARYcorrectedoverlap/model/calibration/q>.5, no fitting/PP/anchors. Retainraw/frequencycontrolsfrozen, no winningarmselection. CachedJerome829/Caesar2494 only, sizesJerome100/200/400/800/full829,Caesar100/200/400/800/1600/full2494. 3fixedSHAentirecontextSIDorders seeds13600..2, nestedprefixes, NOprotectedoriginal100 => composition varies; includeoriginal100asreference andscorefullONLYonce. 31totalviews, overlappingNOTindependent. FreezeallSIDs BEFOREstatistics, predictions BEFOREreferences/metrics. Lookupsfrom135catalogueopaqueIDs; allpresenttypes primary, missing/supportonlyreport, samepresentfullmetricstoavoidcompositionillusion, original13core evaluatedonlywhenpresent plusmissingcoreexplicit; fullmatches135. Reportall3streams, typeerrortransitions againstfull, AUC/NLL/accuracy/counts, neverpoolobservations/choosebestvolume/targetcutoff. Anchorfieldsneverfeatureinputs, ID-equality/counts/sentenceboundariesonly. No newannotations/reserve/sealedlexicaltest/nuclei/defaultclaim, reuseddevelopmentnotfreshvalidation. Goal distinguishlong-contextpattern vs onepassagemixture, notprovevolumealonecausal.'))
    contexts={a:load(p['expanded']) for a,p in INPUTS.items()};old=load(ROOT/'iteration135/predictions.json');models=load(ROOT/'iteration135/models.json');cal=load(ROOT/'iteration135/calibrators.json');selection={};lookups={};byids={};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for author,context in contexts.items():
        assert len(context)==SIZES[author][-1];assert not {s['sent_id'] for s in context}&reserved;lookups[author]={r['type']:r['opaque'] for r in old[author+'-expanded']['corrected']};byids[author]={s['sent_id']:s for s in context};assert len(byids[author])==len(context);selection[author+'/original100']=[s['sent_id'] for s in load(INPUTS[author]['base'])];selection[author+'/full']=[s['sent_id'] for s in context]
        for seed in SEEDS:
            order=sorted(byids[author],key=lambda sid:hashlib.sha256((str(seed)+'|'+sid).encode()).hexdigest())
            for n in SIZES[author][:-1]:selection[author+'/'+str(seed)+'/'+str(n)]=order[:n]
    assert len(selection)==31;save(OUT/'selection.json',selection);save(OUT/'lookups.json',lookups);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['selection.json','lookups.json']}));statistics_byview={};predictions={}
    for key,sids in selection.items():
        author=key.split('/')[0];lookup=lookups[author];context=[byids[author][i] for i in sids];stats=statistics(context,set(lookup.values()));statistics_byview[key]=stats;sentences={i:0 for i in lookup.values()}
        for s in context:
            for identity in {t['id'] for t in s['tokens']}:
                if identity in sentences:sentences[identity]+=1
        predictions[key]={}
        for arm in ARMS:
            rows=[]
            for w,identity in sorted(lookup.items()):
                if identity not in stats:continue
                st=stats[identity];raw=predict_scalar(st[arm],models[arm]['final']);rows.append(dict(type=w,opaque=identity,n=st['n'],sentences=sentences[identity],supported=st['n']>=5 and sentences[identity]>=3,direction_supported=st['supported'],statistic=st[arm],probabilities=dict(raw=raw,new=float(apply_offset([raw],cal[arm])[0]),prior=.5)))
            predictions[key][arm]=rows
        print('predicted',key,flush=True)
    save(OUT/'statistics.json',statistics_byview);save(OUT/'predictions.json',predictions);save(OUT/'predictions-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['statistics.json','predictions.json']}));anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];summary={};paired={}
    for key,arms in predictions.items():
        author=key.split('/')[0];summary[key]={};paired[key]={}
        for arm,rows in arms.items():
            refs=[dict(r,**{'class':anchors[r['type']]}) for r in rows];summary[key][arm]=dict(sentences=len(selection[key]),missing_types=sorted(set(lookups[author])-{r['type'] for r in rows}),metrics={g:{p:metrics(rr,p) for p in ['new','raw','prior']} for g,rr in [('all',refs),('supported',[r for r in refs if r['supported']])]});full={r['type']:dict(r,**{'class':anchors[r['type']]}) for r in predictions[author+'/full'][arm]};present=[r['type'] for r in rows];original={r['type'] for r in old[author+'-base'][arm]};common=[r for r in refs if r['type'] in original];correct=lambda r:(r['probabilities']['new']>.5)==(anchors[r['type']]=='CCONJ');paired[key][arm]=dict(full_same_present_metrics=metrics([full[w] for w in present],'new'),original_core_present_metrics=metrics(common,'new'),missing_original_core=sorted(original-set(present)),correct_here_wrong_full=[r['type'] for r in rows if correct(r) and not correct(full[r['type']])],wrong_here_correct_full=[r['type'] for r in rows if not correct(r) and correct(full[r['type']])])
        m=summary[key]['corrected']['metrics']['all']['new'];print('RESULT',key,m['correct'],m['n'],m['auc'],m['nll'],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'paired-comparisons.json',paired)
if __name__=='__main__':run()
