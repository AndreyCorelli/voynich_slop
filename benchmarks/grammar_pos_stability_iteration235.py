"""All-run initialization stability on fixed corrected graph embeddings."""
from pathlib import Path
from collections import Counter
import json,hashlib,random
import numpy as np
from scipy.optimize import linear_sum_assignment
P=Path('experiments/results/grammar-restoration');O=P/'iteration235';K=17

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def lloyd(x,seed):
    chosen=[random.Random(seed).randrange(len(x))]
    while len(chosen)<K:
        distance=((x[:,None,:]-x[chosen][None,:,:])**2).sum(2).min(1);distance[chosen]=-1;chosen.append(int(np.argmax(distance)))
    centers=x[chosen].copy();previous=None
    for iteration in range(300):
        labels=((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1);new=centers.copy()
        for j in range(K):
            if np.any(labels==j):new[j]=x[labels==j].mean(0)
        movement=float(np.max(np.linalg.norm(new-centers,axis=1)));centers=new
        if previous is not None and np.array_equal(labels,previous) or movement<=1e-10:break
        previous=labels.copy()
    labels=((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
    return dict(seed=seed,labels=labels.tolist(),initial_center_indices=chosen,iterations=iteration+1,centers=centers.tolist())
def ari(u,v):
    table=Counter(zip(u,v));a=Counter(u);b=Counter(v);choose=lambda n:n*(n-1)/2;both=sum(choose(n) for n in table.values());x=sum(choose(n) for n in a.values());y=sum(choose(n) for n in b.values());expected=x*y/choose(len(u));den=.5*(x+y)-expected;return (both-expected)/den if den else 1.
def range_summary(v):return dict(minimum=float(min(v)),mean=float(np.mean(v)),maximum=float(max(v)))
def evaluate(matrix):
    r,c=linear_sum_assignment(-matrix);return dict(one_to_one=float(matrix[r,c].sum()),purity=float(matrix.max(axis=1).sum()))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration234-retry/clusters.json','iteration234-retry/strata.json','iteration234-retry/verification-manifest.json','iteration231/features.json','iteration231/truth.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},initial_seeds=list(range(23500,23531)),null_seeds=list(range(23300,23499))))
    for p,h in read(P/'iteration234-retry/verification-manifest.json').items():assert sha(Path(p))==h
    base=read(P/'iteration234-retry/clusters.json');runs={a:[lloyd(np.array(g['embedding']),seed) for seed in range(23500,23531)] for a,g in base.items()};stability={};co={}
    for a,rr in runs.items():
        labels=np.array([r['labels'] for r in rr]);co[a]=np.mean(labels[:,:,None]==labels[:,None,:],axis=0).tolist();pairs=[ari(u['labels'],v['labels']) for i,u in enumerate(rr) for v in rr[i+1:]];stability[a]=dict(pairwise_ari=range_summary(pairs),reference_ari=range_summary([ari(r['labels'],base[a]['labels']) for r in rr]),singleton_clusters=range_summary([sum(n==1 for n in Counter(r['labels']).values()) for r in rr]),largest_cluster=range_summary([max(Counter(r['labels']).values()) for r in rr]),occupied_groups=range_summary([len(set(r['labels'])) for r in rr]))
    for n,v in [('runs',runs),('co-membership',co),('stability',stability)]:save(O/(n+'.json'),v)
    save(O/'cluster-freeze.json',{n:sha(O/n) for n in ['runs.json','co-membership.json','stability.json']})
    ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');strata=read(P/'iteration234-retry/strata.json');details={};summary={}
    for a,rr in runs.items():
        lookup={r['word']:i for i,r in enumerate(ff[a])};y=np.array([truth[a]['profiles'][lookup[w]] for w in base[a]['words']]);freq=np.array([truth[a]['frequencies'][lookup[w]] for w in base[a]['words']]);all_y=[y]
        for seed in range(23300,23499):
            rng=random.Random(seed);perm=np.arange(len(y))
            for bucket in strata[a]:
                ix=bucket['indices'];source=ix.copy();rng.shuffle(source);perm[ix]=source
            all_y.append(y[perm])
        all_y=np.array(all_y);onehot=np.array([np.eye(K)[r['labels']].T for r in rr]);details[a]={};summary[a]={}
        for weighting,w in [('type_macro',np.ones(len(y))),('token_weighted',freq)]:
            w=w/w.sum();matrices=np.einsum('rcn,snt->rsct',onehot*w[None,None,:],all_y,optimize=True);records=[]
            for i,r in enumerate(rr):
                results=[evaluate(m) for m in matrices[i]];actual=results[0];null=results[1:];records.append(dict(seed=r['seed'],actual=actual,null=null,tails={metric:(1+sum(z[metric]>=actual[metric]-1e-12 for z in null))/200 for metric in actual}))
            details[a][weighting]=records;summary[a][weighting]={metric:dict(actual=range_summary([r['actual'][metric] for r in records]),tails=range_summary([r['tails'][metric] for r in records]),runs_tail_le_05=sum(r['tails'][metric]<=.05 for r in records)) for metric in ['one_to_one','purity']}
    save(O/'details.json',details);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,'ARI',stability[a]['pairwise_ari'],{w:r['purity'] for w,r in v.items()})
if __name__=='__main__':run()
