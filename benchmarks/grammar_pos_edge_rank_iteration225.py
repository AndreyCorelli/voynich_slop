"""Frozen anonymous edge regression for reference POS compatibility."""
from pathlib import Path
import json,hashlib
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration225';AUTHORS=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def top(s,k):
    cut=sorted(s,reverse=True)[min(k,len(s))-1];return [i for i,v in enumerate(s) if v>=cut]
def fit(raw,y,w,cols):
    x=np.array(raw)[:,cols];w=np.array(w);w/=w.sum();mu=w@x;sd=np.sqrt(w@((x-mu)**2));sd[sd<1e-12]=1;x=np.column_stack([np.ones(len(x)),(x-mu)/sd]);pen=np.diag([0]+[.1]*len(cols));b=np.linalg.solve(x.T@(w[:,None]*x)+pen,x.T@(w*np.array(y)));return dict(columns=cols,mean=mu.tolist(),scale=sd.tolist(),beta=b.tolist())
def predict(rows,m):
    x=np.array([r['values'] for r in rows])[:,m['columns']];return (np.column_stack([np.ones(len(x)),(x-m['mean'])/m['scale']])@np.array(m['beta'])).tolist()
def measure(ix,y,edges,totaltypes):
    endpoints={edges[i][side] for i in ix for side in ['a','b']};return dict(edges=len(ix),mean_compatibility=sum(y[i] for i in ix)/len(ix),endpoints=len(endpoints),endpoint_coverage=len(endpoints)/totaltypes)
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/features.json','iteration193/graphs.json','iteration223/details.json','iteration223/profiles.json','iteration224/verification-manifest.json']];save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration224/verification-manifest.json').items():assert sha(Path(p))==h
    ff={a:r for a,r in read(P/'iteration193/features.json').items() if a in AUTHORS};save(O/'features.json',ff);save(O/'feature-freeze.json',{'features.json':sha(O/'features.json')});graphs=read(P/'iteration193/graphs.json');labels={a:d['edge_values'] for a,d in read(P/'iteration223/details.json').items()};models={};pred={};sel={}
    for a in AUTHORS:
        src=[b for b in AUTHORS if b!=a];raw=[r['values'] for b in src for r in ff[b]];y=[v for b in src for v in labels[b]];w=[1/len(ff[b]) for b in src for r in ff[b]];models[a]={n:fit(raw,y,w,cols) for n,cols in [('rich19',list(range(19))),('control3',[0,9,18])]};pred[a]={n:predict(ff[a],m) for n,m in models[a].items()};sel[a]={n:{f'top{k}':top(s,k) for k in [10,20]} for n,s in pred[a].items()}
    for n,v in [('models',models),('predictions',pred),('selections',sel)]:save(O/(n+'.json'),v)
    save(O/'prediction-freeze.json',{n:sha(O/n) for n in ['models.json','predictions.json','selections.json']});summary={};oracle={}
    for a in AUTHORS:
        edges=graphs[a]['descriptors'];assert len(edges)==len(labels[a])==len(ff[a]);assert all((r['a'],r['b'])==(e['a'],e['b']) for r,e in zip(ff[a],edges));nt=len({e[s] for e in edges for s in ['a','b']});y=labels[a];oracle[a]={f'top{k}':top(y,k) for k in [10,20]};summary[a]=dict(all=measure(list(range(len(y))),y,edges,nt),models={n:dict(mse=float(np.mean((np.array(s)-y)**2)),lists={label:measure(ix,y,edges,nt) for label,ix in sel[a][n].items()}) for n,s in pred[a].items()},oracle={label:measure(ix,y,edges,nt) for label,ix in oracle[a].items()})
    save(O/'oracle-selections.json',oracle);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,'all',round(v['all']['mean_compatibility'],4),{n:{k:(d['edges'],round(d['mean_compatibility'],4)) for k,d in r['lists'].items()} for n,r in v['models'].items()},'oracle',{k:(r['edges'],round(r['mean_compatibility'],4)) for k,r in v['oracle'].items()})
if __name__=='__main__':run()
