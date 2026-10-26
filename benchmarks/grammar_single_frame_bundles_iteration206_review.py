"""Independent word-context intersections, count-product scores and pivot-weight replay."""
import gzip,json,random
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_single_frame_bundles_iteration206 import OUT,BASE,REF,OLD,AUTHORS,EPS,ALPHA,Path,load,save,digest
from benchmarks.grammar_pair_detectability_iteration203 import SEEDS,CASES
from benchmarks.grammar_case_applicability_iteration180_review import close

def gzload(p):
    with gzip.open(p,'rt') as f:return json.load(f)
def pv(null,real):return (1+sum(v>=real-EPS for v in null))/(1+len(null))

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'graph-bundle-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for p,h in load(OLD/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    graphs=load(BASE/'graphs.json');refs=load(REF/'development-references.json');views=load(OUT/'view-indices.json');bundles=gzload(OUT/'bundles.json.gz');details=load(OUT/'details.json');summary=load(OUT/'summary.json');transitions=load(OUT/'transitions.json');olddetail=load(OLD/'details.json');oldstats=load(OLD/'statistics.json');edgecount=bundlecount=componentscount=0
    for a in AUTHORS:
        g=graphs[a];ref=refs[a];ids=g['ids'];pos=g['positions'];frequency=Counter(ids);byword=defaultdict(lambda:defaultdict(list))
        for i in range(1,len(ids)-1):
            if pos[i] and pos[i-1] and pos[i+1] and frequency[ids[i]]>=5:byword[ids[i]][(ids[i-1],ids[i+1])].append(i)
        rebuilt=[];words=sorted(byword)
        for n,x in enumerate(words):
            for y in words[n+1:]:
                shared=sorted(set(byword[x])&set(byword[y]))
                if shared:rebuilt.append(dict(a=x,b=y,shared_frames=len(shared),frames=[dict(frame=list(f),a_positions=byword[x][f],b_positions=byword[y][f]) for f in shared]))
        assert rebuilt==gzload(OUT/(a+'-edges.json.gz'));assert [e for e in rebuilt if e['shared_frames']>=2]==g['descriptors'];assert views[a]==dict(one_frame=list(range(len(rebuilt))),two_frames=[i for i,e in enumerate(rebuilt) if e['shared_frames']>=2]);edgecount+=len(rebuilt)
        buckets=defaultdict(list);counts=defaultdict(Counter);codes={'':0,**{c:i+1 for i,c in enumerate(sorted(CASES))}}
        for i,p in enumerate(pos):
            if p:k=(ids[i],ref['pos'][i]);buckets[k].append(i);counts[k][ref['case'][i]]+=1
        probs={k:np.array([v[c]/sum(v.values()) for c in sorted(CASES)]) for k,v in counts.items()};original=np.array([codes[c] for c in ref['case']],dtype=np.int8);cases=[original]
        for seed in SEEDS:
            rng=random.Random(seed);cc=original.copy()
            for k,pp in sorted(buckets.items()):
                vv=[int(original[i]) for i in pp];rng.shuffle(vv);cc[pp]=vv;assert Counter(cc[pp].tolist())==Counter(original[pp].tolist())
            cases.append(cc)
        cm=np.stack(cases);ev=[]
        for e in rebuilt:
            joint=np.zeros(len(cm));expected=0.
            for f in e['frames']:
                pp=f['a_positions'];qq=f['b_positions'];av=np.array([(cm[:,pp]==c).sum(1) for c in range(1,8)]);bv=np.array([(cm[:,qq]==c).sum(1) for c in range(1,8)]);joint+=(av*bv).sum(0)/(len(pp)*len(qq)*len(e['frames']));pavg=sum((probs[(ids[i],ref['pos'][i])] for i in pp),np.zeros(7))/len(pp);qavg=sum((probs[(ids[i],ref['pos'][i])] for i in qq),np.zeros(7))/len(qq);expected+=float(pavg@qavg)/len(e['frames'])
            ev.append(joint-expected)
        ev=np.column_stack(ev)
        with np.load(OUT/(a+'-edge-residuals.npz')) as z:np.testing.assert_allclose(ev,z['values'],atol=1e-9,rtol=1e-9)
        computed_details={}
        for view,indices in views[a].items():
            dd=[rebuilt[i] for i in indices];ve=ev[:,indices];eligible=[]
            for word in sorted({e[k] for e in dd for k in ['a','b']}):
                ix=[i for i,e in enumerate(dd) if word in [e['a'],e['b']]];ff=set();pp=[]
                for i in ix:
                    e=dd[i];side='a_positions' if e['a']==word else 'b_positions'
                    for f in e['frames']:ff.add(tuple(f['frame']));pp.extend(f[side])
                if len(ix)>=2 and len(ff)>=2 and len(set(pp))>=2:eligible.append(dict(word=word,edges=ix,degree=len(ix),unique_frames=len(ff),unique_pivot_occurrences=len(set(pp)),total_pivot_occurrence_uses=len(pp),pivot_occurrence_reuse=len(pp)/len(set(pp))))
            assert eligible==bundles[a][view];calc={n:[] for n in ['sum','largest_edge','largest_pivot','statistic']}
            for b in eligible:
                weighted=defaultdict(list)
                for i in b['edges']:
                    e=dd[i];side='a_positions' if e['a']==b['word'] else 'b_positions';other='b_positions' if side=='a_positions' else 'a_positions'
                    for f in e['frames']:
                        for p in f[side]:
                            for q in f[other]:weighted[p].append((q,1/(len(e['frames'])*len(f['a_positions'])*len(f['b_positions']))))
                pc=[]
                for p,terms in sorted(weighted.items()):
                    q=[t[0] for t in terms];w=np.array([t[1] for t in terms]);ppr=probs[(ids[p],ref['pos'][p])];ex=sum(wj*float(ppr@probs[(ids[qj],ref['pos'][qj])]) for qj,wj in terms);value=np.zeros(len(cm))
                    for c in range(1,8):value+=(cm[:,p]==c)*((cm[:,q]==c)@w)
                    pc.append(value-ex)
                pc=np.column_stack(pc);total=ve[:,b['edges']].sum(1);np.testing.assert_allclose(pc.sum(1),total,atol=1e-9,rtol=1e-9);em=ve[:,b['edges']].max(1);pm=pc.max(1);stat=np.minimum((total[:,None]-ve[:,b['edges']]).min(1),(total[:,None]-pc).min(1))
                for name,value in [('sum',total),('largest_edge',em),('largest_pivot',pm),('statistic',stat)]:calc[name].append(value)
                componentscount+=len(cm)
            calc={n:np.column_stack(v) for n,v in calc.items()}
            with np.load(OUT/(a+'-'+view+'-components.npz')) as z:
                assert set(z.files)==set(calc)
                for n,v in calc.items():np.testing.assert_allclose(v,z[n],atol=1e-9,rtol=1e-9)
            matrix=calc['statistic'];maximum=matrix[1:].max(1);rr=[]
            for j,b in enumerate(eligible):
                real=float(matrix[0,j]);raw=pv(matrix[1:,j],real);adjusted=pv(maximum,real);rr.append(dict(**b,statistic=real,raw_tail=raw,max_stat_tail=adjusted,adjusted_detected=bool(adjusted<=ALPHA and real>EPS),original_sum=float(calc['sum'][0,j]),largest_edge=float(calc['largest_edge'][0,j]),largest_pivot=float(calc['largest_pivot'][0,j])))
            # Float arithmetic is independently factored; tolerate small statistic drift.
            for x,y in zip(rr,details[a][view],strict=True):
                for n in x:
                    if isinstance(x[n],float):assert abs(x[n]-y[n])<1e-9,(a,view,n,x[n],y[n])
                    else:assert x[n]==y[n]
            det=[r for r in rr if r['adjusted_detected']];reuse=Counter(i for r in det for i in r['edges']);expected=dict(edges=len(dd),eligible_bundles=len(eligible),detected=len(det),detected_degrees=[r['degree'] for r in det],detected_unique_frames=[r['unique_frames'] for r in det],detected_unique_pivots=[r['unique_pivot_occurrences'] for r in det],detected_pivot_reuse=[r['pivot_occurrence_reuse'] for r in det],detected_incident_edges=len(reuse),shared_incident_edges=sum(v>1 for v in reuse.values()));close(expected,summary[a][view]);computed_details[view]=rr;bundlecount+=len(eligible)
            if view=='two_frames':
                assert [r['word'] for r in rr]==oldstats[a]['edge_or_pivot']['bundle_order'];np.testing.assert_allclose(matrix,oldstats[a]['edge_or_pivot']['values'],atol=1e-9,rtol=1e-9)
                for x,y in zip(rr,olddetail[a]['edge_or_pivot'],strict=True):
                    for n in ['word','edges','degree','unique_frames','unique_pivot_occurrences','raw_tail','max_stat_tail','adjusted_detected']:close(x[n],y[n])
        old={r['word'] for r in computed_details['two_frames'] if r['adjusted_detected']};new={r['word'] for r in computed_details['one_frame'] if r['adjusted_detected']};oe={r['word'] for r in computed_details['two_frames']};assert transitions[a]==dict(retained=sorted(old&new),lost=sorted(old-new),gained=sorted(new-old),gained_newly_eligible=sorted((new-old)-oe))
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,expanded_edges_rebuilt=edgecount,real_and_null_edge_scores_replayed=edgecount*200,eligible_view_bundles_rebuilt=bundlecount,pivot_sum_reconstructions=componentscount,all_two_frame_graphs_and_205_stats_tails_detections_replayed=True,all_word_pos_case_profiles_preserved=True,all_transitions_and_overlap_counts_replayed=True,no_new_labels_reserves_or_model_inputs=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
