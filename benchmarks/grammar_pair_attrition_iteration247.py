"""Post-hoc stage attribution for every original pair in frozen random halves."""
from pathlib import Path
from collections import Counter
from itertools import combinations
import gzip,json,hashlib
P=Path('experiments/results/grammar-restoration');O=P/'iteration247';AA=['Aquinas','Caesar','Cicero','Jerome','Dante']
FLAGS=['initial_present','initial_clusterable','initial_all_coassigned','deletion_all_present','deletion_all_clusterable','deletion_all_coassigned']
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def summarize(rr):
    cumulative={};keep=rr
    for flag in FLAGS:
        keep=[r for r in keep if r[flag]];cumulative[flag]=len(keep)
    return dict(pair_half_trials=len(rr),marginal={flag:sum(r[flag] for r in rr) for flag in FLAGS},cumulative=cumulative,deletion_evaluated=sum(r['deletion_evaluated'] for r in rr),strict=sum(r['stored_strict'] for r in rr),initial_coassigned_count_histogram=dict(sorted(Counter(r['initial_coassigned_count'] for r in rr if r['initial_present'] and r['initial_clusterable']).items())),deletion_present_count_histogram=dict(sorted(Counter(r['deletion_present_count'] for r in rr if r['deletion_evaluated']).items())))
def run():
    assert not O.exists();O.mkdir();(O/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),P/'iteration238/cores.json',P/'iteration246/results.json',P/'iteration246/verification-manifest.json'];save(O/'design-freeze.json',dict(inputs={str(p):sha(p) for p in paths},authors=AA,flags=FLAGS,interpretation='posthoc mechanism diagnostic; marginals plus cumulative in listed order; unevaluated deletions fail conjunction'))
    for p,h in read(P/'iteration246/verification-manifest.json').items():assert sha(Path(p))==h
    old=read(P/'iteration238/cores.json');previous=read(P/'iteration246/results.json');records=[];both=[];summary={}
    for a in AA:
        pairs=[list(v) for c in old[a] for v in combinations(c['words'],2)]
        for seed in range(24600,24619):
            perhalf=[]
            for half in [0,1]:
                d=json.loads(gzip.decompress((P/'iteration246'/f'{a}-{seed}-{half}.json.gz').read_bytes()));ix={w:i for i,w in enumerate(d['words'])};coremap={w:j for j,c in enumerate(d['cores']) for w in c['words']};deletions=d['deletions'];rows=[]
                for pair in pairs:
                    u,v=pair;present=u in ix and v in ix;ic=sum(present and r['labels'][ix[u]]==r['labels'][ix[v]] for r in d['initial_runs']);dp=[];dc=[];co=[]
                    for r in deletions:
                        p=r['partition'];pi={w:i for i,w in enumerate(p['words'])};has=u in pi and v in pi;dp.append(has);dc.append(p['clusterable']);co.append(bool(has and p['clusterable'] and p['labels'][pi[u]]==p['labels'][pi[v]]))
                    evaluated=len(deletions)==31;row=dict(author=a,seed=seed,half=half,pair=pair,initial_present=present,initial_clusterable=d['clusterable'],initial_coassigned_count=ic,initial_run_count=len(d['initial_runs']),initial_all_coassigned=bool(present and len(d['initial_runs'])==31 and ic==31),deletion_evaluated=evaluated,deletion_present_count=sum(dp),deletion_clusterable_count=sum(dc),deletion_coassigned_count=sum(co),deletion_all_present=evaluated and all(dp),deletion_all_clusterable=evaluated and all(dc),deletion_all_coassigned=evaluated and all(co),stored_strict=bool(u in coremap and v in coremap and coremap[u]==coremap[v]))
                    assert row['stored_strict']==(row['initial_all_coassigned'] and row['deletion_all_coassigned']);rows.append(row);records.append(row)
                perhalf.append(rows)
            for j,pair in enumerate(pairs):
                flags={f:all(rows[j][f] for rows in perhalf) for f in FLAGS};strict=all(rows[j]['stored_strict'] for rows in perhalf);both.append(dict(author=a,seed=seed,pair=pair,**flags,strict=strict))
            assert sum(x['strict'] for x in both if x['author']==a and x['seed']==seed)==previous[f'{a}-{seed}']['original_pairs_retained_both']
        rr=[r for r in records if r['author']==a];bb=[r for r in both if r['author']==a];summary[a]=dict(halves=summarize(rr),both_halves=dict(pair_split_trials=len(bb),marginal={f:sum(r[f] for r in bb) for f in FLAGS},strict=sum(r['strict'] for r in bb)))
    save(O/'pair-half-records.json',records);save(O/'pair-split-records.json',both);save(O/'summary.json',summary)
    for a,r in summary.items():print(a,json.dumps(r),flush=True)
if __name__=='__main__':run()
