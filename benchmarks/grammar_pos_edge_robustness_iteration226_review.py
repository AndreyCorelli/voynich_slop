"""Independent permutation orders, augmented LS predictions and disjoint audit."""
from pathlib import Path
import json,hashlib,random,math
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration226';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-10,rtol=1e-10)
def run():
    ff=read(P/'iteration225/features.json');labels={a:r['edge_values'] for a,r in read(P/'iteration223/details.json').items()};orders=read(O/'permutation-orders.json');pp=read(O/'null-predictions.json');sel=read(O/'null-selections.json');dd=read(O/'disjoint-selections.json');gg=read(P/'iteration193/graphs.json');real=read(P/'iteration225/predictions.json');ss=read(O/'summary.json');nv=read(O/'null-values.json');old=read(P/'iteration225/summary.json');maps={};refits=lists=0
    for a in AA:
        src=[b for b in AA if b!=a];maps[a]={}
        for name,cols in [('rich19',list(range(19))),('control3',[0,9,18])]:
            raw=np.array([r['values'] for b in src for r in ff[b]])[:,cols];w=np.array([1/(3*len(ff[b])) for b in src for r in ff[b]]);mu=w@raw;sd=np.sqrt(w@((raw-mu)**2));sd[sd<1e-12]=1;x=np.column_stack([np.ones(len(raw)),(raw-mu)/sd]);pen=np.diag([0]+[math.sqrt(.1)]*len(cols));aug=np.vstack([np.sqrt(w)[:,None]*x,pen]);targetmap=np.linalg.lstsq(aug,np.vstack([np.diag(np.sqrt(w)),np.zeros((len(cols)+1,len(w)))]),rcond=None)[0];tx=np.array([r['values'] for r in ff[a]])[:,cols];maps[a][name]=np.column_stack([np.ones(len(tx)),(tx-mu)/sd])@targetmap
    for j,seed in enumerate(range(22500,22699)):
        rng=random.Random(seed)
        for a in AA:
            ix=list(range(len(labels[a])));rng.shuffle(ix);assert ix==orders[j][a]
        for a in AA:
            y=[labels[b][i] for b in AA if b!=a for i in orders[j][b]]
            for name,matrix in maps[a].items():
                near(matrix@np.array(y),pp[j][a][name]);refits+=1
                for k in [10,20]:
                    label=f'top{k}';scores=pp[j][a][name];cut=sorted(scores,reverse=True)[k-1];ix=[i for i,v in enumerate(scores) if v>=cut];assert ix==sel[j][a][name][label];near(sum(labels[a][i] for i in ix)/len(ix),nv[a][name][label][j]);lists+=1
    for a in AA:
        edges=gg[a]['descriptors'];totaltypes=len({e[k] for e in edges for k in ['a','b']})
        for name,scores in real[a].items():
            for k in [10,20]:
                label=f'top{k}';used=set();selected=[]
                for i in sorted(range(len(scores)),key=lambda i:(-scores[i],i)):
                    endpoints={edges[i]['a'],edges[i]['b']}
                    if used.isdisjoint(endpoints):selected.append(i);used|=endpoints
                    if len(selected)==k:break
                assert selected==dd[a][name][label] and len(used)==2*len(selected);r=ss[a][name][label];d=r['disjoint'];assert d['edges']==len(selected) and d['endpoints']==len(used) and d['requested']==k and d['shortfall']==k-len(selected);near(d['mean_compatibility'],sum(labels[a][i] for i in selected)/len(selected));near(d['endpoint_coverage'],len(used)/totaltypes);values=nv[a][name][label];near(r['actual'],old[a]['models'][name]['lists'][label]['mean_compatibility']);near(r['null_mean'],sum(values)/199);near(r['null_min'],min(values));near(r['null_max'],max(values));near(r['upper_tail'],(1+sum(v>=r['actual']-1e-12 for v in values))/200)
        for label,r in ss[a]['paired_rich_minus_control'].items():
            values=[x-y for x,y in zip(nv[a]['rich19'][label],nv[a]['control3'][label])];actual=ss[a]['rich19'][label]['actual']-ss[a]['control3'][label]['actual'];near(actual,r['actual']);near(sum(values)/199,r['null_mean']);near((1+sum(v>=actual-1e-12 for v in values))/200,r['upper_tail'])
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration225/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'prediction-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',least_squares_null_replays=refits,null_lists=lists,disjoint_lists=16,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
