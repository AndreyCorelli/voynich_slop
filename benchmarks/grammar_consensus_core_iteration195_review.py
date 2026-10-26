"""Independent per-candidate unanimity and scalar coverage/case metric replay."""
from benchmarks.grammar_consensus_core_iteration195 import OUT,SOURCE,BASE,AUTHORS,Path,load,save,digest
from benchmarks.grammar_case_applicability_iteration180_review import close

def scalar_metrics(rows,eligible):
    n=len(rows);covered=[r for r in rows if r['case_occurrence_pairs']>0];nc=len(covered);ntypes=set();ctypes=set()
    for r in rows:
        ntypes.update([r['a'],r['b']])
        if r['case_occurrence_pairs']:ctypes.update([r['a'],r['b']])
    frames=sum(r['shared_frames'] for r in rows);cf=sum(r['case_frames'] for r in rows);pairs=sum(r['all_occurrence_pairs'] for r in rows);valid=sum(r['case_occurrence_pairs'] for r in rows);matched=sum(r['matching_case_pairs'] for r in rows);total=sum(r['frame_macro_case_agreement'] for r in covered);clean=sum(bool(r['no_case_conflicts']) for r in covered)
    return dict(edges=n,case_edges=nc,edge_applicability=nc/n if n else None,frames=frames,case_frames=cf,frame_applicability=cf/frames if frames else None,all_occurrence_pairs=pairs,case_occurrence_pairs=valid,pair_applicability=valid/pairs if pairs else None,matching_case_pairs=matched,edge_macro_frame_case_agreement=total/nc if nc else None,pooled_case_agreement=matched/valid if valid else None,no_case_conflict_edges=clean,no_case_conflict_fraction=clean/nc if nc else None,types_involved=len(ntypes),case_types_involved=len(ctypes),eligible_types=eligible,case_type_coverage=len(ctypes)/eligible if eligible else None,edge_joint_yield=total/n if n else None,matching_pairs_per_all_pairs=matched/pairs if pairs else None)

def run():
    assert not (OUT/'audit.json').exists();hashes=0
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(Path(p))==h;hashes+=1
    for p,h in load(OUT/'selection-freeze.json').items():assert digest(OUT/p)==h;hashes+=1
    for p,h in load(SOURCE/'verification-manifest.json').items():assert digest(Path(p))==h;hashes+=1
    pred=load(SOURCE/'predictions.json');trials=load(SOURCE/'trials.json');rr=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');selection=load(OUT/'selections.json');membership=load(OUT/'membership.json');views=load(OUT/'views.json');summary=load(OUT/'summary.json');details=load(OUT/'details.json');comparisons=load(OUT/'comparisons.json');old=load(SOURCE/'summary.json');ncandidates=groups=0
    for a in AUTHORS:
        n=len(rr[a]);nviews=len(pred[a]);expected={k:[] for k in ['rich_baseline','control_baseline','rich_core','control_core','both_core']};assert views[a]==dict(trials=list(pred[a]),unique_nonempty_source_sets=len({tuple(t['source_authors']) for t in trials[a].values()}))
        supports=[]
        # Candidate-by-candidate rank test, never intersect saved selections.
        for i in range(n):
            yes={}
            for model in ['rich','frequency_support']:
                yes[model]=[v for v,mm in pred[a].items() if sum(p>mm[model][i] for p in mm[model])<10]
                base=pred[a]['baseline'][model]
                if sum(p>base[i] for p in base)<10:expected['rich_baseline' if model=='rich' else 'control_baseline'].append(i)
            inrich=len(yes['rich'])==nviews;incontrol=len(yes['frequency_support'])==nviews
            if inrich:expected['rich_core'].append(i)
            if incontrol:expected['control_core'].append(i)
            if inrich and incontrol:expected['both_core'].append(i)
            supports.append(dict(edge=i,rich_views=yes['rich'],control_views=yes['frequency_support']));ncandidates+=1
        assert expected==selection[a];assert supports==membership[a]
        positive=[bool(r['case_occurrence_pairs']) for r in rr[a]];available=sum(positive);alltypes={r[k] for r in rr[a] for k in ['a','b']}
        for policy,ix in expected.items():
            rows=[rr[a][i] for i in ix];metric=scalar_metrics(rows,sizes[a]['types']);tp=sum(positive[i] for i in ix)
            s=dict(metrics=metric,false_positives=len(ix)-tp,available_applicable_pairs=available,applicable_pair_recall=tp/available if available else None,all_candidates=n,candidate_retention=len(ix)/n if n else None,type_retention=metric['types_involved']/len(alltypes) if alltypes else None);close(s,summary[a][policy])
            assert details[a][policy]==[dict(edge=i,applicable=positive[i],**rr[a][i]) for i in ix]
            for baseline in ['rich_baseline','control_baseline']:
                bx=expected[baseline];retained=[i for i in bx if i in ix];removed=[i for i in bx if i not in ix];den=sum(positive[i] for i in bx);useful=sum(positive[i] for i in retained)
                c=dict(retained_baseline_pairs=len(retained),removed_baseline_pairs=len(removed),retained_useful_pairs=useful,lost_useful_pairs=sum(positive[i] for i in removed),removed_false_positives=sum(not positive[i] for i in removed),useful_retention=useful/den if den else None);close(c,comparisons[a][policy][baseline])
            groups+=1
        for name,model in [('rich_baseline','rich'),('control_baseline','frequency_support')]:close(summary[a][name]['metrics'],old[a]['baseline'][model]['lists']['top10'])
    save(OUT/'audit.json',dict(passed=True,hashes_verified=hashes,candidate_memberships_rebuilt=ncandidates,policy_metric_groups=groups,baseline_metric_replays=12,comparison_groups=groups*2,all_empty_and_tied_selections_preserved=True,new_models_or_reserved_labels=False,scalar_metrics_independent_of_runner=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
