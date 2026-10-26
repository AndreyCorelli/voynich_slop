"""Fixed 10% sentence deletions, anonymous graph rebuild and pair retention."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,hashlib,random
from benchmarks.grammar_pos_spectral_iteration234_retry import cluster
from benchmarks.grammar_pos_stability_iteration235 import lloyd
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration237';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def rebuild(g,removed):
    positions=[p if p is not None and tuple(p[:2]) not in removed else None for p in g['positions']];counts=Counter(w for w,p in zip(g['ids'],positions) if p is not None);frames=defaultdict(lambda:defaultdict(list))
    for i in range(1,len(g['ids'])-1):
        if all(positions[j] is not None for j in [i-1,i,i+1]) and counts[g['ids'][i]]>=5:frames[(g['ids'][i-1],g['ids'][i+1])][g['ids'][i]].append(i)
    pairs=defaultdict(list)
    for f,words in sorted(frames.items()):
        for a,b in combinations(sorted(words),2):pairs[(a,b)].append(dict(frame=list(f),a_positions=words[a],b_positions=words[b]))
    return [dict(a=a,b=b,shared_frames=len(ff),frames=ff) for (a,b),ff in sorted(pairs.items()) if len(ff)>=2]
def partition(edges):
    words=sorted({e[k] for e in edges for k in ['a','b']})
    if len(words)<17:return dict(clusterable=False,words=words,labels=None,reason='fewer than17 graph nodes')
    g=cluster({'descriptors':edges});r=lloyd(np.array(g['embedding']),23500);return dict(clusterable=True,words=g['words'],labels=r['labels'],embedding_dimension=g['embedding_dimension'],zero_eigenvalues=g['zero_eigenvalues'],initial_center_indices=r['initial_center_indices'],iterations=r['iterations'])
def ranges(v):return dict(minimum=min(v),mean=float(np.mean(v)),maximum=max(v)) if v else None
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_spectral_iteration234_retry.py'),Path('benchmarks/grammar_pos_stability_iteration235.py')]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration235/runs.json','iteration234-retry/clusters.json','iteration236/cores.json','iteration236/verification-manifest.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(23700,23731)),initial_seed=23500))
    for p,h in read(P/'iteration236/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];oldruns=read(P/'iteration235/runs.json');baselines={};graphs={};partitions={}
    for a in AA:
        g=gg[a];edges=rebuild(g,set());assert edges==g['descriptors'];part=partition(edges);assert part['labels']==oldruns[a][0]['labels'];baselines[a]=dict(edges=len(edges),partition=part);sentences=sorted({tuple(p[:2]) for p in g['positions'] if p is not None});graphs[a]=[];partitions[a]=[]
        for seed in range(23700,23731):
            deleted=sorted(random.Random(seed).sample(sentences,int(.1*len(sentences))));edges=rebuild(g,set(deleted));graphs[a].append(dict(seed=seed,total_sentences=len(sentences),deleted_sentences=[list(v) for v in deleted],descriptors=edges));partitions[a].append(dict(seed=seed,**partition(edges)))
    for n,v in [('baselines',baselines),('graphs',graphs),('partitions',partitions)]:save(O/(n+'.json'),v)
    save(O/'partition-freeze.json',{n:sha(O/n) for n in ['baselines.json','graphs.json','partitions.json']})
    cores=read(P/'iteration236/cores.json');details={};summary={}
    for a in AA:
        cc=[c for c in cores[a] if c['size']>=2];pairs=[(u,v) for c in cc for u,v in combinations(c['words'],2)];originalnodes={w for c in cc for w in c['words']};details[a]=[]
        for graph,part in zip(graphs[a],partitions[a]):
            present=set(part['words']);labels=dict(zip(part['words'],part['labels'])) if part['clusterable'] else {};surviving=[(u,v) for u,v in pairs if u in present and v in present];retained=[(u,v) for u,v in surviving if part['clusterable'] and labels[u]==labels[v]];intact=[c for c in cc if all(w in labels for w in c['words']) and len({labels[w] for w in c['words']})==1];details[a].append(dict(seed=part['seed'],clusterable=part['clusterable'],edges=len(graph['descriptors']),graph_nodes=len(present),core_nodes_surviving=len(originalnodes&present),original_pairs=len(pairs),surviving_pairs=len(surviving),retained_pairs=len(retained),unconditional_retention=len(retained)/len(pairs),conditional_retention=len(retained)/len(surviving) if surviving else None,pair_survival=len(surviving)/len(pairs),intact_cores=len(intact),original_cores=len(cc)))
        rr=details[a];summary[a]=dict(unclusterable_runs=sum(not r['clusterable'] for r in rr),original_pairs=len(pairs),unconditional_retention=ranges([r['unconditional_retention'] for r in rr]),conditional_retention=ranges([r['conditional_retention'] for r in rr if r['conditional_retention'] is not None]),pair_survival=ranges([r['pair_survival'] for r in rr]),graph_nodes=ranges([r['graph_nodes'] for r in rr]),intact_cores=ranges([r['intact_cores'] for r in rr]))
    save(O/'details.json',details);save(O/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
