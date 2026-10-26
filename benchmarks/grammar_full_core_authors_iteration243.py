"""Fixed matched full-selector controls for all remaining admitted authors."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,random,gzip
import numpy as np
from benchmarks.grammar_full_core_null_iteration241 import pipeline,compress
from benchmarks.grammar_pos_cores_iteration236 import measures
P=Path('experiments/results/grammar-restoration');O=P/'iteration243';AA=['Aquinas','Caesar','Cicero','Dante']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_full_core_null_iteration241.py','grammar_pos_text_robustness_iteration237.py','grammar_pos_spectral_iteration234_retry.py','grammar_pos_stability_iteration235.py','grammar_pos_cores_iteration236.py']]+[P/n for n in ['iteration193/graphs.json','iteration198/graphs.json','iteration238/cores.json','iteration240/graphs.json','iteration240/verification-manifest.json','iteration242/verification-manifest.json','iteration201/development-references.json','iteration200/pos-references.json','iteration231/design-freeze.json']]
    save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},authors=AA,shuffle_seeds=list(range(24000,24019)),init_seeds=list(range(23500,23531)),deletion_seeds=list(range(23700,23731)),primary='largest fully global-POS-pure non-singleton core over all cores and classes; zero if absent'))
    for previous in ['iteration240','iteration242']:
        for p,h in read(P/previous/'verification-manifest.json').items():assert sha(Path(p))==h
    gg=read(P/'iteration193/graphs.json');gg['Dante']=read(P/'iteration198/graphs.json')['primary'];cached=read(P/'iteration240/graphs.json');originalcores=read(P/'iteration238/cores.json');files={}
    for a in AA:
        (O/a).mkdir();g=gg[a];sentences=defaultdict(list)
        for i,p in enumerate(g['positions']):
            if p is not None:sentences[tuple(p[:2])].append(i)
        files[a]=[]
        for seed in [None]+list(range(24000,24019)):
            ids=g['ids'].copy()
            if seed is not None:
                rng=random.Random(seed)
                for _,ix in sorted(sentences.items()):
                    vv=[g['ids'][i] for i in ix];rng.shuffle(vv)
                    for i,w in zip(ix,vv):ids[i]=w
            result=pipeline(dict(ids=ids,positions=g['positions']))
            if seed is None:assert result['cores']==originalcores[a]
            else:assert result['initial_graph']==cached[a][seed-24000]['descriptors']
            path=O/a/('real.json.gz' if seed is None else f'null-{seed}.json.gz');compress(path,result);files[a].append(path);print(a,seed,'frozen',flush=True)
    save(O/'selection-freeze.json',{str(p):sha(p) for ff in files.values() for p in ff})
    tags=read(P/'iteration231/design-freeze.json')['tags'];refs=read(P/'iteration201/development-references.json');dref=read(P/'iteration200/pos-references.json')['pos_by_stream_position'];results={};summary={}
    for a in AA:
        g=gg[a];ref=dref if a=='Dante' else refs[a]['pos'];counts=defaultdict(Counter);frequency=Counter()
        for i,p in enumerate(g['positions']):
            if p is not None:counts[g['ids'][i]][ref[i]]+=1;frequency[g['ids'][i]]+=1
        profiles={w:[c[t]/sum(c.values()) for t in tags] for w,c in counts.items()};rr=[]
        for path in files[a]:
            d=json.loads(gzip.decompress(path.read_bytes()));cc=[c for c in d['cores'] if c['size']>1];pure=[]
            for c in cc:
                tt=[t for t in tags if all(counts[w][t]==sum(counts[w].values()) for w in c['words'])]
                if tt:pure.append(dict(words=c['words'],size=c['size'],reference_tag=tt[0],tokens=sum(frequency[w] for w in c['words'])))
            selected={w for c in cc for w in c['words']};rr.append(dict(trial=path.name,clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),joint_cores=len(cc),core_sizes=[c['size'] for c in cc],covered_words=len(selected),covered_tokens=sum(frequency[w] for w in selected),pure_cores=pure,largest_pure_core=max((c['size'] for c in pure),default=0),metrics=measures(np.array([profiles[w] for w in d['words']]),cc)))
        results[a]=rr;actual=rr[0];null=rr[1:];ex=sum(r['largest_pure_core']>=actual['largest_pure_core'] for r in null);summary[a]=dict(real=actual,null_largest_pure_sizes=[r['largest_pure_core'] for r in null],exceedances=ex,upper_tail=(1+ex)/20,zero_joint_output=sum(not r['joint_cores'] for r in null),unclusterable=sum(not r['clusterable'] for r in null),null_trials=19)
    save(O/'results.json',results);save(O/'summary.json',summary)
    for a,s in summary.items():print(a,'real',s['real']['largest_pure_core'],'nullmax',max(s['null_largest_pure_sizes']),'tail',s['upper_tail'],'empty',s['zero_joint_output'],flush=True)
if __name__=='__main__':run()
