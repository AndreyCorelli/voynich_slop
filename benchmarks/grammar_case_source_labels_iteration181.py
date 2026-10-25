"""Frozen source-label permutations for both applicability pipelines."""
from benchmarks.grammar_case_applicability_iteration180 import *
OUT=ROOT/'iteration181'
NULL_SEEDS=list(range(18100,18299))
ARMS={'rich':list(range(len(COLS))),'frequency_support':CONTROL}


def scalar_scores(summary):
    c=summary['classification'];t=summary['lists']['top10']
    return dict(nll=c['nll'],brier=c['brier'],auc=c['auc'],top10_applicability=t['edge_applicability'],top10_joint_yield=t['edge_joint_yield'],top10_case_types=t['case_types_involved'])

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py'),ROOT/'iteration180/verification-manifest.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},seeds=NULL_SEEDS,design='Exact180 features/19rich +3frequency-support pipelines, fixed ridge.1/scaling/optimizer/threshold/top10/top20 tie policies, no retuning. Source52 labels with18 positives,199 fixed random permutations seeds18100..18298, numpydefault_rng(seed).permutation(y); same permuted labels for both arms. Original-label fit is copied from180 as frozen baseline. Freeze label vectors before fitting; freeze all source-only null models then all target predictions before target scoring. Primary rich targetNLL lower vs199 permuted-label fits. Secondary Brier/AUC/top10 applicability/joint yield/case types, and paired rich-minus-control improvement under same label assignments. Retain every model/list/emptythreshold/calibration bin. Descriptive corrected tail(1+as-or-more-extreme)/200, nll/brier lowertail, others upper; cannot claim formal independent significance due correlated edge labels and reused development target. No extra target annotations/reserves/sealeddata or namedcase/POS/nucleus recovery. Independent label inventories/Newton fits/predictions/metric replay; exact180 originals mandatory.'))
    y=load(ROOT/'iteration180/source-labels.json');labels={'original':y,**{'label'+str(s):np.random.default_rng(s).permutation(y).tolist() for s in NULL_SEEDS}};save(OUT/'source-labels.json',labels);save(OUT/'label-freeze.json',dict(inputs={str(OUT/'source-labels.json'):digest(OUT/'source-labels.json')}))
    ff=load(ROOT/'iteration180/features.json');raw=[r['values'] for r in ff['earlier']];actual=load(ROOT/'iteration180/models.json');models={'original':{a:actual[a] for a in ARMS}}
    for view,yy in labels.items():
        if view!='original':models[view]={a:fit(raw,yy,cols) for a,cols in ARMS.items()}
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(OUT/'models.json'):digest(OUT/'models.json')}))
    predictions={v:{a:predict(ff['replication'],m) for a,m in arms.items()} for v,arms in models.items()};save(OUT/'predictions.json',predictions);save(OUT/'prediction-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}))
    rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];target=[int(r['case_occurrence_pairs']>0) for r in rr];summary={};selections={}
    for view,arms in predictions.items():
        summary[view]={};selections[view]={}
        for arm,pp in arms.items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cut=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cut]
            selections[view][arm]=lists;summary[view][arm]=dict(classification=evaluate(target,pp),lists={name:metrics([rr[i] for i in ix],857) for name,ix in lists.items()})
    save(OUT/'selections.json',selections);save(OUT/'summary.json',summary)
    scalars={v:{a:scalar_scores(s) for a,s in arms.items()} for v,arms in summary.items()}
    for v,arms in scalars.items():arms['rich_gain']={m:(arms['frequency_support'][m]-arms['rich'][m] if m in ['nll','brier'] else arms['rich'][m]-arms['frequency_support'][m]) for m in arms['rich']}
    save(OUT/'scalar-scores.json',scalars);contrasts={}
    for arm in ['rich','frequency_support','rich_gain']:
        contrasts[arm]={}
        for metric,actual in scalars['original'][arm].items():
            nn=[scalars['label'+str(s)][arm][metric] for s in NULL_SEEDS];lower=arm!='rich_gain' and metric in ['nll','brier'];tail=sum(x<=actual if lower else x>=actual for x in nn);contrasts[arm][metric]=dict(actual=actual,extreme='lower' if lower else 'higher',nulls=len(nn),mean=sum(nn)/len(nn),min=min(nn),max=max(nn),as_or_more_extreme=tail,descriptive_corrected_tail=(1+tail)/(1+len(nn)))
    save(OUT/'contrasts.json',contrasts);print(json.dumps(contrasts),flush=True)
if __name__=='__main__':run()
