"""Additional-author development transfer of unchanged POS-pair selectors."""
from pathlib import Path
from collections import Counter,defaultdict
import math,json,hashlib,random
from benchmarks.grammar_pos_edge_rank_iteration225 import fit,predict,top
from benchmarks.grammar_case_applicability_iteration180 import features_for
P=Path('experiments/results/grammar-restoration');O=P/'iteration229';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def greedy(order,edges,k):
    used=set();ix=[]
    for i in order:
        e=edges[i]
        if used.isdisjoint([e['a'],e['b']]):ix.append(i);used.update([e['a'],e['b']])
        if len(ix)==k:break
    return ix

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_edge_rank_iteration225.py'),Path('benchmarks/grammar_case_applicability_iteration180.py')]+[P/n for n in ['iteration198/graphs.json','iteration198/provenance-status.json','iteration199/features.json','iteration200/pos-references.json','iteration200/verification-manifest.json','iteration225/features.json','iteration223/details.json','iteration228/verification-manifest.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(22800,22999)),status='Dante POS consumed200; additional-author development only'))
    for it in ['iteration200','iteration228']:
        for p,h in read(P/it/'verification-manifest.json').items():assert sha(Path(p))==h
    g=read(P/'iteration198/graphs.json')['primary'];edges=g['descriptors'];ff=features_for(g['ids'],edges);assert ff==read(P/'iteration199/features.json');counts=Counter(g['ids']);frames=defaultdict(set)
    for i in range(1,len(g['ids'])-1):
        if all(g['positions'][j] is not None for j in [i-1,i,i+1]):frames[g['ids'][i]].add((g['ids'][i-1],g['ids'][i+1]))
    scores=dict(support=[e['shared_frames'] for e in edges],frequency_high=[(math.log(counts[e['a']])+math.log(counts[e['b']]))/2 for e in edges],frequency_low=[-(math.log(counts[e['a']])+math.log(counts[e['b']]))/2 for e in edges],jaccard=[len(frames[e['a']]&frames[e['b']])/len(frames[e['a']]|frames[e['b']]) for e in edges]);save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')})
    source=read(P/'iteration225/features.json');labels=read(P/'iteration223/details.json');raw=[r['values'] for a in AA for r in source[a]];y=[v for a in AA for v in labels[a]['edge_values']];w=[1/len(source[a]) for a in AA for r in source[a]];models={name:fit(raw,y,w,cols) for name,cols in [('rich19',list(range(19))),('control3',[0,9,18])]};scores.update({n:predict(ff,m) for n,m in models.items()});selections={n:dict(tied={f'top{k}':top(s,k) for k in [10,20]},disjoint={f'top{k}':greedy(sorted(range(len(s)),key=lambda i:(-s[i],i)),edges,k) for k in [10,20]}) for n,s in scores.items()};randomlists=[];orders=[]
    for seed in range(22800,22999):
        order=list(range(len(edges)));random.Random(seed).shuffle(order);priority={i:j for j,i in enumerate(order)};orders.append(order);methods={n:sorted(order,key=lambda i:(-s[i],priority[i])) for n,s in scores.items()};methods['uniform']=order;randomlists.append({n:{f'top{k}':greedy(order,edges,k) for k in [10,20]} for n,order in methods.items()})
    for n,v in [('models',models),('scores',scores),('selections',selections),('random-orders',orders),('random-selections',randomlists)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['models.json','scores.json','selections.json','random-orders.json','random-selections.json']})
    pos=read(P/'iteration200/pos-references.json')['pos_by_stream_position'];profiles=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p:profiles[g['ids'][i]][pos[i]]+=1
    prob={word:{t:n/sum(v.values()) for t,n in v.items()} for word,v in profiles.items()};y=[sum(v*prob[e['b']].get(t,0) for t,v in prob[e['a']].items()) for e in edges];nt=len({e[k] for e in edges for k in ['a','b']})
    def measure(ix):return dict(edges=len(ix),mean_compatibility=sum(y[i] for i in ix)/len(ix),endpoints=len({edges[i][k] for i in ix for k in ['a','b']}))
    summary=dict(status='additional-author development; POS consumed200',candidate_edges=len(edges),endpoint_types=nt,all=measure(list(range(len(edges)))),methods={n:{mode:{label:measure(ix) for label,ix in ll.items()} for mode,ll in modes.items()} for n,modes in selections.items()},random={})
    randomvalues={n:{label:[measure(ll[n][label])['mean_compatibility'] for ll in randomlists] for label in ['top10','top20']} for n in list(scores)+['uniform']}
    for n,methods in randomvalues.items():
        summary['random'][n]={}
        for label,values in methods.items():
            v=dict(mean=sum(values)/199,minimum=min(values),maximum=max(values),min_selected=min(len(ll[n][label]) for ll in randomlists),max_selected=max(len(ll[n][label]) for ll in randomlists))
            if n!='uniform':
                diff=[x-y for x,y in zip(values,randomvalues['uniform'][label])];v.update(paired_mean_gain=sum(diff)/199,fraction_positive=sum(x>1e-12 for x in diff)/199)
            summary['random'][n][label]=v
    save(O/'labels.json',y);save(O/'random-values.json',randomvalues);save(O/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
