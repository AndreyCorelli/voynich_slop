"""Independent priorities, greedy matching and empirical summaries."""
from pathlib import Path
import json,random,hashlib,math
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration228';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def close(a,b):assert math.isclose(a,b,abs_tol=1e-11,rel_tol=1e-11)
def describe(v):return dict(mean=sum(v)/len(v),minimum=min(v),maximum=max(v),q05=float(np.quantile(v,.05)),q95=float(np.quantile(v,.95)))
def run():
    gg=read(P/'iteration193/graphs.json');scores=read(P/'iteration227/scores.json');orders=read(O/'random-orders.json');sel=read(O/'selections.json');dd=read(O/'details.json');ss=read(O/'summary.json');labels=read(P/'iteration223/details.json');old=read(P/'iteration227/summary.json');count=0
    for j,seed in enumerate(range(22800,22999)):
        rng=random.Random(seed)
        for a in AA:
            edges=gg[a]['descriptors'];order=list(range(len(edges)));rng.shuffle(order);assert order==orders[j][a];rank={v:i for i,v in enumerate(order)}
            for name in list(scores[a])+['uniform']:
                sequence=order if name=='uniform' else sorted(range(len(edges)),key=lambda i:(-scores[a][name][i],rank[i]))
                for k in [10,20]:
                    used=set();chosen=[]
                    for i in sequence:
                        e=edges[i];ends={e['a'],e['b']}
                        if not used.intersection(ends):chosen.append(i);used|=ends
                        if len(chosen)==k:break
                    label=f'top{k}';assert chosen==sel[j][a][name][label];assert len(used)==2*len(chosen);assert dd[a][name][label]['selected'][j]==len(chosen);close(dd[a][name][label]['compatibility'][j],sum(labels[a]['edge_values'][i] for i in chosen)/len(chosen));count+=1
    for a in AA:
        for name,methods in dd[a].items():
            for label,d in methods.items():
                r=ss[a][name][label];v=d['compatibility'];expected=describe(v)
                for k,x in expected.items():close(x,r['compatibility'][k])
                assert r['selected_min']==min(d['selected']) and r['selected_max']==max(d['selected']) and r['shortfall_runs']==sum(n<int(label[3:]) for n in d['selected'])
                if name=='uniform':assert r['deterministic'] is None
                else:
                    assert r['deterministic']==old[a]['rankings'][name]['disjoint'][label]['mean_compatibility'];diff=[x-y for x,y in zip(v,dd[a]['uniform'][label]['compatibility'])];expected=describe(diff);expected['fraction_positive']=sum(x>1e-12 for x in diff)/199
                    for k,x in expected.items():close(x,r['paired_difference'][k])
    hashes=0
    freeze=read(O/'design-freeze.json');assert freeze['seeds']==list(range(22800,22999)) and freeze['author_order']==AA
    for manifest in [freeze['inputs'],read(P/'iteration227/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'selection-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',greedy_lists=count,summary_groups=40,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
