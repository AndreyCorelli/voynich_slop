"""Validate every frozen discovered shared group on unused sentence splits."""
from pathlib import Path
from itertools import combinations
from collections import Counter,defaultdict
import json,gzip,random,hashlib
from benchmarks.grammar_diffusion_cores_iteration250 import pipeline,compress
from benchmarks.grammar_disjoint_cores_iteration245 import cross,evaluate
P=Path('experiments/results/grammar-restoration');O=P/'iteration252';SEEDS=list(range(25200,25219))
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def validate(groups,halves):
    maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in halves];out=[]
    for c in groups:
        ww=c['words'];pairs=list(combinations(ww,2));initial=[all(w in d['words'] for w in ww) for d in halves];present=[all(w in m for w in ww) for m in maps];intact=[p and len({m[w] for w in ww})==1 for p,m in zip(present,maps)];retained=[list((u,v)) for u,v in pairs if all(u in m and v in m and m[u]==m[v] for m in maps)];out.append(dict(group_id=c['group_id'],initial_graph_present_by_half=initial,strict_present_by_half=present,intact_by_half=intact,intact_both=all(intact),pairs=len(pairs),retained_pairs_both=len(retained),retained_pair_words=retained))
    return out

def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_diffusion_cores_iteration250.py','grammar_pos_text_robustness_iteration237.py','grammar_pos_stability_iteration235.py','grammar_disjoint_cores_iteration245.py','grammar_pos_cores_iteration236.py']]+[P/n for n in ['iteration193/graphs.json','iteration250/cross-half-cores.json','iteration250/verification-manifest.json','iteration251/verification-manifest.json','iteration201/development-references.json','iteration231/design-freeze.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=SEEDS,primary='each fixed group intact in both halves across all19 unused splits; no group selection or success cutoff',representation='unchanged250 time1'))
    for previous in ['iteration250','iteration251']:
        for p,h in read(P/previous/'verification-manifest.json').items():assert sha(Path(p))==h
    discovery=defaultdict(list)
    for key,d in read(P/'iteration250/cross-half-cores.json').items():
        if key.startswith('Aquinas-'):
            for c in d['cores']:
                if c['size']>1:discovery[tuple(c['words'])].append(int(key.rsplit('-',1)[1]))
    groups=[dict(group_id=f'G{i+1}',words=list(ww),discovery_splits=ss) for i,(ww,ss) in enumerate(sorted(discovery.items()))];assert len(groups)==2;save(O/'frozen-groups.json',groups)
    g=read(P/'iteration193/graphs.json')['Aquinas'];order=list(dict.fromkeys(tuple(p[:2]) for p in g['positions'] if p is not None));splits={};shared={};files=[O/'frozen-groups.json']
    for seed in SEEDS:
        chosen=set(random.Random(seed).sample(order,len(order)//2));keys=[[list(k) for k in order if k in chosen],[list(k) for k in order if k not in chosen]];splits[str(seed)]=keys;dd=[]
        for half in [0,1]:
            kept=set(map(tuple,keys[half]));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];d=pipeline(dict(ids=g['ids'],positions=positions));path=O/f'{seed}-{half}.json.gz';compress(path,d);files.append(path);dd.append(d)
        shared[str(seed)]=cross(*dd);print('frozen',seed,flush=True)
    save(O/'splits.json',splits);save(O/'cross-half-cores.json',shared);files.extend([O/'splits.json',O/'cross-half-cores.json']);save(O/'selection-freeze.json',{str(p):sha(p) for p in files})
    ref=read(P/'iteration201/development-references.json')['Aquinas']['pos'];counts=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p is not None:counts[g['ids'][i]][ref[i]]+=1
    results=[]
    for seed in SEEDS:
        dd=[json.loads(gzip.decompress((O/f'{seed}-{half}.json.gz').read_bytes())) for half in [0,1]];results.append(dict(seed=seed,fixed_groups=validate(groups,dd),shared=evaluate(shared[str(seed)],counts),halves=[dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),non_singleton_cores=sum(c['size']>1 for c in d['cores'])) for d in dd]))
    summary=[]
    for c in groups:
        rr=[next(v for v in r['fixed_groups'] if v['group_id']==c['group_id']) for r in results];summary.append(dict(group_id=c['group_id'],words=c['words'],discovery_splits=c['discovery_splits'],validation_splits=len(rr),initial_graph_present_both=sum(all(r['initial_graph_present_by_half']) for r in rr),strict_present_both=sum(all(r['strict_present_by_half']) for r in rr),intact_both=sum(r['intact_both'] for r in rr),intact_half_count=sum(sum(r['intact_by_half']) for r in rr),retained_pair_trials=sum(r['retained_pairs_both'] for r in rr),pair_trials=sum(r['pairs'] for r in rr),reference=evaluate(dict(words=c['words'],cores=[dict(words=c['words'],size=len(c['words']),indices=list(range(len(c['words']))))]),counts)))
    save(O/'results.json',results);save(O/'summary.json',dict(fixed_groups=summary,shared_output_splits=sum(bool(r['shared']['core_sizes']) for r in results),pure_shared_output_splits=sum(bool(r['shared']['pure_cores']) for r in results)))
    for c in summary:print(c['group_id'],'size',len(c['words']),'initial both',c['initial_graph_present_both'],'strict both',c['strict_present_both'],'intactboth',c['intact_both'],'pairs',c['retained_pair_trials'],'/',c['pair_trials'],flush=True)
if __name__=='__main__':run()
