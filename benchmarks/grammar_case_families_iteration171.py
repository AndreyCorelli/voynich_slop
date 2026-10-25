"""Reference-only occurrence POS family stratification of fixed case graphs."""
from benchmarks.grammar_context_concentration_iteration170 import *
OUT=ROOT/'iteration171'
PD={'PRON','DET'}
NOMINAL={'NOUN','PROPN','ADJ','NUM'}
GROUPS=['all','pd_involving','neither_pd','both_nominal','other_neither']

def family(a,b):
    if a in PD or b in PD:return 'pd_involving'
    return 'both_nominal' if a in NOMINAL and b in NOMINAL else 'other_neither'

def score(dd,cases,tags):
    result={g:[] for g in GROUPS}
    for e in dd:
        counts={g:[] for g in GROUPS}
        for f in e['frames']:
            row={g:[0,0,0] for g in GROUPS}
            for a in f['a_positions']:
                for b in f['b_positions']:
                    k=family(tags[a],tags[b]);groups=['all',k]+(['neither_pd'] if k!='pd_involving' else [])
                    valid=cases[a] in CASES and cases[b] in CASES
                    for g in groups:
                        row[g][0]+=1;row[g][1]+=int(valid);row[g][2]+=int(valid and cases[a]==cases[b])
            for g in GROUPS:counts[g].append(row[g])
        for g,rows in counts.items():
            fractions=[m/v for n,v,m in rows if v];total,valid,matched=[sum(r[k] for r in rows) for k in range(3)]
            result[g].append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=len(fractions),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fractions)/len(fractions) if fractions else None,no_case_conflicts=matched==valid if valid else None))
    return result

def references(pool):
    source=load(ROOT/'iteration44/annotations-truth.json')
    selection=load(ROOT/('iteration159' if pool=='earlier' else 'iteration168')/'selection.json')
    key='Cicero' if pool=='earlier' else 'fit-Cicero'
    tt=[t for sid in selection[key]['sent_ids'] for t in source[sid]['tokens']]
    return [t['pos'] for t in tt],[t.get('case','') for t in tt]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration170/verification-manifest.json',ROOT/'iteration159/selection.json',ROOT/'iteration168/selection.json',ROOT/'iteration44/annotations-truth.json']+[p[n] for p in POOLS.values() for n in ['descriptors','cases','transforms']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Unchanged floor5 two-distinct-frame graphs, both Cicero pools, all sixteen existing shuffles. Occurrence Cartesian pairs stratified before case scoring: PD if either POS PRON/DET; neither otherwise; within neither both_nominal if both NOUN/PROPN/ADJ/NUM, other_neither otherwise. These three disjoint leaves partition all pairs; neither is union of latter two. No majority POS/type assignment, no label filter for inference, no graph edits. Within each group keep recognized-case pairs, average within frame then covered frames then covered edges exactly166. Report ALL groups, empty/sparse controls, coverage, pooled counts, null maxima/tails. Denominators all graph edges/frames retained: applicability includes family membership. Same edge may appear in multiple strata due occurrence ambiguity; macro means not additive. Exact all-group baseline and pair-count partition identities required. Freeze references then detailed scores before summaries. No new annotations/reserve/sealed data; conditional concentration diagnostic, not POS or named-case predictor.'))
    refs={p:dict(zip(['pos','case'],references(p))) for p in POOLS}
    for pool,p in POOLS.items():assert refs[pool]['case']==load(p['cases'])[p['key']]
    save(OUT/'references.json',refs);save(OUT/'reference-freeze.json',dict(inputs={str(OUT/'references.json'):digest(OUT/'references.json')}));details={}
    for pool,p in POOLS.items():
        vv=load(p['descriptors'])[p['key']];vv=vv['5'] if p['nested'] else vv;trans=load(p['transforms'])[p['key']];details[pool]={}
        for v,dd in vv.items():
            ix=trans[v];cc=refs[pool]['case'];tt=refs[pool]['pos']
            if ix is not None:cc=[cc[k] for k in ix];tt=[tt[k] for k in ix]
            details[pool][v]=score([e for e in dd if e['shared_frames']>=2],cc,tt)
    save(OUT/'details.json',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json'):digest(OUT/'details.json')}))
    summary={pool:{v:{g:summarize_cases(rows,588 if pool=='earlier' else 857)['2'] for g,rows in gg.items()} for v,gg in vv.items()} for pool,vv in details.items()};contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for g in GROUPS:
            a=vv['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[vv['word'+str(s)][g]['edge_macro_frame_case_agreement'] for s in SEEDS if vv['word'+str(s)][g]['case_edges']]
            contrasts[pool][g]=dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=sum(y>=x for y in nn) if x is not None else None)
        print(pool,json.dumps(contrasts[pool]),flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
