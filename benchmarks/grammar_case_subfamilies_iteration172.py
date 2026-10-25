"""Reference-only occurrence POS family stratification of fixed case graphs."""
from benchmarks.grammar_context_concentration_iteration170 import *
from itertools import combinations_with_replacement
OUT=ROOT/'iteration172'
PD={'PRON','DET'}
TAGS=sorted({'ADJ','ADP','ADV','AUX','CCONJ','DET','INTJ','NOUN','NUM','PART','PRON','PROPN','PUNCT','SCONJ','SYM','VERB','X'})
PAIR_KEYS=['/'.join(p) for p in combinations_with_replacement(TAGS,2)]
GROUPS=['all','pd_involving','both_pd','exactly_one_pd','neither_pd']

def family(a,b):
    n=int(a in PD)+int(b in PD)
    return ['neither_pd','exactly_one_pd','both_pd'][n]

def composition(dd,cases,tags):
    rows={k:dict(all_pairs=0,case_pairs=0,matching_cases=0) for k in PAIR_KEYS}
    for e in dd:
        for f in e['frames']:
            for a in f['a_positions']:
                for b in f['b_positions']:
                    r=rows['/'.join(sorted([tags[a],tags[b]]))];r['all_pairs']+=1
                    if cases[a] in CASES and cases[b] in CASES:
                        r['case_pairs']+=1;r['matching_cases']+=int(cases[a]==cases[b])
    return rows

def score(dd,cases,tags):
    result={g:[] for g in GROUPS}
    for e in dd:
        counts={g:[] for g in GROUPS}
        for f in e['frames']:
            row={g:[0,0,0] for g in GROUPS}
            for a in f['a_positions']:
                for b in f['b_positions']:
                    k=family(tags[a],tags[b]);groups=['all',k]+(['pd_involving'] if k!='neither_pd' else [])
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
    paths=[Path(__file__),ROOT/'iteration171/verification-manifest.json',ROOT/'iteration159/selection.json',ROOT/'iteration168/selection.json',ROOT/'iteration44/annotations-truth.json']+[p[n] for p in POOLS.values() for n in ['descriptors','cases','transforms']]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Fixed171 graphs, references and sixteen shuffles. Partition occurrence pairs into both PRON/DET, exactly one PRON/DET, neither; all and PD-involving unions are historical controls. Same166 case/frame/edge macro scoring and all-graph applicability; no graph filtering. Exact unordered POS pair composition pooled all/eligible/matching counts for ALL153 combinations of fixed17 UD tags, including zeros, not macro scores or endpoint direction. Assert inventory fits fixed tags before evaluation. Freeze references before detailed scores and composition; then summaries/null contrasts. Independent pair partitions and exact historical all/PD/neither baselines. No inference labels, new annotations, reserve or sealed data; diagnostic of within-family substitution versus cross-family case compatibility, not morphological agreement or links between co-occurring endpoints.'))
    refs={p:dict(zip(['pos','case'],references(p))) for p in POOLS}
    for pool,p in POOLS.items():assert refs[pool]['case']==load(p['cases'])[p['key']]
    save(OUT/'references.json',refs);save(OUT/'reference-freeze.json',dict(inputs={str(OUT/'references.json'):digest(OUT/'references.json')}));details={};compositions={}
    for pool,p in POOLS.items():
        vv=load(p['descriptors'])[p['key']];vv=vv['5'] if p['nested'] else vv;trans=load(p['transforms'])[p['key']];details[pool]={};compositions[pool]={}
        assert set(refs[pool]['pos'])<=set(TAGS)
        for v,dd in vv.items():
            ix=trans[v];cc=refs[pool]['case'];tt=refs[pool]['pos']
            if ix is not None:cc=[cc[k] for k in ix];tt=[tt[k] for k in ix]
            primary=[e for e in dd if e['shared_frames']>=2];details[pool][v]=score(primary,cc,tt);compositions[pool][v]=composition(primary,cc,tt)
    save(OUT/'details.json',details);save(OUT/'composition.json',compositions);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['details.json','composition.json']}))
    summary={pool:{v:{g:summarize_cases(rows,588 if pool=='earlier' else 857)['2'] for g,rows in gg.items()} for v,gg in vv.items()} for pool,vv in details.items()};contrasts={}
    for pool,vv in summary.items():
        contrasts[pool]={}
        for g in GROUPS:
            a=vv['original'][g];x=a['edge_macro_frame_case_agreement'];nn=[vv['word'+str(s)][g]['edge_macro_frame_case_agreement'] for s in SEEDS if vv['word'+str(s)][g]['case_edges']]
            contrasts[pool][g]=dict(actual=a,null_with_case=len(nn),null_mean=sum(nn)/len(nn) if nn else None,null_max=max(nn) if nn else None,null_at_least_actual=sum(y>=x for y in nn) if x is not None else None)
        print(pool,json.dumps(contrasts[pool]),flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
