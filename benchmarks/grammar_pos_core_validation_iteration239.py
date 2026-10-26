"""Unused-seed sentence-deletion validation of frozen joint cores."""
from pathlib import Path
from itertools import combinations
import json,hashlib,random
import numpy as np
from benchmarks.grammar_pos_text_robustness_iteration237 import rebuild,partition
P=Path('experiments/results/grammar-restoration');O=P/'iteration239';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def ranges(v):return dict(minimum=min(v),mean=float(np.mean(v)),maximum=max(v)) if v else None
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_text_robustness_iteration237.py')]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration238/cores.json','iteration238/verification-manifest.json','iteration237/baselines.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},seeds=list(range(23900,23931)),deletion_fractions=[.1,.2],initial_seed=23500))
    for p,h in read(P/'iteration238/verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];graphs={};parts={}
    for a in AA:
        g=gg[a];sentences=sorted({tuple(p[:2]) for p in g['positions'] if p is not None});graphs[a]={};parts[a]={}
        for fraction in [.1,.2]:
            name=str(fraction);graphs[a][name]=[];parts[a][name]=[]
            for seed in range(23900,23931):
                removed=sorted(random.Random(seed).sample(sentences,int(fraction*len(sentences))));edges=rebuild(g,set(removed));graphs[a][name].append(dict(seed=seed,deleted_sentences=[list(v) for v in removed],total_sentences=len(sentences),descriptors=edges));parts[a][name].append(dict(seed=seed,**partition(edges)))
    save(O/'graphs.json',graphs);save(O/'partitions.json',parts);save(O/'partition-freeze.json',{n:sha(O/n) for n in ['graphs.json','partitions.json']})
    cores=read(P/'iteration238/cores.json');baseline=read(P/'iteration237/baselines.json');details={};summary={};corestats={}
    for a in AA:
        cc=[c for c in cores[a] if c['size']>1];pairs=[(u,v) for c in cc for u,v in combinations(c['words'],2)];base=baseline[a]['partition'];bm=dict(zip(base['words'],base['labels']));assert all(bm[u]==bm[v] for u,v in pairs);details[a]={};summary[a]={};corestats[a]={}
        for fraction,rr in parts[a].items():
            details[a][fraction]=[];corestats[a][fraction]=[dict(words=c['words'],size=c['size'],all_endpoints_survive=0,intact=0) for c in cc]
            for graph,part in zip(graphs[a][fraction],rr):
                present=set(part['words']);labels=dict(zip(part['words'],part['labels'])) if part['clusterable'] else {};surviving=[(u,v) for u,v in pairs if u in present and v in present];retained=sum(part['clusterable'] and labels[u]==labels[v] for u,v in surviving);intact=0
                for i,c in enumerate(cc):
                    available=all(w in present for w in c['words']);coassigned=all(w in labels for w in c['words']) and len({labels[w] for w in c['words']})==1;corestats[a][fraction][i]['all_endpoints_survive']+=available;corestats[a][fraction][i]['intact']+=coassigned;intact+=coassigned
                details[a][fraction].append(dict(seed=part['seed'],clusterable=part['clusterable'],edges=len(graph['descriptors']),graph_nodes=len(present),original_pairs=len(pairs),surviving_pairs=len(surviving),retained_pairs=retained,unconditional_retention=retained/len(pairs) if pairs else None,conditional_retention=retained/len(surviving) if surviving else None,pair_survival=len(surviving)/len(pairs) if pairs else None,intact_cores=intact,original_cores=len(cc)))
            records=details[a][fraction];summary[a][fraction]=dict(original_pairs=len(pairs),original_cores=len(cc),unclusterable_runs=sum(not r['clusterable'] for r in records),unconditional_retention=ranges([r['unconditional_retention'] for r in records if r['unconditional_retention'] is not None]),conditional_retention=ranges([r['conditional_retention'] for r in records if r['conditional_retention'] is not None]),pair_survival=ranges([r['pair_survival'] for r in records if r['pair_survival'] is not None]),intact_cores=ranges([r['intact_cores'] for r in records]))
    for n,v in [('details',details),('core-statistics',corestats),('summary',summary)]:save(O/(n+'.json'),v)
    print(json.dumps(summary,indent=2));print('CORE',json.dumps(corestats))
if __name__=='__main__':run()
