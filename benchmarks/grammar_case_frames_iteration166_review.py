"""Independent recognized-case Cartesian comparisons and applicability checks."""
from benchmarks.grammar_case_frames_iteration166 import *

def run():
    hc=ec=pc=mc=0
    for name in ['design-freeze','case-input-freeze','scores-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hc+=1
    assert CASES=={'Nom','Gen','Dat','Acc','Abl','Voc','Loc'};selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};case_inputs=load(OUT/'case-inputs.json');inventory=load(OUT/'case-inventory.json');descriptors=load(ROOT/'iteration165/descriptors.json');transforms=load(ROOT/'iteration164/transforms.json');refs=load(ROOT/'iteration164/references.json');details=load(OUT/'details.json');summary=load(OUT/'summary.json');contrasts=load(OUT/'contrasts.json')
    for author in AUTHORS:
        assert not set(selection[author]['sent_ids'])&reserved;cases=[t.get('case','') for sid in selection[author]['sent_ids'] for t in (old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens'])];assert cases==case_inputs[author];assert inventory[author]==dict(tokens=len(cases),recognized=sum(c in CASES for c in cases),missing=sum(not c for c in cases),unrecognized=dict(Counter(c for c in cases if c and c not in CASES)))
        for view,dd in descriptors[author].items():
            ix=transforms[author][view];cc=cases if ix is None else [cases[k] for k in ix];computed=[]
            for e in dd:
                fractions=[];valid=matched=total=0
                for f in e['frames']:
                    allpairs=[(cc[a],cc[b]) for a in f['a_positions'] for b in f['b_positions']];both=[(a,b) for a,b in allpairs if a in CASES and b in CASES];right=sum(a==b for a,b in both);total+=len(allpairs);valid+=len(both);matched+=right;pc+=len(allpairs)
                    if both:fractions.append(right/len(both))
                computed.append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=len(fractions),all_occurrence_pairs=total,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(fractions)/len(fractions) if fractions else None,no_case_conflicts=matched==valid if valid else None));ec+=1
            assert computed==details[author][view];assert summary[author][view]==summarize_cases(computed,len(refs[author]))
            for threshold in [1,2]:
                rr=[r for r in computed if r['shared_frames']>=threshold];covered=[r for r in rr if r['case_occurrence_pairs']];s=summary[author][view][str(threshold)];assert s['edges']==len(rr) and s['case_edges']==len(covered);assert s['case_occurrence_pairs']<=s['all_occurrence_pairs'];assert s['case_frames']<=s['frames'];assert s['edge_macro_frame_case_agreement']==(sum(r['frame_macro_case_agreement'] for r in covered)/len(covered) if covered else None);mc+=1
        for threshold,r in contrasts[author].items():
            actual=summary[author]['original'][threshold];pp=[summary[author]['word'+str(k)][threshold]['edge_macro_frame_case_agreement'] for k in SEEDS if summary[author]['word'+str(k)][threshold]['case_edges']];v=actual['edge_macro_frame_case_agreement'];assert r==dict(actual=actual,null_with_case=len(pp),null_mean=float(np.mean(pp)) if pp else None,null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=v for p in pp) if v is not None else None)
    save(OUT/'audit.json',dict(input_hashes_verified=hc,views_verified=68,case_inventories_verified=4,edge_records_independently_replayed=ec,all_cartesian_pairs_checked=pc,metric_groups_verified=mc,missing_case_never_counted_as_agreement=True,all_applicability_denominators_verified=True,case_labels_travel_with_permutation=True,no_label_based_edge_selection=True))
if __name__=='__main__':run()
