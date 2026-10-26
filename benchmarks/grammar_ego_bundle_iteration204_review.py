"""Independent bundle reconstruction, explicit deletions and null-max tails."""
from collections import Counter
from benchmarks.grammar_ego_bundle_iteration204 import OUT,BASE,SOURCE,AUTHORS,STATS,EPS,ALPHA,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close

def explicit_stat(values,kind):
    if kind=='sum':return sum(values)
    if kind=='mean':return sum(values)/len(values)
    return min(sum(v for j,v in enumerate(values) if j!=removed) for removed in range(len(values)))

def pv(null,real):return (1+sum(x>=real-EPS for x in null))/(1+len(null))

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'bundle-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for p,h in load(SOURCE/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    assert (OUT/'bundle-freeze.json').stat().st_mtime_ns <= (OUT/'details.json').stat().st_mtime_ns
    graphs=load(BASE/'graphs.json');edges=load(SOURCE/'edge-details.json');nulls=load(SOURCE/'null-surplus-matrices.json');bundles=load(OUT/'bundles.json');details=load(OUT/'details.json');summaries=load(OUT/'summary.json');savednull=load(OUT/'null-bundle-statistics.json');overlap=load(OUT/'detected-bundle-overlap.json');nb=ng=nn=0
    for a in AUTHORS:
        dd=graphs[a]['descriptors'];words=sorted({e[k] for e in dd for k in ['a','b']});rebuilt=[]
        for word in words:
            ix=[i for i,e in enumerate(dd) if word in [e['a'],e['b']]];uses=[];frames=set();peredge=[]
            for i in ix:
                e=dd[i];side='a_positions' if word==e['a'] else 'b_positions';pp=[]
                for f in e['frames']:uses.extend(f[side]);pp.extend(f[side]);frames.add(tuple(f['frame']))
                peredge.append(set(pp))
            remaining=[len(set().union(*(pp for j,pp in enumerate(peredge) if j!=removed))) for removed in range(len(peredge))];rebuilt.append(dict(word=word,edges=ix,degree=len(ix),unique_frames=len(frames),unique_pivot_occurrences=len(set(uses)),total_pivot_occurrence_uses=len(uses),pivot_occurrence_reuse=len(uses)/len(set(uses)) if uses else None,min_unique_pivot_occurrences_after_edge_deletion=min(remaining,default=0)))
        close(rebuilt,bundles[a]);nb+=len(rebuilt);old={e[k] for e in edges[a] if e['adjusted_detected'] for k in ['a','b']}
        for kind in STATS:
            eligible=[b for b in rebuilt if kind!='drop_strongest_sum' or b['degree']>=2];observed=[explicit_stat([edges[a][i]['surplus'] for i in b['edges']],kind) for b in eligible];matrix=[[explicit_stat([row[i] for i in b['edges']],kind) for b in eligible] for row in nulls[a]];maximum=[max(row) for row in matrix] if eligible else [];close(dict(bundle_order=[b['word'] for b in eligible],statistics=matrix,maxima=maximum),savednull[a][kind]);rr=[]
            for j,b in enumerate(eligible):
                values=[row[j] for row in matrix];raw=pv(values,observed[j]);adjusted=pv(maximum,observed[j]);assert adjusted+EPS>=raw;mean=sum(values)/len(values);variance=sum((v-mean)**2 for v in values)/len(values);rr.append(dict(**b,statistic=observed[j],raw_tail=raw,max_stat_tail=adjusted,raw_detected=raw<=ALPHA and observed[j]>EPS,adjusted_detected=adjusted<=ALPHA and observed[j]>EPS,is_previously_detected_edge_endpoint=b['word'] in old,null_min=min(values),null_max=max(values),null_mean=mean,sampled_null_variance=variance))
            close(rr,details[a][kind]);det=[r for r in rr if r['adjusted_detected']];detwords={r['word'] for r in det};edgeuses=Counter(i for r in det for i in r['edges']);s=dict(eligible_bundles=len(eligible),raw_detected=sum(r['raw_detected'] for r in rr),max_stat_detected=len(det),previous_edge_detected_endpoint_types=len(old),detected_centers_in_previous_endpoints=len(detwords&old),additional_centers=len(detwords-old),detected_degrees=[r['degree'] for r in det],detected_unique_pivot_occurrences=[r['unique_pivot_occurrences'] for r in det],detected_pivot_occurrence_reuse=[r['pivot_occurrence_reuse'] for r in det],detected_incident_edges=len(edgeuses),incident_edges_shared_between_detected_bundles=sum(v>1 for v in edgeuses.values()));close(s,summaries[a][kind])
            expectedoverlap=[dict(left=x['word'],right=y['word'],shared_edges=sorted(set(x['edges'])&set(y['edges']))) for i,x in enumerate(det) for y in det[i+1:] if set(x['edges'])&set(y['edges'])];assert expectedoverlap==overlap[a][kind];ng+=len(eligible);nn+=len(eligible)*len(matrix)
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,anonymous_endpoint_bundles_rebuilt=nb,real_statistic_bundle_groups=ng,null_statistic_bundle_groups=nn,all_primary_deletions_replayed_by_explicit_enumeration=True,all_per_author_maxima_and_raw_adjusted_tails_replayed=True,all_overlap_and_occurrence_reuse_replayed=True,no_new_gold_or_prediction_changes=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
