"""Conditional occurrence case agreement on exactly the existing frame graph."""
from benchmarks.grammar_occurrence_frames_iteration165 import *
OUT=ROOT/'iteration166';CASES={'Nom','Gen','Dat','Acc','Abl','Voc','Loc'}

def score_cases(descriptors,cases):
    details=[]
    for e in descriptors:
        agreements=[];matched=valid=allpairs=coveredframes=0
        for f in e['frames']:
            aa=f['a_positions'];bb=f['b_positions'];allpairs+=len(aa)*len(bb);pairs=[(cases[a],cases[b]) for a in aa for b in bb if cases[a] in CASES and cases[b] in CASES];same=sum(a==b for a,b in pairs)
            if pairs:agreements.append(same/len(pairs));coveredframes+=1
            matched+=same;valid+=len(pairs)
        details.append(dict(a=e['a'],b=e['b'],shared_frames=e['shared_frames'],case_frames=coveredframes,all_occurrence_pairs=allpairs,case_occurrence_pairs=valid,matching_case_pairs=matched,frame_macro_case_agreement=sum(agreements)/len(agreements) if agreements else None,no_case_conflicts=matched==valid if valid else None))
    return details

def summarize_cases(details,eligible):
    result={}
    for threshold in [1,2]:
        rr=[r for r in details if r['shared_frames']>=threshold];covered=[r for r in rr if r['case_occurrence_pairs']];pairs=sum(r['all_occurrence_pairs'] for r in rr);valid=sum(r['case_occurrence_pairs'] for r in rr);matched=sum(r['matching_case_pairs'] for r in rr);frames=sum(r['shared_frames'] for r in rr);caseframes=sum(r['case_frames'] for r in rr);types={r[k] for r in rr for k in ['a','b']};casetypes={r[k] for r in covered for k in ['a','b']};result[str(threshold)]=dict(edges=len(rr),case_edges=len(covered),edge_applicability=len(covered)/len(rr) if rr else None,frames=frames,case_frames=caseframes,frame_applicability=caseframes/frames if frames else None,all_occurrence_pairs=pairs,case_occurrence_pairs=valid,pair_applicability=valid/pairs if pairs else None,matching_case_pairs=matched,edge_macro_frame_case_agreement=sum(r['frame_macro_case_agreement'] for r in covered)/len(covered) if covered else None,pooled_case_agreement=matched/valid if valid else None,no_case_conflict_edges=sum(r['no_case_conflicts'] for r in covered),no_case_conflict_fraction=sum(r['no_case_conflicts'] for r in covered)/len(covered) if covered else None,types_involved=len(types),case_types_involved=len(casetypes),eligible_types=eligible,case_type_coverage=len(casetypes)/eligible)
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration165/verification-manifest.json',ROOT/'iteration165/descriptors.json',ROOT/'iteration164/streams.json',ROOT/'iteration164/transforms.json',ROOT/'iteration164/references.json',ROOT/'iteration158/selection.json',ROOT/'iteration159/selection.json',ROOT/'iteration40/data-truth.json',ROOT/'iteration44/annotations-truth.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ConditionalCASEdiagnostic onEXACT165frozenedge/frame/occurrence descriptors, noedgechanges. Primary>=2distinctsharedframes, secondary>=1, supportedtypes>=5 unchanged. RecognizedcaseEXACT{Nom,Gen,Dat,Acc,Abl,Voc,Loc}; empty/multi/otherunscoredneveragreement. Casesfromexisting40/44token.caseONLY, travelwithtoken164fixedwordshuffles. WithinframeCartesianpairswhereBOTHrecognizedcase, fractionmatch; equalweighteligibleframeswithinedge/equalweighteligibleedges primary. ReportALLoriginaledge/frame/pair applicability andcase-typecoverage, pooledcaseagreement/no-conflict-coverededgessecondary; edgeswithoutcaseNone notperfect. No case labelsselectedges ordeployableconfidencefilter; conditionalmorphologicalagreement NOTdetectionofcasebearingpositions/namedcaserecovery/nuclei. Freezecaseinputinventory beforecomparisons, allcaseedgescores beforeaggregate/nullmetrics. No newannotations/reserve/sealedworks/fitting, no changingrecognizedcases/support afteroutcomes.'))
    descriptors=load(ROOT/'iteration165/descriptors.json');streams=load(ROOT/'iteration164/streams.json');transforms=load(ROOT/'iteration164/transforms.json');refs=load(ROOT/'iteration164/references.json');selection={**load(ROOT/'iteration158/selection.json'),**load(ROOT/'iteration159/selection.json')};old=load(ROOT/'iteration40/data-truth.json');source=load(ROOT/'iteration44/annotations-truth.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};case_inputs={};inventory={}
    for author in AUTHORS:
        sids=selection[author]['sent_ids'];assert not set(sids)&reserved;tokens=[t for sid in sids for t in (old[sid] if author in ['Caesar','Jerome'] else source[sid]['tokens'])];assert [hashlib.sha256(('frames164-'+author+'|'+t['word']).encode()).hexdigest() for t in tokens]==streams[author];case_inputs[author]=[t.get('case','') for t in tokens];inventory[author]=dict(tokens=len(tokens),recognized=sum(c in CASES for c in case_inputs[author]),missing=sum(not c for c in case_inputs[author]),unrecognized=dict(Counter(c for c in case_inputs[author] if c and c not in CASES)))
    save(OUT/'case-inputs.json',case_inputs);save(OUT/'case-inventory.json',inventory);save(OUT/'case-input-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['case-inputs.json','case-inventory.json']}));details={}
    for author,vv in descriptors.items():
        details[author]={}
        for view,dd in vv.items():
            ix=transforms[author][view];cases=case_inputs[author] if ix is None else [case_inputs[author][k] for k in ix];details[author][view]=score_cases(dd,cases)
    save(OUT/'details.json',details);save(OUT/'scores-freeze.json',dict(inputs={str(OUT/'details.json'):digest(OUT/'details.json')}));summary={a:{view:summarize_cases(dd,len(refs[a])) for view,dd in vv.items()} for a,vv in details.items()};contrasts={}
    for author,vv in summary.items():
        contrasts[author]={}
        for threshold in ['1','2']:
            actual=vv['original'][threshold];null=[vv['word'+str(k)][threshold] for k in SEEDS];pp=[r['edge_macro_frame_case_agreement'] for r in null if r['case_edges']];value=actual['edge_macro_frame_case_agreement'];contrasts[author][threshold]=dict(actual=actual,null_with_case=len(pp),null_mean=float(np.mean(pp)) if pp else None,null_max=max(pp) if pp else None,null_at_least_actual=sum(p>=value for p in pp) if value is not None else None)
        print(author,contrasts[author],flush=True)
    save(OUT/'summary.json',summary);save(OUT/'contrasts.json',contrasts)
if __name__=='__main__':run()
