"""Full strict-core extraction: fixed diffusion representation is the only change."""
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
import json,gzip,hashlib,random
import numpy as np
from benchmarks.grammar_pos_text_robustness_iteration237 import rebuild
from benchmarks.grammar_pos_stability_iteration235 import lloyd
from benchmarks.grammar_disjoint_cores_iteration245 import cross,evaluate
P=Path('experiments/results/grammar-restoration');O=P/'iteration250';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def compress(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':'),allow_nan=False).encode(),mtime=0))
def embedding(edges):
    words=sorted({e[k] for e in edges for k in ['a','b']});ix={w:i for i,w in enumerate(words)};adj=np.zeros((len(words),len(words)))
    for e in edges:i,j=ix[e['a']],ix[e['b']];adj[i,j]=adj[j,i]=1
    degree=adj.sum(1);lap=np.eye(len(words))-adj/np.sqrt(degree[:,None]*degree[None,:]);ev,v=np.linalg.eigh(lap);x=v*np.exp(-ev/2)[None,:];x/=np.linalg.norm(x,axis=1)[:,None];return words,x

def partition(edges):
    words=sorted({e[k] for e in edges for k in ['a','b']})
    if len(words)<17:return dict(clusterable=False,words=words,labels=None)
    words,x=embedding(edges);r=lloyd(x,23500);return dict(clusterable=True,words=words,labels=r['labels'],initial_center_indices=r['initial_center_indices'],iterations=r['iterations'])
def pipeline(g):
    edges=rebuild(g,set());words=sorted({e[k] for e in edges for k in ['a','b']})
    if len(words)<17:return dict(initial_graph=edges,words=words,clusterable=False,initial_runs=[],deletions=[],cores=[])
    words,x=embedding(edges);runs=[lloyd(x,s) for s in range(23500,23531)];sentences=sorted({tuple(p[:2]) for p in g['positions'] if p is not None});deletions=[]
    for seed in range(23700,23731):
        removed=sorted(random.Random(seed).sample(sentences,int(.1*len(sentences))));ee=rebuild(g,set(removed));deletions.append(dict(seed=seed,removed=[list(v) for v in removed],graph=ee,partition=partition(ee)))
    maps=[dict(zip(r['partition']['words'],r['partition']['labels'])) if r['partition']['clusterable'] else {} for r in deletions];groups=defaultdict(list)
    for i,w in enumerate(words):
        if all(w in m for m in maps):groups[tuple(r['labels'][i] for r in runs)+tuple(m[w] for m in maps)].append(i)
    cores=[dict(indices=ix,words=[words[i] for i in ix],size=len(ix),pairs=[list(p) for p in combinations(ix,2)]) for ix in sorted(groups.values(),key=lambda ix:[words[i] for i in ix])];return dict(initial_graph=edges,words=words,clusterable=True,initial_runs=runs,deletions=deletions,cores=cores)

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_pos_text_robustness_iteration237.py','grammar_pos_stability_iteration235.py','grammar_disjoint_cores_iteration245.py','grammar_pos_cores_iteration236.py']]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration238/cores.json','iteration246/splits.json','iteration246/results.json','iteration246/verification-manifest.json','iteration249/verification-manifest.json','iteration201/development-references.json','iteration200/pos-references.json','iteration231/design-freeze.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},authors=AA,representation='all eigenvectors weighted exp(-lambda/2), row-normalize; fixed time1',init_seeds=list(range(23500,23531)),deletion_seeds=list(range(23700,23731))))
    for previous in ['iteration246','iteration249']:
        for p,h in read(P/previous/'verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];splits=read(P/'iteration246/splits.json');files=[];crosses={}
    for a in AA:
        g=gg[a];full=pipeline(g);p=O/f'{a}-full.json.gz';compress(p,full);files.append(p);print(a,'full frozen',flush=True)
        for seed in range(24600,24619):
            halves=[]
            for h in [0,1]:
                kept=set(map(tuple,splits[f'{a}-{seed}'][h]));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];d=pipeline(dict(ids=g['ids'],positions=positions));old=json.loads(gzip.decompress((P/'iteration246'/f'{a}-{seed}-{h}.json.gz').read_bytes()));assert d['initial_graph']==old['initial_graph'];assert [r['graph'] for r in d['deletions']]==[r['graph'] for r in old['deletions']];p=O/f'{a}-{seed}-{h}.json.gz';compress(p,d);files.append(p);halves.append(d)
            crosses[f'{a}-{seed}']=cross(*halves)
        print(a,'all halves frozen',flush=True)
    save(O/'cross-half-cores.json',crosses);files.append(O/'cross-half-cores.json');save(O/'selection-freeze.json',{str(p):sha(p) for p in files})
    refs=read(P/'iteration201/development-references.json');dref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'];original=read(P/'iteration238/cores.json');fullresults={};results={}
    for a in AA:
        g=gg[a];ref=dref if a=='Dante' else refs[a]['pos'];counts=defaultdict(Counter)
        for i,p in enumerate(g['positions']):
            if p is not None:counts[g['ids'][i]][ref[i]]+=1
        d=json.loads(gzip.decompress((O/f'{a}-full.json.gz').read_bytes()));fullresults[a]=dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),global_profiles=evaluate(d,counts))
        pairs=[(u,v) for c in original[a] for u,v in combinations(c['words'],2)]
        for seed in range(24600,24619):
            dd=[json.loads(gzip.decompress((O/f'{a}-{seed}-{h}.json.gz').read_bytes())) for h in [0,1]];local=[defaultdict(Counter),defaultdict(Counter)];first=set(map(tuple,splits[f'{a}-{seed}'][0]))
            for i,p in enumerate(g['positions']):
                if p is not None:local[int(tuple(p[:2]) not in first)][g['ids'][i]][ref[i]]+=1
            maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in dd];present=[(u,v) for u,v in pairs if all(u in m and v in m for m in maps)];retained=[(u,v) for u,v in present if all(m[u]==m[v] for m in maps)];results[f'{a}-{seed}']=dict(halves=[dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),global_profiles=evaluate(d,counts),local_profiles=evaluate(d,local[h])) for h,d in enumerate(dd)],shared=evaluate(crosses[f'{a}-{seed}'],counts),original_pairs=len(pairs),original_pairs_present_both=len(present),original_pairs_retained_both=len(retained),retained_pair_words=[list(p) for p in retained],unconditional_retention=len(retained)/len(pairs) if pairs else None)
    save(O/'full-results.json',fullresults);save(O/'results.json',results)
    for a in AA:
        rr=[v for k,v in results.items() if k.startswith(a+'-')];print(a,'full cores',fullresults[a]['global_profiles']['core_sizes'],'shared splits',sum(bool(r['shared']['core_sizes']) for r in rr),'original retained',sum(r['original_pairs_retained_both'] for r in rr),flush=True)
if __name__=='__main__':run()
