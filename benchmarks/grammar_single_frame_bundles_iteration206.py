"""Fixed one-vs-two shared-frame evidence graphs inside robust development bundles."""
import gzip,json,math
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_pivot_deletion_iteration205 import ROOT,Path,load,save,digest,AUTHORS,EPS,ALPHA,tail,probabilities,case_matrix
OUT=ROOT/'iteration206';BASE=ROOT/'iteration193';REF=ROOT/'iteration201';OLD=ROOT/'iteration205'
POLICY='Fixed193 four development streams/normalization/boundaries/frequencyfloor5 and201CasePOS profiles; no newtext/gold/reserve/Dante/models. Freeze ALL one-or-more-sharedframe edges; exact>=2subset must equal193; two views1frame/2frames, no targetchoice. Freeze anonymous endpointbundles with>=2edges,>=2distinctsharedframes and>=2pivots before reference load. Compare SAME205primary total−max(largestedge,largestpivot), original edge/frame/Cartesianweights peredge with no renormalization. Reproduce SAME203199wordPOSCasepermutations, preserve correlations; graph-specific per-author max-over-ALLeligiblebundles tail(1+exceedances)/200/positive1e-12/tie1e-12/alpha.05. Oneframeedge never a reliable standaloneconstraint. Exactold205twoframe primary stats/tails/detections required; allauthors/retained-lost-new/neweligibility/degree/frame/occurrence reuse and overlaps. No statistic/threshold/winner selection or annotation-free predictor/identity/POSrestoration claim; devoracle evidencecoverage diagnostic, finite conditionalnull caveats preserved.'

def gzsave(path,value):
    with gzip.open(path,'wt') as f:json.dump(value,f)

def all_edges(g):
    ids=g['ids'];pos=g['positions'];counts=Counter(ids);frames=defaultdict(lambda:defaultdict(list))
    for i in range(1,len(ids)-1):
        if pos[i] and pos[i-1] and pos[i+1] and counts[ids[i]]>=5:frames[(ids[i-1],ids[i+1])][ids[i]].append(i)
    pairs=defaultdict(list)
    for f,centers in sorted(frames.items()):
        words=sorted(centers)
        for i,a in enumerate(words):
            for b in words[i+1:]:pairs[(a,b)].append(dict(frame=list(f),a_positions=centers[a],b_positions=centers[b]))
    return [dict(a=a,b=b,shared_frames=len(ff),frames=ff) for (a,b),ff in sorted(pairs.items())]

def bundles_for(dd):
    members=defaultdict(list)
    for i,e in enumerate(dd):
        for word in [e['a'],e['b']]:members[word].append(i)
    result=[]
    for word,ix in sorted(members.items()):
        frames=set();pivots=set();uses=0
        for i in ix:
            e=dd[i];side='a_positions' if e['a']==word else 'b_positions'
            for f in e['frames']:frames.add(tuple(f['frame']));pivots.update(f[side]);uses+=len(f[side])
        if len(ix)>=2 and len(frames)>=2 and len(pivots)>=2:result.append(dict(word=word,edges=ix,degree=len(ix),unique_frames=len(frames),unique_pivot_occurrences=len(pivots),total_pivot_occurrence_uses=uses,pivot_occurrence_reuse=uses/len(pivots)))
    return result

def edge_terms(e,g,ref,probs):
    pp=[];qq=[];ww=[];ee=[]
    for f in e['frames']:
        weight=1/(e['shared_frames']*len(f['a_positions'])*len(f['b_positions']))
        for p in f['a_positions']:
            a=probs[(g['ids'][p],ref['pos'][p])]
            for q in f['b_positions']:
                b=probs[(g['ids'][q],ref['pos'][q])];pp.append(p);qq.append(q);ww.append(weight);ee.append(sum(v*b.get(c,0) for c,v in a.items()))
    return pp,qq,np.array(ww),np.array(ee)

def score_bundles(dd,bb,ev,termdata,cm):
    sums=[];edge_max=[];pivot_max=[];stats=[]
    for b in bb:
        bypivot=defaultdict(list)
        for i in b['edges']:
            pp,qq,weights,expected=termdata[i];side_a=dd[i]['a']==b['word']
            for p,q,w,x in zip(pp,qq,weights,expected):bypivot[p if side_a else q].append((q if side_a else p,w,x))
        total=ev[:,b['edges']].sum(axis=1);check=np.zeros(len(cm));pm=np.full(len(cm),-np.inf)
        for p,terms in sorted(bypivot.items()):
            qq=[t[0] for t in terms];weights=np.array([t[1] for t in terms]);expect=sum(t[1]*t[2] for t in terms);v=(((cm[:,p,None]>0)&(cm[:,p,None]==cm[:,qq]))@weights)-expect;check+=v;pm=np.maximum(pm,v)
        np.testing.assert_allclose(total,check,atol=1e-9,rtol=1e-9);em=ev[:,b['edges']].max(axis=1);sums.append(total);edge_max.append(em);pivot_max.append(pm);stats.append(total-np.maximum(em,pm))
    return {n:np.column_stack(v) for n,v in [('sum',sums),('largest_edge',edge_max),('largest_pivot',pivot_max),('statistic',stats)]}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_pivot_deletion_iteration205.py'),BASE/'graphs.json',REF/'development-references.json']+[OLD/n for n in ['verification-manifest.json','candidates.json','details.json','statistics.json']];save(OUT/'design-freeze.json',dict(policy=POLICY,inputs={str(p):digest(p) for p in paths}))
    for p,h in load(OLD/'verification-manifest.json').items():assert digest(Path(p))==h
    graphs=load(BASE/'graphs.json');edges={a:all_edges(graphs[a]) for a in AUTHORS};views={};bundles={}
    for a in AUTHORS:
        assert [e for e in edges[a] if e['shared_frames']>=2]==graphs[a]['descriptors'];views[a]={'one_frame':list(range(len(edges[a]))),'two_frames':[i for i,e in enumerate(edges[a]) if e['shared_frames']>=2]};bundles[a]={v:bundles_for([edges[a][i] for i in ix]) for v,ix in views[a].items()};gzsave(OUT/(a+'-edges.json.gz'),edges[a])
    save(OUT/'view-indices.json',views);gzsave(OUT/'bundles.json.gz',bundles);save(OUT/'graph-bundle-freeze.json',{p.name:digest(p) for p in sorted(OUT.glob('*edges.json.gz'))+[OUT/'view-indices.json',OUT/'bundles.json.gz']})
    refs=load(REF/'development-references.json');olddetails=load(OLD/'details.json');oldstats=load(OLD/'statistics.json');details={};summary={};transitions={}
    for a in AUTHORS:
        g=graphs[a];ref=refs[a];cm=case_matrix(g,ref);probs=probabilities(g,ref);terms=[edge_terms(e,g,ref,probs) for e in edges[a]];ev=[]
        for pp,qq,ww,expect in terms:ev.append((((cm[:,pp]>0)&(cm[:,pp]==cm[:,qq]))@ww)-float(ww@expect))
        ev=np.column_stack(ev);np.savez_compressed(OUT/(a+'-edge-residuals.npz'),values=ev);details[a]={};summary[a]={}
        for view,ix in views[a].items():
            dd=[edges[a][i] for i in ix];bb=bundles[a][view];components=score_bundles(dd,bb,ev[:,ix],[terms[i] for i in ix],cm);np.savez_compressed(OUT/(a+'-'+view+'-components.npz'),**components);matrix=components['statistic'];maxima=matrix[1:].max(axis=1);rr=[]
            for j,b in enumerate(bb):
                real=float(matrix[0,j]);raw=float(tail(matrix[1:,j],real));adjusted=float(tail(maxima,real));rr.append(dict(**b,statistic=real,raw_tail=raw,max_stat_tail=adjusted,adjusted_detected=bool(adjusted<=ALPHA and real>EPS),original_sum=float(components['sum'][0,j]),largest_edge=float(components['largest_edge'][0,j]),largest_pivot=float(components['largest_pivot'][0,j])))
            details[a][view]=rr;det=[r for r in rr if r['adjusted_detected']];edgeuse=Counter(i for r in det for i in r['edges']);summary[a][view]=dict(edges=len(dd),eligible_bundles=len(bb),detected=len(det),detected_degrees=[r['degree'] for r in det],detected_unique_frames=[r['unique_frames'] for r in det],detected_unique_pivots=[r['unique_pivot_occurrences'] for r in det],detected_pivot_reuse=[r['pivot_occurrence_reuse'] for r in det],detected_incident_edges=len(edgeuse),shared_incident_edges=sum(v>1 for v in edgeuse.values()))
            if view=='two_frames':
                assert [b['word'] for b in bb]==oldstats[a]['edge_or_pivot']['bundle_order'];np.testing.assert_allclose(matrix,oldstats[a]['edge_or_pivot']['values'],atol=1e-9,rtol=1e-9);assert {r['word'] for r in det}=={r['word'] for r in olddetails[a]['edge_or_pivot'] if r['adjusted_detected']}
        oldset={r['word'] for r in details[a]['two_frames'] if r['adjusted_detected']};newset={r['word'] for r in details[a]['one_frame'] if r['adjusted_detected']};oldeligible={r['word'] for r in details[a]['two_frames']};transitions[a]=dict(retained=sorted(oldset&newset),lost=sorted(oldset-newset),gained=sorted(newset-oldset),gained_newly_eligible=sorted((newset-oldset)-oldeligible));print(a,summary[a],{k:len(v) for k,v in transitions[a].items()},flush=True)
    for n,obj in [('details',details),('summary',summary),('transitions',transitions)]:save(OUT/(n+'.json'),obj)
if __name__=='__main__':run()
