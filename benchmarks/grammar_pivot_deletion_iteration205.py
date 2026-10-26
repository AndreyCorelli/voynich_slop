"""Bundle evidence after deleting one edge or one reused pivot occurrence."""
import random
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_pair_detectability_iteration203 import ROOT,Path,load,save,digest,AUTHORS,EPS,ALPHA,SEEDS,tail,CASES
OUT=ROOT/'iteration205';BASE=ROOT/'iteration193';REF=ROOT/'iteration201';EDGE=ROOT/'iteration203';BUNDLE=ROOT/'iteration204'
STATS=['edge_only','pivot_only','edge_or_pivot']
POLICY='Fixed development193graphs,201CasePOS profiles,204anonymous bundles; no newraw/reserve/Dante/models. Freeze all degree>=2 and>=2distinctpivot candidates before reference load. Reproduce EXACT203Caseassignments (same199seeds/buckets), verify all edge residuals and204edge-only statistics/tails. Decompose each edge residual into Cartesian match-minus-profile-expectation terms weighted1/(edge_sharedframes*a_frame_count*b_frame_count). Per-center pivot contribution sums ALL terms involving that pivot occurrence across incidentedges; weights/profiles/graph fixed, no renormalizing after deletion. Sum pivotcontributions must equal sum edge residuals for real/every null. Primary total−max(maxedge,maxpivot), comparators total−maxedge andtotal−maxpivot, sameeligiblecenters. This is minimum over removing ONEedge OR ONEpivot, not simultaneous deletion. Sameoperation pernull, per-author/per-stat maxoverALLeligiblebundles tail(1+exceedances)/200/tol1e-12/positive1e-12/alpha.05; no acrossfamily correction/winner or assumptiondetectionsnested. All retained/lost/gained and contribution concentration/overlap reported. Oracle reference robustness, not annotation-free selector/namedcase/word recovery; conditional/conservative199null limitations remain.'

def probabilities(g,ref):
    counts=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p:counts[(g['ids'][i],ref['pos'][i])][ref['case'][i]]+=1
    return {k:{c:n/sum(v.values()) for c,n in v.items() if c in CASES} for k,v in counts.items()}

def case_matrix(g,ref):
    code={'':0,**{c:i+1 for i,c in enumerate(sorted(CASES))}};original=np.array([code[c] for c in ref['case']],dtype=np.int8);buckets=defaultdict(list)
    for i,p in enumerate(g['positions']):
        if p:buckets[(g['ids'][i],ref['pos'][i])].append(i)
    matrix=[original]
    for seed in SEEDS:
        rng=random.Random(seed);cc=original.copy()
        for key,pp in sorted(buckets.items()):
            vv=[int(original[i]) for i in pp];rng.shuffle(vv);cc[pp]=vv
        matrix.append(cc)
    return np.stack(matrix)

def blueprint(g,b,ref,probs):
    bypivot=defaultdict(list)
    for edge in b['edges']:
        e=g['descriptors'][edge];side='a_positions' if e['a']==b['word'] else 'b_positions';other='b_positions' if side=='a_positions' else 'a_positions'
        for f in e['frames']:
            weight=1/(e['shared_frames']*len(f['a_positions'])*len(f['b_positions']))
            for p in f[side]:
                a=probs[(g['ids'][p],ref['pos'][p])]
                for q in f[other]:
                    otherprofile=probs[(g['ids'][q],ref['pos'][q])];expected=sum(v*otherprofile.get(c,0) for c,v in a.items());bypivot[p].append(dict(partner=q,weight=weight,expected_match=expected,edge=edge))
    return [dict(position=p,terms=terms) for p,terms in sorted(bypivot.items())]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),BASE/'graphs.json',REF/'development-references.json',REF/'labels.json']+[EDGE/n for n in ['verification-manifest.json','edge-details.json','null-surplus-matrices.json']]+[BUNDLE/n for n in ['verification-manifest.json','bundles.json','details.json','null-bundle-statistics.json']];save(OUT/'design-freeze.json',dict(policy=POLICY,statistics=STATS,inputs={str(p):digest(p) for p in paths}))
    for folder in [EDGE,BUNDLE]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h
    candidates={a:[b for b in bb if b['degree']>=2 and b['unique_pivot_occurrences']>=2] for a,bb in load(BUNDLE/'bundles.json').items()};save(OUT/'candidates.json',candidates);save(OUT/'candidate-freeze.json',{'candidates.json':digest(OUT/'candidates.json')})
    graphs=load(BASE/'graphs.json');refs=load(REF/'development-references.json');labels=load(REF/'labels.json');oldedges=load(EDGE/'edge-details.json');oldnull=load(EDGE/'null-surplus-matrices.json');olddetails=load(BUNDLE/'details.json');oldstats=load(BUNDLE/'null-bundle-statistics.json');blueprints={};contributions={};details={};summary={};statistics={}
    for a in AUTHORS:
        g=graphs[a];ref=refs[a];cm=case_matrix(g,ref);probs=probabilities(g,ref);edgevalues=[]
        for i,e in enumerate(g['descriptors']):
            match=np.zeros(len(cm))
            for f in e['frames']:
                pp=[p for p in f['a_positions'] for _ in f['b_positions']];qq=f['b_positions']*len(f['a_positions']);match+=np.mean((cm[:,pp]>0)&(cm[:,pp]==cm[:,qq]),axis=1)/e['shared_frames']
            edgevalues.append(match-labels[a][i]['expected_frame_macro_joint_matching'])
        ev=np.column_stack(edgevalues);np.testing.assert_allclose(ev[0],[r['surplus'] for r in oldedges[a]],atol=1e-11,rtol=1e-11);np.testing.assert_allclose(ev[1:],oldnull[a],atol=1e-11,rtol=1e-11)
        blueprints[a]={};contributions[a]={};columns={k:[] for k in STATS}
        for b in candidates[a]:
            bp=blueprint(g,b,ref,probs);blueprints[a][b['word']]=bp;pc=[]
            for pivot in bp:
                p=pivot['position'];qq=[t['partner'] for t in pivot['terms']];weights=np.array([t['weight'] for t in pivot['terms']]);expected=sum(t['weight']*t['expected_match'] for t in pivot['terms']);pc.append((((cm[:,p,None]>0)&(cm[:,p,None]==cm[:,qq]))@weights)-expected)
            pv=np.column_stack(pc);total=ev[:,b['edges']].sum(axis=1);np.testing.assert_allclose(pv.sum(axis=1),total,atol=1e-10,rtol=1e-10);emax=ev[:,b['edges']].max(axis=1);pmax=pv.max(axis=1);columns['edge_only'].append(total-emax);columns['pivot_only'].append(total-pmax);columns['edge_or_pivot'].append(total-np.maximum(emax,pmax));contributions[a][b['word']]=dict(pivot_order=[p['position'] for p in bp],values=pv.tolist(),sum=total.tolist(),largest_edge=emax.tolist(),largest_pivot=pmax.tolist())
        matrices={k:np.column_stack(v) for k,v in columns.items()};assert [b['word'] for b in candidates[a]]==oldstats[a]['drop_strongest_sum']['bundle_order'];np.testing.assert_allclose(matrices['edge_only'][1:],oldstats[a]['drop_strongest_sum']['statistics'],atol=1e-10,rtol=1e-10);np.testing.assert_allclose(matrices['edge_only'][0],[r['statistic'] for r in olddetails[a]['drop_strongest_sum']],atol=1e-10,rtol=1e-10)
        olddet={r['word'] for r in olddetails[a]['drop_strongest_sum'] if r['adjusted_detected']};details[a]={};summary[a]={};statistics[a]={}
        for kind,matrix in matrices.items():
            maximum=matrix[1:].max(axis=1);rr=[]
            for j,b in enumerate(candidates[a]):
                real=float(matrix[0,j]);raw=float(tail(matrix[1:,j],real));adjusted=float(tail(maximum,real));v=contributions[a][b['word']];rr.append(dict(**b,statistic=real,raw_tail=raw,max_stat_tail=adjusted,raw_detected=raw<=ALPHA and real>EPS,adjusted_detected=adjusted<=ALPHA and real>EPS,previous_edge_only_detected=b['word'] in olddet,original_sum=v['sum'][0],largest_edge_contribution=v['largest_edge'][0],largest_pivot_contribution=v['largest_pivot'][0]))
            detected={r['word'] for r in rr if r['adjusted_detected']};details[a][kind]=rr;summary[a][kind]=dict(eligible_bundles=len(rr),detected=len(detected),previous_edge_only_detected=len(olddet),retained=sorted(detected&olddet),lost=sorted(olddet-detected),gained=sorted(detected-olddet));statistics[a][kind]=dict(bundle_order=[b['word'] for b in candidates[a]],values=matrix.tolist(),null_maxima=maximum.tolist())
            if kind=='edge_only':assert detected==olddet
        print(a,{kind:{k:(len(v) if isinstance(v,list) else v) for k,v in row.items()} for kind,row in summary[a].items()},flush=True)
    for n,obj in [('blueprints',blueprints),('pivot-contributions',contributions),('details',details),('summary',summary),('statistics',statistics)]:save(OUT/(n+'.json'),obj)
if __name__=='__main__':run()
