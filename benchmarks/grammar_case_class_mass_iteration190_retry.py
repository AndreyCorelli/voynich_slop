"""Fixed range-abstention controls across all frozen endpoint omissions."""
from benchmarks.grammar_case_abstention_iteration187 import *
from itertools import combinations
OUT=ROOT/'iteration190-retry'
POLICIES=['none','all_coordinates','left_entropy']
ENTROPY=[COLS.index('mean_left_entropy'),COLS.index('difference_left_entropy')]

def masks_for(features,indices):
    raw=np.array([features['earlier'][i]['values'] for i in indices]);target=np.array([r['values'] for r in features['replication']]);outside=(target<raw.min(0)-1e-12)|(target>raw.max(0)+1e-12)
    return dict(none=list(range(len(target))),all_coordinates=[i for i,row in enumerate(outside) if not any(row)],left_entropy=[i for i,row in enumerate(outside) if not any(row[ENTROPY])])

def fit_mass(raw,y,columns,reference):
    yy=np.array(y);mass=np.array([(18/52)/sum(yy==1) if c else (34/52)/sum(yy==0) for c in yy]);mean=np.array(reference['mean']);scale=np.array(reference['scale']);x=np.column_stack([np.ones(len(raw)),(np.array(raw)[:,columns]-mean)/scale])
    def loss(beta):
        z=x@beta;pen=beta.copy();pen[0]=0
        return float(mass@(np.logaddexp(0,z)-yy*z)+.05*(pen@pen)),x.T@(mass*(expit(z)-yy))+.1*pen
    r=minimize(loss,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=1000,ftol=1e-13,gtol=1e-9));gradient=float(max(abs(loss(r.x)[1])));fallback=False
    if gradient>1e-6:
        r=minimize(loss,r.x,jac=True,method='BFGS',options=dict(maxiter=1000,gtol=1e-9));gradient=float(max(abs(loss(r.x)[1])));fallback=True
    assert gradient<=1e-6,(r.message,gradient)
    return dict(optimizer_success=bool(r.success),optimizer_message=str(r.message),fallback=fallback,columns=columns,mean=mean.tolist(),scale=scale.tolist(),beta=r.x.tolist(),strength=.1,objective=float(r.fun),gradient_max=float(max(abs(loss(r.x)[1]))),positive_mass=18/52,negative_mass=34/52)

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_class_mass_iteration190.py'),ROOT/'iteration190/design-freeze.json',Path('benchmarks/grammar_case_fixed_scaling_iteration184.py'),ROOT/'iteration189/verification-manifest.json',ROOT/'iteration188/omissions.json',ROOT/'iteration188/accepted-masks.json',ROOT/'iteration188/summary.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Numerical retry of190 aborted before model/prediction/target scoring: preserve same objective/scientific design, accept stationary solutions only when maxgradient<=1e-6; if LBFGS gradient fails threshold use BFGS on identical objective, record all statuses. Diagnostic training-mass control, all EXACT188 double-endpoint masks and original, no new omission/coordinate/threshold selection. Preserve original source class masses18/52positive and34/52negative; equal weight within each retained class, weighted NLL sum +.1/2 slopeL2, unpenalizedintercept. Same180 rich/control columns/full-source scales/feature values/optimizer; unchanged187 none/all19/entropy2 ranges from retained source, trim/refill rules. Original fit copied180 (original source weighting identical), no model chosen from target outcomes. Freeze omissions+masks, all fits and all target probabilities/selections before labels. Primary paired rich entropy-refilltop10 applicability versus188, alongside full-target NONE NLL/Brier/AUC/calibration and useful-pair loss; retain all worse cases and known weak source-positive strata from189 without selecting newgroups. Cache duplicate masks, preserve oneclass outcomes. No fresh author/vocabulary validation, namedcase/POS/nuclei claim or causal proof; independent weighted Newton/model/mask/metric/baseline/paired audit.'))
    ff=load(ROOT/'iteration180/features.json');source=ff['earlier'];omissions=load(ROOT/'iteration188/omissions.json')
    save(OUT/'omissions.json',omissions);save(OUT/'omission-freeze.json',dict(inputs={str(OUT/'omissions.json'):digest(OUT/'omissions.json')}))
    masks={v:masks_for(ff,o['training']) for v,o in omissions.items() if o['training']};save(OUT/'accepted-masks.json',masks);save(OUT/'mask-freeze.json',dict(inputs={str(OUT/'accepted-masks.json'):digest(OUT/'accepted-masks.json')}))
    y=load(ROOT/'iteration180/source-labels.json');reference=load(ROOT/'iteration180/models.json');models={};skipped={};cache={}
    for view,o in omissions.items():
        ix=o['training'];yy=[y[i] for i in ix]
        if len(set(yy))<2:skipped[view]=dict(training=len(ix),positives=sum(yy),reason='zero_or_oneclass');continue
        key=tuple(ix)
        if key not in cache:cache[key]={arm:(reference[arm] if view=='original' else fit_mass([source[i]['values'] for i in ix],yy,cols,reference[arm])) for arm,cols in ARMS.items()}
        models[view]=cache[key]
    save(OUT/'models.json',models);save(OUT/'skipped.json',skipped);save(OUT/'model-freeze.json',dict(inputs={str(OUT/n):digest(OUT/n) for n in ['models.json','skipped.json']}))
    predictions={v:{a:predict(ff['replication'],m) for a,m in arms.items()} for v,arms in models.items()};save(OUT/'predictions.json',predictions);save(OUT/'prediction-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}));oldsel={}
    for v,arms in predictions.items():
        oldsel[v]={}
        for arm,pp in arms.items():
            lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
            for k in [10,20]:
                cutoff=sorted(pp,reverse=True)[min(k,len(pp))-1];lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cutoff]
            oldsel[v][arm]=lists
    selections={}
    for v,arms in predictions.items():
        selections[v]={}
        for policy,accepted in masks[v].items():
            selections[v][policy]={};allowed=set(accepted)
            for arm,pp in arms.items():
                lists={'trim_'+label:[i for i in ix if i in allowed] for label,ix in oldsel[v][arm].items()}
                for k in [10,20]:
                    threshold=sorted([pp[i] for i in accepted],reverse=True)[min(k,len(accepted))-1] if accepted else None;lists['refill_top'+str(k)]=[i for i in accepted if threshold is not None and pp[i]>=threshold]
                selections[v][policy][arm]=lists
    save(OUT/'selections.json',selections);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selections.json'):digest(OUT/'selections.json')}))
    rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];labels=[int(r['case_occurrence_pairs']>0) for r in rr];summary={}
    for v,policies in selections.items():
        summary[v]={}
        for policy,arms in policies.items():
            accepted=masks[v][policy];rejected=sorted(set(range(len(rr)))-set(accepted));coverage=dict(total=len(rr),accepted=len(accepted),rejected=len(rejected),acceptance=len(accepted)/len(rr),applicable_accepted=sum(labels[i] for i in accepted),applicable_lost=sum(labels[i] for i in rejected),noncase_rejected=sum(not labels[i] for i in rejected));summary[v][policy]=dict(coverage=coverage,arms={})
            for arm,lists in arms.items():
                pp=predictions[v][arm];summary[v][policy]['arms'][arm]=dict(accepted_classification=evaluate([labels[i] for i in accepted],[pp[i] for i in accepted]) if accepted else None,lists={name:metrics([rr[i] for i in ix],857) for name,ix in lists.items()})
    save(OUT/'summary.json',summary);ranges={};paired={}
    for policy in POLICIES:
        ranges[policy]={};rows=[s[policy] for v,s in summary.items() if v!='original']
        for metric in ['accepted','applicable_lost','noncase_rejected']:
            vals=[r['coverage'][metric] for r in rows];ranges[policy][metric]=dict(min=min(vals),max=max(vals),mean=sum(vals)/len(vals))
        for arm in ARMS:
            ranges[policy][arm]={}
            for label in ['trim_top10','refill_top10']:
                ranges[policy][arm][label]={}
                for metric in ['edges','case_edges','edge_applicability','edge_joint_yield','case_types_involved']:
                    vals=[r['arms'][arm]['lists'][label][metric] for r in rows];defined=[v for v in vals if v is not None];ranges[policy][arm][label][metric]=dict(min=min(defined) if defined else None,max=max(defined) if defined else None,mean=sum(defined)/len(defined) if defined else None,undefined=len(vals)-len(defined))
    for v,s in summary.items():
        if v=='original':continue
        paired[v]={}
        for policy in POLICIES:
            paired[v][policy]={}
            for arm in ARMS:
                base=s['none']['arms'][arm]['lists']['refill_top10'];after=s[policy]['arms'][arm]['lists']['refill_top10'];paired[v][policy][arm]=dict(base_case_pairs=base['case_edges'],after_case_pairs=after['case_edges'],case_pair_change=after['case_edges']-base['case_edges'],base_joint_yield=base['edge_joint_yield'],after_joint_yield=after['edge_joint_yield'])
    save(OUT/'ranges.json',ranges);save(OUT/'paired.json',paired);old=load(ROOT/'iteration188/summary.json');mass_comparison={}
    for v,policies in summary.items():
        if v=='original':continue
        mass_comparison[v]={}
        for policy,s in policies.items():
            mass_comparison[v][policy]={}
            for arm in ARMS:
                before=old[v][policy]['arms'][arm];after=s['arms'][arm];mass_comparison[v][policy][arm]=dict(old_case_pairs=before['lists']['refill_top10']['case_edges'],new_case_pairs=after['lists']['refill_top10']['case_edges'],case_pair_change=after['lists']['refill_top10']['case_edges']-before['lists']['refill_top10']['case_edges'],old_joint=before['lists']['refill_top10']['edge_joint_yield'],new_joint=after['lists']['refill_top10']['edge_joint_yield'],old_accepted_nll=before['accepted_classification']['nll'],new_accepted_nll=after['accepted_classification']['nll'])
    save(OUT/'mass-comparison.json',mass_comparison);print(json.dumps(ranges),flush=True)
if __name__=='__main__':run()
