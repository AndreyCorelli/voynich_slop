"""Unsupervised two-sided-frame relations, evaluated only after edge freezing."""
from benchmarks.grammar_broad_author_iteration158 import *
from itertools import combinations
OUT=ROOT/'iteration164';AUTHORS=['Caesar','Jerome','Cicero','Palladius'];SEEDS=list(range(16400,16416))

def frame_edges(ids):
    counts=Counter(ids);eligible={w for w,n in counts.items() if n>=5};frames={}
    for j in range(1,len(ids)-1):
        if ids[j] in eligible:frames.setdefault((ids[j-1],ids[j+1]),set()).add(ids[j])
    shared=Counter()
    for ww in frames.values():
        for a,b in combinations(sorted(ww),2):shared[(a,b)]+=1
    return [dict(a=a,b=b,shared_frames=n) for (a,b),n in sorted(shared.items())]

def evaluate(edges,reference,eligible):
    out={}
    for threshold in [1,2]:
        selected=[e for e in edges if e['shared_frames']>=threshold];involved={e[k] for e in selected for k in ['a','b']};correct=sum(reference[e['a']]['modal']==reference[e['b']]['modal'] for e in selected);tagpairs=Counter('|'.join(sorted([reference[e['a']]['modal'],reference[e['b']]['modal']])) for e in selected)
        out[str(threshold)]=dict(edges=len(selected),same_pos=correct,precision=correct/len(selected) if selected else None,types_involved=len(involved),eligible_types=len(eligible),type_coverage=len(involved)/len(eligible),tag_pairs=dict(sorted(tagpairs.items())))
    return out

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration163/verification-manifest.json',ROOT/'iteration160/word-views.json',ROOT/'iteration158/selection.json',ROOT/'iteration159/selection.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration44/annotations-truth.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Fourexactcachedoriginalwordstreams160Caesar/Jerome/Cicero/Palladius. FlatconcatenatedopaqueIDequality/orderonly, no anchors/POS/names/classcatalogueforedges; no sentenceboundaries. Alltypes>=5occurrences eligible, purityNOTfilter. Frame=(leftID,rightID); fordistincteligiblemiddletypes countDISTINCTsharedframes (not repeatedtokens). PRIMARY>=2sharedframes, secondary>=1 allreported no supporttuning. Inferredrelation predicts SAME EXACT modalUDPOS, not sevenPOSunion; tiesmodallexical, cachedreferenceonlyafteredgesfrozen. No clustering/learnedboundary/namedPOS/nuclei. Eachstream original+16globalwordshuffle permutations16400..15 preservealltypecounts; freezeinputs/permutations beforeedges, allactual+null edgesbeforePOSreferences/metrics. Report pairprecision, counts, supportedtypecoverage, classpairmix; emptyedgesprecisionNone neverperfect. Nullprecision distribution/max/tail descriptive andedgecounts/coverage, notindependentformalreplications. Labelsusedonlyevaluation; no newannotations/reserve/sealedworks. Sparse/highprecision relationpotentiallyusefulonlywithcoverage andnulladvantage; no fulltaggingclaim.'))
    views=load(ROOT/'iteration160/word-views.json');selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};streams={};lookups={};transforms={}
    for author in AUTHORS:
        words=[w for s in views[author]['original'] for w in s['words']];lookup={w:hashlib.sha256(('frames164-'+author+'|'+w).encode()).hexdigest() for w in set(words)};streams[author]=[lookup[w] for w in words];lookups[author]=lookup;transforms[author]={'original':None,**{'word'+str(seed):np.random.default_rng(seed).permutation(len(words)).tolist() for seed in SEEDS}}
    for n,x in [('streams',streams),('transforms',transforms)]:save(OUT/(n+'.json'),x)
    save(OUT/'input-freeze.json',dict(inputs={str(OUT/(n+'.json')):digest(OUT/(n+'.json')) for n in ['streams','transforms']}));edges={}
    for author,seq in streams.items():
        edges[author]={}
        for view,ix in transforms[author].items():edges[author][view]=frame_edges(seq if ix is None else [seq[k] for k in ix])
    save(OUT/'edges.json',edges);save(OUT/'edges-freeze.json',dict(inputs={str(OUT/'edges.json'):digest(OUT/'edges.json')}));old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};references={};summary={};contrasts={}
    for author in AUTHORS:
        sids=selection[author]['sent_ids'];assert not set(sids)&reserved;cc={}
        for sid in sids:
            for t in (old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens']):cc.setdefault(t['word'],Counter())[t['pos']]+=1
        refs={lookups[author][w]:dict(word=w,n=sum(c.values()),modal=sorted(c,key=lambda tag:(-c[tag],tag))[0],purity=max(c.values())/sum(c.values())) for w,c in cc.items() if sum(c.values())>=5};references[author]=refs;summary[author]={view:evaluate(ee,refs,set(refs)) for view,ee in edges[author].items()};contrasts[author]={}
        for threshold in ['1','2']:
            actual=summary[author]['original'][threshold];null=[summary[author]['word'+str(seed)][threshold] for seed in SEEDS];nonempty=[r['precision'] for r in null if r['precision'] is not None];contrasts[author][threshold]=dict(actual=actual,null_nonempty=len(nonempty),null_precision_mean=float(np.mean(nonempty)) if nonempty else None,null_precision_max=max(nonempty) if nonempty else None,null_precision_at_least_actual=sum(p>=actual['precision'] for p in nonempty) if actual['precision'] is not None else None,null_edge_counts=[r['edges'] for r in null]);
        print(author,contrasts[author],flush=True)
    save(OUT/'references.json',references);save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
