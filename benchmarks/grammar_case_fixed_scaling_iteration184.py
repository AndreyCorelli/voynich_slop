"""All-source-endpoint omission sensitivity of fixed applicability models."""
from benchmarks.grammar_case_source_labels_iteration181 import *
OUT=ROOT/'iteration184'

def fit_fixed(raw,y,columns,reference):
    mean=np.array(reference['mean']);scale=np.array(reference['scale']);xx=np.array(raw)[:,columns];x=np.column_stack([np.ones(len(xx)),(xx-mean)/scale]);y=np.array(y)
    def loss(beta):
        z=x@beta;pen=beta.copy();pen[0]=0
        return float(np.mean(np.logaddexp(0,z)-y*z)+.05*(pen@pen)),x.T@(expit(z)-y)/len(y)+.1*pen
    r=minimize(loss,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=1000,ftol=1e-13,gtol=1e-9));assert r.success,r.message
    return dict(columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),strength=.1,objective=float(r.fun),gradient_max=float(max(abs(loss(r.x)[1]))))

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_applicability_iteration180.py'),ROOT/'iteration183/verification-manifest.json',ROOT/'iteration183/omissions.json',ROOT/'iteration183/summary.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Repeat EXACT183 all53 opaque source-endpoint labeled-neighborhood omissions and same180 rich/control pipelines. ONLY changed intervention: fix mean/std to each original180 full-source reference model for every fit, while deleting incident training examples. Source unlabeled features from omitted examples admitted to scaling; no target statistics or labels. Feature projection unchanged, not token deletion. Same ridge.1/unweightedmeanNLL/intercept/optimizer/threshold/top10/top20/ties, no tuning. Exact180 originals, all lowdata/oneclass cases retained. Freeze copied omissions, models, target predictions before evaluating target. Primary paired per-omission differences vs183 in targetNLL and top10 applicability; report all53, rich/control ranges and sourcepair21 known leverage cases as declared diagnostic, no favorableendpointselection. No fresh validation/namedcase/POS/nuclei claim; sameauthor/development/47distinct correlated masks. Independent fixedscaling/Newton/prediction/metrics/range/pairedcontrast replay required.'))
    ff=load(ROOT/'iteration180/features.json');source=ff['earlier'];omissions=load(ROOT/'iteration183/omissions.json')
    save(OUT/'omissions.json',omissions);save(OUT/'omission-freeze.json',dict(inputs={str(OUT/'omissions.json'):digest(OUT/'omissions.json')}))
    y=load(ROOT/'iteration180/source-labels.json');original=load(ROOT/'iteration180/models.json');models={};skipped={}
    for view,o in omissions.items():
        ix=o['training'];yy=[y[i] for i in ix]
        if len(set(yy))<2:skipped[view]=dict(training=len(ix),positives=sum(yy),reason='oneclass');continue
        models[view]={a:(original[a] if view=='original' else fit_fixed([source[i]['values'] for i in ix],yy,cols,original[a])) for a,cols in ARMS.items()}
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
    ranges['matched_rich_nll_better_than_control']=sum(s['rich']['classification']['nll']<s['frequency_support']['classification']['nll'] for v,s in summary.items() if v!='original');save(OUT/'ranges.json',ranges)
    old=load(ROOT/'iteration183/summary.json');paired={}
    for view,arms in summary.items():
        if view=='original':continue
        paired[view]={}
        for arm,s in arms.items():
            before=scalar_scores(old[view][arm]);after=scalar_scores(s);paired[view][arm]={m:dict(rescaled=before[m],fixed=after[m],fixed_minus_rescaled=after[m]-before[m]) for m in before}
    save(OUT/'paired.json',paired);print(json.dumps(ranges),flush=True)
if __name__=='__main__':run()
