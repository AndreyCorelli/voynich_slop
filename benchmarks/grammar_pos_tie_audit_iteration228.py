"""Fixed tie randomization and matched uniform greedy matching controls."""
from pathlib import Path
import json,hashlib,random
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration228';AA=['Aquinas','Caesar','Cicero','Jerome']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def select(order,edges,k):
    used=set();ix=[]
    for i in order:
        e=edges[i]
        if used.isdisjoint([e['a'],e['b']]):ix.append(i);used.update([e['a'],e['b']])
        if len(ix)==k:break
    return ix

def describe(values):return dict(mean=float(np.mean(values)),minimum=min(values),maximum=max(values),q05=float(np.quantile(values,.05)),q95=float(np.quantile(values,.95)))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration193/graphs.json','iteration227/scores.json','iteration227/summary.json','iteration227/verification-manifest.json','iteration223/details.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(22800,22999)),author_order=AA,quantiles='numpy linear .05/.95'))
    for p,h in read(P/'iteration227/verification-manifest.json').items():assert sha(Path(p))==h
    graphs=read(P/'iteration193/graphs.json');scores=read(P/'iteration227/scores.json');orders=[];lists=[]
    for seed in range(22800,22999):
        rng=random.Random(seed);oo={};ss={}
        for a in AA:
            edges=graphs[a]['descriptors'];order=list(range(len(edges)));rng.shuffle(order);oo[a]=order;priority={i:j for j,i in enumerate(order)};methods={name:sorted(order,key=lambda i:(-s[i],priority[i])) for name,s in scores[a].items()};methods['uniform']=order;ss[a]={name:{f'top{k}':select(rank,edges,k) for k in [10,20]} for name,rank in methods.items()}
        orders.append(oo);lists.append(ss)
    save(O/'random-orders.json',orders);save(O/'selections.json',lists);save(O/'selection-freeze.json',{n:sha(O/n) for n in ['random-orders.json','selections.json']})
    labels=read(P/'iteration223/details.json');old=read(P/'iteration227/summary.json');details={};summary={}
    for a in AA:
        y=labels[a]['edge_values'];details[a]={};summary[a]={}
        for name in list(scores[a])+['uniform']:
            details[a][name]={};summary[a][name]={}
            for label in ['top10','top20']:
                ixsets=[ss[a][name][label] for ss in lists];values=[sum(y[i] for i in ix)/len(ix) for ix in ixsets];counts=[len(ix) for ix in ixsets];details[a][name][label]=dict(compatibility=values,selected=counts);summary[a][name][label]=dict(compatibility=describe(values),selected_min=min(counts),selected_max=max(counts),shortfall_runs=sum(n<int(label[3:]) for n in counts),deterministic=old[a]['rankings'][name]['disjoint'][label]['mean_compatibility'] if name!='uniform' else None)
        for name in scores[a]:
            for label in ['top10','top20']:
                differences=[x-y for x,y in zip(details[a][name][label]['compatibility'],details[a]['uniform'][label]['compatibility'])];summary[a][name][label]['paired_difference']=dict(**describe(differences),fraction_positive=sum(v>1e-12 for v in differences)/199)
    save(O/'details.json',details);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{name:{label:dict(mean=round(d['compatibility']['mean'],4),minimum=round(d['compatibility']['minimum'],4),maximum=round(d['compatibility']['maximum'],4),positive=d.get('paired_difference',{}).get('fraction_positive')) for label,d in rr.items()} for name,rr in v.items()})
if __name__=='__main__':run()
