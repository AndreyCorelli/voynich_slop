"""Component-aware graph-only spectral grouping, fixed comparison to233."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,random
import numpy as np
from scipy.optimize import linear_sum_assignment
P=Path('experiments/results/grammar-restoration');O=P/'iteration234-retry';AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];K=17

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def cluster(g):
    words=sorted({e[s] for e in g['descriptors'] for s in ['a','b']});lookup={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
    for e in g['descriptors']:i,j=lookup[e['a']],lookup[e['b']];adj[i,j]=adj[j,i]=1
    degree=adj.sum(1);lap=np.eye(len(words))-adj/np.sqrt(degree[:,None]*degree[None,:]);eigenvalues,vectors=np.linalg.eigh(lap);zero=int(sum(eigenvalues<=1e-10));dim=min(len(words),zero+K);boundary=dim-1
    while dim<len(words) and abs(eigenvalues[dim]-eigenvalues[boundary])<=1e-10:dim+=1
    x=vectors[:,:dim];norm=np.linalg.norm(x,axis=1);assert np.all(norm>1e-12);x=x/norm[:,None];rng=random.Random(23300);chosen=[rng.randrange(len(words))]
    while len(chosen)<K:
        distance=((x[:,None,:]-x[chosen][None,:,:])**2).sum(2).min(1);distance[chosen]=-1;chosen.append(int(np.argmax(distance)))
    centers=x[chosen].copy();previous=None
    for iteration in range(300):
        distance=((x[:,None,:]-centers[None,:,:])**2).sum(2);labels=distance.argmin(1);new=centers.copy()
        for j in range(K):
            if np.any(labels==j):new[j]=x[labels==j].mean(0)
        movement=float(np.max(np.linalg.norm(new-centers,axis=1)));centers=new
        if previous is not None and np.array_equal(labels,previous) or movement<=1e-10:break
        previous=labels.copy()
    labels=((x[:,None,:]-centers[None,:,:])**2).sum(2).argmin(1)
    return dict(words=words,labels=labels.tolist(),embedding=x.tolist(),eigenvalues=eigenvalues.tolist(),embedding_dimension=dim,zero_eigenvalues=int(sum(abs(eigenvalues)<=1e-10)),initial_center_indices=chosen,centers=centers.tolist(),iterations=iteration+1,occupied=len(set(labels.tolist())))

def score(labels,y,weights):
    w=np.array(weights,dtype=float);w/=w.sum();y=np.array(y);m=np.zeros((K,K))
    for i,j in enumerate(labels):m[j]+=w[i]*y[i]
    rows,cols=linear_sum_assignment(-m);return dict(one_to_one=float(m[rows,cols].sum()),purity=float(m.max(1).sum()),majority=float((w@y).max()),profile_oracle=float(w@y.max(1)),mapping={str(i):int(j) for i,j in zip(rows,cols)},matrix=m.tolist())
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_spectral_iteration234.py'),P/'iteration234/design-freeze.json']+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration231/features.json','iteration231/truth.json','iteration231/design-freeze.json','iteration201/development-references.json','iteration199/case-references.json','iteration233/verification-manifest.json','iteration233/summary.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},clusters=K,seeds=list(range(23300,23499)),initialization='farthest first with initial index Random(23300); one run; all zero modes plus17 positive directions; full boundary eigenspace'))
    for p,h in read(P/'iteration233/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];groups={a:cluster(gg[a]) for a in AA};save(O/'clusters.json',groups);save(O/'cluster-freeze.json',{'clusters.json':sha(O/'clusters.json')})
    ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');case=read(P/'iteration201/development-references.json');case['Dante']={'case':read(P/'iteration199/case-references.json')['case_by_stream_position']};details={};summary={};strata={}
    for a,g in groups.items():
        index={r['word']:i for i,r in enumerate(ff[a])};y=np.array([truth[a]['profiles'][index[w]] for w in g['words']]);freq=[truth[a]['frequencies'][index[w]] for w in g['words']];casewords={gg[a]['ids'][i] for i,p in enumerate(gg[a]['positions']) if p is not None and case[a]['case'][i]};buckets=defaultdict(list)
        for i,(w,n) in enumerate(zip(g['words'],freq)):b=sum(n>=t for t in [10,20,50,100]);buckets[(b,int(w in casewords))].append(i)
        strata[a]=[dict(frequency_bin=b,case_bearing=c,indices=ix) for (b,c),ix in sorted(buckets.items())];details[a]={};summary[a]={}
        for weighting,w in [('type_macro',[1]*len(y)),('token_weighted',freq)]:
            actual=score(g['labels'],y,w);null=[]
            for seed in range(23300,23499):
                rng=random.Random(seed);perm=np.arange(len(y))
                for key,ix in sorted(buckets.items()):
                    source=ix.copy();rng.shuffle(source);perm[ix]=source
                result=score(g['labels'],y[perm],w);null.append({k:result[k] for k in ['one_to_one','purity','majority','profile_oracle']})
            details[a][weighting]=dict(actual=actual,null=null);summary[a][weighting]=dict(nodes=len(y),occupied_groups=g['occupied'],embedding_dimension=g['embedding_dimension'],zero_eigenvalues=g['zero_eigenvalues'],actual={k:actual[k] for k in ['one_to_one','purity','majority','profile_oracle']},null={metric:dict(mean=sum(r[metric] for r in null)/199,maximum=max(r[metric] for r in null),upper_tail=(1+sum(r[metric]>=actual[metric]-1e-12 for r in null))/200) for metric in ['one_to_one','purity']})
    for n,v in [('strata',strata),('details',details),('summary',summary)]:save(O/(n+'.json'),v)
    previous=read(P/'iteration233/summary.json');save(O/'comparison.json',{a:{w:dict(previous=previous[a][w],current=summary[a][w]) for w in summary[a]} for a in AA})
    for a in AA:print(a,{w:dict(previous=round(previous[a][w]['actual']['purity'],4),current=round(summary[a][w]['actual']['purity'],4),tail=summary[a][w]['null']['purity']['upper_tail'],dimension=groups[a]['embedding_dimension']) for w in summary[a]})
if __name__=='__main__':run()
