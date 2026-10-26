"""Frozen disjoint complete-sentence halves, unchanged strict-core extraction."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import gzip,json,hashlib,random
import numpy as np
from benchmarks.grammar_full_core_null_iteration241 import pipeline,compress
from benchmarks.grammar_pos_cores_iteration236 import measures
P=Path('experiments/results/grammar-restoration');O=P/'iteration246';BASE=['Aquinas','Caesar','Cicero','Jerome','Dante'];AA=[f'{a}-{seed}' for a in BASE for seed in range(24600,24619)]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def cross(left,right):
    maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in [left,right]];groups=defaultdict(list)
    for w in sorted(maps[0].keys()&maps[1].keys()):groups[maps[0][w],maps[1][w]].append(w)
    words=sorted(maps[0].keys()&maps[1].keys());ix={w:i for i,w in enumerate(words)}
    return dict(words=words,cores=[dict(words=ww,indices=[ix[w] for w in ww],size=len(ww),pairs=[list(v) for v in combinations([ix[w] for w in ww],2)]) for ww in sorted(groups.values())])
def evaluate(d,counts):
    tags=read(P/'iteration231/design-freeze.json')['tags'];profiles={w:[c[t]/sum(c.values()) for t in tags] for w,c in counts.items()};cc=[c for c in d['cores'] if c['size']>1];selected={w for c in cc for w in c['words']};pure=[]
    for c in cc:
        tt=[t for t in tags if all(counts[w][t]==sum(counts[w].values()) for w in c['words'])]
        if tt:pure.append(dict(words=c['words'],size=c['size'],reference_tag=tt[0],tokens=sum(sum(counts[w].values()) for w in c['words'])))
    return dict(core_sizes=[c['size'] for c in cc],covered_words=len(selected),covered_tokens=sum(sum(counts[w].values()) for w in selected),text_tokens=sum(sum(c.values()) for c in counts.values()),pure_cores=pure,largest_pure_core=max((c['size'] for c in pure),default=0),metrics=measures(np.array([profiles[w] for w in d['words']]),cc))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_full_core_null_iteration241.py','grammar_pos_text_robustness_iteration237.py','grammar_pos_spectral_iteration234_retry.py','grammar_pos_stability_iteration235.py','grammar_pos_cores_iteration236.py']]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration238/cores.json','iteration245/verification-manifest.json','iteration201/development-references.json','iteration200/pos-references.json','iteration231/design-freeze.json']]
    save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},authors=AA,split='Random(seed).sample(first-occurrence sentence order,floor(N/2)); complement second half',split_seeds=list(range(24600,24619)),primary_profiles='full admitted global POS; half-local secondary',init_seeds=list(range(23500,23531)),deletion_seeds=list(range(23700,23731))))
    for p,h in read(P/'iteration245/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];gg={key:gg[key.rsplit('-',1)[0]] for key in AA};splits={};shared={};data={};files=[]
    for a in AA:
        g=gg[a];order=list(dict.fromkeys(tuple(p[:2]) for p in g['positions'] if p is not None));mid=len(order)//2;chosen=set(random.Random(int(a.rsplit('-',1)[1])).sample(order,mid));splits[a]=[[list(v) for v in order if v in chosen],[list(v) for v in order if v not in chosen]];data[a]=[]
        for half,keys in enumerate(splits[a]):
            kept={tuple(k) for k in keys};positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];d=pipeline(dict(ids=g['ids'],positions=positions));path=O/f'{a}-{half}.json.gz';compress(path,d);files.append(path);data[a].append(d);print(a,half,'nodes',len(d['words']),'clusterable',d['clusterable'],'cores',[c['size'] for c in d['cores'] if c['size']>1],flush=True)
        shared[a]=cross(*data[a])
    save(O/'splits.json',splits);save(O/'cross-half-cores.json',shared);files.extend([O/'splits.json',O/'cross-half-cores.json']);save(O/'selection-freeze.json',{str(p):sha(p) for p in files})
    refs=read(P/'iteration201/development-references.json');dref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'];original=read(P/'iteration238/cores.json');results={}
    for a in AA:
        g=gg[a];base=a.rsplit('-',1)[0];ref=dref if base=='Dante' else refs[base]['pos'];counts=defaultdict(Counter);local=[defaultdict(Counter),defaultdict(Counter)];first={tuple(k) for k in splits[a][0]}
        for i,p in enumerate(g['positions']):
            if p is not None:counts[g['ids'][i]][ref[i]]+=1;local[int(tuple(p[:2]) not in first)][g['ids'][i]][ref[i]]+=1
        maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in data[a]];pairs=[(u,v) for c in original[base] for u,v in combinations(c['words'],2)];retained=[(u,v) for u,v in pairs if all(u in m and v in m and m[u]==m[v] for m in maps)];present=[(u,v) for u,v in pairs if all(u in m and v in m for m in maps)]
        halves=[dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),global_profiles=evaluate(d,counts),local_profiles=evaluate(d,local[h])) for h,d in enumerate(data[a])];results[a]=dict(halves=halves,shared=evaluate(shared[a],counts),original_pairs=len(pairs),original_pairs_present_both=len(present),original_pairs_retained_both=len(retained),retained_pair_words=[list(v) for v in retained],unconditional_retention=len(retained)/len(pairs) if pairs else None)
    save(O/'results.json',results)
    for a,r in results.items():print(a,'shared',r['shared']['core_sizes'],'original retention',r['original_pairs_retained_both'],'/',r['original_pairs'],flush=True)
if __name__=='__main__':run()
