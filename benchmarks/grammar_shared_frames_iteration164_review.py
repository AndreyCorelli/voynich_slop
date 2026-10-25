"""Independent pairwise frame-set intersections and all null/reference checks."""
from benchmarks.grammar_shared_frames_iteration164 import *

def independent_edges(ids):
    counts=Counter(ids);wanted=sorted(w for w,n in counts.items() if n>=5);contexts={w:set() for w in wanted}
    for j,w in enumerate(ids):
        if w in contexts and 0<j<len(ids)-1:contexts[w].add((ids[j-1],ids[j+1]))
    return [dict(a=a,b=b,shared_frames=len(contexts[a]&contexts[b])) for a,b in combinations(wanted,2) if contexts[a]&contexts[b]]

def run():
    hc=ec=mc=0
    for name in ['design-freeze','input-freeze','edges-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    views=load(ROOT/'iteration160/word-views.json');streams=load(OUT/'streams.json');transforms=load(OUT/'transforms.json');edges=load(OUT/'edges.json');refs=load(OUT/'references.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for author in AUTHORS:
        words=[w for s in views[author]['original'] for w in s['words']];ids=[hashlib.sha256(('frames164-'+author+'|'+w).encode()).hexdigest() for w in words];assert ids==streams[author];counts=Counter(words);assert not set(selection[author]['sent_ids'])&reserved;tags={}
        for sid in selection[author]['sent_ids']:
            for t in (old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens']):tags.setdefault(t['word'],Counter())[t['pos']]+=1
        expected={}
        for w,n in counts.items():
            if n<5:continue
            c=tags[w];expected[hashlib.sha256(('frames164-'+author+'|'+w).encode()).hexdigest()]=dict(word=w,n=n,modal=sorted(c,key=lambda tag:(-c[tag],tag))[0],purity=max(c.values())/n)
        assert refs[author]==expected;assert set(transforms[author])=={'original',*['word'+str(k) for k in SEEDS]}
        for view,ix in transforms[author].items():
            if view=='original':assert ix is None;seq=ids
            else:assert ix==np.random.default_rng(int(view[4:])).permutation(len(ids)).tolist();seq=[ids[k] for k in ix]
            assert Counter(seq)==Counter(ids);ee=independent_edges(seq);assert ee==edges[author][view];ec+=len(ee)
            for threshold in ['1','2']:
                selected=[e for e in ee if e['shared_frames']>=int(threshold)];right=sum(expected[e['a']]['modal']==expected[e['b']]['modal'] for e in selected);involved={e[k] for e in selected for k in ['a','b']};m=summary[author][view][threshold];assert m['edges']==len(selected) and m['same_pos']==right;assert m['precision']==(right/len(selected) if selected else None);assert m['types_involved']==len(involved) and m['type_coverage']==len(involved)/len(expected);mc+=1
            assert summary[author][view]==evaluate(ee,expected,set(expected))
        for threshold,c in contrasts[author].items():
            actual=summary[author]['original'][threshold];null=[summary[author]['word'+str(seed)][threshold] for seed in SEEDS];p=[m['precision'] for m in null if m['precision'] is not None];assert c==dict(actual=actual,null_nonempty=len(p),null_precision_mean=float(np.mean(p)) if p else None,null_precision_max=max(p) if p else None,null_precision_at_least_actual=sum(x>=actual['precision'] for x in p) if actual['precision'] is not None else None,null_edge_counts=[r['edges'] for r in null])
    save(OUT/'audit.json',dict(input_hashes_verified=hc,views_verified=68,edge_records_independently_reconstructed=ec,metric_groups_verified=mc,all_references_nulls_and_contrasts_verified=True,distinct_frame_not_token_support_verified=True,all_supported_types_and_empty_sets_retained=True,no_fitting_or_pos_inputs_to_edges=True))
if __name__=='__main__':run()
