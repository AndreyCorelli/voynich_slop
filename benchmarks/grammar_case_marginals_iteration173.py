"""Fixed-graph, within-POS case-label permutation diagnostic."""
from benchmarks.grammar_case_subfamilies_iteration172 import *
import gzip
OUT=ROOT/'iteration173'
LABEL_SEEDS=list(range(17300,17499))

def gzsave(path,obj):
    with gzip.open(path,'wt') as f:json.dump(obj,f,separators=(',',':'))

def gzload(path):
    with gzip.open(path,'rt') as f:return json.load(f)

def permuted_cases(tags,cases,seed):
    result=list(cases);rng=np.random.default_rng(seed)
    for tag in sorted(set(tags)):
        ix=[i for i,t in enumerate(tags) if t==tag];permutation=rng.permutation(len(ix))
        for j,k in enumerate(ix):result[k]=cases[ix[int(permutation[j])]]
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_subfamilies_iteration172.py'),ROOT/'iteration172/verification-manifest.json',ROOT/'iteration172/references.json',ROOT/'iteration172/summary.json']+[p['descriptors'] for p in POOLS.values()]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},seeds=LABEL_SEEDS,design='Same two original floor5/two-frame graphs, exact172 POS/case references. Original plus199 fixed label permutations seeds17300..17498. For each seed and pool, numpy default_rng; sorted POS inventory; permute case labels among ALL tokens of each exact POS, including missing/unrecognized labels. Word identity, token positions, POS and graph unchanged. No text shuffles or label-based graph selection; no training, new annotations, reserve or sealed data. Freeze all case assignments before score computation; gzip detailed scores before aggregates. Five fixed172 strata and166 weighting unchanged; all empty groups and changing case coverage retained. Compare actual to nonempty null mean/max and count>=actual; (1+count)/(1+199) only when all199 nulls and actual nonempty, descriptive conditional randomization tail, not fresh validation. Primary both_pd; others fixed descriptive controls. Verify exact original172 baseline and within-POS inventories. Token-case null destroys word-specific morphology, so rejecting it alone does not isolate contextual utility beyond word-type case frequencies or create a predictor.'))
    refs=load(ROOT/'iteration172/references.json');assignments={};inventory={}
    for pool,r in refs.items():
        assignments[pool]={'original':r['case'],**{'case'+str(s):permuted_cases(r['pos'],r['case'],s) for s in LABEL_SEEDS}}
        inventory[pool]={t:dict(Counter(c for tag,c in zip(r['pos'],r['case']) if tag==t)) for t in sorted(set(r['pos']))}
    gzsave(OUT/'case-assignments.json.gz',assignments);save(OUT/'inventory.json',inventory);save(OUT/'assignment-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['case-assignments.json.gz','inventory.json']}));details={}
    for pool,p in POOLS.items():
        dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;primary=[e for e in dd['original'] if e['shared_frames']>=2]
        details[pool]={view:score(primary,cc,refs[pool]['pos']) for view,cc in assignments[pool].items()}
    gzsave(OUT/'details.json.gz',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json.gz'):digest(OUT/'details.json.gz')}))
    summary={pool:{v:{g:summarize_cases(rows,588 if pool=='earlier' else 857)['2'] for g,rows in gg.items()} for v,gg in vv.items()} for pool,vv in details.items()};contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for g in GROUPS:
            a=vv['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[vv['case'+str(s)][g]['edge_macro_frame_case_agreement'] for s in LABEL_SEEDS if vv['case'+str(s)][g]['case_edges']];tail=sum(y>=x for y in nn) if x is not None else None
            contrasts[pool][g]=dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=tail,conditional_tail=(1+tail)/(1+len(LABEL_SEEDS)) if x is not None and len(nn)==len(LABEL_SEEDS) else None,min_null_case_edges=min(vv['case'+str(s)][g]['case_edges'] for s in LABEL_SEEDS),max_null_case_edges=max(vv['case'+str(s)][g]['case_edges'] for s in LABEL_SEEDS))
        print(pool,json.dumps(contrasts[pool]),flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
