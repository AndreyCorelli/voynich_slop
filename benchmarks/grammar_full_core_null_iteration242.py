"""Matched complete strict-core pipeline on fixed Jerome order controls."""
from pathlib import Path
from collections import defaultdict,Counter
from itertools import combinations
import json,hashlib,random,gzip
import numpy as np
from benchmarks.grammar_pos_text_robustness_iteration237 import rebuild,partition
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
from benchmarks.grammar_pos_stability_iteration235 import lloyd
from benchmarks.grammar_pos_cores_iteration236 import measures
P=Path('experiments/results/grammar-restoration');O=P/'iteration242'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def compress(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':'),allow_nan=False).encode(),mtime=0))
def pipeline(g):
    edges=rebuild(g,set());words=sorted({e[k] for e in edges for k in ['a','b']});sentences=sorted({tuple(p[:2]) for p in g['positions'] if p is not None})
    if len(words)<17:return dict(initial_graph=edges,words=words,clusterable=False,initial_runs=[],deletions=[],cores=[])
    embedding=np.array(cluster({'descriptors':edges})['embedding']);runs=[lloyd(embedding,s) for s in range(23500,23531)];deletions=[]
    for seed in range(23700,23731):
        removed=sorted(random.Random(seed).sample(sentences,int(.1*len(sentences))));ee=rebuild(g,set(removed));deletions.append(dict(seed=seed,removed=[list(v) for v in removed],graph=ee,partition=partition(ee)))
    maps=[dict(zip(r['partition']['words'],r['partition']['labels'])) if r['partition']['clusterable'] else {} for r in deletions];groups=defaultdict(list)
    for i,w in enumerate(words):
        if all(w in m for m in maps):groups[tuple(r['labels'][i] for r in runs)+tuple(m[w] for m in maps)].append(i)
    cores=[dict(indices=ix,words=[words[i] for i in ix],size=len(ix),pairs=[list(pair) for pair in combinations(ix,2)]) for ix in sorted(groups.values(),key=lambda ix:[words[i] for i in ix])]
    return dict(initial_graph=edges,words=words,clusterable=True,initial_runs=runs,deletions=deletions,cores=cores)
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_full_core_null_iteration241.py'),P/'iteration241/verification-manifest.json']+[Path('benchmarks')/n for n in ['grammar_pos_text_robustness_iteration237.py','grammar_pos_spectral_iteration234_retry.py','grammar_pos_stability_iteration235.py','grammar_pos_cores_iteration236.py']]+[P/n for n in ['iteration193/graphs.json','iteration238/cores.json','iteration240/graphs.json','iteration240/verification-manifest.json','iteration201/development-references.json','iteration231/design-freeze.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},shuffle_seeds=list(range(24000,24199)),init_seeds=list(range(23500,23531)),deletion_seeds=list(range(23700,23731)),primary='largest fully global-POS-pure non-singleton core, max over all groups and POS classes'))
    for p,h in read(P/'iteration240/verification-manifest.json').items():assert sha(Path(p))==h
    original=read(P/'iteration193/graphs.json')['Jerome'];cached=read(P/'iteration240/graphs.json')['Jerome'];sentences=defaultdict(list)
    for i,p in enumerate(original['positions']):
        if p is not None:sentences[tuple(p[:2])].append(i)
    for p,h in read(P/'iteration241/verification-manifest.json').items():assert sha(Path(p))==h
    files=[]
    for name in ['real.json.gz']+[f'null-{seed}.json.gz' for seed in range(24000,24019)]:
        path=O/name;path.write_bytes((P/'iteration241'/name).read_bytes());files.append(path)
    print('reused frozen real and19 controls',flush=True)
    for seed in range(24019,24199):
        ids=original['ids'].copy();rng=random.Random(seed)
        for sentence,ix in sorted(sentences.items()):
            values=[original['ids'][i] for i in ix];rng.shuffle(values)
            for i,w in zip(ix,values):ids[i]=w
        result=pipeline(dict(ids=ids,positions=original['positions']));assert result['initial_graph']==cached[seed-24000]['descriptors'];path=O/f'null-{seed}.json.gz';compress(path,result);files.append(path);print('frozen',seed,'joint non-singleton cores',sum(c['size']>1 for c in result['cores']),flush=True)
    save(O/'selection-freeze.json',{str(p):sha(p) for p in files})
    tags=read(P/'iteration231/design-freeze.json')['tags'];ref=read(P/'iteration201/development-references.json')['Jerome']['pos'];counts=defaultdict(Counter);frequency=Counter()
    for i,p in enumerate(original['positions']):
        if p is not None:counts[original['ids'][i]][ref[i]]+=1;frequency[original['ids'][i]]+=1
    profiles={w:[c[t]/sum(c.values()) for t in tags] for w,c in counts.items()};results=[]
    for path in files:
        data=json.loads(gzip.decompress(path.read_bytes()));cc=[c for c in data['cores'] if c['size']>1];pure=[]
        for c in cc:
            common=[t for t in range(len(tags)) if all(profiles[w][t]==1. for w in c['words'])]
            if common:pure.append(dict(words=c['words'],size=c['size'],reference_tag=tags[common[0]],tokens=sum(frequency[w] for w in c['words'])))
        selected={w for c in cc for w in c['words']};y=np.array([profiles[w] for w in data['words']]);results.append(dict(trial=path.name,clusterable=data['clusterable'],nodes=len(data['words']),edges=len(data['initial_graph']),joint_cores=len(cc),core_sizes=[c['size'] for c in cc],covered_words=len(selected),covered_tokens=sum(frequency[w] for w in selected),pure_cores=pure,largest_pure_core=max((c['size'] for c in pure),default=0),metrics=measures(y,cc)))
    real=results[0];null=results[1:];summary=dict(real=real,null_largest_pure_sizes=[r['largest_pure_core'] for r in null],exceedances=sum(r['largest_pure_core']>=real['largest_pure_core'] for r in null),upper_tail=(1+sum(r['largest_pure_core']>=real['largest_pure_core'] for r in null))/200,zero_joint_output=sum(not r['joint_cores'] for r in null),null_trials=199)
    save(O/'results.json',results);save(O/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
