"""Independent degree-preserving replay, scalar averaging and metrics."""
from pathlib import Path
from collections import Counter
import json,random,math,hashlib
from benchmarks.grammar_case_applicability_iteration180_review import independent_evaluate,close
P=Path('experiments/results/grammar-restoration');O=P/'iteration222'
def read(p):return json.loads(p.read_text())
def swap_replay(edges,seed):
    rng=random.Random(seed);ee=[tuple(e) for e in edges];present=set(ee);accepted=attempts=0
    while accepted<10*len(ee) and attempts<100*len(ee):
        attempts+=1;i,j=rng.sample(range(len(ee)),2);a,b=ee[i];c,d=ee[j]
        if len({a,b,c,d})!=4:continue
        if rng.randrange(2)==1:c,d=d,c
        first=tuple(sorted([a,c]));second=tuple(sorted([b,d]))
        if first in present or second in present:continue
        present.difference_update([ee[i],ee[j]]);present.update([first,second]);ee[i]=first;ee[j]=second;accepted+=1
    return sorted(ee),dict(seed=seed,attempts=attempts,accepted=accepted,target=10*len(ee))
def run():
    ff=read(P/'iteration221/features.json');nodes=read(P/'iteration220/nodes.json');rewired=read(O/'rewired-edges.json');audit=read(O/'rewiring-audit.json');scores=read(O/'scores.json');dd=read(O/'details.json');ss=read(O/'summary.json');projection=read(P/'iteration221/center-projection.json');labels=read(P/'iteration220/labels.json');support=read(P/'iteration207/predictions.json');yy=read(P/'iteration207/teacher-labels.json');original=read(P/'iteration221/predictions.json');graphs=metrics=0
    for a,rows in ff.items():
        ix={r['word']:i for i,r in enumerate(rows)};edges=sorted({tuple(sorted([ix[r['word']],ix[v]])) for r in nodes[a] for v in r['neighbors']});degrees=Counter(v for e in edges for v in e);y=[labels[a][r['word']] for r in rows];cy=[y[i] for i in projection[a]]
        for j,seed in enumerate(range(22200,22399)):
            ee,log=swap_replay(edges,seed);assert ee==[tuple(e) for e in rewired[a][j]] and log==audit[a][j];assert len(set(ee))==len(edges) and all(u!=v for u,v in ee);assert Counter(v for e in ee for v in e)==degrees;graphs+=1
        for variant,methods in scores[a].items():
            seed=original[a][variant]['original'];assert seed==methods['original']
            for method,sets in methods.items():
                vectors=sets if method=='rewired' else [sets]
                for j,p in enumerate(vectors):
                    if method=='global_mean':expected=[(z+sum(seed)/len(seed))/2 for z in seed]
                    elif method=='original':expected=seed
                    else:
                        ee=edges if method=='actual' else rewired[a][j];adj=[[] for _ in seed]
                        for u,v in ee:adj[u].append(v);adj[v].append(u)
                        expected=[(seed[i]+sum(seed[v] for v in neighbors)/len(neighbors))/2 for i,neighbors in enumerate(adj)]
                    close(expected,p);cp=[p[i] for i in projection[a]];allm=independent_evaluate(y,p);cm=independent_evaluate(cy,cp);keep=[i for i,v in enumerate(cp) if v>=.5];product=[p*q for p,q in zip(cp,support[a]['full12'])];v=dd[a][variant][method][j] if method=='rewired' else dd[a][variant][method];expectedmetrics=dict(all_auc=allm['auc'],all_nll=allm['nll'],center_auc=cm['auc'],center_nll=cm['nll'],retained=sum(yy[a][i] for i in keep),admissions=len(keep))
                    for mode,ps,universe in [('hard',support[a]['full12'],keep),('product',product,list(range(len(cp))))]:
                        for k in [3,5]:
                            cut=sorted([ps[i] for i in universe],reverse=True)[min(k,len(universe))-1] if universe else None;selected=[i for i in universe if ps[i]>=cut] if universe else [];expectedmetrics[f'{mode}{k}_hits']=sum(yy[a][i] for i in selected);expectedmetrics[f'{mode}{k}_selected']=len(selected)
                    close(expectedmetrics,v);metrics+=1
            for metric,r in ss[a][variant].items():
                null=[v[metric] for v in dd[a][variant]['rewired']];value=dd[a][variant]['actual'][metric];low=metric.endswith('nll');tail=(1+sum(v<=value+1e-12 if low else v>=value-1e-12 for v in null))/200;close(r,dict(original=dd[a][variant]['original'][metric],actual=value,global_mean=dd[a][variant]['global_mean'][metric],null_mean=sum(null)/199,null_min=min(null),null_max=max(null),directional_tail=tail))
    hashes=0
    for manifest in [read(O/'design-freeze.json'),read(P/'iteration221-finalization/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for fn in ['graph-freeze.json','score-freeze.json']:
        for p,h in read(O/fn).items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',rewired_graphs=graphs,metric_groups=metrics,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
