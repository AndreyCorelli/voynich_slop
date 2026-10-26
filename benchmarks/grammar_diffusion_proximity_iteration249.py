"""Continuous spectral proximity before clustering, on frozen graph outputs."""
from pathlib import Path
from itertools import combinations
import gzip,json,hashlib
import numpy as np

P=Path('experiments/results/grammar-restoration');O=P/'iteration249';AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];TOL=1e-10

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def stats(v):return dict(count=len(v),minimum=float(min(v)),mean=float(np.mean(v)),median=float(np.median(v)),maximum=float(max(v))) if v else None

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_pair_proximity_iteration248.py')]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration238/cores.json','iteration246/verification-manifest.json','iteration248/verification-manifest.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},authors=AA,tie_absolute_tolerance=TOL,rank='1-(number of all unordered graph-node pairs strictly closer + half ties)/number of pairs; missing or ineligible unconditional zero',geometry='all eigenvectors weighted exp(-lambda/2), row-normalized, fixed time1; eligible graph>=17nodes'))
    for previous in ['iteration246','iteration248']:
        for p,h in read(P/previous/'verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];old=read(P/'iteration238/cores.json');records=[];geometry=[]
    for a in AA:
        pairs=[list(p) for c in old[a] for p in combinations(c['words'],2)]
        for seed,half in [(None,None)]+[(s,h) for s in range(24600,24619) for h in [0,1]]:
            edges=gg[a]['descriptors'] if seed is None else json.loads(gzip.decompress((P/'iteration246'/f'{a}-{seed}-{half}.json.gz').read_bytes()))['initial_graph'];words=sorted({e[k] for e in edges for k in ['a','b']});ix={w:i for i,w in enumerate(words)};eligible=len(words)>=17
            if eligible:
                adj=np.zeros((len(words),len(words)))
                for e in edges:i,j=ix[e['a']],ix[e['b']];adj[i,j]=adj[j,i]=1
                degree=adj.sum(1);lap=np.eye(len(words))-adj/np.sqrt(degree[:,None]*degree[None,:]);ev,vectors=np.linalg.eigh(lap);x=vectors*np.exp(-ev/2)[None,:];x/=np.linalg.norm(x,axis=1)[:,None];distance=np.maximum(0,((x[:,None,:]-x[None,:,:])**2).sum(2));pool=distance[np.triu_indices(len(words),1)];dim=len(words);zero=int(sum(abs(ev)<=1e-10))
            else:dim=zero=None;pool=[]
            geometry.append(dict(author=a,seed=seed,half=half,nodes=len(words),edges=len(edges),eligible=eligible,dimension=dim,zero_modes=zero,saturated=eligible and dim==len(words),node_pairs=len(pool),equal_distance_collapse=eligible and float(np.ptp(pool))<=TOL,distance_spread=float(np.ptp(pool)) if eligible else None))
            for pair in pairs:
                u,v=pair;present=u in ix and v in ix;available=present and eligible;d=float(distance[ix[u],ix[v]]) if available else None;less=int(np.sum(pool<d-TOL)) if available else None;equal=int(np.sum(abs(pool-d)<=TOL)) if available else None;rank=1-(less+.5*equal)/len(pool) if available else None
                records.append(dict(author=a,seed=seed,half=half,pair=pair,present=present,eligible=eligible,available=available,distance=d,strictly_closer=less,ties=equal,pool_size=len(pool),closeness=rank,tie_fraction=equal/len(pool) if available else None,unconditional_closeness=rank if available else 0.))
        print(a,'geometry and ranks reconstructed',flush=True)
    save(O/'graph-geometry.json',geometry);save(O/'pair-records.json',records);summary={}
    for a in AA:
        rr=[r for r in records if r['author']==a];full=[r for r in rr if r['seed'] is None];halves=[r for r in rr if r['seed'] is not None];lookup={tuple(r['pair']):r['closeness'] for r in full};gs=[g for g in geometry if g['author']==a and g['seed'] is not None];pairdetails=[]
        for pair,base in lookup.items():
            hh=[r for r in halves if tuple(r['pair'])==pair];byseed={s:[r for r in hh if r['seed']==s] for s in range(24600,24619)};pairdetails.append(dict(pair=list(pair),full_closeness=base,available_halves=sum(r['available'] for r in hh),conditional_half_closeness=stats([r['closeness'] for r in hh if r['available']]),unconditional_half_closeness=stats([r['unconditional_closeness'] for r in hh]),both_half_minimum_closeness=stats([min(r['unconditional_closeness'] for r in split) for split in byseed.values()])))
        summary[a]=dict(full_closeness=stats([r['closeness'] for r in full if r['available']]),half_pair_cases=len(halves),present_halves=sum(r['present'] for r in halves),available_halves=sum(r['available'] for r in halves),conditional_half_closeness=stats([r['closeness'] for r in halves if r['available']]),unconditional_half_closeness=stats([r['unconditional_closeness'] for r in halves]),conditional_change_from_full=stats([r['closeness']-lookup[tuple(r['pair'])] for r in halves if r['available']]),conditional_tie_fraction=stats([r['tie_fraction'] for r in halves if r['available']]),eligible_half_graphs=sum(g['eligible'] for g in gs),full_rank_half_graphs=sum(g['saturated'] for g in gs),collapsed_half_graphs=sum(g['equal_distance_collapse'] for g in gs),pairs=pairdetails)
    save(O/'summary.json',summary)
    baseline=read(P/'iteration248/pair-records.json');assert len(baseline)==len(records);paired=[]
    for old,new in zip(baseline,records):
        for key in ['author','seed','half','pair','present','eligible','available']:assert old[key]==new[key]
        paired.append(dict(author=new['author'],seed=new['seed'],half=new['half'],pair=new['pair'],available=new['available'],closeness_change=new['closeness']-old['closeness'] if new['available'] else None,unconditional_change=new['unconditional_closeness']-old['unconditional_closeness']))
    save(O/'paired-changes.json',paired);comparison={}
    for a in AA:
        rr=[r for r in paired if r['author']==a and r['seed'] is not None];comparison[a]=dict(conditional_change=stats([r['closeness_change'] for r in rr if r['available']]),unconditional_change=stats([r['unconditional_change'] for r in rr]),improved=sum(r['available'] and r['closeness_change']>TOL for r in rr),tied=sum(r['available'] and abs(r['closeness_change'])<=TOL for r in rr),worse=sum(r['available'] and r['closeness_change'] < -TOL for r in rr))
    save(O/'comparison.json',comparison)
    for a,s in summary.items():print(a,{k:v for k,v in s.items() if k!='pairs'},flush=True)
if __name__=='__main__':run()
