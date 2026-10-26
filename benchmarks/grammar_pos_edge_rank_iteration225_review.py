"""Independent rational targets, augmented least squares and ranking audit."""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
import json,hashlib,math
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration225'
def read(p):return json.loads(p.read_text())
def near(x,y,tol=1e-11):assert np.allclose(x,y,atol=tol,rtol=tol)
def run():
    ff=read(O/'features.json');gg=read(P/'iteration193/graphs.json');ref=read(P/'iteration201/development-references.json');oldlabels=read(P/'iteration223/details.json');mm=read(O/'models.json');pp=read(O/'predictions.json');sel=read(O/'selections.json');oracle=read(O/'oracle-selections.json');ss=read(O/'summary.json');labels={};fits=lists=0
    assert ff=={a:r for a,r in read(P/'iteration193/features.json').items() if a in ff}
    for a in ff:
        counts=defaultdict(Counter)
        for i,p in enumerate(gg[a]['positions']):
            if p is not None:counts[gg[a]['ids'][i]][ref[a]['pos'][i]]+=1
        profiles={w:{t:F(n,sum(v.values())) for t,n in v.items()} for w,v in counts.items()};labels[a]=[float(sum((v*profiles[e['b']].get(t,0) for t,v in profiles[e['a']].items()),F(0))) for e in gg[a]['descriptors']];near(labels[a],oldlabels[a]['edge_values'])
    for a in ff:
        src=[b for b in ff if b!=a];edges=gg[a]['descriptors'];totaltypes=len({e[k] for e in edges for k in ['a','b']})
        for name,m in mm[a].items():
            assert m['columns']==(list(range(19)) if name=='rich19' else [0,9,18]);raw=np.array([r['values'] for b in src for r in ff[b]])[:,m['columns']];y=np.array([v for b in src for v in labels[b]]);w=np.array([1/(3*len(ff[b])) for b in src for r in ff[b]]);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;near(mu,m['mean']);near(sd,m['scale']);x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);pen=np.diag([0]+[math.sqrt(.1)]*len(m['columns']));aug=np.vstack([np.sqrt(w)[:,None]*x,pen]);target=np.concatenate([np.sqrt(w)*y,np.zeros(x.shape[1])]);beta=np.linalg.lstsq(aug,target,rcond=None)[0];near(beta,m['beta']);fits+=1
            tx=np.array([r['values'] for r in ff[a]])[:,m['columns']];pred=(np.column_stack([np.ones(len(tx)),(tx-mu)/sd])@np.array(m['beta'])).tolist();near(pred,pp[a][name]);near(np.mean((np.array(pred)-labels[a])**2),ss[a]['models'][name]['mse'])
        collections=[('all',list(range(len(edges))),ss[a]['all'])]
        for name,scores in list(pp[a].items())+[('oracle',labels[a])]:
            for k in [10,20]:
                cutoff=sorted(scores,reverse=True)[min(k,len(scores))-1];ix=[i for i,v in enumerate(scores) if v>=cutoff];expected=oracle[a]['top'+str(k)] if name=='oracle' else sel[a][name]['top'+str(k)];assert ix==expected;metric=ss[a]['oracle']['top'+str(k)] if name=='oracle' else ss[a]['models'][name]['lists']['top'+str(k)];collections.append((name,ix,metric));lists+=1
        for name,ix,m in collections:
            ends={edges[i][k] for i in ix for k in ['a','b']};assert m['edges']==len(ix) and m['endpoints']==len(ends);near(m['mean_compatibility'],sum(labels[a][i] for i in ix)/len(ix));near(m['endpoint_coverage'],len(ends)/totaltypes)
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration224/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for fn in ['feature-freeze.json','prediction-freeze.json']:
        for p,h in read(O/fn).items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',rational_targets=sum(map(len,labels.values())),least_squares_refits=fits,lists=lists,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
