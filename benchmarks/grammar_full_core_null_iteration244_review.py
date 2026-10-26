"""Independent full-pipeline graph, clustering, intersection and purity replay."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import gzip,json,hashlib,random
import numpy as np
from scipy.linalg import eigh
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
from benchmarks.grammar_pos_cores_iteration236_review import measure
P=Path('experiments/results/grammar-restoration');O=P/'iteration244'
def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-8,rtol=1e-8)
def rebuild(g,removed):
    valid=[p is not None and tuple(p[:2]) not in removed for p in g['positions']];freq=Counter(w for w,v in zip(g['ids'],valid) if v);frames=defaultdict(lambda:defaultdict(list))
    for i in range(1,len(valid)-1):
        if valid[i-1] and valid[i] and valid[i+1] and freq[g['ids'][i]]>=5:frames[(g['ids'][i-1],g['ids'][i+1])][g['ids'][i]].append(i)
    pairs=defaultdict(list)
    for f,words in sorted(frames.items()):
        for u,v in combinations(sorted(words),2):pairs[u,v].append(dict(frame=list(f),a_positions=words[u],b_positions=words[v]))
    return [dict(a=u,b=v,shared_frames=len(ff),frames=ff) for (u,v),ff in sorted(pairs.items()) if len(ff)>=2]
def lloyd(x,seed):
    chosen=[random.Random(seed).randrange(len(x))]
    while len(chosen)<17:
        d=np.sum((x[:,None,:]-x[chosen][None,:,:])**2,axis=2).min(1);d[chosen]=-1;chosen.append(int(np.argmax(d)))
    centers=x[chosen].copy();previous=None
    for iteration in range(300):
        labels=np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1);new=centers.copy()
        for k in range(17):
            if any(labels==k):new[k]=np.mean(x[labels==k],axis=0)
        movement=max(np.linalg.norm(new-centers,axis=1));centers=new
        if previous is not None and np.array_equal(labels,previous) or movement<=1e-10:break
        previous=labels.copy()
    return np.sum((x[:,None,:]-centers[None,:,:])**2,axis=2).argmin(1).tolist(),chosen,iteration+1,centers

def embedding(edges,independent=False):
    result=cluster({'descriptors':edges});x=np.array(result['embedding'])
    if independent:
        words=result['words'];lookup={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
        for e in edges:u,v=lookup[e['a']],lookup[e['b']];adj[u,v]=adj[v,u]=1
        degree=adj.sum(1);ev,vectors=eigh(np.eye(len(words))-np.diag(degree**-.5)@adj@np.diag(degree**-.5),driver='evd');dim=min(len(words),sum(ev<=1e-10)+17);boundary=dim-1
        while dim<len(words) and abs(ev[dim]-ev[boundary])<=1e-10:dim+=1
        z=vectors[:,:dim];z/=np.linalg.norm(z,axis=1)[:,None];near(z@z.T,x@x.T)
    return result['words'],x

def run():
    original=read(P/'iteration193/graphs.json')['Aquinas'];ref=read(P/'iteration201/development-references.json')['Aquinas']['pos'];tags=read(P/'iteration231/design-freeze.json')['tags'];sentences=defaultdict(list);counts=defaultdict(Counter);frequency=Counter()
    for i,p in enumerate(original['positions']):
        if p is not None:sentences[tuple(p[:2])].append(i);counts[original['ids'][i]][ref[i]]+=1;frequency[original['ids'][i]]+=1
    profiles={w:[c[t]/sum(c.values()) for t in tags] for w,c in counts.items()};paths=[O/'real.json.gz']+[O/f'null-{s}.json.gz' for s in range(24000,24199)];results=read(O/'results.json');summary=read(O/'summary.json');graphchecks=lloyds=geometries=0
    for ti,path in enumerate(paths):
        data=json.loads(gzip.decompress(path.read_bytes()));ids=original['ids'].copy()
        if ti:
            rng=random.Random(23999+ti)
            for sentence,ix in sorted(sentences.items()):
                vv=[original['ids'][i] for i in ix];rng.shuffle(vv)
                for i,w in zip(ix,vv):ids[i]=w
        g=dict(ids=ids,positions=original['positions']);edges=rebuild(g,set());assert edges==data['initial_graph'];graphchecks+=1;words,x=embedding(edges,True);geometries+=1;assert words==data['words'] and data['clusterable']
        for j,r in enumerate(data['initial_runs']):
            assert r['seed']==23500+j;labels,initial,iterations,centers=lloyd(x,r['seed']);assert labels==r['labels'] and initial==r['initial_center_indices'] and iterations==r['iterations'];near(centers,r['centers']);lloyds+=1
        maps=[]
        for j,r in enumerate(data['deletions']):
            seed=23700+j;removed=sorted(random.Random(seed).sample(sorted(sentences),int(.1*len(sentences))));assert r['seed']==seed and r['removed']==[list(v) for v in removed];ee=rebuild(g,set(removed));assert ee==r['graph'];graphchecks+=1;p=r['partition'];ww=sorted({e[k] for e in ee for k in ['a','b']});assert ww==p['words']
            if len(ww)>=17:
                assert p['clusterable'];ww,z=embedding(ee,j==15);geometries+=int(j==15);labels,initial,iterations,_=lloyd(z,23500);assert labels==p['labels'] and initial==p['initial_center_indices'] and iterations==p['iterations'];maps.append(dict(zip(ww,labels)));lloyds+=1
            else:assert not p['clusterable'];maps.append({})
        groups=defaultdict(list)
        for i,w in enumerate(words):
            if all(w in m for m in maps):groups[tuple(r['labels'][i] for r in data['initial_runs'])+tuple(m[w] for m in maps)].append(i)
        expected=[dict(indices=ix,words=[words[i] for i in ix],size=len(ix),pairs=[list(p) for p in combinations(ix,2)]) for ix in sorted(groups.values(),key=lambda ix:[words[i] for i in ix])];assert expected==data['cores']
        if ti==0:assert expected==read(P/'iteration238/cores.json')['Aquinas']
        cc=[c for c in expected if c['size']>1];pure=[]
        for c in cc:
            puretags=[t for t in tags if all(len(counts[w])==1 and t in counts[w] for w in c['words'])]
            if puretags:pure.append(dict(words=c['words'],size=c['size'],reference_tag=puretags[0],tokens=sum(frequency[w] for w in c['words'])))
        r=results[ti];selected={w for c in cc for w in c['words']};assert r['trial']==path.name and r['clusterable']==data['clusterable'] and r['nodes']==len(words) and r['edges']==len(edges) and r['joint_cores']==len(cc) and r['core_sizes']==[c['size'] for c in cc] and r['covered_words']==len(selected) and r['covered_tokens']==sum(frequency[w] for w in selected) and r['pure_cores']==pure and r['largest_pure_core']==max((c['size'] for c in pure),default=0)
        for k,v in measure([profiles[w] for w in words],cc).items():
            if v is None:assert r['metrics'][k] is None
            else:near(v,r['metrics'][k])
    assert summary['real']==results[0] and summary['null_largest_pure_sizes']==[r['largest_pure_core'] for r in results[1:]];exceed=sum(r['largest_pure_core']>=results[0]['largest_pure_core'] for r in results[1:]);assert summary['exceedances']==exceed and summary['upper_tail']==(1+exceed)/200 and summary['zero_joint_output']==sum(not r['joint_cores'] for r in results[1:]) and summary['null_trials']==199
    for name in ['real.json.gz']+[f'null-{seed}.json.gz' for seed in range(24000,24019)]:assert (O/name).read_bytes()==(P/'iteration243'/'Aquinas'/name).read_bytes()
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration240/verification-manifest.json'),read(P/'iteration231/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    for p,h in read(O/'selection-freeze.json').items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',matched_graph_replays=graphchecks,initialization_and_deletion_lloyd_replays=lloyds,independent_geometry_samples=geometries,full_core_intersections=200,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
