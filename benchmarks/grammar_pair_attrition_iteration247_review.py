"""Independent record-level flag and aggregate reconstruction; no POS access."""
from pathlib import Path
from itertools import combinations
from collections import Counter
import json,gzip,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration247';AA=['Aquinas','Caesar','Cicero','Jerome','Dante'];FLAGS=['initial_present','initial_clusterable','initial_all_coassigned','deletion_all_present','deletion_all_clusterable','deletion_all_coassigned']
def read(p):return json.loads(p.read_text())
def run():
    old=read(P/'iteration238/cores.json');records=read(O/'pair-half-records.json');both=read(O/'pair-split-records.json');summary=read(O/'summary.json');previous=read(P/'iteration246/results.json');lookup={(r['author'],r['seed'],r['half'],tuple(r['pair'])):r for r in records};bb={(r['author'],r['seed'],tuple(r['pair'])):r for r in both};assert len(lookup)==len(records) and len(bb)==len(both);checked=partitions=0
    for a in AA:
        pairs=[p for c in old[a] for p in combinations(c['words'],2)]
        for seed in range(24600,24619):
            for half in range(2):
                d=json.loads(gzip.decompress((P/'iteration246'/f'{a}-{seed}-{half}.json.gz').read_bytes()));endpoints={e[k] for e in d['initial_graph'] for k in ['a','b']};assert endpoints==set(d['words']);init=[dict(zip(d['words'],p['labels'])) for p in d['initial_runs']];deletions=d['deletions'];presence=[set(p['partition']['words']) for p in deletions];maps=[dict(zip(p['partition']['words'],p['partition']['labels'])) if p['partition']['clusterable'] else {} for p in deletions];strictpairs={tuple(v) for c in d['cores'] for v in combinations(c['words'],2)};partitions+=len(init)+len(deletions)
                for pair in pairs:
                    u,v=pair;ic=sum(u in m and v in m and m[u]==m[v] for m in init);dp=sum(u in pp and v in pp for pp in presence);dc=sum(p['partition']['clusterable'] for p in deletions);co=sum(u in m and v in m and m[u]==m[v] for m in maps);evaluated=len(deletions)==31;expected=dict(author=a,seed=seed,half=half,pair=list(pair),initial_present={u,v}<=endpoints,initial_clusterable=len(endpoints)>=17,initial_coassigned_count=ic,initial_run_count=len(init),initial_all_coassigned=len(init)==31 and ic==31,deletion_evaluated=evaluated,deletion_present_count=dp,deletion_clusterable_count=dc,deletion_coassigned_count=co,deletion_all_present=evaluated and dp==31,deletion_all_clusterable=evaluated and dc==31,deletion_all_coassigned=evaluated and co==31,stored_strict=pair in strictpairs)
                    assert expected==lookup[a,seed,half,pair];assert expected['stored_strict']==(expected['initial_all_coassigned'] and expected['deletion_all_coassigned']);checked+=1
            for pair in pairs:
                rr=[lookup[a,seed,h,pair] for h in range(2)];expected=dict(author=a,seed=seed,pair=list(pair),**{f:rr[0][f] and rr[1][f] for f in FLAGS},strict=all(r['stored_strict'] for r in rr));assert expected==bb[a,seed,pair]
            assert sum(bb[a,seed,p]['strict'] for p in pairs)==previous[f'{a}-{seed}']['original_pairs_retained_both']
        rr=[r for r in records if r['author']==a];ss=[r for r in both if r['author']==a];cumulative={}
        for i,f in enumerate(FLAGS):cumulative[f]=sum(all(r[k] for k in FLAGS[:i+1]) for r in rr)
        expected=dict(halves=dict(pair_half_trials=len(rr),marginal={f:sum(r[f] for r in rr) for f in FLAGS},cumulative=cumulative,deletion_evaluated=sum(r['deletion_evaluated'] for r in rr),strict=sum(r['stored_strict'] for r in rr),initial_coassigned_count_histogram={str(k):v for k,v in sorted(Counter(r['initial_coassigned_count'] for r in rr if r['initial_present'] and r['initial_clusterable']).items())},deletion_present_count_histogram={str(k):v for k,v in sorted(Counter(r['deletion_present_count'] for r in rr if r['deletion_evaluated']).items())}),both_halves=dict(pair_split_trials=len(ss),marginal={f:sum(r[f] for r in ss) for f in FLAGS},strict=sum(r['strict'] for r in ss)))
        assert expected==summary[a]
    assert checked==len(records)==912 and len(both)==456;hashes=0
    for manifest in [read(O/'design-freeze.json')['inputs'],read(P/'iteration246/verification-manifest.json')]:
        for p,h in manifest.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h;hashes+=1
    result=dict(status='passed',pair_half_records=checked,pair_split_records=len(both),saved_partitions_inspected=partitions,author_summaries=5,hashes=hashes);(O/'independent-review.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
