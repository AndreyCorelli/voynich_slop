"""All-source-endpoint omission sensitivity of fixed applicability models."""
from benchmarks.grammar_case_source_labels_iteration181 import *
OUT=ROOT/'iteration183'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py'),ROOT/'iteration182/verification-manifest.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Freeze every opaque source endpoint from180 source52 pairs; omit each one by removing all incident labeled training pairs. No label-selected omissions. Same180 rich19 andfrequency/support3, fixedridge.1/unweightedmeanNLL/unpenalizedintercept; recompute scaling ONLY remaining training rows, feature values unchanged (full source anonymous context features remain available). Thus training-label-neighborhood sensitivity not full corpus token deletion or leave-one-word-out feature projection. Baseline exact180. Freeze all omission indices before labels, all models before predictions and all target probabilities before evaluation. Retain every lowdata/oneclass outcome (if oneclass report skipped, do not fabricate fit). Fixed.5/top10/top20 tie-inclusive lists and target classification/calibration, all ranges and original baseline. Primary rich targetNLL min/max and count beating fixed180 frequency_support NLL; compare matched omitted-control too, report AUC/top10 applicability/jointyield/type ranges and baseline-top10 overlap. Correlated omissions NOT independent replications. No hyperparameter/target tuning/new annotations/reserves/sealeddata or namedcase/POS/nucleus claims. Independent omissions/Newton/model/prediction/metric replay required.'))
    ff=load(ROOT/'iteration180/features.json');source=ff['earlier'];endpoints=sorted({r[k] for r in source for k in ['a','b']});omissions={'original':dict(endpoint=None,training=list(range(len(source))))}
    for i,w in enumerate(endpoints):omissions['omit'+str(i)]=dict(endpoint=w,training=[j for j,r in enumerate(source) if w not in [r['a'],r['b']]])
    save(OUT/'omissions.json',omissions);save(OUT/'omission-freeze.json',dict(inputs={str(OUT/'omissions.json'):digest(OUT/'omissions.json')}))
    y=load(ROOT/'iteration180/source-labels.json');original=load(ROOT/'iteration180/models.json');models={};skipped={}
    for view,o in omissions.items():
        ix=o['training'];yy=[y[i] for i in ix]
        if len(set(yy))<2:skipped[view]=dict(training=len(ix),positives=sum(yy),reason='oneclass');continue
        models[view]={a:(original[a] if view=='original' else fit([source[i]['values'] for i in ix],yy,cols)) for a,cols in ARMS.items()}
    save(OUT/'models.json',models);save(OUT/'skipped.json',skipped);save(OUT/'model-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['models.json','skipped.json']}))
    predictions={v:{a:predict(ff['replication'],m) for a,m in arms.items()} for v,arms in models.items()};save(OUT/'predictions.json',predictions);save(OUT/'prediction-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}))
    rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];yy=[int(r['case_occurrence_pairs']>0) for r in rr];summary={};selections={}
    for view,arms in predictions.items():
        summary[view]={};selections[view]={}
        for arm,pp in arms.items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            selections[view][arm]=lists;summary[view][arm]=dict(classification=evaluate(yy,pp),lists={label:metrics([rr[i] for i in ix],857) for label,ix in lists.items()})
    save(OUT/'selections.json',selections);save(OUT/'summary.json',summary);ranges={};baseline_control=summary['original']['frequency_support']['classification']['nll']
    for arm in ARMS:
        scalars={v:scalar_scores(s[arm]) for v,s in summary.items() if v!='original'};ranges[arm]={}
        for m in ['nll','brier','auc','top10_applicability','top10_joint_yield','top10_case_types']:
            vals=[r[m] for r in scalars.values()];ranges[arm][m]=dict(n=len(vals),min=min(vals) if vals else None,max=max(vals) if vals else None,mean=sum(vals)/len(vals) if vals else None)
        base=set(selections['original'][arm]['top10']);overlap=[len(base&set(s[arm]['top10'])) for v,s in selections.items() if v!='original'];ranges[arm]['baseline_top10_overlap']=dict(min=min(overlap),max=max(overlap));ranges[arm]['nll_better_than_original_control']=sum(s[arm]['classification']['nll']<baseline_control for v,s in summary.items() if v!='original')
    ranges['matched_rich_nll_better_than_control']=sum(s['rich']['classification']['nll']<s['frequency_support']['classification']['nll'] for v,s in summary.items() if v!='original');save(OUT/'ranges.json',ranges);print(json.dumps(ranges),flush=True)
if __name__=='__main__':run()
