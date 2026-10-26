"""Independent Lloyd/ARI, scalar controls, all assignments and sampled LP duals."""
from pathlib import Path
from collections import Counter
import json,random,hashlib
import numpy as np
from scipy.optimize import linear_sum_assignment,linprog
P=Path('experiments/results/grammar-restoration');O=P/'iteration235';K=17
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-9,rtol=1e-9)
def ari(u,v):
    table=np.zeros((K,K),int)
    for a,b in zip(u,v):table[a,b]+=1
    comb=lambda z:np.sum(z*(z-1)/2);both=comb(table);first=comb(table.sum(1));second=comb(table.sum(0));expected=first*second/(len(u)*(len(u)-1)/2);den=(first+second)/2-expected;return (both-expected)/den if den else 1.
def ranges(v):return dict(minimum=float(min(v)),mean=float(np.mean(v)),maximum=float(max(v)))
def run():
    base=read(P/'iteration234-retry/clusters.json');runs=read(O/'runs.json');co=read(O/'co-membership.json');stability=read(O/'stability.json');ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');strata=read(P/'iteration234-retry/strata.json');dd=read(O/'details.json');ss=read(O/'summary.json');replays=certs=metricgroups=0
    constraints=np.zeros((K*K,2*K))
    for i in range(K):
        for j in range(K):constraints[i*K+j,i]=-1;constraints[i*K+j,K+j]=-1
    for a,rr in runs.items():
        x=np.array(base[a]['embedding']);assert [r['seed'] for r in rr]==list(range(23500,23531))
        for r in rr:
            chosen=[random.Random(r['seed']).randrange(len(x))]
            while len(chosen)<K:
                distance=np.min(np.sum((x[:,None,:]-x[chosen][None,:,:])**2,axis=2),axis=1);distance[chosen]=-1;chosen.append(int(np.argmax(distance)))
            assert chosen==r['initial_center_indices'];centers=x[chosen].copy();previous=None
            for iteration in range(300):
                label=np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1);new=centers.copy()
                for j in range(K):
                    if any(label==j):new[j]=np.mean(x[label==j],axis=0)
                movement=max(np.linalg.norm(new-centers,axis=1));centers=new
                if previous is not None and np.array_equal(label,previous) or movement<=1e-10:break
                previous=label.copy()
            expected=np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1);assert expected.tolist()==r['labels'] and iteration+1==r['iterations'];near(centers,r['centers']);replays+=1
        cm=np.zeros((len(x),len(x)))
        for r in rr:
            for i,u in enumerate(r['labels']):cm[i]+=[int(u==v)/31 for v in r['labels']]
        near(cm,co[a]);expected=dict(pairwise_ari=ranges([ari(u['labels'],v['labels']) for i,u in enumerate(rr) for v in rr[i+1:]]),reference_ari=ranges([ari(r['labels'],base[a]['labels']) for r in rr]),singleton_clusters=ranges([sum(n==1 for n in Counter(r['labels']).values()) for r in rr]),largest_cluster=ranges([max(Counter(r['labels']).values()) for r in rr]),occupied_groups=ranges([len(set(r['labels'])) for r in rr]))
        for name,v in expected.items():
            for key,z in v.items():near(z,stability[a][name][key])
        lookup={r['word']:i for i,r in enumerate(ff[a])};y=np.array([truth[a]['profiles'][lookup[w]] for w in base[a]['words']]);freq=np.array([truth[a]['frequencies'][lookup[w]] for w in base[a]['words']]);assignments=[np.arange(len(y))]
        for seed in range(23300,23499):
            rng=random.Random(seed);perm=np.arange(len(y))
            for bucket in strata[a]:
                ix=bucket['indices'];order=ix.copy();rng.shuffle(order);perm[ix]=order
            assignments.append(perm)
        for weighting,ww in [('type_macro',np.ones(len(y))),('token_weighted',freq)]:
            w=ww/ww.sum()
            for ri,r in enumerate(rr):
                record=dd[a][weighting][ri];assert record['seed']==r['seed']
                for ai,permutation in enumerate(assignments):
                    matrix=np.zeros((K,K));np.add.at(matrix,r['labels'],w[:,None]*y[permutation]);i,j=linear_sum_assignment(-matrix);value=dict(one_to_one=float(matrix[i,j].sum()),purity=float(matrix.max(1).sum()));stored=record['actual'] if ai==0 else record['null'][ai-1]
                    for k,v in value.items():near(v,stored[k])
                    metricgroups+=1
                    if ai in [0,1,100,199]:
                        dual=linprog(np.ones(2*K),A_ub=constraints,b_ub=-matrix.ravel(),bounds=[(None,None)]*(2*K),method='highs');assert dual.success;assert np.all(dual.x[:K,None]+dual.x[None,K:]>=matrix-1e-9);near(dual.fun,value['one_to_one']);certs+=1
                for metric,tail in record['tails'].items():near(tail,(1+sum(z[metric]>=record['actual'][metric]-1e-12 for z in record['null']))/200)
            for metric,v in ss[a][weighting].items():
                records=dd[a][weighting];actual=ranges([r['actual'][metric] for r in records]);tails=ranges([r['tails'][metric] for r in records])
                for k,z in actual.items():near(z,v['actual'][k])
                for k,z in tails.items():near(z,v['tails'][k])
                assert v['runs_tail_le_05']==sum(r['tails'][metric]<=.05 for r in records)
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration234-retry/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'cluster-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',lloyd_replays=replays,assignment_metric_groups=metricgroups,assignment_dual_certificates=certs,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
