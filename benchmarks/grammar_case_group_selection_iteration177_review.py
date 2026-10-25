"""Independent ranking, tie inclusion, selection aggregation and baseline audit."""
from benchmarks.grammar_case_components_iteration175_review import independent_summary
from benchmarks.grammar_case_group_selection_iteration177 import *

def run():
    hashes=views=metricgroups=0
    for name in ['design-freeze','selection-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h;hashes+=1
    graphs=load(ROOT/'iteration176/components.json');features=load(OUT/'features.json');selections=load(OUT/'selections.json');boundaries=load(OUT/'boundaries.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json');baseline=load(ROOT/'iteration176/summary.json')
    for pool,p in POOLS.items():
        key='Cicero' if pool=='earlier' else 'fit-Cicero';stream=load(ROOT/('iteration164' if pool=='earlier' else 'iteration168')/'streams.json')[key];counts=Counter(stream);dd=load(p['descriptors'])[p['key']];dd=dd['5'] if p['nested'] else dd
        for view,cc in graphs[pool].items():
            strengths={frozenset([e['a'],e['b']]):e['shared_frames'] for e in dd[view] if e['shared_frames']>=2};expected=[]
            for i,c in enumerate(cc):
                f=sum(math.log(counts[x]) for x in c['types'])/len(c['types']);direct=[r for r in c['pairs'] if r['direct']];s=sum(math.log(strengths[frozenset([r['a'],r['b']])]) for r in direct)/len(direct);expected.append(dict(component=i,frequency=f,support=s,combined=f+s))
            assert expected==features[pool][view];assert selections[pool][view]['all']==list(range(len(cc)))
            for rank in ['frequency','support','combined']:
                ordered=sorted(range(len(cc)),key=lambda i:expected[i][rank],reverse=True)
                for k in [10,20,40]:
                    name=rank+str(k);cut=expected[ordered[min(k,len(cc))-1]][rank] if cc else None;indices=sorted(i for i in ordered if expected[i][rank]>=cut)
                    assert selections[pool][view][name]==indices
                    assert boundaries[pool][view][name]==dict(requested=k,selected=len(indices),threshold=cut,ties_at_boundary=sum(r[rank]==cut for r in expected))
    with gzip.open(ROOT/'iteration176/scores.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);pool,view=row['pool'],row['view'];gv='original' if view.startswith('case') else view;cc=graphs[pool][gv]
            for name,indices in selections[pool][gv].items():
                index={old:new for new,old in enumerate(indices)};rr=[dict(r,component=index[r['component']]) for r in row['records'] if r['component'] in index];small=[cc[i] for i in indices];independent=independent_summary(rr,small)
                for mode in MODES:
                    for g in GROUPS:
                        r=independent[mode][g];r['case_component_applicability']=len(r['component_details'])/len(indices) if indices else None;r['case_pair_applicability']=r['case_occurrence_pairs']/r['all_occurrence_pairs'] if r['all_occurrence_pairs'] else None;r['component_joint_yield']=sum(v['agreement'] for v in r['component_details'].values())/len(indices) if indices else None;r['matching_pairs_per_all_pairs']=r['matching_case_pairs']/r['all_occurrence_pairs'] if r['all_occurrence_pairs'] else None
                        assert r==summary[pool][view][name][mode][g];metricgroups+=1
                        if name=='all':
                            old={k:v for k,v in r.items() if k not in ['case_component_applicability','case_pair_applicability','component_joint_yield','matching_pairs_per_all_pairs']};assert old==baseline[pool][view][mode][g]
            views+=1
    for pool,vv in summary.items():
        for name,ss in vv['original'].items():
            for metric in ['component_macro_agreement','case_component_applicability','component_joint_yield','case_pair_applicability','matching_pairs_per_all_pairs']:
                actual=ss['all']['all'][metric];assert contrasts[pool][name][metric]['actual']==actual
                for label,names in [('word_null',['word'+str(s) for s in SEEDS]),('profile_null',['case'+str(s) for s in LABEL_SEEDS])]:
                    nn=[vv[v][name]['all']['all'][metric] for v in names if vv[v][name]['all']['all'][metric] is not None]
                    assert contrasts[pool][name][metric][label]==dict(nonempty=len(nn),mean=sum(nn)/len(nn) if nn else None,min=min(nn) if nn else None,max=max(nn) if nn else None,at_least_actual=sum(x>=actual for x in nn) if actual is not None else None)
    save(OUT/'audit.json',dict(input_selection_hashes_verified=hashes,graph_rankings_verified=34,assignment_views_verified=views,selected_metric_groups_verified=metricgroups,all_ties_and_no_label_selection_verified=True,all_baselines_exact=True,all_null_contrasts_verified=True))
    print('audit passed',views,metricgroups,flush=True)
if __name__=='__main__':run()
