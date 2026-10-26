"""Fixed source-label shuffles and greedy endpoint-disjoint selections."""
from pathlib import Path
import json,hashlib,random
import numpy as np
from benchmarks.grammar_pos_edge_rank_iteration225 import fit,predict,top,measure
P=Path('experiments/results/grammar-restoration');O=P/'iteration226';AUTHORS=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def disjoint(scores,edges,k):
    used=set();ix=[]
    for i in sorted(range(len(scores)),key=lambda i:(-scores[i],i)):
        e=edges[i]
        if e['a'] in used or e['b'] in used:continue
        ix.append(i);used.update([e['a'],e['b']])
        if len(ix)==k:break
    return ix

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_edge_rank_iteration225.py')]+[P/n for n in ['iteration225/features.json','iteration225/predictions.json','iteration225/selections.json','iteration225/summary.json','iteration225/verification-manifest.json','iteration193/graphs.json','iteration223/details.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(22500,22699)),author_order=AUTHORS))
    for p,h in read(P/'iteration225/verification-manifest.json').items():assert sha(Path(p))==h
    ff=read(P/'iteration225/features.json');actual=read(P/'iteration225/predictions.json');graphs=read(P/'iteration193/graphs.json');labels={a:r['edge_values'] for a,r in read(P/'iteration223/details.json').items()};dd={a:{n:{f'top{k}':disjoint(s,graphs[a]['descriptors'],k) for k in [10,20]} for n,s in actual[a].items()} for a in AUTHORS};nullpred=[];nullsel=[];permutations=[]
    for seed in range(22500,22699):
        rng=random.Random(seed);shuffled={};orders={}
        for a in AUTHORS:
            order=list(range(len(labels[a])));rng.shuffle(order);orders[a]=order;shuffled[a]=[labels[a][i] for i in order]
        permutations.append(orders);pp={};ss={}
        for a in AUTHORS:
            source=[b for b in AUTHORS if b!=a];raw=[r['values'] for b in source for r in ff[b]];y=[v for b in source for v in shuffled[b]];w=[1/len(ff[b]) for b in source for r in ff[b]];pp[a]={};ss[a]={}
            for name,cols in [('rich19',list(range(19))),('control3',[0,9,18])]:
                m=fit(raw,y,w,cols);p=predict(ff[a],m);pp[a][name]=p;ss[a][name]={f'top{k}':top(p,k) for k in [10,20]}
        nullpred.append(pp);nullsel.append(ss)
    for n,v in [('permutation-orders',permutations),('null-predictions',nullpred),('null-selections',nullsel),('disjoint-selections',dd)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['permutation-orders.json','null-predictions.json','null-selections.json','disjoint-selections.json']})
    old=read(P/'iteration225/summary.json');summary={};nullvalues={}
    for a in AUTHORS:
        edges=graphs[a]['descriptors'];nt=len({e[s] for e in edges for s in ['a','b']});summary[a]={};nullvalues[a]={}
        for name in ['rich19','control3']:
            summary[a][name]={};nullvalues[a][name]={}
            for label in ['top10','top20']:
                values=[sum(labels[a][i] for i in ss[a][name][label])/len(ss[a][name][label]) for ss in nullsel];nullvalues[a][name][label]=values;real=old[a]['models'][name]['lists'][label]['mean_compatibility'];ix=dd[a][name][label];summary[a][name][label]=dict(actual=real,null_mean=sum(values)/199,null_min=min(values),null_max=max(values),upper_tail=(1+sum(v>=real-1e-12 for v in values))/200,disjoint=dict(**measure(ix,labels[a],edges,nt),requested=int(label[3:]),shortfall=int(label[3:])-len(ix)))
        summary[a]['paired_rich_minus_control']={}
        for label in ['top10','top20']:
            real=summary[a]['rich19'][label]['actual']-summary[a]['control3'][label]['actual'];values=[x-y for x,y in zip(nullvalues[a]['rich19'][label],nullvalues[a]['control3'][label])];summary[a]['paired_rich_minus_control'][label]=dict(actual=real,null_mean=sum(values)/199,upper_tail=(1+sum(v>=real-1e-12 for v in values))/200)
    save(O/'null-values.json',nullvalues);save(O/'summary.json',summary)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
