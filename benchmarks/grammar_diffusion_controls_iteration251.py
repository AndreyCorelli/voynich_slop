"""Matched complete selection: every order control replays all nineteen splits."""
from pathlib import Path
from collections import defaultdict,Counter
import json,gzip,random,hashlib
from benchmarks.grammar_diffusion_cores_iteration250 import pipeline,compress
from benchmarks.grammar_disjoint_cores_iteration245 import cross,evaluate
P=Path('experiments/results/grammar-restoration');O=P/'iteration251';SPLITS=list(range(24600,24619));TRIALS=['real']+[str(s) for s in range(24000,24019)]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__)]+[Path('benchmarks')/n for n in ['grammar_diffusion_cores_iteration250.py','grammar_pos_text_robustness_iteration237.py','grammar_pos_stability_iteration235.py','grammar_disjoint_cores_iteration245.py','grammar_pos_cores_iteration236.py']]+[P/n for n in ['iteration193/graphs.json','iteration246/splits.json','iteration250/cross-half-cores.json','iteration250/verification-manifest.json','iteration201/development-references.json','iteration231/design-freeze.json']];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},shuffle_seeds=list(range(24000,24019)),split_seeds=SPLITS,primary='largest fully global-POS-pure shared non-singleton core over ALL splits/cores/POS classes, zero if absent',finite_tail='(1+controls>=real)/20'))
    for p,h in read(P/'iteration250/verification-manifest.json').items():assert sha(Path(p))==h
    g=read(P/'iteration193/graphs.json')['Aquinas'];splits=read(P/'iteration246/splits.json');sentences=defaultdict(list)
    for i,p in enumerate(g['positions']):
        if p is not None:sentences[tuple(p[:2])].append(i)
    files=[];audit=[]
    for trial in TRIALS:
        directory=O/trial;directory.mkdir();ids=g['ids'].copy();rng=random.Random(int(trial)) if trial!='real' else None
        if rng:
            for _,ix in sorted(sentences.items()):
                vv=[g['ids'][i] for i in ix];rng.shuffle(vv);assert Counter(vv)==Counter(g['ids'][i] for i in ix)
                for i,w in zip(ix,vv):ids[i]=w
        assert Counter(ids)==Counter(g['ids']);audit.append(dict(trial=trial,sentences=len(sentences),changed_lexical_positions=sum(ids[i]!=g['ids'][i] for ix in sentences.values() for i in ix)))
        crosses={}
        for seed in SPLITS:
            halves=[]
            for half in [0,1]:
                path=directory/f'{seed}-{half}.json.gz'
                if trial=='real':path.write_bytes((P/'iteration250'/f'Aquinas-{seed}-{half}.json.gz').read_bytes());d=json.loads(gzip.decompress(path.read_bytes()))
                else:
                    kept=set(map(tuple,splits[f'Aquinas-{seed}'][half]));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];d=pipeline(dict(ids=ids,positions=positions));compress(path,d)
                halves.append(d);files.append(path)
            crosses[str(seed)]=cross(*halves)
            if trial=='real':assert crosses[str(seed)]==read(P/'iteration250/cross-half-cores.json')[f'Aquinas-{seed}']
        path=directory/'cross-half-cores.json';save(path,crosses);files.append(path);print('frozen',trial,flush=True)
    save(O/'shuffle-audit.json',audit);files.append(O/'shuffle-audit.json');save(O/'selection-freeze.json',{str(p):sha(p) for p in files})
    ref=read(P/'iteration201/development-references.json')['Aquinas']['pos'];counts=defaultdict(Counter)
    for i,p in enumerate(g['positions']):
        if p is not None:counts[g['ids'][i]][ref[i]]+=1
    results={}
    for trial in TRIALS:
        cc=read(O/trial/'cross-half-cores.json');rows=[dict(split_seed=seed,**evaluate(cc[str(seed)],counts)) for seed in SPLITS];half_status=[]
        for seed in SPLITS:
            for half in [0,1]:
                d=json.loads(gzip.decompress((O/trial/f'{seed}-{half}.json.gz').read_bytes()));half_status.append(dict(split_seed=seed,half=half,clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),non_singleton_cores=sum(c['size']>1 for c in d['cores'])))
        results[trial]=dict(splits=rows,halves=half_status,largest_pure_shared_core=max(r['largest_pure_core'] for r in rows),shared_output_splits=sum(bool(r['core_sizes']) for r in rows),pure_shared_output_splits=sum(bool(r['pure_cores']) for r in rows))
    actual=results['real']['largest_pure_shared_core'];assert actual==2;null=[results[t]['largest_pure_shared_core'] for t in TRIALS[1:]];ex=sum(v>=actual for v in null);summary=dict(real=results['real'],null_largest_pure_shared_cores=null,exceedances=ex,upper_tail=(1+ex)/20,null_trials=19,controls_without_shared_output=sum(not results[t]['shared_output_splits'] for t in TRIALS[1:]),controls_without_pure_shared_output=sum(not results[t]['pure_shared_output_splits'] for t in TRIALS[1:]))
    save(O/'results.json',results);save(O/'summary.json',summary);print('real',actual,'null',null,'tail',summary['upper_tail'],flush=True)
if __name__=='__main__':run()
