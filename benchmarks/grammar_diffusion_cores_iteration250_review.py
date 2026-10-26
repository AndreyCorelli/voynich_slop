"""Independent graph/Lloyd/core replay plus matrix-exponential geometry audit."""
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
import gzip,json,random,hashlib
import numpy as np
from scipy.linalg import expm
from benchmarks.grammar_full_core_null_iteration244_review import rebuild,lloyd,near
from benchmarks.grammar_disjoint_cores_iteration245_review import expectedcores,metrics,compare
from benchmarks.grammar_diffusion_cores_iteration250 import embedding
P=Path('experiments/results/grammar-restoration');O=P/'iteration250';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def geometry(edges,independent):
    words,x=embedding(edges)
    if independent:
        ix={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
        for e in edges:i,j=ix[e['a']],ix[e['b']];adj[i,j]=adj[j,i]=1
        degree=adj.sum(0);lap=np.eye(len(words))-adj/np.sqrt(np.outer(degree,degree));k=expm(-lap);norm=np.sqrt(np.diag(k));near(x@x.T,k/norm[:,None]/norm[None,:])
    return words,x

def audit(g,d):
    edges=rebuild(g,set());assert edges==d['initial_graph'];words=sorted({e[k] for e in edges for k in ['a','b']});assert words==d['words'] and d['clusterable']==(len(words)>=17);graphs=1;runs=geometries=0
    if not d['clusterable']:assert d['initial_runs']==d['deletions']==d['cores']==[];return graphs,runs,geometries
    _,x=geometry(edges,True);geometries+=1;assert len(d['initial_runs'])==len(d['deletions'])==31;maps=[];sentences=sorted({tuple(p[:2]) for p in g['positions'] if p is not None})
    for j,r in enumerate(d['initial_runs']):
        assert r['seed']==23500+j;y,initial,n,centers=lloyd(x,23500+j);assert y==r['labels'] and initial==r['initial_center_indices'] and n==r['iterations'];near(centers,r['centers']);runs+=1
    for j,r in enumerate(d['deletions']):
        removed=sorted(random.Random(23700+j).sample(sentences,int(.1*len(sentences))));assert r['seed']==23700+j and r['removed']==[list(v) for v in removed];ee=rebuild(g,set(removed));graphs+=1;assert ee==r['graph'];p=r['partition'];ww=sorted({e[k] for e in ee for k in ['a','b']});assert ww==p['words'] and p['clusterable']==(len(ww)>=17)
        if p['clusterable']:
            _,z=geometry(ee,j==15);geometries+=int(j==15);y,initial,n,_=lloyd(z,23500);assert y==p['labels'] and initial==p['initial_center_indices'] and n==p['iterations'];maps.append(dict(zip(ww,y)));runs+=1
        else:assert p['labels'] is None;maps.append({})
    groups=defaultdict(list)
    for i,w in enumerate(words):
        if all(w in m for m in maps):groups[tuple(r['labels'][i] for r in d['initial_runs'])+tuple(m[w] for m in maps)].append(w)
    assert expectedcores(words,groups.values())==d['cores'];return graphs,runs,geometries

def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];splits=read(P/'iteration246/splits.json');cross=read(O/'cross-half-cores.json');results=read(O/'results.json');full=read(O/'full-results.json');refs=read(P/'iteration201/development-references.json');tags=read(P/'iteration231/design-freeze.json')['tags'];old=read(P/'iteration238/cores.json');previous=read(P/'iteration246/results.json');graphs=runs=geometries=0
    for a in AA:
        g=gg[a];ref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'] if a=='Dante' else refs[a]['pos'];globalcounts=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p is not None:globalcounts[g['ids'][i]][ref[i]]+=1
        d=json.loads(gzip.decompress((O/f'{a}-full.json.gz').read_bytes()));ng,nr,nm=audit(g,d);graphs+=ng;runs+=nr;geometries+=nm;compare(full[a],dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),global_profiles=metrics(d,globalcounts,tags)))
        order=list(dict.fromkeys(tuple(p[:2]) for p in g['positions'] if p is not None))
        for seed in range(24600,24619):
            chosen=set(random.Random(seed).sample(order,len(order)//2));keys=[[list(k) for k in order if k in chosen],[list(k) for k in order if k not in chosen]];assert keys==splits[f'{a}-{seed}'];dd=[];local=[defaultdict(Counter),defaultdict(Counter)]
            for half in [0,1]:
                kept=set(map(tuple,keys[half]));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];d=json.loads(gzip.decompress((O/f'{a}-{seed}-{half}.json.gz').read_bytes()));dd.append(d);ng,nr,nm=audit(dict(ids=g['ids'],positions=positions),d);graphs+=ng;runs+=nr;geometries+=nm
                for i,p in enumerate(positions):
                    if p is not None:local[half][g['ids'][i]][ref[i]]+=1
                prior=previous[f'{a}-{seed}']['halves'][half];assert prior['nodes']==len(d['words']) and prior['edges']==len(d['initial_graph']) and prior['clusterable']==d['clusterable']
            maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in dd];common=sorted(set(maps[0])&set(maps[1]));groups=defaultdict(list)
            for w in common:groups[maps[0][w],maps[1][w]].append(w)
            shared=dict(words=common,cores=expectedcores(common,groups.values()));assert shared==cross[f'{a}-{seed}'];rr=results[f'{a}-{seed}']
            for half,d in enumerate(dd):compare(rr['halves'][half],dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),global_profiles=metrics(d,globalcounts,tags),local_profiles=metrics(d,local[half],tags)))
            compare(rr['shared'],metrics(shared,globalcounts,tags));pairs=[(u,v) for c in old[a] for u,v in combinations(c['words'],2)];present=[(u,v) for u,v in pairs if all(u in m and v in m for m in maps)];retained=[(u,v) for u,v in present if all(m[u]==m[v] for m in maps)];assert rr['original_pairs']==len(pairs) and rr['original_pairs_present_both']==len(present) and rr['original_pairs_retained_both']==len(retained) and rr['retained_pair_words']==[list(p) for p in retained] and rr['unconditional_retention']==(len(retained)/len(pairs) if pairs else None)
        print(a,'independent replay passed',flush=True)
    hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(O/'selection-freeze.json'),read(P/'iteration246/verification-manifest.json'),read(P/'iteration249/verification-manifest.json'),read(P/'iteration245/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',graph_replays=graphs,lloyd_replays=runs,matrix_exponential_checks=geometries,full_graphs=5,half_graphs=190,cross_intersections=95,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
