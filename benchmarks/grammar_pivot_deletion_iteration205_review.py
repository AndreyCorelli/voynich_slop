"""Independent scalar occurrence contributions and explicit edge/observation deletions."""
import random
from collections import Counter,defaultdict
from fractions import Fraction
from benchmarks.grammar_pivot_deletion_iteration205 import OUT,BASE,REF,EDGE,BUNDLE,AUTHORS,SEEDS,STATS,EPS,ALPHA,CASES,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close

def pv(values,actual):return (1+sum(x>=actual-EPS for x in values))/(len(values)+1)

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'candidate-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for folder in [EDGE,BUNDLE]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    graphs=load(BASE/'graphs.json');refs=load(REF/'development-references.json');labels=load(REF/'labels.json');candidates=load(OUT/'candidates.json');oldbundles=load(BUNDLE/'bundles.json');oldedge=load(EDGE/'edge-details.json');oldnull=load(EDGE/'null-surplus-matrices.json');olddetail=load(BUNDLE/'details.json');blueprints=load(OUT/'blueprints.json');savedcontrib=load(OUT/'pivot-contributions.json');stats=load(OUT/'statistics.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');nb=terms=recon=0
    for a in AUTHORS:
        assert candidates[a]==[b for b in oldbundles[a] if b['degree']>=2 and b['unique_pivot_occurrences']>=2];g=graphs[a];ref=refs[a];buckets=defaultdict(list);counts=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p:key=(g['ids'][i],ref['pos'][i]);buckets[key].append(i);counts[key][ref['case'][i]]+=1
        caseassign=[ref['case']]
        for seed in SEEDS:
            rng=random.Random(seed);cc=ref['case'].copy()
            for key,pp in sorted(buckets.items()):
                values=[ref['case'][i] for i in pp];rng.shuffle(values)
                for i,v in zip(pp,values):cc[i]=v
                assert Counter(cc[i] for i in pp)==counts[key]
            caseassign.append(cc)
        edgevalues=[[r['surplus'] for r in oldedge[a]]]+oldnull[a];newstats={k:[[] for _ in caseassign] for k in STATS}
        for b in candidates[a]:
            edgeids=b['edges'];allpivots=sorted({p for i in edgeids for f in g['descriptors'][i]['frames'] for p in f['a_positions' if g['descriptors'][i]['a']==b['word'] else 'b_positions']});bp=[]
            for p in allpivots:
                pt=[]
                for i in edgeids:
                    e=g['descriptors'][i];side='a_positions' if e['a']==b['word'] else 'b_positions';other='b_positions' if side=='a_positions' else 'a_positions'
                    for f in e['frames']:
                        if p not in f[side]:continue
                        for q in f[other]:
                            aa=counts[(g['ids'][p],ref['pos'][p])];bb=counts[(g['ids'][q],ref['pos'][q])];expected=Fraction(sum(aa[c]*bb[c] for c in CASES),sum(aa.values())*sum(bb.values()));weight=Fraction(1,e['shared_frames']*len(f['a_positions'])*len(f['b_positions']));pt.append(dict(partner=q,weight=float(weight),expected_match=float(expected),edge=i));terms+=1
                bp.append(dict(position=p,terms=pt))
            close(bp,blueprints[a][b['word']]);matrix=[];sums=[];largestedge=[];largestpivot=[]
            for ri,cc in enumerate(caseassign):
                contribution=[]
                for pivot in bp:
                    p=pivot['position'];v=sum((int(cc[p] in CASES and cc[p]==cc[t['partner']])-t['expected_match'])*t['weight'] for t in pivot['terms']);contribution.append(v)
                ev=[edgevalues[ri][i] for i in edgeids];total=sum(ev);assert abs(sum(contribution)-total)<1e-10;matrix.append(contribution);sums.append(total);largestedge.append(max(ev));largestpivot.append(max(contribution));recon+=1
                # Explicitly enumerate deletion alternatives, not total-minus-maximum.
                edgeonly=min(sum(v for j,v in enumerate(ev) if j!=deleted) for deleted in range(len(ev)));pivotonly=min(sum(v for j,v in enumerate(contribution) if j!=deleted) for deleted in range(len(contribution)));newstats['edge_only'][ri].append(edgeonly);newstats['pivot_only'][ri].append(pivotonly);newstats['edge_or_pivot'][ri].append(min(edgeonly,pivotonly))
            close(dict(pivot_order=allpivots,values=matrix,sum=sums,largest_edge=largestedge,largest_pivot=largestpivot),savedcontrib[a][b['word']]);nb+=1
        olddet={r['word'] for r in olddetail[a]['drop_strongest_sum'] if r['adjusted_detected']}
        for kind,matrix in newstats.items():
            maximum=[max(row) for row in matrix[1:]];close(dict(bundle_order=[b['word'] for b in candidates[a]],values=matrix,null_maxima=maximum),stats[a][kind]);computed=[]
            for j,b in enumerate(candidates[a]):
                real=matrix[0][j];raw=pv([row[j] for row in matrix[1:]],real);adjusted=pv(maximum,real);assert adjusted+EPS>=raw;v=savedcontrib[a][b['word']];computed.append(dict(**b,statistic=real,raw_tail=raw,max_stat_tail=adjusted,raw_detected=raw<=ALPHA and real>EPS,adjusted_detected=adjusted<=ALPHA and real>EPS,previous_edge_only_detected=b['word'] in olddet,original_sum=v['sum'][0],largest_edge_contribution=v['largest_edge'][0],largest_pivot_contribution=v['largest_pivot'][0]))
            close(computed,details[a][kind]);det={r['word'] for r in computed if r['adjusted_detected']};close(dict(eligible_bundles=len(computed),detected=len(det),previous_edge_only_detected=len(olddet),retained=sorted(det&olddet),lost=sorted(olddet-det),gained=sorted(det-olddet)),summary[a][kind])
            if kind=='edge_only':assert det==olddet;close(computed,[{**r,'previous_edge_only_detected':r['word'] in olddet,'original_sum':computed[j]['original_sum'],'largest_edge_contribution':computed[j]['largest_edge_contribution'],'largest_pivot_contribution':computed[j]['largest_pivot_contribution']} for j,r in enumerate(computed)])
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,eligible_bundles_replayed=nb,weighted_comparison_terms_replayed=terms,real_and_null_pivot_sum_reconstructions=recon,word_pos_case_profiles_preserved=True,explicit_edge_and_pivot_deletion_enumeration=True,all_204_edge_only_detections_replayed=True,all_205_tail_and_transition_results_replayed=True,no_new_raw_gold_reserve_or_model_inputs=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
