"""Occurrence POS agreement on the fixed shared-frame graph."""
from benchmarks.grammar_shared_frames_iteration164 import *
OUT=ROOT/'iteration165'

def score_occurrences(ids,tags,edges):
    locations={}
    for j in range(1,len(ids)-1):locations.setdefault(ids[j],{}).setdefault((ids[j-1],ids[j+1]),Counter())[tags[j]]+=1
    details=[]
    for edge in edges:
        a,b=edge['a'],edge['b'];frames=set(locations[a])&set(locations[b]);assert len(frames)==edge['shared_frames'];agreements=[];matches=pairs=0
        for frame in sorted(frames):
            aa,bb=locations[a][frame],locations[b][frame];total=sum(aa.values())*sum(bb.values());same=sum(n*bb.get(tag,0) for tag,n in aa.items());agreements.append(same/total);matches+=same;pairs+=total
        details.append(dict(**edge,frame_macro_agreement=sum(agreements)/len(agreements),matching_occurrence_pairs=matches,occurrence_pairs=pairs,no_conflicts=matches==pairs,frames_with_any_conflict=sum(x<1 for x in agreements)))
    return details

def summarize(details,eligible):
    result={}
    for threshold in [1,2]:
        selected=[r for r in details if r['shared_frames']>=threshold];n=len(selected);types={r[k] for r in selected for k in ['a','b']};pairs=sum(r['occurrence_pairs'] for r in selected);matches=sum(r['matching_occurrence_pairs'] for r in selected);result[str(threshold)]=dict(edges=n,edge_macro_frame_agreement=sum(r['frame_macro_agreement'] for r in selected)/n if n else None,pooled_occurrence_agreement=matches/pairs if pairs else None,matching_occurrence_pairs=matches,occurrence_pairs=pairs,no_conflict_edges=sum(r['no_conflicts'] for r in selected),no_conflict_fraction=sum(r['no_conflicts'] for r in selected)/n if n else None,types_involved=len(types),eligible_types=eligible,type_coverage=len(types)/eligible)
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration164/verification-manifest.json',ROOT/'iteration164/streams.json',ROOT/'iteration164/transforms.json',ROOT/'iteration164/edges.json',ROOT/'iteration164/references.json',ROOT/'iteration164/summary.json',ROOT/'iteration158/selection.json',ROOT/'iteration159/selection.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration44/annotations-truth.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Reference diagnostic ONLY: exact1644streams/68views/edges, alltypes>=5, primary>=2distinctsharedframes secondary>=1. NOedgechange or fitting. Repeatedoccurrenceweightfixed: for each edge/frame, compare Cartesianpairs ofoccurrencesoftwoDISTINCTmiddlewordtypes; exactUDPOS agreement meanwithinframe, equalweightframeswithinedge, equalweightededges primary. Secondary pooledoccurrenceagreement andno-conflictedgefraction(requireALLpairedoccurrencesPOSmatch). Missingtagsnotanticipatedcachedcomplete, assertnone; labelsneverinputedges. AttachactualtokenPOScache40/44afterfreeze, traveloccurrencePOSwithtoken through164exactnullpermutations, neverwordmodalPOSsubstitution. Freezeallframeidentity/occurrencepairdescriptorsBEFOREtagscores, then allscores before aggregate/nullcomparisons. Reportactual/nullprecisionmax/tail/coverage andoldmodalcomparison, emptysetsNone. No newannotations/reserve/sealedworks/inferrednamedPOS/nuclei/fullcoverage. This evaluatesconditionalcontextualrelation notnewedgeconfidencecriterion; no selectingno-conflictedgesusingtruth.'))
    streams=load(ROOT/'iteration164/streams.json');transforms=load(ROOT/'iteration164/transforms.json');edges=load(ROOT/'iteration164/edges.json');refs=load(ROOT/'iteration164/references.json');selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};tags={};descriptors={}
    for author in AUTHORS:
        sids=selection[author]['sent_ids'];assert not set(sids)&reserved;tokens=[t for sid in sids for t in (old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens'])];assert [hashlib.sha256(('frames164-'+author+'|'+t['word']).encode()).hexdigest() for t in tokens]==streams[author];assert all(t['pos'] for t in tokens);tags[author]=[t['pos'] for t in tokens];descriptors[author]={}
        for view,ix in transforms[author].items():
            ids=streams[author] if ix is None else [streams[author][k] for k in ix];locations={}
            for j in range(1,len(ids)-1):locations.setdefault(ids[j],{}).setdefault((ids[j-1],ids[j+1]),[]).append(j)
            descriptors[author][view]=[dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],frames=[dict(frame=list(frame),a_positions=locations[e['a']][frame],b_positions=locations[e['b']][frame]) for frame in sorted(set(locations[e['a']])&set(locations[e['b']]))]) for e in edges[author][view]]
    save(OUT/'descriptors.json',descriptors);save(OUT/'descriptors-freeze.json',dict(inputs={str(OUT/'descriptors.json'):digest(OUT/'descriptors.json')}));details={}
    for author in AUTHORS:
        details[author]={}
        for view,ix in transforms[author].items():
            ids=streams[author] if ix is None else [streams[author][k] for k in ix];tt=tags[author] if ix is None else [tags[author][k] for k in ix];details[author][view]=score_occurrences(ids,tt,edges[author][view])
    save(OUT/'details.json',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json'):digest(OUT/'details.json')}));summary={a:{v:summarize(rr,len(refs[a])) for v,rr in vv.items()} for a,vv in details.items()};contrasts={}
    for author,views in summary.items():
        contrasts[author]={}
        for threshold in ['1','2']:
            actual=views['original'][threshold];null=[views['word'+str(seed)][threshold] for seed in SEEDS];nonempty=[r['edge_macro_frame_agreement'] for r in null if r['edges']];value=actual['edge_macro_frame_agreement'];contrasts[author][threshold]=dict(actual=actual,null_nonempty=len(nonempty),null_mean=float(np.mean(nonempty)) if nonempty else None,null_max=max(nonempty) if nonempty else None,null_at_least_actual=sum(x>=value for x in nonempty) if value is not None else None)
        print(author,contrasts[author],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
