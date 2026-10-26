"""Stable mutual diffusion-neighbor pairs, without global partitioning."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,gzip,hashlib
import numpy as np
from benchmarks.grammar_diffusion_cores_iteration250 import embedding,compress
P=Path('experiments/results/grammar-restoration');O=P/'iteration253';AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];TOL=1e-10

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def neighbors(edges):
    words=sorted({e[k] for e in edges for k in ['a','b']})
    if len(words)<17:return dict(nodes=len(words),eligible=False,pairs=[])
    _,x=embedding(edges);distance=np.maximum(0,((x[:,None,:]-x[None,:,:])**2).sum(2));np.fill_diagonal(distance,np.inf);close=distance<=distance.min(1)[:,None]+TOL;mutual=close&close.T;return dict(nodes=len(words),eligible=True,pairs=[[words[i],words[j]] for i,j in combinations(range(len(words)),2) if mutual[i,j]])
def case(d):
    initial=neighbors(d['initial_graph']);deletions=[dict(seed=r['seed'],**neighbors(r['graph'])) for r in d['deletions']];stable=set(map(tuple,initial['pairs']))
    if len(deletions)!=31:stable=set()
    for r in deletions:stable&=set(map(tuple,r['pairs']))
    return dict(initial=initial,deletions=deletions,stable_pairs=[list(p) for p in sorted(stable)])
def evaluate(pairs,counts,tags):
    profiles={w:np.array([c[t]/sum(c.values()) for t in tags]) for w,c in counts.items()};compat=[];purity=[];pure=[];words={w for pair in pairs for w in pair}
    for pair in pairs:
        u,v=pair;compat.append(float(profiles[u]@profiles[v]));purity.append(float((profiles[u]+profiles[v]).max()/2));tt=[t for t in tags if counts[u][t]==sum(counts[u].values()) and counts[v][t]==sum(counts[v].values())]
        if tt:pure.append(dict(words=pair,reference_tag=tt[0]))
    return dict(pairs=len(pairs),mean_compatibility=float(np.mean(compat)) if compat else None,mean_oracle_pair_purity=float(np.mean(purity)) if purity else None,pure_pairs=pure,covered_words=len(words),covered_tokens=sum(sum(counts[w].values()) for w in words),text_tokens=sum(sum(c.values()) for c in counts.values()))

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_diffusion_cores_iteration250.py')]+[P/n for n in ['iteration250/verification-manifest.json','iteration252/verification-manifest.json','iteration252/frozen-groups.json','iteration193/graphs.json','iteration198/graphs.json','iteration201/development-references.json','iteration200/pos-references.json','iteration231/design-freeze.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},method='mutual nearest in initial and31deletiongraphs; allnearestties, no transitive closure',tolerance=TOL,eligibility=17))
    for previous in ['iteration250','iteration252']:
        for p,h in read(P/previous/'verification-manifest.json').items():assert sha(Path(p))==h
    cases={};files=[];source={};cross={}
    for a in AA:
        specs=[(f'{a}-full',P/'iteration250'/f'{a}-full.json.gz')]+[(f'{a}-{s}-{h}',P/'iteration250'/f'{a}-{s}-{h}.json.gz') for s in range(24600,24619) for h in [0,1]]
        if a=='Aquinas':specs.extend((f'{a}-{s}-{h}',P/'iteration252'/f'{s}-{h}.json.gz') for s in range(25200,25219) for h in [0,1])
        for key,path in specs:
            d=json.loads(gzip.decompress(path.read_bytes()));c=case(d);cases[key]=c;source[key]=dict(path=str(path),sha256=sha(path));out=O/f'{key}.json.gz';compress(out,c);files.append(out)
        print(a,'all anonymous cases frozen',flush=True)
        seeds=list(range(24600,24619))+(list(range(25200,25219)) if a=='Aquinas' else [])
        for s in seeds:cross[f'{a}-{s}']=[list(p) for p in sorted(set(map(tuple,cases[f'{a}-{s}-0']['stable_pairs']))&set(map(tuple,cases[f'{a}-{s}-1']['stable_pairs'])))]
    save(O/'source-cases.json',source);save(O/'cross-half-pairs.json',cross);files.extend([O/'source-cases.json',O/'cross-half-pairs.json']);save(O/'selection-freeze.json',{str(p):sha(p) for p in files})
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];refs=read(P/'iteration201/development-references.json');tags=read(P/'iteration231/design-freeze.json')['tags'];results={};groups=read(P/'iteration252/frozen-groups.json');fixed=[]
    for a in AA:
        g=gg[a];ref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'] if a=='Dante' else refs[a]['pos'];counts=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p is not None:counts[g['ids'][i]][ref[i]]+=1
        results[a]=dict(full=evaluate(cases[f'{a}-full']['stable_pairs'],counts,tags),halves={key:evaluate(c['stable_pairs'],counts,tags) for key,c in cases.items() if key.startswith(a+'-') and not key.endswith('full')},shared={key:evaluate(pp,counts,tags) for key,pp in cross.items() if key.startswith(a+'-')})
        if a=='Aquinas':
            for c in groups:
                pairs=set(combinations(c['words'],2))
                for lo in [24600,25200]:
                    rr=[set(map(tuple,cross[f'{a}-{s}'])) for s in range(lo,lo+19)];fixed.append(dict(group_id=c['group_id'],split_family=lo,fixed_pairs=len(pairs),pair_trials=19*len(pairs),retained_pair_trials=sum(len(pairs&r) for r in rr),all_pairs_recovered_splits=sum(pairs<=r for r in rr)))
    save(O/'results.json',results);save(O/'fixed-group-retention.json',fixed)
    for a,r in results.items():
        for lo in ([24600,25200] if a=='Aquinas' else [24600]):
            rr=[r['shared'][f'{a}-{s}'] for s in range(lo,lo+19)];print(a,lo,'shared nonempty',sum(v['pairs']>0 for v in rr),'pair trials',sum(v['pairs'] for v in rr),'fully pure',sum(len(v['pure_pairs']) for v in rr),flush=True)
    print('fixed',fixed,flush=True)
if __name__=='__main__':run()
