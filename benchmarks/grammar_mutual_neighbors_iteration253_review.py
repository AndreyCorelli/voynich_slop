"""Independent matrix-exponential nearest-neighbor and relation audit."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import gzip,json,hashlib,math
import numpy as np
from scipy.linalg import expm
from benchmarks.grammar_diffusion_controls_iteration251_review_retry import compare
P=Path('experiments/results/grammar-restoration');O=P/'iteration253';TOL=1e-10;AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];SOLVES=0

def read(p):return json.loads(p.read_text())
def neighbors(edges):
    global SOLVES
    words=sorted({e[k] for e in edges for k in ['a','b']});n=len(words)
    if n<17:return dict(nodes=n,eligible=False,pairs=[])
    ix={w:i for i,w in enumerate(words)};adj=np.zeros((n,n))
    for e in edges:i,j=ix[e['a']],ix[e['b']];adj[i,j]=adj[j,i]=1
    degree=adj.sum(0);kernel=expm(-(np.eye(n)-adj/np.sqrt(np.outer(degree,degree))));norm=np.sqrt(np.diag(kernel));gram=kernel/norm[:,None]/norm[None,:];distance=np.maximum(0,2-2*gram);direct=[]
    for i in range(n):
        minimum=min(distance[i,j] for j in range(n) if j!=i);direct.append({j for j in range(n) if j!=i and distance[i,j]<=minimum+TOL})
    pairs=[[words[i],words[j]] for i,j in combinations(range(n),2) if j in direct[i] and i in direct[j]];SOLVES+=1;return dict(nodes=n,eligible=True,pairs=pairs)
def metric(pairs,counts,tags):
    words={w for p in pairs for w in p};compat=[];purity=[];pure=[]
    for pair in pairs:
        profiles=[{t:counts[w][t]/sum(counts[w].values()) for t in tags} for w in pair];compat.append(sum(profiles[0][t]*profiles[1][t] for t in tags));purity.append(max((profiles[0][t]+profiles[1][t])/2 for t in tags))
        if all(len(counts[w])==1 for w in pair):
            tt={next(iter(counts[w])) for w in pair}
            if len(tt)==1:pure.append(dict(words=pair,reference_tag=next(iter(tt))))
    return dict(pairs=len(pairs),mean_compatibility=sum(compat)/len(compat) if compat else None,mean_oracle_pair_purity=sum(purity)/len(purity) if purity else None,pure_pairs=pure,covered_words=len(words),covered_tokens=sum(sum(counts[w].values()) for w in words),text_tokens=sum(sum(c.values()) for c in counts.values()))
def run():
    sources=read(O/'source-cases.json');cross=read(O/'cross-half-pairs.json');results=read(O/'results.json');fixed=read(O/'fixed-group-retention.json');groups=read(P/'iteration252/frozen-groups.json');cases={};graphs=0
    for key,source in sources.items():
        path=Path(source['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256'];d=json.loads(gzip.decompress(path.read_bytes()));c=json.loads(gzip.decompress((O/f'{key}.json.gz').read_bytes()));initial=neighbors(d['initial_graph']);assert initial==c['initial'];graphs+=1;deletions=[];sets=[set(map(tuple,initial['pairs']))]
        for r in d['deletions']:
            rr=dict(seed=r['seed'],**neighbors(r['graph']));deletions.append(rr);sets.append(set(map(tuple,rr['pairs'])));graphs+=1
        expected=sorted(set.intersection(*sets)) if len(sets)==32 else [];assert deletions==c['deletions'] and [list(p) for p in expected]==c['stable_pairs'];cases[key]=c
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];refs=read(P/'iteration201/development-references.json');tags=read(P/'iteration231/design-freeze.json')['tags'];expectedfixed=[]
    for a in AA:
        g=gg[a];ref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'] if a=='Dante' else refs[a]['pos'];counts=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p is not None:counts[g['ids'][i]][ref[i]]+=1
        halves={key:metric(c['stable_pairs'],counts,tags) for key,c in cases.items() if key.startswith(a+'-') and not key.endswith('full')};shared={}
        for seed in list(range(24600,24619))+(list(range(25200,25219)) if a=='Aquinas' else []):
            pp=sorted(set(map(tuple,cases[f'{a}-{seed}-0']['stable_pairs']))&set(map(tuple,cases[f'{a}-{seed}-1']['stable_pairs'])));pp=[list(p) for p in pp];assert pp==cross[f'{a}-{seed}'];shared[f'{a}-{seed}']=metric(pp,counts,tags)
        compare(dict(full=metric(cases[f'{a}-full']['stable_pairs'],counts,tags),halves=halves,shared=shared),results[a])
        if a=='Aquinas':
            for c in groups:
                pairs=set(combinations(c['words'],2))
                for lo in [24600,25200]:
                    ss=[set(map(tuple,cross[f'{a}-{seed}'])) for seed in range(lo,lo+19)];expectedfixed.append(dict(group_id=c['group_id'],split_family=lo,fixed_pairs=len(pairs),pair_trials=19*len(pairs),retained_pair_trials=sum(len(pairs&s) for s in ss),all_pairs_recovered_splits=sum(pairs<=s for s in ss)))
        print(a,'independent metrics passed',flush=True)
    compare(expectedfixed,fixed);assert len(cases)==233 and len(cross)==114;hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(O/'selection-freeze.json'),read(P/'iteration250/verification-manifest.json'),read(P/'iteration252/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',cases=len(cases),cross_intersections=len(cross),graph_relation_replays=graphs,matrix_exponentials=SOLVES,author_metrics=5,fixed_group_summaries=4,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
