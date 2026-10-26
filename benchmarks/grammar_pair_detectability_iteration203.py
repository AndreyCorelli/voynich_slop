"""Development-only localization audit under fixed word/POS-profile permutations."""
import random
from collections import defaultdict,Counter
import numpy as np
from benchmarks.grammar_contextual_surplus_iteration201 import ROOT,Path,load,save,digest,AUTHORS,EPS,CASES
OUT=ROOT/'iteration203';BASE=ROOT/'iteration193';LABEL=ROOT/'iteration201';SLOTS=ROOT/'iteration202';SEEDS=list(range(20300,20499));ALPHA=.05
POLICY='Development-only fixed193graphs/201CasePOS/analyticlabels and unchanged201evaluationlists+202predictedlists, copied/frozen before null computation. 199seeds20300..20498; shuffle Case INCLUDINGmissing among ALL lexical positions in each opaquewordxPOS bucket, preserve every profile. Edge statistic =201unconditional frame-macro jointmatching minus fixed analytic expectation; no conditional equality denominator. Raw tail and per-author max-over-ALL-graph-edges adjusted tail=(1+count(null>=observed-1e-12))/200; fixedalpha.05 and observed surplus>1e-12 to call local detections. Maxstat controls shared-edge multiple checks under joint exchangeability baseline; not universal correctness probabilities or automatically strong FWER under arbitrary partial alternatives. Aggregate graph uses mean edge surplus, same tail formula. Record everyedge, negative/zero/positive and sampled-zero-variance (<=1e-24variance), nullmaxdistribution, all fixedlist/oracle detection coverage; no selected model/view/tail threshold or learned use of gold significance. Gold201oracle lists are evaluation only, never predictions. No new raw/reference/reserve/Dante data, fits, scores or selections. This follow-up asks localizable evidence versus pooled effect; maxstat may be conservative,199resolution.005, no non-detection impliesabsence.'

def joint_matches(dd,cc):
    out=[]
    for e in dd:
        ff=[]
        for f in e['frames']:
            match=sum(cc[i] in CASES and cc[j] in CASES and cc[i]==cc[j] for i in f['a_positions'] for j in f['b_positions']);ff.append(match/(len(f['a_positions'])*len(f['b_positions'])))
        out.append(sum(ff)/len(ff))
    return np.array(out)

def tail(values,actual):return (1+sum(v>=actual-EPS for v in values))/(len(values)+1)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__)]+[BASE/n for n in ['graphs.json','development-references.json']]+[LABEL/n for n in ['verification-manifest.json','development-references.json','labels.json','evaluation-selections.json','outputs.json']]+[SLOTS/n for n in ['verification-manifest.json','selections.json','outputs.json']]
    save(OUT/'design-freeze.json',dict(policy=POLICY,seeds=SEEDS,alpha=ALPHA,tolerance=EPS,inputs={str(p):digest(p) for p in paths}))
    for folder in [LABEL,SLOTS]:
        for p,h in load(folder/'verification-manifest.json').items():assert digest(Path(p))==h
    lists201=load(LABEL/'evaluation-selections.json');lists202=load(SLOTS/'selections.json');lists={a:{**{'201/'+n:ix for n,ix in lists201[a].items()},**{'202/'+n:ix for n,ix in lists202[a].items()}} for a in AUTHORS};save(OUT/'fixed-lists.json',lists);save(OUT/'selection-freeze.json',{'fixed-lists.json':digest(OUT/'fixed-lists.json')})
    graphs=load(BASE/'graphs.json');refs=load(LABEL/'development-references.json');labels=load(LABEL/'labels.json');nulls={};edge_details={};summary={};list_summary={}
    for a in AUTHORS:
        g=graphs[a];dd=g['descriptors'];ref=refs[a];expected=np.array([r['expected_frame_macro_joint_matching'] for r in labels[a]]);observed=joint_matches(dd,ref['case'])-expected;assert np.allclose(observed,[r['surplus'] for r in labels[a]],atol=1e-12,rtol=1e-12)
        buckets=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p:buckets[(g['ids'][i],ref['pos'][i])].append(i)
        matrix=[]
        for seed in SEEDS:
            rng=random.Random(seed);cc=ref['case'].copy()
            for key in sorted(buckets):
                pp=buckets[key];values=[ref['case'][i] for i in pp];rng.shuffle(values)
                for i,c in zip(pp,values):cc[i]=c
            matrix.append((joint_matches(dd,cc)-expected).tolist())
        nulls[a]=matrix;arr=np.array(matrix);maximum=arr.max(axis=1);means=arr.mean(axis=1);details=[]
        for i,r in enumerate(labels[a]):
            raw=tail(arr[:,i],observed[i]);adjusted=tail(maximum,observed[i]);variance=float(np.var(arr[:,i]));details.append(dict(edge=i,a=r['a'],b=r['b'],surplus=float(observed[i]),positive_surplus=bool(observed[i]>EPS),raw_tail=raw,max_stat_tail=adjusted,raw_detected=bool(raw<=ALPHA and observed[i]>EPS),adjusted_detected=bool(adjusted<=ALPHA and observed[i]>EPS),null_min=float(arr[:,i].min()),null_max=float(arr[:,i].max()),null_mean=float(arr[:,i].mean()),sampled_null_variance=variance,sampled_zero_variance=variance<=1e-24))
        edge_details[a]=details;raw={r['edge'] for r in details if r['raw_detected']};adj={r['edge'] for r in details if r['adjusted_detected']};assert adj<=raw
        summary[a]=dict(edges=len(dd),positive_surplus=int(sum(observed>EPS)),negative_surplus=int(sum(observed<-EPS)),zero_surplus=int(sum(abs(observed)<=EPS)),raw_detected=len(raw),max_stat_detected=len(adj),raw_detected_endpoint_types=len({r[k] for r in details if r['raw_detected'] for k in ['a','b']}),adjusted_detected_endpoint_types=len({r[k] for r in details if r['adjusted_detected'] for k in ['a','b']}),sampled_zero_variance=sum(r['sampled_zero_variance'] for r in details),aggregate_mean_surplus=float(observed.mean()),aggregate_tail=tail(means,float(observed.mean())),null_aggregate_min=float(means.min()),null_aggregate_max=float(means.max()),null_max_stat_min=float(maximum.min()),null_max_stat_max=float(maximum.max()))
        list_summary[a]={}
        for name,ix in lists[a].items():
            chosen=[details[i] for i in ix];list_summary[a][name]=dict(selected=len(ix),positive_surplus=sum(r['positive_surplus'] for r in chosen),raw_detected=sum(r['raw_detected'] for r in chosen),max_stat_detected=sum(r['adjusted_detected'] for r in chosen),sampled_zero_variance=sum(r['sampled_zero_variance'] for r in chosen),mean_surplus=sum(r['surplus'] for r in chosen)/len(ix) if ix else None)
        print(a,summary[a],flush=True)
    for name,obj in [('null-surplus-matrices',nulls),('edge-details',edge_details),('summary',summary),('fixed-list-detectability',list_summary)]:save(OUT/(name+'.json'),obj)
if __name__=='__main__':run()
