"""Fixed-graph development source-author deletion audit; no source selection."""
from benchmarks.grammar_multi_author_iteration193 import AUTHORS,ROOT,Path,load,save,digest,weighted_fit,predict,CONTROL,evaluate
from benchmarks.grammar_multi_author_review192_193 import listmetrics
OUT=ROOT/'iteration194'
BASE=ROOT/'iteration193'
POLICY='Source-author influence only. Reuse193 admission, graphs,19features and case references unchanged. Each six target authors has baseline and all five single-source-author omissions; target never trains itself. Empty-source omissions explicitly retained as no-ops. Same equal total mass per remaining nonempty source author, recomputed source-only weighted standardization, fixed meanNLL +.1/2 slopeL2, intercept free. Rich19/control3 and sourceprior; no entropy repair, new labels/data, hyperparameter or threshold choice. All36 model sets and target probabilities saved/frozen before metrics. Fixed .5 and top10/20 with exact boundary ties. Replay193 baseline predictions/metrics; report every deletion, training positive evidence, calibration, applicability, conditional case equality, type coverage and target shortlisted errors; do not choose a target-winning source subset. Predeclared questions: singleton-negative Palladius mass, Aquinas top10 failure, robustness of Caesar/Cicero/Jerome shortlists. Known reused development targets, no reserved evaluation or nucleus/POS/namedcase claim.'

def selections(pp):
    result={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
    for k in [10,20]:
        cut=sorted(pp,reverse=True)[min(k,len(pp))-1] if pp else None
        result['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
    return result

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_multi_author_iteration193.py'),Path('benchmarks/grammar_multi_author_review192_193.py')]+[BASE/n for n in ['verification-manifest.json','features.json','development-references.json','finalized-sizes.json','models.json','predictions.json','finalized-summary.json']]
    save(OUT/'design-freeze.json',dict(policy=POLICY,inputs={str(p):digest(p) for p in paths}))
    for path,h in load(BASE/'verification-manifest.json').items():assert digest(Path(path))==h
    ff=load(BASE/'features.json');refs=load(BASE/'development-references.json');sizes=load(BASE/'finalized-sizes.json')
    trials={}
    for target in AUTHORS:
        trials[target]={}
        for omitted in [None]+[a for a in AUTHORS if a!=target]:
            name='baseline' if omitted is None else 'without-'+omitted
            train=[a for a in AUTHORS if a!=target and a!=omitted and ff[a]]
            trials[target][name]=dict(target=target,omitted=omitted,source_authors=train,training_rows=sum(len(ff[a]) for a in train),training_positives=sum(r['case_occurrence_pairs']>0 for a in train for r in refs[a]),per_author={a:dict(rows=len(ff[a]),positives=sum(r['case_occurrence_pairs']>0 for r in refs[a]),weight=1/len(train)) for a in train},empty_source_noop=omitted is not None and not ff[omitted])
    save(OUT/'trials.json',trials);save(OUT/'trial-freeze.json',{'trials.json':digest(OUT/'trials.json')})
    models={};pred={}
    for target,vv in trials.items():
        models[target]={};pred[target]={}
        for name,t in vv.items():
            train=t['source_authors'];raw=[r['values'] for a in train for r in ff[a]];y=[int(r['case_occurrence_pairs']>0) for a in train for r in refs[a]];weights=[1/len(ff[a]) for a in train for r in ff[a]]
            mm={label:weighted_fit(raw,y,weights,cols) for label,cols in [('rich',list(range(19))),('frequency_support',CONTROL)]};prior=sum(w*v for w,v in zip(weights,y))/sum(weights);mm['prior']=dict(probability=prior)
            models[target][name]=mm;pred[target][name]={label:([prior]*len(ff[target]) if label=='prior' else (predict(ff[target],m) if ff[target] else [])) for label,m in mm.items()}
    save(OUT/'models.json',models);save(OUT/'predictions.json',pred);save(OUT/'prediction-freeze.json',{n:digest(OUT/n) for n in ['models.json','predictions.json']})
    oldpred=load(BASE/'predictions.json');summary={};lists={};details={};contrasts={}
    for target,vv in pred.items():
        assert vv['baseline']==oldpred[target]
        rr=refs[target];y=[int(r['case_occurrence_pairs']>0) for r in rr];summary[target]={};lists[target]={};details[target]={};contrasts[target]={}
        for name,mm in vv.items():
            summary[target][name]={};lists[target][name]={};details[target][name]={};contrasts[target][name]={}
            for label,pp in mm.items():
                ix=selections(pp);lists[target][name][label]=ix;summary[target][name][label]=dict(classification=evaluate(y,pp) if pp else None,lists={k:listmetrics([rr[i] for i in sel],sizes[target]['types']) for k,sel in ix.items()})
                details[target][name][label]=[dict(edge=i,probability=pp[i],applicable=bool(y[i]),**rr[i]) for i in ix['top10']]
                s=summary[target][name][label];b=summary[target]['baseline'][label]
                contrasts[target][name][label]=dict(top10_applicable_change=s['lists']['top10']['case_edges']-b['lists']['top10']['case_edges'],top10_size_change=s['lists']['top10']['edges']-b['lists']['top10']['edges'],nll_change=s['classification']['nll']-b['classification']['nll'] if pp else None,brier_change=s['classification']['brier']-b['classification']['brier'] if pp else None,auc_change=s['classification']['auc']-b['classification']['auc'] if pp and s['classification']['auc'] is not None else None,top10_entered=sorted(set(ix['top10'])-set(lists[target]['baseline'][label]['top10'])),top10_left=sorted(set(lists[target]['baseline'][label]['top10'])-set(ix['top10'])))
    for n,v in [('summary',summary),('selections',lists),('shortlist-details',details),('contrasts',contrasts)]:save(OUT/(n+'.json'),v)
    for target,vv in summary.items():
        print(target,{name:{label:(v['lists']['top10']['case_edges'],v['lists']['top10']['edges'],round(v['classification']['nll'],6) if v['classification'] else None) for label,v in mm.items()} for name,mm in vv.items()},flush=True)
if __name__=='__main__':run()
