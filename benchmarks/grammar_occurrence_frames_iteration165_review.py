"""Independent Cartesian occurrence comparisons on frozen descriptors."""
from benchmarks.grammar_occurrence_frames_iteration165 import *

def run():
    hc=ec=pc=mc=0
    for name in ['design-freeze','descriptors-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    streams=load(ROOT/'iteration164/streams.json');transforms=load(ROOT/'iteration164/transforms.json');edges=load(ROOT/'iteration164/edges.json');descriptors=load(OUT/'descriptors.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');refs=load(ROOT/'iteration164/references.json');selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for author in AUTHORS:
        sids=selection[author]['sent_ids'];assert not set(sids)&reserved;tokens=[t for sid in sids for t in (old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens'])];assert all(t['pos'] for t in tokens);original=streams[author];tags=[t['pos'] for t in tokens];assert original==[hashlib.sha256(('frames164-'+author+'|'+t['word']).encode()).hexdigest() for t in tokens]
        for view,ix in transforms[author].items():
            permutation=list(range(len(original))) if ix is None else ix;ids=[original[k] for k in permutation];tt=[tags[k] for k in permutation];contexts={}
            for j in range(1,len(ids)-1):contexts.setdefault(ids[j],{}).setdefault((ids[j-1],ids[j+1]),[]).append(j)
            dd=descriptors[author][view];assert [(r['a'],r['b'],r['shared_frames']) for r in dd]==[(r['a'],r['b'],r['shared_frames']) for r in edges[author][view]];computed=[]
            for r in dd:
                a,b=r['a'],r['b'];shared=sorted(set(contexts[a])&set(contexts[b]));assert r['frames']==[dict(frame=list(frame),a_positions=contexts[a][frame],b_positions=contexts[b][frame]) for frame in shared];assert len(shared)==r['shared_frames'];agreements=[];matches=total=0
                for frame in r['frames']:
                    pairs=[(tt[j],tt[k]) for j in frame['a_positions'] for k in frame['b_positions']];same=sum(a==b for a,b in pairs);agreements.append(same/len(pairs));matches+=same;total+=len(pairs);pc+=len(pairs)
                computed.append(dict(a=a,b=b,shared_frames=len(shared),frame_macro_agreement=sum(agreements)/len(agreements),matching_occurrence_pairs=matches,occurrence_pairs=total,no_conflicts=matches==total,frames_with_any_conflict=sum(v<1 for v in agreements)));ec+=1
            assert details[author][view]==computed;assert summary[author][view]==summarize(computed,len(refs[author]))
            for threshold in [1,2]:
                rr=[r for r in computed if r['shared_frames']>=threshold];m=summary[author][view][str(threshold)];assert m['edges']==len(rr);assert m['edge_macro_frame_agreement']==(sum(r['frame_macro_agreement'] for r in rr)/len(rr) if rr else None);assert m['no_conflict_edges']==sum(r['no_conflicts'] for r in rr);mc+=1
        for threshold,c in contrasts[author].items():
            actual=summary[author]['original'][threshold];null=[summary[author]['word'+str(k)][threshold] for k in SEEDS];p=[m['edge_macro_frame_agreement'] for m in null if m['edges']];v=actual['edge_macro_frame_agreement'];assert c==dict(actual=actual,null_nonempty=len(p),null_mean=float(np.mean(p)) if p else None,null_max=max(p) if p else None,null_at_least_actual=sum(x>=v for x in p) if v is not None else None)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,views_verified=68,edge_descriptors_independently_verified=ec,cartesian_occurrence_pairs_compared=pc,metric_groups_verified=mc,occurrence_labels_travel_with_permutation=True,all_nulls_and_empty_outcomes_verified=True,no_edge_changes_or_label_based_selection=True))
if __name__=='__main__':run()
