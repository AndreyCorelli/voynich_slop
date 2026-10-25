"""Independent union-find graph reconstruction and matrix case-count replay."""
from benchmarks.grammar_case_components_iteration175 import *

def rebuild(dd):
    parent={};positions={};edges=set()
    def root(x):
        while parent[x]!=x:x=parent[x]
        return x
    for e in dd:
        if e['shared_frames']<2:continue
        a,b=e['a'],e['b'];parent.setdefault(a,a);parent.setdefault(b,b);parent[root(a)]=root(b);edges.add(tuple(sorted([a,b])))
        for f in e['frames']:
            positions.setdefault(a,set()).update(f['a_positions']);positions.setdefault(b,set()).update(f['b_positions'])
    groups={}
    for x in parent:groups.setdefault(root(x),[]).append(x)
    result=[]
    for types in sorted([sorted(v) for v in groups.values()]):
        result.append(dict(types=types,positions={x:sorted(positions[x]) for x in types},pairs=[dict(a=a,b=b,direct=(a,b) in edges) for a,b in combinations(types,2)]))
    return result

def matrices(component,tags,cases):
    types=component['types'];tot=np.zeros((2,len(types)),dtype=np.int64);counts=np.zeros((2,len(types),len(CASES)),dtype=np.int64);caseindex={c:i for i,c in enumerate(sorted(CASES))}
    for j,x in enumerate(types):
        for i in component['positions'][x]:
            k=int(tags[i] in {'PRON','DET'});tot[k,j]+=1
            if cases[i] in caseindex:counts[k,j,caseindex[cases[i]]]+=1
    recognized=counts.sum(axis=2);blocks={}
    for a in [0,1]:
        for b in [0,1]:blocks[a,b]=(np.outer(tot[a],tot[b]),np.outer(recognized[a],recognized[b]),counts[a]@counts[b].T)
    mapping={'both_pd':[(1,1)],'exactly_one_pd':[(0,1),(1,0)],'neither_pd':[(0,0)],'pd_involving':[(1,1),(0,1),(1,0)],'all':[(0,0),(0,1),(1,0),(1,1)]}
    return {g:[sum(blocks[k][i] for k in kk) for i in range(3)] for g,kk in mapping.items()}

def independent_summary(rows,cc):
    result={}
    for mode in MODES:
        result[mode]={};rr=[r for r in rows if mode=='all' or r['direct']==(mode=='direct')]
        for g in GROUPS:
            covered=[r for r in rr if r['stats'][g][1]];by={}
            for ci in range(len(cc)):
                fractions=[r['stats'][g][2]/r['stats'][g][1] for r in covered if r['component']==ci]
                if fractions:by[str(ci)]=dict(case_type_pairs=len(fractions),agreement=sum(fractions)/len(fractions))
            total,valid,match=[sum(r['stats'][g][i] for r in rr) for i in range(3)];means=[r['agreement'] for r in by.values()];types={r[k] for r in covered for k in ['a','b']}
            result[mode][g]=dict(components=len(cc),types=sum(len(c['types']) for c in cc),type_pairs=len(rr),case_components=len(by),case_type_pairs=len(covered),case_types=len(types),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=match,component_macro_agreement=sum(means)/len(means) if means else None,type_pair_macro_agreement=sum(sum(r['stats'][g][2]/r['stats'][g][1] for r in covered if r['component']==ci) for ci in range(len(cc)))/len(covered) if covered else None,pooled_agreement=match/valid if valid else None,component_details=by)
    return result

def run():
    hashes=records=views=0
    for name in ['design-freeze','components-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    graphs=load(OUT/'components.json');refs=load(ROOT/'iteration172/references.json');assignments=gzload(ROOT/'iteration174/case-assignments.json.gz');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');transforms={}
    for pool,p in POOLS.items():
        vv=load(p['descriptors'])[p['key']];vv=vv['5'] if p['nested'] else vv
        assert graphs[pool]=={v:rebuild(dd) for v,dd in vv.items()};transforms[pool]=load(p['transforms'])[p['key']]
    seen=set()
    with gzip.open(OUT/'scores.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);pool,view=row['pool'],row['view'];assert (pool,view) not in seen;seen.add((pool,view));cc=graphs[pool]['original' if view.startswith('case') else view];tt=refs[pool]['pos'];ca=refs[pool]['case']
            if view.startswith('case'):ca=assignments[pool][view]
            elif transforms[pool][view] is not None:
                ix=transforms[pool][view];tt=[tt[k] for k in ix];ca=[ca[k] for k in ix]
            expected=[]
            for ci,c in enumerate(cc):
                mm=matrices(c,tt,ca);indices={x:i for i,x in enumerate(c['types'])}
                for p in c['pairs']:
                    a,b=indices[p['a']],indices[p['b']];expected.append(dict(component=ci,**p,stats={g:[int(m[a,b]) for m in mm[g]] for g in GROUPS}));records+=1
            assert row['records']==expected
            assert summary[pool][view]==independent_summary(expected,cc)
            for g in GROUPS:
                for key in ['all_occurrence_pairs','case_occurrence_pairs','matching_case_pairs']:
                    ss=summary[pool][view];assert ss['all'][g][key]==ss['direct'][g][key]+ss['transitive'][g][key]
            views+=1
    assert seen=={(pool,v) for pool in POOLS for v in ['original',*('word'+str(s) for s in SEEDS),*('case'+str(s) for s in LABEL_SEEDS)]}
    for pool,vv in summary.items():
        for mode in MODES:
            for g in GROUPS:
                a=vv['original'][mode][g];x=a['component_macro_agreement'];assert contrasts[pool][mode][g]['actual']==a
                for name,vnames in [('word_null',['word'+str(s) for s in SEEDS]),('profile_null',['case'+str(s) for s in LABEL_SEEDS])]:
                    nn=[vv[v][mode][g]['component_macro_agreement'] for v in vnames if vv[v][mode][g]['case_type_pairs']]
                    assert contrasts[pool][mode][g][name]==dict(nonempty=len(nn),mean=sum(nn)/len(nn) if nn else None,min=min(nn) if nn else None,max=max(nn) if nn else None,at_least_actual=sum(y>=x for y in nn) if x is not None else None)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,graph_views_independently_rebuilt=34,assignment_views_verified=views,pair_records_independently_scored=records,all_components_positions_and_direct_flags=True,matrix_counts_and_independent_component_summaries=True,all_null_contrasts_and_pair_partitions=True))
    print('audit passed',views,records,flush=True)
if __name__=='__main__':run()
