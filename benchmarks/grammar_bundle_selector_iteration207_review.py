"""Independent scalar features and Newton refits for iteration207."""
from pathlib import Path
from collections import Counter,defaultdict
import json,math,hashlib
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
import numpy as np
from scipy.special import expit
P=Path('experiments/results/grammar-restoration');O=P/'iteration207'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def near(x,y,tol=1e-10):assert np.allclose(x,y,atol=tol,rtol=tol),(x,y)
def run():
    ff=read(O/'features.json');gg=read(P/'iteration193/graphs.json');bb=read(P/'iteration205/candidates.json');dd=read(P/'iteration205/details.json');models=read(O/'models.json');pred=read(O/'predictions.json');ss=read(O/'summary.json');sel=read(O/'selections.json');yy=read(O/'teacher-labels.json');checked=0
    for a,rows in ff.items():
        g=gg[a];counts=Counter(g['ids']);adj=defaultdict(set)
        for e in g['descriptors']:adj[e['a']].add(e['b']);adj[e['b']].add(e['a'])
        contexts=defaultdict(list)
        for i in range(1,len(g['ids'])-1):
            if all(g['positions'][j] is not None for j in [i-1,i,i+1]):contexts[g['ids'][i]].append((g['ids'][i-1],g['ids'][i+1]))
        for r,b in zip(rows,bb[a]):
            w=r['word'];edges=[(i,e) for i,e in enumerate(g['descriptors']) if w in (e['a'],e['b'])];assert [i for i,e in edges]==b['edges']
            frames=set();pivots=set();uses=0
            for _,e in edges:
                side='a' if e['a']==w else 'b'
                for f in e['frames']:frames.add(tuple(f['frame']));pivots.update(f[side+'_positions']);uses+=len(f[side+'_positions'])
            assert len(frames)==b['unique_frames'] and len(pivots)==b['unique_pivot_occurrences']
            c=contexts[w];n=len(c)
            def entropy(items):
                return sum(-v/n*math.log(v/n) for v in Counter(items).values())/math.log(n) if n>1 else 0.
            x=[math.log(counts[w]),math.log1p(len(adj[w])),math.log1p(len(frames)),math.log1p(len(pivots)),uses/len(pivots),len(pivots)/counts[w],sum(math.log(counts[v]) for v in adj[w])/len(adj[w]),sum(math.log1p(len(adj[v])) for v in adj[w])/len(adj[w]),entropy([l for l,r in c]),entropy([r for l,r in c]),entropy(c),len(set(c))/n if n else 0.]
            near(x,r['values']);checked+=1
        assert yy[a]==[int(r['adjusted_detected']) for r in dd[a]['edge_or_pivot']]
        for name,m in models[a].items():
            sources=[s for s in ff if s!=a];raw=np.array([r['values'] for s in sources for r in ff[s]])[:,m['columns']];y=np.array([v for s in sources for v in yy[s]]);weights=np.array([1/(3*len(ff[s])) for s in sources for r in ff[s]])
            mu=weights@raw;sd=np.sqrt(weights@((raw-mu)**2));sd[sd<1e-12]=1;near(mu,m['mean']);near(sd,m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);b=np.zeros(x.shape[1]);pen=np.eye(len(b))*.1;pen[0,0]=0
            def loss(v):return weights@(np.logaddexp(0,x@v)-y*(x@v))+.5*v@pen@v
            for it in range(100):
                p=expit(x@b);grad=x.T@(weights*(p-y))+pen@b
                if max(abs(grad))<1e-12:break
                h=x.T@((weights*p*(1-p))[:,None]*x)+pen;step=np.linalg.solve(h,grad);rate=1.
                while loss(b-rate*step)>loss(b)-1e-4*rate*(grad@step):
                    rate*=.5
                    if rate<1e-10:break
                b-=rate*step
            near(b,m['beta'],2e-6)
            target=np.array([r['values'] for r in rows])[:,m['columns']];out=expit(np.column_stack([np.ones(len(rows)),(target-mu)/sd])@np.array(m['beta']));near(out,pred[a][name]);close(independent_evaluate(yy[a],pred[a][name]),ss[a]['models'][name]['classification'])
        near(pred[a]['frequency'],[r['values'][0] for r in rows]);near(pred[a]['degree'],[r['values'][1] for r in rows])
        for name,scores in pred[a].items():
            y=yy[a];positive=[i for i,v in enumerate(y) if v];negative=[i for i,v in enumerate(y) if not v]
            auc=sum((scores[i]>scores[j])+.5*(scores[i]==scores[j]) for i in positive for j in negative)/(len(positive)*len(negative)) if positive and negative else None
            for k in [3,5]:
                ix=[i for i,s in enumerate(scores) if s>=sorted(scores,reverse=True)[k-1]];assert ix==sel[a][name]['top'+str(k)];v=ss[a]['models'][name]['lists']['top'+str(k)];assert v['selected']==len(ix) and v['supported']==sum(y[i] for i in ix);assert v['auc']==auc
                near(v['precision'],sum(y[i] for i in ix)/len(ix));near(v['coverage'],len(ix)/len(y))
                if positive:near(v['recall'],sum(y[i] for i in ix)/len(positive))
                else:assert v['recall'] is None
    hashes=0
    for fn in ['design-freeze.json','feature-freeze.json','prediction-freeze.json']:
        d=read(O/fn);d=d.get('inputs',d)
        for p,h in d.items():
            path=Path(p) if '/' in p else O/p;assert sha(path)==h;hashes+=1
    result=dict(status='passed',feature_rows=checked,newton_refits=8,rank_lists=32,freeze_hashes=hashes)
    (O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
