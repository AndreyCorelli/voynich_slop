"""Independent unique-bundle rankings, tie policy and full summary replay."""
from benchmarks.grammar_case_pair_selection_iteration178 import *

def independent_metrics(rows,eligible):
    covered=[r for r in rows if r['case_occurrence_pairs']];types={r[k] for r in rows for k in ['a','b']};ctypes={r[k] for r in covered for k in ['a','b']};n=len(rows);nc=len(covered);frames=sum(r['shared_frames'] for r in rows);cf=sum(r['case_frames'] for r in rows);pairs=sum(r['all_occurrence_pairs'] for r in rows);valid=sum(r['case_occurrence_pairs'] for r in rows);match=sum(r['matching_case_pairs'] for r in rows);nonconflict=sum(r['no_case_conflicts'] for r in covered);total=sum(r['frame_macro_case_agreement'] for r in covered)
    return dict(edges=n,case_edges=nc,edge_applicability=nc/n if n else None,frames=frames,case_frames=cf,frame_applicability=cf/frames if frames else None,all_occurrence_pairs=pairs,case_occurrence_pairs=valid,pair_applicability=valid/pairs if pairs else None,matching_case_pairs=match,edge_macro_frame_case_agreement=total/nc if nc else None,pooled_case_agreement=match/valid if valid else None,no_case_conflict_edges=nonconflict,no_case_conflict_fraction=nonconflict/nc if nc else None,types_involved=len(types),case_types_involved=len(ctypes),eligible_types=eligible,case_type_coverage=len(ctypes)/eligible,edge_joint_yield=total/n if n else None,matching_pairs_per_all_pairs=match/pairs if pairs else None)

def run():
    hashes=groups=views=0
    for name in ['design-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    features=load(OUT/'features.json');selections=load(OUT/'selections.json');boundaries=load(OUT/'boundaries.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');old=load(ROOT/'iteration172/details.json');profile=gzload(ROOT/'iteration174/details.json.gz');baseword=load(ROOT/'iteration172/summary.json');baseprofile=load(ROOT/'iteration174/summary.json')
    for pool,p in POOLS.items():
        key='Cicero' if pool=='earlier' else 'fit-Cicero';counts=Counter(load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key]);dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd
        for view,ee in dd.items():
            ee=[e for e in ee if e['shared_frames']>=2];assert len({frozenset([e['a'],e['b']]) for e in ee})==len(ee);expected=[]
            for i,e in enumerate(ee):
                f=sum([math.log(counts[e['a']]),math.log(counts[e['b']])])/2;s=math.log(e['shared_frames']);expected.append(dict(edge=i,a=e['a'],b=e['b'],shared_frames=e['shared_frames'],frequency=f,support=s,combined=f+s))
            assert expected==features[pool][view];assert selections[pool][view]['all']==list(range(len(ee)))
            for rank in ['frequency','support','combined']:
                order=sorted(range(len(ee)),key=lambda i:expected[i][rank],reverse=True)
                for k in [10,20,40]:
                    cut=expected[order[min(k,len(ee))-1]][rank] if ee else None;ix=sorted(i for i in order if expected[i][rank]>=cut);name=rank+str(k)
                    assert selections[pool][view][name]==ix;assert boundaries[pool][view][name]==dict(requested=k,selected=len(ix),threshold=cut,ties_at_boundary=sum(r[rank]==cut for r in expected))
        assert old[pool]['original']==profile[pool]['original'];allrows={**old[pool],**profile[pool]}
        for view,gg in allrows.items():
            gv='original' if view.startswith('case') else view
            for name,ix in selections[pool][gv].items():
                for g,rr in gg.items():
                    computed=independent_metrics([rr[i] for i in ix],588 if pool=='earlier' else 857);assert computed==summary[pool][view][name][g];groups+=1
                    if name=='all':
                        historical=(baseprofile if view.startswith('case') else baseword)[pool][view][g];assert {k:v for k,v in computed.items() if k not in ['edge_joint_yield','matching_pairs_per_all_pairs']}==historical
            views+=1
        vv=summary[pool]
        for name,gg in vv['original'].items():
            for metric in METRICS:
                actual=gg['all'][metric];assert contrasts[pool][name][metric]['actual']==actual
                for label,names in [('word_null',['word'+str(s) for s in SEEDS]),('profile_null',['case'+str(s) for s in LABEL_SEEDS])]:
                    nn=[vv[v][name]['all'][metric] for v in names if vv[v][name]['all'][metric] is not None];assert contrasts[pool][name][metric][label]==dict(nonempty=len(nn),mean=sum(nn)/len(nn) if nn else None,min=min(nn) if nn else None,max=max(nn) if nn else None,at_least_actual=sum(x>=actual for x in nn) if actual is not None else None)
    save(OUT/'audit.json',dict(input_selection_hashes_verified=hashes,graph_rankings_verified=34,assignment_views_verified=views,selected_stratum_metric_groups_verified=groups,unique_pairs_and_tie_inclusion_verified=True,all172_174_baselines_exact=True,all_null_contrasts_verified=True))
    print('audit passed',views,groups,flush=True)
if __name__=='__main__':run()
