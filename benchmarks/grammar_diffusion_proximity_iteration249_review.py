"""Independent SciPy evd distances, explicit pair ranks and summaries."""
from pathlib import Path
from itertools import combinations
import json,gzip,hashlib,statistics
import numpy as np
from scipy.linalg import expm
P=Path('experiments/results/grammar-restoration');O=P/'iteration249';AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];TOL=1e-10

def read(p):return json.loads(p.read_text())
def near(a,b):assert np.allclose(a,b,atol=1e-8,rtol=1e-8)
def stats(v):return dict(count=len(v),minimum=min(v),mean=statistics.mean(v),median=statistics.median(v),maximum=max(v)) if v else None

def compare(a,b):
    if isinstance(a,dict):
        assert a.keys()==b.keys()
        for k in a:compare(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(a,float):near(a,b)
    else:assert a==b

def run():
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];old=read(P/'iteration238/cores.json');records=read(O/'pair-records.json');geometries=read(O/'graph-geometry.json');summary=read(O/'summary.json');lookup={(r['author'],r['seed'],r['half'],tuple(r['pair'])):r for r in records};glookup={(g['author'],g['seed'],g['half']):g for g in geometries};assert len(lookup)==len(records) and len(glookup)==len(geometries);checked=solves=saturated=0
    for a in AA:
        pairs=list(p for c in old[a] for p in combinations(c['words'],2))
        for seed,half in [(None,None)]+[(s,h) for s in range(24600,24619) for h in range(2)]:
            edges=gg[a]['descriptors'] if seed is None else json.loads(gzip.decompress((P/'iteration246'/f'{a}-{seed}-{half}.json.gz').read_bytes()))['initial_graph'];words=sorted({e[k] for e in edges for k in ['a','b']});index={w:i for i,w in enumerate(words)};eligible=len(words)>=17;pool=[];dim=zero=None
            if eligible:
                n=len(words);adj=np.zeros((n,n))
                for e in edges:u,v=index[e['a']],index[e['b']];adj[u,v]=adj[v,u]=1
                degree=np.sum(adj,axis=0);lap=np.eye(n)-adj/np.sqrt(np.outer(degree,degree));ev=np.linalg.eigvalsh(lap);zero=int(sum(abs(ev)<=1e-10));dim=n;kernel=expm(-lap);norm=np.sqrt(np.diag(kernel));gram=kernel/norm[:,None]/norm[None,:];near(gram,gram.T);near(np.diag(gram),np.ones(n));distance=np.maximum(0,2-2*gram);pool=[float(distance[i,j]) for i,j in combinations(range(n),2)];solves+=1
                if max(pool)-min(pool)<=TOL:saturated+=1
            expected=dict(author=a,seed=seed,half=half,nodes=len(words),edges=len(edges),eligible=eligible,dimension=dim,zero_modes=zero,saturated=eligible and dim==len(words),node_pairs=len(pool),equal_distance_collapse=eligible and max(pool)-min(pool)<=TOL,distance_spread=max(pool)-min(pool) if eligible else None);compare(expected,glookup[a,seed,half])
            for pair in pairs:
                u,v=pair;present=u in index and v in index;available=eligible and present;d=float(distance[index[u],index[v]]) if available else None;less=sum(v<d-TOL for v in pool) if available else None;equal=sum(abs(v-d)<=TOL for v in pool) if available else None;score=1-(less+equal/2)/len(pool) if available else None;expected=dict(author=a,seed=seed,half=half,pair=list(pair),present=present,eligible=eligible,available=available,distance=d,strictly_closer=less,ties=equal,pool_size=len(pool),closeness=score,tie_fraction=equal/len(pool) if available else None,unconditional_closeness=score if available else 0.);compare(expected,lookup[a,seed,half,pair]);checked+=1
        rr=[r for r in records if r['author']==a];full=[r for r in rr if r['seed'] is None];hh=[r for r in rr if r['seed'] is not None];base={tuple(r['pair']):r['closeness'] for r in full};gs=[g for g in geometries if g['author']==a and g['seed'] is not None];details=[]
        for pair,score in base.items():
            pp=[r for r in hh if tuple(r['pair'])==pair];details.append(dict(pair=list(pair),full_closeness=score,available_halves=sum(r['available'] for r in pp),conditional_half_closeness=stats([r['closeness'] for r in pp if r['available']]),unconditional_half_closeness=stats([r['unconditional_closeness'] for r in pp]),both_half_minimum_closeness=stats([min(r['unconditional_closeness'] for r in pp if r['seed']==s) for s in range(24600,24619)])))
        expected=dict(full_closeness=stats([r['closeness'] for r in full if r['available']]),half_pair_cases=len(hh),present_halves=sum(r['present'] for r in hh),available_halves=sum(r['available'] for r in hh),conditional_half_closeness=stats([r['closeness'] for r in hh if r['available']]),unconditional_half_closeness=stats([r['unconditional_closeness'] for r in hh]),conditional_change_from_full=stats([r['closeness']-base[tuple(r['pair'])] for r in hh if r['available']]),conditional_tie_fraction=stats([r['tie_fraction'] for r in hh if r['available']]),eligible_half_graphs=sum(g['eligible'] for g in gs),full_rank_half_graphs=sum(g['saturated'] for g in gs),collapsed_half_graphs=sum(g['equal_distance_collapse'] for g in gs),pairs=details);compare(expected,summary[a]);print(a,'passed',flush=True)
    old=read(P/'iteration248/pair-records.json');paired=read(O/'paired-changes.json');assert len(old)==len(records)==len(paired);comparison={}
    for before,after,actual in zip(old,records,paired):
        for k in ['author','seed','half','pair','present','eligible','available']:assert before[k]==after[k]
        expected=dict(author=after['author'],seed=after['seed'],half=after['half'],pair=after['pair'],available=after['available'],closeness_change=after['closeness']-before['closeness'] if after['available'] else None,unconditional_change=after['unconditional_closeness']-before['unconditional_closeness']);compare(expected,actual)
    for a in AA:
        rr=[r for r in paired if r['author']==a and r['seed'] is not None];comparison[a]=dict(conditional_change=stats([r['closeness_change'] for r in rr if r['available']]),unconditional_change=stats([r['unconditional_change'] for r in rr]),improved=sum(r['available'] and r['closeness_change']>TOL for r in rr),tied=sum(r['available'] and abs(r['closeness_change'])<=TOL for r in rr),worse=sum(r['available'] and r['closeness_change'] < -TOL for r in rr))
    compare(comparison,read(O/'comparison.json'))
    assert checked==len(records)==936 and len(geometries)==195;hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration246/verification-manifest.json'),read(P/'iteration248/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',pair_records=checked,graph_logs=195,independent_matrix_exponentials=solves,collapsed_graphs=saturated,author_summaries=5,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
