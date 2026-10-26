"""Independent eigenspace geometry, Lloyd replay, profiles and LP-dual scores."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,random
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import linprog
P=Path('experiments/results/grammar-restoration');O=P/'iteration233';K=17
def read(p):return json.loads(p.read_text())
def near(a,b,tol=1e-9):assert np.allclose(a,b,atol=tol,rtol=tol)
def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];groups=read(O/'clusters.json');strata=read(O/'strata.json');truth=read(P/'iteration231/truth.json');ff=read(P/'iteration231/features.json');dd=read(O/'details.json');ss=read(O/'summary.json');case=read(P/'iteration201/development-references.json');case['Dante']={'case':read(P/'iteration199/case-references.json')['case_by_stream_position']};certificates=0
    constraints=np.zeros((K*K,2*K))
    for i in range(K):
        for j in range(K):constraints[i*K+j,i]=-1;constraints[i*K+j,K+j]=-1
    def certify(labels,y,ww):
        w=np.array(ww,dtype=float);w/=w.sum();m=np.zeros((K,K))
        for i,label in enumerate(labels):m[label]+=w[i]*y[i]
        dual=linprog(np.ones(2*K),A_ub=constraints,b_ub=-m.ravel(),bounds=[(None,None)]*(2*K),method='highs');assert dual.success;assert np.all(dual.x[:K,None]+dual.x[None,K:]>=m-1e-9)
        return dict(one_to_one=float(dual.fun),purity=float(sum(max(row) for row in m)),majority=float(max(w@y)),profile_oracle=float(w@np.max(y,axis=1))),m
    for a,g in groups.items():
        words=sorted({e[s] for e in gg[a]['descriptors'] for s in ['a','b']});assert words==g['words'];index={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
        for e in gg[a]['descriptors']:u,v=index[e['a']],index[e['b']];adj[u,v]=adj[v,u]=1
        degree=adj.sum(1);lap=np.eye(len(words))-np.diag(degree**-.5)@adj@np.diag(degree**-.5);ev,vectors=eigh(lap,driver='evr');dim=K
        while dim<len(words) and abs(ev[dim]-ev[K-1])<=1e-10:dim+=1
        near(ev,g['eigenvalues']);assert dim==g['embedding_dimension'] and g['zero_eigenvalues']==sum(abs(ev)<=1e-10);z=vectors[:,:dim];z/=np.linalg.norm(z,axis=1)[:,None];x=np.array(g['embedding']);near(z@z.T,x@x.T,1e-8)
        # Replay algorithm on frozen coordinates; rotations preserve geometry but numerical tie order can vary.
        chosen=[random.Random(23300).randrange(len(words))]
        while len(chosen)<K:
            distances=np.min(np.sum((x[:,None,:]-x[chosen][None,:,:])**2,axis=2),axis=1);distances[chosen]=-1;chosen.append(int(np.argmax(distances)))
        assert chosen==g['initial_center_indices'];centers=x[chosen].copy();previous=None
        for iteration in range(300):
            labels=np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1);new=centers.copy()
            for j in range(K):
                if any(labels==j):new[j]=x[labels==j].mean(0)
            movement=max(np.linalg.norm(new-centers,axis=1));centers=new
            if previous is not None and np.array_equal(labels,previous) or movement<=1e-10:break
            previous=labels.copy()
        labels=np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1);assert labels.tolist()==g['labels'] and iteration+1==g['iterations'];near(centers,g['centers']);assert len(set(labels))==g['occupied']
        lookup={r['word']:i for i,r in enumerate(ff[a])};y=np.array([truth[a]['profiles'][lookup[w]] for w in words]);freq=[truth[a]['frequencies'][lookup[w]] for w in words];casewords={gg[a]['ids'][i] for i,p in enumerate(gg[a]['positions']) if p is not None and case[a]['case'][i]};buckets=defaultdict(list)
        for i,(w,n) in enumerate(zip(words,freq)):buckets[(sum(n>=t for t in [10,20,50,100]),int(w in casewords))].append(i)
        assert strata[a]==[dict(frequency_bin=b,case_bearing=c,indices=ix) for (b,c),ix in sorted(buckets.items())]
        for weighting,w in [('type_macro',[1]*len(y)),('token_weighted',freq)]:
            actual,m=certify(labels,y,w);certificates+=1;near(m,dd[a][weighting]['actual']['matrix']);near([actual[k] for k in actual],[dd[a][weighting]['actual'][k] for k in actual]);mapping=dd[a][weighting]['actual']['mapping'];assert len(set(mapping.values()))==K;near(sum(m[int(i),j] for i,j in mapping.items()),actual['one_to_one'])
            for j,seed in enumerate(range(23300,23499)):
                rng=random.Random(seed);perm=np.arange(len(y))
                for key,ix in sorted(buckets.items()):
                    shuffled=ix.copy();rng.shuffle(shuffled);perm[ix]=shuffled
                expected,_=certify(labels,y[perm],w);certificates+=1;near([expected[k] for k in expected],[dd[a][weighting]['null'][j][k] for k in expected])
            r=ss[a][weighting];near([actual[k] for k in actual],[r['actual'][k] for k in actual]);assert r['nodes']==len(y) and r['occupied_groups']==g['occupied'] and r['embedding_dimension']==dim and r['zero_eigenvalues']==g['zero_eigenvalues']
            for metric,values in r['null'].items():
                null=[z[metric] for z in dd[a][weighting]['null']];near(sum(null)/199,values['mean']);near(max(null),values['maximum']);near((1+sum(v>=r['actual'][metric]-1e-12 for v in null))/200,values['upper_tail'])
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration232/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'cluster-freeze.json').items():assert hashlib.sha256((O/p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',eigenspace_and_clustering_replays=5,assignment_dual_certificates=certificates,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
