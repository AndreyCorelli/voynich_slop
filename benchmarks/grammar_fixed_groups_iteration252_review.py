"""Independent frozen-candidate, split, partition and fixed-recovery audit."""
from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import json,gzip,random,hashlib
from benchmarks.grammar_diffusion_cores_iteration250_review import audit
from benchmarks.grammar_disjoint_cores_iteration245_review import expectedcores,metrics
from benchmarks.grammar_diffusion_controls_iteration251_review_retry import compare
P=Path('experiments/results/grammar-restoration');O=P/'iteration252';SEEDS=list(range(25200,25219))
def read(p):return json.loads(p.read_text())
def run():
    source=read(P/'iteration250/cross-half-cores.json');inventory=defaultdict(list)
    for key,d in source.items():
        if key.startswith('Aquinas-'):
            for c in d['cores']:
                if c['size']>=2:inventory[tuple(c['words'])].append(int(key.rsplit('-',1)[1]))
    groups=[dict(group_id=f'G{i+1}',words=list(ww),discovery_splits=ss) for i,(ww,ss) in enumerate(sorted(inventory.items()))];assert groups==read(O/'frozen-groups.json');g=read(P/'iteration193/graphs.json')['Aquinas'];ref=read(P/'iteration201/development-references.json')['Aquinas']['pos'];tags=read(P/'iteration231/design-freeze.json')['tags'];counts=defaultdict(Counter);first={}
    for i,p in enumerate(g['positions']):
        if p is not None:first.setdefault(tuple(p[:2]),i);counts[g['ids'][i]][ref[i]]+=1
    order=sorted(first,key=first.get);splits=read(O/'splits.json');crosses=read(O/'cross-half-cores.json');actual=read(O/'results.json');summary=read(O/'summary.json');new=[];graphs=runs=geometry=0
    for j,seed in enumerate(SEEDS):
        chosen=set(random.Random(seed).sample(order,len(order)//2));keys=[[list(k) for k in order if k in chosen],[list(k) for k in order if k not in chosen]];assert keys==splits[str(seed)];assert not set(map(tuple,keys[0]))&set(map(tuple,keys[1]));dd=[]
        for half in [0,1]:
            kept=set(map(tuple,keys[half]));positions=[p if p is not None and tuple(p[:2]) in kept else None for p in g['positions']];d=json.loads(gzip.decompress((O/f'{seed}-{half}.json.gz').read_bytes()));dd.append(d);ng,nr,nm=audit(dict(ids=g['ids'],positions=positions),d);graphs+=ng;runs+=nr;geometry+=nm
        maps=[{w:j for j,c in enumerate(d['cores']) for w in c['words']} for d in dd];common=sorted(set(maps[0])&set(maps[1]));gg=defaultdict(list)
        for w in common:gg[maps[0][w],maps[1][w]].append(w)
        shared=dict(words=common,cores=expectedcores(common,gg.values()));assert shared==crosses[str(seed)];fixed=[]
        for c in groups:
            ww=c['words'];initial=[set(ww)<=set(d['words']) for d in dd];present=[set(ww)<=set(m) for m in maps];intact=[p and all(m[w]==m[ww[0]] for w in ww) for p,m in zip(present,maps)];pairs=list(combinations(ww,2));retained=[list((u,v)) for u,v in pairs if all(u in m and v in m and m[u]==m[v] for m in maps)];fixed.append(dict(group_id=c['group_id'],initial_graph_present_by_half=initial,strict_present_by_half=present,intact_by_half=intact,intact_both=all(intact),pairs=len(pairs),retained_pairs_both=len(retained),retained_pair_words=retained))
        expected=dict(seed=seed,fixed_groups=fixed,shared=metrics(shared,counts,tags),halves=[dict(clusterable=d['clusterable'],nodes=len(d['words']),edges=len(d['initial_graph']),non_singleton_cores=sum(c['size']>1 for c in d['cores'])) for d in dd]);compare(expected,actual[j]);new.append(expected)
    ss=[]
    for c in groups:
        rr=[next(v for v in r['fixed_groups'] if v['group_id']==c['group_id']) for r in new];ss.append(dict(group_id=c['group_id'],words=c['words'],discovery_splits=c['discovery_splits'],validation_splits=19,initial_graph_present_both=sum(all(r['initial_graph_present_by_half']) for r in rr),strict_present_both=sum(all(r['strict_present_by_half']) for r in rr),intact_both=sum(r['intact_both'] for r in rr),intact_half_count=sum(sum(r['intact_by_half']) for r in rr),retained_pair_trials=sum(r['retained_pairs_both'] for r in rr),pair_trials=sum(r['pairs'] for r in rr),reference=metrics(dict(words=c['words'],cores=[dict(words=c['words'],size=len(c['words']),indices=list(range(len(c['words']))))]),counts)))
    compare(dict(fixed_groups=ss,shared_output_splits=sum(bool(r['shared']['core_sizes']) for r in new),pure_shared_output_splits=sum(bool(r['shared']['pure_cores']) for r in new)),summary);hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(O/'selection-freeze.json'),read(P/'iteration250/verification-manifest.json'),read(P/'iteration251/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',frozen_groups=len(groups),splits=19,halves=38,graph_replays=graphs,lloyd_replays=runs,matrix_exponential_checks=geometry,cross_intersections=19,fixed_group_split_records=38,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
