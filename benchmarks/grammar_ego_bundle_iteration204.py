"""Anonymous endpoint bundles with max-statistic and single-edge-deletion controls."""
from collections import defaultdict,Counter
import numpy as np
from benchmarks.grammar_pair_detectability_iteration203 import ROOT,Path,load,save,digest,AUTHORS,EPS,ALPHA,tail
OUT=ROOT/'iteration204';BASE=ROOT/'iteration193';SOURCE=ROOT/'iteration203';STATS=['sum','mean','drop_strongest_sum']
POLICY='Development-only fixed193graphs/reused203observed and199joint wordxPOS null matrices. Before loading surplus define every endpoint ego-bundle as all incident graph edges, no annotations; freeze all members and structure diagnostics. Comparator sum/mean eligibledegree>=1; PRIMARYdrop_strongest_sum eligibledegree>=2, min single-edge-deletion remaining sum = total-max. Apply identical operation in EACHnull, preserving correlations; per-author per-stat maximum over ALLeligible bundles adjusted tails, raw tails, same(1+exceedances)/200/tolerance1e-12/alpha.05 and positivestat>1e-12. Three statfamilies separate, no bestfamily claim/cross-familycorrection; primary fixed. Store all candidates/non-detections, degrees/uniquecontexts/pivotoccurrence reuse; primary deletion avoids one edge alone but not necessarily shared-observation dependence. Compare supportedcenters with203detectededgeendpointtypes, counts extra centers and sharedunderlyingedges; count-types not independent confirmations or Latinwordidentities. No transitiveCase/POSclass assumption, models, selections/featurechanges/newlabels/raw/Dante/reserve inputs or annotation-freeinference claim. Oracle evidence localization only, conditionalexchangeability/conservative finite199null/resolution.005 caveats preserved.'

def bundle_structure(dd):
    neighbors=defaultdict(list)
    for i,e in enumerate(dd):
        for word in [e['a'],e['b']]:neighbors[word].append(i)
    result=[]
    for word,ix in sorted(neighbors.items()):
        occurrences=[];frames=set();edge_pivots={}
        for i in ix:
            e=dd[i];key='a_positions' if e['a']==word else 'b_positions';pp=set()
            for f in e['frames']:frames.add(tuple(f['frame']));pp.update(f[key]);occurrences.extend(f[key])
            edge_pivots[i]=pp
        unique=set(occurrences);min_remaining=min((len(set().union(*(p for j,p in edge_pivots.items() if j!=i))) for i in ix),default=0)
        result.append(dict(word=word,edges=ix,degree=len(ix),unique_frames=len(frames),unique_pivot_occurrences=len(unique),total_pivot_occurrence_uses=len(occurrences),pivot_occurrence_reuse=len(occurrences)/len(unique) if unique else None,min_unique_pivot_occurrences_after_edge_deletion=min_remaining))
    return result

def statistic(values,kind):
    total=values.sum(axis=-1)
    return total if kind=='sum' else (total/values.shape[-1] if kind=='mean' else total-values.max(axis=-1))

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),BASE/'graphs.json']+[SOURCE/n for n in ['verification-manifest.json','edge-details.json','null-surplus-matrices.json','summary.json']];save(OUT/'design-freeze.json',dict(policy=POLICY,statistics=STATS,alpha=ALPHA,tolerance=EPS,inputs={str(p):digest(p) for p in paths}))
    for p,h in load(SOURCE/'verification-manifest.json').items():assert digest(Path(p))==h
    graphs=load(BASE/'graphs.json');bundles={a:bundle_structure(graphs[a]['descriptors']) for a in AUTHORS};save(OUT/'bundles.json',bundles);save(OUT/'bundle-freeze.json',{'bundles.json':digest(OUT/'bundles.json')})
    edges=load(SOURCE/'edge-details.json');nulls=load(SOURCE/'null-surplus-matrices.json');details={};summary={};overlap={};null_stats={}
    for a in AUTHORS:
        observed=np.array([e['surplus'] for e in edges[a]]);null=np.array(nulls[a]);oldtypes={e[k] for e in edges[a] if e['adjusted_detected'] for k in ['a','b']};details[a]={};summary[a]={};null_stats[a]={};overlap[a]={}
        for kind in STATS:
            bb=[b for b in bundles[a] if kind!='drop_strongest_sum' or b['degree']>=2];values=np.array([statistic(observed[b['edges']],kind) for b in bb]);matrix=np.column_stack([statistic(null[:,b['edges']],kind) for b in bb]) if bb else np.empty((len(null),0));maximum=matrix.max(axis=1) if bb else np.array([]);rows=[]
            for j,b in enumerate(bb):
                v=float(values[j]);raw=float(tail(matrix[:,j],v));adjusted=float(tail(maximum,v));rows.append(dict(**b,statistic=v,raw_tail=raw,max_stat_tail=adjusted,raw_detected=bool(raw<=ALPHA and v>EPS),adjusted_detected=bool(adjusted<=ALPHA and v>EPS),is_previously_detected_edge_endpoint=b['word'] in oldtypes,null_min=float(matrix[:,j].min()),null_max=float(matrix[:,j].max()),null_mean=float(matrix[:,j].mean()),sampled_null_variance=float(matrix[:,j].var())))
            detected=[r for r in rows if r['adjusted_detected']];detectedwords={r['word'] for r in detected};edgeuse=Counter(i for r in detected for i in r['edges']);details[a][kind]=rows;null_stats[a][kind]=dict(bundle_order=[b['word'] for b in bb],statistics=matrix.tolist(),maxima=maximum.tolist());summary[a][kind]=dict(eligible_bundles=len(bb),raw_detected=sum(r['raw_detected'] for r in rows),max_stat_detected=len(detected),previous_edge_detected_endpoint_types=len(oldtypes),detected_centers_in_previous_endpoints=len(detectedwords&oldtypes),additional_centers=len(detectedwords-oldtypes),detected_degrees=[r['degree'] for r in detected],detected_unique_pivot_occurrences=[r['unique_pivot_occurrences'] for r in detected],detected_pivot_occurrence_reuse=[r['pivot_occurrence_reuse'] for r in detected],detected_incident_edges=len(edgeuse),incident_edges_shared_between_detected_bundles=sum(n>1 for n in edgeuse.values()))
            overlap[a][kind]=[dict(left=x['word'],right=y['word'],shared_edges=sorted(set(x['edges'])&set(y['edges']))) for i,x in enumerate(detected) for y in detected[i+1:] if set(x['edges'])&set(y['edges'])]
        print(a,summary[a],flush=True)
    for n,obj in [('details',details),('summary',summary),('detected-bundle-overlap',overlap),('null-bundle-statistics',null_stats)]:save(OUT/(n+'.json'),obj)
if __name__=='__main__':run()
