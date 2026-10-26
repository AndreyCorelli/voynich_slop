"""Frozen no-refill source-omission consensus cores on development graphs."""
from benchmarks.grammar_source_author_influence_iteration194 import ROOT,AUTHORS,Path,load,save,digest
from benchmarks.grammar_multi_author_review192_193 import listmetrics
OUT=ROOT/'iteration195'
SOURCE=ROOT/'iteration194'
BASE=ROOT/'iteration193'
POLICY='Freeze exactly three consensus policies: rich_core=intersection of rich top10 across baseline and all five single-source omissions; control_core=same for frequency_support; both_core=intersection of those cores. Baseline rich/control top10 retained as comparators. Reconstruct top10 from frozen194 probabilities with all exact ties; keep empty lists and empty graphs, no refill or selected subset. Duplicate no-op source views harmless for intersection; record unique source sets. Freeze all selections and candidate membership before loading193 case references. No model fit, probability calibration, new labels/raw text/reserves, ranking/threshold adjustment or winner selected. Report all six authors and five policies: selected/applicable/false-positive counts, precision, available-positive recall, endpoint/type coverage, conditional frame case equality, joint yield, loss of useful baseline pairs, retained stable errors and exact baseline replay. Diagnostic on reused development data; stable source consensus does not imply correctness, exact identities, named cases or fresh validation.'

def top10(pp):
    if not pp:return []
    cut=sorted(pp,reverse=True)[min(10,len(pp))-1]
    return [i for i,p in enumerate(pp) if p>=cut]

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_multi_author_review192_193.py')]+[SOURCE/n for n in ['verification-manifest.json','predictions.json','trials.json','summary.json']]+[BASE/n for n in ['development-references.json','finalized-sizes.json']]
    save(OUT/'design-freeze.json',dict(policy=POLICY,inputs={str(p):digest(p) for p in paths}))
    for path,h in load(SOURCE/'verification-manifest.json').items():assert digest(Path(path))==h
    pp=load(SOURCE/'predictions.json');trials=load(SOURCE/'trials.json');selected={};membership={};views={}
    for a in AUTHORS:
        views[a]=dict(trials=list(pp[a]),unique_nonempty_source_sets=len({tuple(t['source_authors']) for t in trials[a].values()}));cores={};membership[a]=[]
        permodel={m:{v:set(top10(mm[m])) for v,mm in pp[a].items()} for m in ['rich','frequency_support']}
        for m,vv in permodel.items():cores[m]=set.intersection(*vv.values())
        selected[a]=dict(rich_baseline=top10(pp[a]['baseline']['rich']),control_baseline=top10(pp[a]['baseline']['frequency_support']),rich_core=sorted(cores['rich']),control_core=sorted(cores['frequency_support']),both_core=sorted(cores['rich']&cores['frequency_support']))
        for i in range(len(pp[a]['baseline']['rich'])):
            membership[a].append(dict(edge=i,rich_views=[v for v,ix in permodel['rich'].items() if i in ix],control_views=[v for v,ix in permodel['frequency_support'].items() if i in ix]))
    for name,obj in [('selections',selected),('membership',membership),('views',views)]:save(OUT/(name+'.json'),obj)
    save(OUT/'selection-freeze.json',{n:digest(OUT/n) for n in ['selections.json','membership.json','views.json']})
    rr=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json');old=load(SOURCE/'summary.json');summary={};details={};comparisons={}
    for a in AUTHORS:
        rows=rr[a];positives={i for i,r in enumerate(rows) if r['case_occurrence_pairs']};alltypes={r[k] for r in rows for k in ['a','b']};summary[a]={};details[a]={};comparisons[a]={}
        for policy,ix in selected[a].items():
            chosen=[rows[i] for i in ix];metrics=listmetrics(chosen,sizes[a]['types']);n=len(ix);tp=len(set(ix)&positives)
            summary[a][policy]=dict(metrics=metrics,false_positives=n-tp,available_applicable_pairs=len(positives),applicable_pair_recall=tp/len(positives) if positives else None,all_candidates=len(rows),candidate_retention=n/len(rows) if rows else None,type_retention=metrics['types_involved']/len(alltypes) if alltypes else None)
            details[a][policy]=[dict(edge=i,applicable=i in positives,**rows[i]) for i in ix]
            comparisons[a][policy]={}
            for label in ['rich_baseline','control_baseline']:
                base=set(selected[a][label]);retained=base&set(ix);removed=base-set(ix);den=len(base&positives)
                comparisons[a][policy][label]=dict(retained_baseline_pairs=len(retained),removed_baseline_pairs=len(removed),retained_useful_pairs=len(retained&positives),lost_useful_pairs=len(removed&positives),removed_false_positives=len(removed-positives),useful_retention=len(retained&positives)/den if den else None)
        for policy,label in [('rich_baseline','rich'),('control_baseline','frequency_support')]:assert summary[a][policy]['metrics']==old[a]['baseline'][label]['lists']['top10']
    for name,obj in [('summary',summary),('details',details),('comparisons',comparisons)]:save(OUT/(name+'.json'),obj)
    for a,policies in summary.items():print(a,{p:dict(applicable=v['metrics']['case_edges'],selected=v['metrics']['edges'],precision=v['metrics']['edge_applicability'],case_types=v['metrics']['case_types_involved'],agreement=v['metrics']['edge_macro_frame_case_agreement'],joint=v['metrics']['edge_joint_yield']) for p,v in policies.items()},flush=True)
if __name__=='__main__':run()
