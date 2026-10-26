"""Continuous spectral proximity before clustering, on frozen graph outputs."""
from pathlib import Path
from itertools import combinations
import gzip,json,hashlib
import numpy as np
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
P=Path('experiments/results/grammar-restoration');O=P/'iteration248';AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];TOL=1e-10

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def stats(v):return dict(count=len(v),minimum=float(min(v)),mean=float(np.mean(v)),median=float(np.median(v)),maximum=float(max(v))) if v else None

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_pos_spectral_iteration234_retry.py')]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration238/cores.json','iteration246/verification-manifest.json','iteration247/verification-manifest.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},authors=AA,tie_absolute_tolerance=TOL,rank='1-(number of all unordered graph-node pairs strictly closer + half ties)/number of pairs; missing or ineligible unconditional zero',geometry='same pre-kmeans corrected234 row-normalized embedding; eligible graph>=17nodes'))
    for previous in ['iteration246','iteration247']:
        for p,h in read(P/previous/'verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];old=read(P/'iteration238/cores.json');records=[];geometry=[]
    for a in AA:
        pairs=[list(p) for c in old[a] for p in combinations(c['words'],2)]
        for seed,half in [(None,None)]+[(s,h) for s in range(24600,24619) for h in [0,1]]:
            edges=gg[a]['descriptors'] if seed is None else json.loads(gzip.decompress((P/'iteration246'/f'{a}-{seed}-{half}.json.gz').read_bytes()))['initial_graph'];words=sorted({e[k] for e in edges for k in ['a','b']});ix={w:i for i,w in enumerate(words)};eligible=len(words)>=17
            if eligible:
                c=cluster({'descriptors':edges});assert c['words']==words;x=np.array(c['embedding']);distance=np.maximum(0,((x[:,None,:]-x[None,:,:])**2).sum(2));pool=distance[np.triu_indices(len(words),1)];dim=c['embedding_dimension'];zero=c['zero_eigenvalues']
            else:dim=zero=None;pool=[]
            geometry.append(dict(author=a,seed=seed,half=half,nodes=len(words),edges=len(edges),eligible=eligible,dimension=dim,zero_modes=zero,saturated=eligible and dim==len(words),node_pairs=len(pool)))
            for pair in pairs:
                u,v=pair;present=u in ix and v in ix;available=present and eligible;d=float(distance[ix[u],ix[v]]) if available else None;less=int(np.sum(pool<d-TOL)) if available else None;equal=int(np.sum(abs(pool-d)<=TOL)) if available else None;rank=1-(less+.5*equal)/len(pool) if available else None
                records.append(dict(author=a,seed=seed,half=half,pair=pair,present=present,eligible=eligible,available=available,distance=d,strictly_closer=less,ties=equal,pool_size=len(pool),closeness=rank,tie_fraction=equal/len(pool) if available else None,unconditional_closeness=rank if available else 0.))
        print(a,'geometry and ranks reconstructed',flush=True)
    save(O/'graph-geometry.json',geometry);save(O/'pair-records.json',records);summary={}
    for a in AA:
        rr=[r for r in records if r['author']==a];full=[r for r in rr if r['seed'] is None];halves=[r for r in rr if r['seed'] is not None];lookup={tuple(r['pair']):r['closeness'] for r in full};gs=[g for g in geometry if g['author']==a and g['seed'] is not None];pairdetails=[]
        for pair,base in lookup.items():
            hh=[r for r in halves if tuple(r['pair'])==pair];byseed={s:[r for r in hh if r['seed']==s] for s in range(24600,24619)};pairdetails.append(dict(pair=list(pair),full_closeness=base,available_halves=sum(r['available'] for r in hh),conditional_half_closeness=stats([r['closeness'] for r in hh if r['available']]),unconditional_half_closeness=stats([r['unconditional_closeness'] for r in hh]),both_half_minimum_closeness=stats([min(r['unconditional_closeness'] for r in split) for split in byseed.values()])))
        summary[a]=dict(full_closeness=stats([r['closeness'] for r in full if r['available']]),half_pair_cases=len(halves),present_halves=sum(r['present'] for r in halves),available_halves=sum(r['available'] for r in halves),conditional_half_closeness=stats([r['closeness'] for r in halves if r['available']]),unconditional_half_closeness=stats([r['unconditional_closeness'] for r in halves]),conditional_change_from_full=stats([r['closeness']-lookup[tuple(r['pair'])] for r in halves if r['available']]),conditional_tie_fraction=stats([r['tie_fraction'] for r in halves if r['available']]),eligible_half_graphs=sum(g['eligible'] for g in gs),saturated_half_graphs=sum(g['saturated'] for g in gs),pairs=pairdetails)
    save(O/'summary.json',summary)
    for a,s in summary.items():print(a,{k:v for k,v in s.items() if k!='pairs'},flush=True)
if __name__=='__main__':run()
