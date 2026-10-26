"""Full matched pipeline replay, independent metrics and selection-tail audit."""
from pathlib import Path
from collections import Counter,defaultdict
import gzip,json,random,hashlib
from benchmarks.grammar_diffusion_cores_iteration250_review import audit
from benchmarks.grammar_disjoint_cores_iteration245_review import expectedcores,metrics,compare
P=Path('experiments/results/grammar-restoration');O=P/'iteration251';SPLITS=list(range(24600,24619));TRIALS=['real']+[str(s) for s in range(24000,24019)]
def read(p):return json.loads(p.read_text())
def run():
    g=read(P/'iteration193/graphs.json')['Aquinas'];splits=read(P/'iteration246/splits.json');results=read(O/'results.json');summary=read(O/'summary.json');shuffleaudit=read(O/'shuffle-audit.json');ref=read(P/'iteration201/development-references.json')['Aquinas']['pos'];tags=read(P/'iteration231/design-freeze.json')['tags'];counts=defaultdict(Counter);sentences=defaultdict(list)
    for i,p in enumerate(g['positions']):
        if p is not None:sentences[tuple(p[:2])].append(i);counts[g['ids'][i]][ref[i]]+=1
    graphs=runs=geometry=reuse=0
    for trial in TRIALS:
        ids=g['ids'].copy()
        if trial!='real':
            rng=random.Random(int(trial))
            for key in sorted(sentences):
                ix=sentences[key];vv=[g['ids'][i] for i in ix];rng.shuffle(vv)
                for i,w in zip(ix,vv):ids[i]=w
        for ix in sentences.values():assert Counter(ids[i] for i in ix)==Counter(g['ids'][i] for i in ix)
        assert Counter(ids)==Counter(g['ids']);assert shuffleaudit[TRIALS.index(trial)]==dict(trial=trial,sentences=len(sentences),changed_lexical_positions=sum(ids[i]!=g['ids'][i] for ix in sentences.values() for i in ix));crosses=read(O/trial/'cross-half-cores.json');rows=[];status=[]
        for seed in SPLITS:
            dd=[]
            for half in [0,1]:
                path=O/trial/f'{seed}-{half}.json.gz';d=json.loads(gzip.decompress(path.read_bytes()));dd.append(d);kept=set(map(tuple,splits[f'Aquinas-{seed}'][half]));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];ng,nr,nm=audit(dict(ids=ids,positions=positions),d);graphs+=ng;runs+=nr;geometry+=nm;status.append(dict(split_seed=seed,half=half,clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),non_singleton_cores=sum(c['size']>1 for c in d['cores'])))
                if trial=='real':assert path.read_bytes()==(P/'iteration250'/f'Aquinas-{seed}-{half}.json.gz').read_bytes();reuse+=1
            maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in dd];words=sorted(set(maps[0])&set(maps[1]));groups=defaultdict(list)
            for w in words:groups[maps[0][w],maps[1][w]].append(w)
            shared=dict(words=words,cores=expectedcores(words,groups.values()));assert shared==crosses[str(seed)];rows.append(dict(split_seed=seed,**metrics(shared,counts,tags)))
            if trial=='real':assert shared==read(P/'iteration250/cross-half-cores.json')[f'Aquinas-{seed}']
        expected=dict(splits=rows,halves=status,largest_pure_shared_core=max(r['largest_pure_core'] for r in rows),shared_output_splits=sum(bool(r['core_sizes']) for r in rows),pure_shared_output_splits=sum(bool(r['pure_cores']) for r in rows));compare(expected,results[trial]);print(trial,'independent replay passed',flush=True)
    null=[results[t]['largest_pure_shared_core'] for t in TRIALS[1:]];ex=sum(v>=results['real']['largest_pure_shared_core'] for v in null);expected=dict(real=results['real'],null_largest_pure_shared_cores=null,exceedances=ex,upper_tail=(1+ex)/20,null_trials=19,controls_without_shared_output=sum(not results[t]['shared_output_splits'] for t in TRIALS[1:]),controls_without_pure_shared_output=sum(not results[t]['pure_shared_output_splits'] for t in TRIALS[1:]));compare(expected,summary);hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(O/'selection-freeze.json'),read(P/'iteration250/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',trials=20,halves=760,cross_intersections=380,graph_replays=graphs,lloyd_replays=runs,matrix_exponential_checks=geometry,byte_identical_reused_half_outputs=reuse,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
