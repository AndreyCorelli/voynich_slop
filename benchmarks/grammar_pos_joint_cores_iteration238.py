"""Strict initialization-and-sentence-deletion unanimous core intersection."""
from pathlib import Path
from collections import defaultdict
from itertools import combinations
import json,hashlib,random
import numpy as np
from benchmarks.grammar_pos_cores_iteration236 import measures
P=Path('experiments/results/grammar-restoration');O=P/'iteration238'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pos_cores_iteration236.py')]+[P/n for n in ['iteration236/cores.json','iteration236/summary.json','iteration237/partitions.json','iteration237/verification-manifest.json','iteration234-retry/clusters.json','iteration234-retry/strata.json','iteration231/features.json','iteration231/truth.json','iteration231/summary.json']];save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration237/verification-manifest.json').items():assert sha(Path(p))==h
    original=read(P/'iteration236/cores.json');parts=read(P/'iteration237/partitions.json');base=read(P/'iteration234-retry/clusters.json');cores={};exclusions={}
    for a,cc in original.items():
        lookup={w:i for i,w in enumerate(base[a]['words'])};maps=[dict(zip(p['words'],p['labels'])) if p['clusterable'] else {} for p in parts[a]];groups=defaultdict(list);excluded=[]
        for ci,c in enumerate(cc):
            for w in c['words']:
                missing=[p['seed'] for p,m in zip(parts[a],maps) if w not in m]
                if missing:excluded.append(dict(word=w,index=lookup[w],missing_seeds=missing));continue
                groups[(ci,)+tuple(m[w] for m in maps)].append(lookup[w])
        cores[a]=[dict(indices=ix,words=[base[a]['words'][i] for i in ix],size=len(ix),pairs=[list(p) for p in combinations(ix,2)]) for ix in sorted(groups.values(),key=lambda ix:[base[a]['words'][i] for i in ix])];exclusions[a]=excluded
    save(O/'cores.json',cores);save(O/'exclusions.json',exclusions);save(O/'core-freeze.json',{n:sha(O/n) for n in ['cores.json','exclusions.json']})
    ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');coverage=read(P/'iteration231/summary.json');strata=read(P/'iteration234-retry/strata.json');previous=read(P/'iteration236/summary.json');details={};summary={}
    for a,allcores in cores.items():
        lookup={r['word']:i for i,r in enumerate(ff[a])};y=np.array([truth[a]['profiles'][lookup[w]] for w in base[a]['words']]);frequency=np.array([truth[a]['frequencies'][lookup[w]] for w in base[a]['words']]);cc=[c for c in allcores if c['size']>=2];actual=measures(y,cc);null=[]
        for seed in range(23300,23499):
            rng=random.Random(seed);perm=np.arange(len(y))
            for bucket in strata[a]:
                ix=bucket['indices'];source=ix.copy();rng.shuffle(source);perm[ix]=source
            null.append(measures(y[perm],cc))
        selected=[i for c in cc for i in c['indices']];details[a]=dict(actual=actual,null=null,individual_cores=[dict(words=c['words'],indices=c['indices'],size=c['size'],metrics=measures(y,[c])) for c in cc]);summary[a]=dict(original=previous[a],surviving_all_runs=len(y)-len(exclusions[a]),excluded_nodes=len(exclusions[a]),all_joint_cores=len(allcores),nonsingleton_cores=len(cc),singletons=sum(c['size']==1 for c in allcores),sizes=[c['size'] for c in cc],pairs=sum(len(c['pairs']) for c in cc),covered_nodes=len(selected),graph_nodes=len(y),graph_node_coverage=len(selected)/len(y),covered_tokens=int(frequency[selected].sum()),text_token_coverage=float(frequency[selected].sum()/coverage[a]['coverage']['text_tokens']),text_type_coverage=len(selected)/coverage[a]['coverage']['text_word_types'],actual=actual,null={k:dict(mean=float(np.mean([r[k] for r in null])),maximum=max(r[k] for r in null),upper_tail=(1+sum(r[k]>=v-1e-12 for r in null))/200) if v is not None else None for k,v in actual.items()})
    save(O/'details.json',details);save(O/'summary.json',summary)
    for a,v in summary.items():print(a,{k:z for k,z in v.items() if k not in ['original','null']},'tails',{k:(z['upper_tail'] if z else None) for k,z in v['null'].items()})
if __name__=='__main__':run()
