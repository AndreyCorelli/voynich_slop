"""Fixed-graph, within-POS case-label permutation diagnostic."""
from benchmarks.grammar_case_subfamilies_iteration172 import *
import gzip
OUT=ROOT/'iteration174'
LABEL_SEEDS=list(range(17400,17599))

def gzsave(path,obj):
    with gzip.open(path,'wt') as f:json.dump(obj,f,separators=(',',':'))

def gzload(path):
    with gzip.open(path,'rt') as f:return json.load(f)

def grouped_positions(ids,tags):
    groups={}
    for i,(word,tag) in enumerate(zip(ids,tags)):groups.setdefault(word+'|'+tag,[]).append(i)
    return dict(sorted(groups.items()))

def permuted_cases(groups,cases,seed):
    result=list(cases);rng=np.random.default_rng(seed)
    for ix in groups.values():
        permutation=rng.permutation(len(ix))
        for j,k in enumerate(ix):result[k]=cases[ix[int(permutation[j])]]
    return result

def graph_positions(dd,tags):
    result={g:set() for g in GROUPS}
    for e in dd:
        for f in e['frames']:
            for a in f['a_positions']:
                for b in f['b_positions']:
                    k=family(tags[a],tags[b]);gg=['all',k]+(['pd_involving'] if k!='neither_pd' else [])
                    for g in gg:result[g].update([a,b])
    return {g:sorted(pp) for g,pp in result.items()}

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_subfamilies_iteration172.py'),ROOT/'iteration173/verification-manifest.json',ROOT/'iteration172/references.json',ROOT/'iteration172/summary.json']+[p['descriptors'] for p in POOLS.values()]+[ROOT/'iteration164/streams.json',ROOT/'iteration168/streams.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},seeds=LABEL_SEEDS,design='Same two original floor5/two-frame graphs, exact172 references. Primary both_pd; all five172 strata unchanged. 199 fixed seeds17400..17598. Within each pool, group token indices by opaque word ID plus exact POS, sorted string keys; numpy default_rng per seed, permute all case labels within every group including missing/unrecognized and singleton groups. Word/POS case inventories preserved, not merely POS inventory. Freeze assignments, group indices/inventories and graph-relevant-position sets before score computation; detailed scores before aggregation. Report all-group and stratum unique graph positions, potentially movable positions whose word/POS group has >1 distinct case label, recognized-original movable positions, actual changed-position counts for every seed and ranges. Evaluate with166 weighting, empty groups retained; corrected conditional tail same173 only all199 controls nonempty. Exact172 original baseline and independent profile/movement/replay audit required. No new annotations/reserves/sealed data or deployable POS/case/nuclei predictor. Null tests occurrence-context information beyond empirical word/POS case profiles; invariance or high null scores do not negate useful type grouping. No seed/edge/outcome selection.'))
    refs=load(ROOT/'iteration172/references.json');assignments={};inventory={};movement={};group_inputs={};graphs={}
    for pool,p in POOLS.items():
        r=refs[pool];key='Cicero' if pool=='earlier' else 'fit-Cicero';ids=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key];groups=grouped_positions(ids,r['pos']);group_inputs[pool]=groups
        dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd;graphs[pool]=[e for e in dd['original'] if e['shared_frames']>=2]
        assignments[pool]={'original':r['case'],**{'case'+str(seed):permuted_cases(groups,r['case'],seed) for seed in LABEL_SEEDS}}
        inventory[pool]={k:dict(Counter(r['case'][i] for i in ix)) for k,ix in groups.items()}
        movable={i for k,ix in groups.items() if len(inventory[pool][k])>1 for i in ix};positions=graph_positions(graphs[pool],r['pos']);movement[pool]={}
        for g,pp in positions.items():
            movement[pool][g]=dict(positions=pp,graph_positions=len(pp),potentially_movable=sum(i in movable for i in pp),recognized_original_movable=sum(i in movable and r['case'][i] in CASES for i in pp),changed_by_seed={'case'+str(seed):sum(assignments[pool]['case'+str(seed)][i]!=r['case'][i] for i in pp) for seed in LABEL_SEEDS})
    gzsave(OUT/'case-assignments.json.gz',assignments);save(OUT/'inventory.json',inventory);save(OUT/'group-inputs.json',group_inputs);save(OUT/'movement.json',movement);save(OUT/'assignment-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['case-assignments.json.gz','inventory.json','group-inputs.json','movement.json']}));details={}
    for pool in POOLS:details[pool]={view:score(graphs[pool],cc,refs[pool]['pos']) for view,cc in assignments[pool].items()}
    gzsave(OUT/'details.json.gz',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json.gz'):digest(OUT/'details.json.gz')}))
    summary={pool:{v:{g:summarize_cases(rows,588 if pool=='earlier' else 857)['2'] for g,rows in gg.items()} for v,gg in vv.items()} for pool,vv in details.items()};contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for g in GROUPS:
            a=vv['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[vv['case'+str(s)][g]['edge_macro_frame_case_agreement'] for s in LABEL_SEEDS if vv['case'+str(s)][g]['case_edges']];tail=sum(y>=x for y in nn) if x is not None else None
            contrasts[pool][g]=dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_min=min(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=tail,conditional_tail=(1+tail)/(1+len(LABEL_SEEDS)) if x is not None and len(nn)==len(LABEL_SEEDS) else None,min_null_case_edges=min(vv['case'+str(s)][g]['case_edges'] for s in LABEL_SEEDS),max_null_case_edges=max(vv['case'+str(s)][g]['case_edges'] for s in LABEL_SEEDS))
        print(pool,json.dumps(contrasts[pool]),flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
