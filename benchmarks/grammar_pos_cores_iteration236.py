"""Unanimous initialization cores; evaluation-only POS compatibility."""
from pathlib import Path
from collections import defaultdict
import itertools,json,hashlib,random
import numpy as np
P=Path('experiments/results/grammar-restoration');O=P/'iteration236'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def measures(y,cores):
    pairmeans=[];allpairs=[];purities=[];wordpure=0;words=0
    for core in cores:
        ix=core['indices'];pairs=[float(y[i]@y[j]) for i,j in itertools.combinations(ix,2)];pairmeans.append(sum(pairs)/len(pairs));allpairs.extend(pairs);mass=y[ix].sum(0);purities.append(float(mass.max()/len(ix)));wordpure+=float(mass.max());words+=len(ix)
    return dict(core_macro_compatibility=float(np.mean(pairmeans)) if pairmeans else None,pair_weighted_compatibility=float(np.mean(allpairs)) if allpairs else None,core_macro_oracle_purity=float(np.mean(purities)) if purities else None,word_weighted_oracle_purity=wordpure/words if words else None)
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[P/n for n in ['iteration235/runs.json','iteration235/verification-manifest.json','iteration234-retry/clusters.json','iteration234-retry/strata.json','iteration231/features.json','iteration231/truth.json','iteration231/summary.json']];save(O/'design-freeze.json',{str(p):sha(p) for p in paths})
    for p,h in read(P/'iteration235/verification-manifest.json').items():assert sha(Path(p))==h
    runs=read(P/'iteration235/runs.json');base=read(P/'iteration234-retry/clusters.json');cores={}
    for a,rr in runs.items():
        groups=defaultdict(list)
        for i,w in enumerate(base[a]['words']):groups[tuple(r['labels'][i] for r in rr)].append(i)
        groups=sorted(groups.values(),key=lambda ix:[base[a]['words'][i] for i in ix]);cores[a]=[dict(indices=ix,words=[base[a]['words'][i] for i in ix],size=len(ix),pairs=[list(pair) for pair in itertools.combinations(ix,2)]) for ix in groups]
    save(O/'cores.json',cores);save(O/'core-freeze.json',{'cores.json':sha(O/'cores.json')})
    ff=read(P/'iteration231/features.json');truth=read(P/'iteration231/truth.json');coverage=read(P/'iteration231/summary.json');strata=read(P/'iteration234-retry/strata.json');details={};summary={}
    for a,allcores in cores.items():
        lookup={r['word']:i for i,r in enumerate(ff[a])};y=np.array([truth[a]['profiles'][lookup[w]] for w in base[a]['words']]);frequency=np.array([truth[a]['frequencies'][lookup[w]] for w in base[a]['words']]);cc=[c for c in allcores if c['size']>=2];actual=measures(y,cc);null=[]
        for seed in range(23300,23499):
            rng=random.Random(seed);perm=np.arange(len(y))
            for bucket in strata[a]:
                ix=bucket['indices'];source=ix.copy();rng.shuffle(source);perm[ix]=source
            null.append(measures(y[perm],cc))
        nodeix=[i for c in cc for i in c['indices']];details[a]=dict(actual=actual,null=null,individual_cores=[dict(words=c['words'],indices=c['indices'],size=c['size'],metrics=measures(y,[c])) for c in cc]);summary[a]=dict(all_cores=len(allcores),nonsingleton_cores=len(cc),singletons=sum(c['size']==1 for c in allcores),sizes=[c['size'] for c in cc],pairs=sum(len(c['pairs']) for c in cc),covered_nodes=len(nodeix),graph_nodes=len(y),graph_node_coverage=len(nodeix)/len(y),covered_tokens=int(frequency[nodeix].sum()),text_token_coverage=float(frequency[nodeix].sum()/coverage[a]['coverage']['text_tokens']),text_type_coverage=len(nodeix)/coverage[a]['coverage']['text_word_types'],actual=actual,null={k:dict(mean=float(np.mean([r[k] for r in null])),maximum=max(r[k] for r in null),upper_tail=(1+sum(r[k]>=v-1e-12 for r in null))/200) if v is not None else None for k,v in actual.items()})
    save(O/'details.json',details);save(O/'summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
