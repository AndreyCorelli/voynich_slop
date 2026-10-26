"""Independent cached Dante features/profiles, LS and selection audit."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
import json,hashlib,math,random
import numpy as np
from benchmarks.grammar_case_applicability_iteration180_review import independent_features,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration229'
def read(p):return json.loads(p.read_text())
def run():
    g=read(P/'iteration198/graphs.json')['primary'];edges=g['descriptors'];ff=read(O/'features.json');close(independent_features(g['ids'],edges),ff);assert ff==read(P/'iteration199/features.json');source=read(P/'iteration225/features.json');labels=read(P/'iteration223/details.json');mm=read(O/'models.json');scores=read(O/'scores.json');sel=read(O/'selections.json');rs=read(O/'random-selections.json');orders=read(O/'random-orders.json');ss=read(O/'summary.json');values=read(O/'random-values.json');raw=np.array([r['values'] for a in source for r in source[a]]);sy=np.array([v for a in source for v in labels[a]['edge_values']]);w=np.array([1/(4*len(source[a])) for a in source for r in source[a]])
    for name,m in mm.items():
        xx=raw[:,m['columns']];mu=w@xx;sd=np.sqrt(w@((xx-mu)**2));sd[sd<1e-12]=1;close(mu.tolist(),m['mean']);close(sd.tolist(),m['scale']);x=np.column_stack([np.ones(len(xx)),(xx-mu)/sd]);aug=np.vstack([np.sqrt(w)[:,None]*x,np.diag([0]+[math.sqrt(.1)]*len(m['columns']))]);b=np.linalg.lstsq(aug,np.concatenate([np.sqrt(w)*sy,np.zeros(x.shape[1])]),rcond=None)[0];close(b.tolist(),m['beta']);tx=np.array([r['values'] for r in ff])[:,m['columns']];close((np.column_stack([np.ones(len(tx)),(tx-mu)/sd])@np.array(m['beta'])).tolist(),scores[name])
    count=Counter(g['ids']);frames=defaultdict(set)
    for i in range(1,len(g['ids'])-1):
        if all(g['positions'][j] is not None for j in [i-1,i,i+1]):frames[g['ids'][i]].add((g['ids'][i-1],g['ids'][i+1]))
    expected=dict(support=[e['shared_frames'] for e in edges],frequency_high=[math.log(count[e['a']]*count[e['b']])/2 for e in edges],frequency_low=[-math.log(count[e['a']]*count[e['b']])/2 for e in edges],jaccard=[len(frames[e['a']]&frames[e['b']])/len(frames[e['a']]|frames[e['b']]) for e in edges])
    for name,v in expected.items():close(v,scores[name])
    pos=read(P/'iteration200/pos-references.json')['pos_by_stream_position'];counts=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p is not None:counts[g['ids'][i]][pos[i]]+=1
    profiles={word:{t:F(n,sum(c.values())) for t,n in c.items()} for word,c in counts.items()};y=[float(sum((v*profiles[e['b']].get(t,0) for t,v in profiles[e['a']].items()),F(0))) for e in edges];close(y,read(O/'labels.json'))
    def measure(ix):return dict(edges=len(ix),mean_compatibility=sum(y[i] for i in ix)/len(ix),endpoints=len({edges[i][k] for i in ix for k in ['a','b']}))
    def greedy(order,k):
        ix=[];used=set()
        for i in order:
            ends={edges[i]['a'],edges[i]['b']}
            if used.isdisjoint(ends):ix.append(i);used|=ends
            if len(ix)==k:break
        return ix
    close(ss['all'],measure(list(range(len(edges)))));assert ss['candidate_edges']==76 and ss['endpoint_types']==76
    for name,s in scores.items():
        for k in [10,20]:
            label=f'top{k}';cut=sorted(s,reverse=True)[k-1];tied=[i for i,v in enumerate(s) if v>=cut];disjoint=greedy(sorted(range(len(s)),key=lambda i:(-s[i],i)),k)
            for mode,ix in [('tied',tied),('disjoint',disjoint)]:assert ix==sel[name][mode][label];close(measure(ix),ss['methods'][name][mode][label])
    nlists=0
    for j,seed in enumerate(range(22800,22999)):
        order=list(range(len(edges)));random.Random(seed).shuffle(order);assert orders[j]==order;priority={i:r for r,i in enumerate(order)}
        for name in list(scores)+['uniform']:
            ranking=order if name=='uniform' else sorted(order,key=lambda i:(-scores[name][i],priority[i]))
            for k in [10,20]:
                label=f'top{k}';ix=greedy(ranking,k);assert ix==rs[j][name][label];close(measure(ix)['mean_compatibility'],values[name][label][j]);nlists+=1
    for name,methods in values.items():
        for label,v in methods.items():
            n=[len(r[name][label]) for r in rs];expected=dict(mean=sum(v)/199,minimum=min(v),maximum=max(v),min_selected=min(n),max_selected=max(n))
            if name!='uniform':
                diff=[x-y for x,y in zip(v,values['uniform'][label])];expected.update(paired_mean_gain=sum(diff)/199,fraction_positive=sum(x>1e-12 for x in diff)/199)
            close(expected,ss['random'][name][label])
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs']]+[read(P/it/'verification-manifest.json') for it in ['iteration200','iteration228']]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for fn in ['feature-freeze.json','prediction-freeze.json']:
        for p,h in read(O/fn).items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',features=76,rational_labels=76,least_squares_refits=2,random_lists=nlists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
