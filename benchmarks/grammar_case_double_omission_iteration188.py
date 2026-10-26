"""Fixed range-abstention controls across all frozen endpoint omissions."""
from benchmarks.grammar_case_abstention_iteration187 import *
from itertools import combinations
OUT=ROOT/'iteration188'
POLICIES=['none','all_coordinates','left_entropy']
ENTROPY=[COLS.index('mean_left_entropy'),COLS.index('difference_left_entropy')]

def masks_for(features,indices):
    raw=np.array([features['earlier'][i]['values'] for i in indices]);target=np.array([r['values'] for r in features['replication']]);outside=(target<raw.min(0)-1e-12)|(target>raw.max(0)+1e-12)
    return dict(none=list(range(len(target))),all_coordinates=[i for i,row in enumerate(outside) if not any(row)],left_entropy=[i for i,row in enumerate(outside) if not any(row[ENTROPY])])

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_fixed_scaling_iteration184.py'),ROOT/'iteration187/verification-manifest.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration180/predictions.json',ROOT/'iteration180/selections.json',ROOT/'iteration180/summary.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='ALL unordered pairs of53 source graph endpoints:1378 double-omissions plus exact180 original. Remove union of incident labeled training pairs, no endpoint/label selection; enumerate/freeze indices before labels. Same180 rich/control columns/ridge.1/full-source scaling/feature projection; original full-source unlabeled features remain admitted, NOT token deletion. Cache identical retained-index fits but report every endpoint-pair mask and distinct count; skip/report every zero/oneclass fit without fabricating outputs. Same187 none/all19/leftentropy2 range policies from retained-source raw features, tolerance1e-12, freeze masks before target scoring. Freeze source models and all target probabilities then trimmed/refilled lists before target labels. Primary rich leftentropy refilltop10 versus none across ALL trainable omissions, all accepted coverage/applicable loss/conditional probability calibration/listmetrics/ranges retained. Baseline original matches180 and187 original masks/lists. No coordinate/threshold/model selection or confidence/default adoption; correlated sameauthor reused-development perturbations, not independent/newauthor validation, no namedcase/POS/nuclei. Independently reconstruct all1378 masks, fit fixed-scale Newton models, all predictions/masks/ties/metrics/ranges/paired outputs; retain all worst cases.'))
    ff=load(ROOT/'iteration180/features.json');source=ff['earlier'];endpoints=sorted({r[k] for r in source for k in ['a','b']});omissions={'original':dict(endpoints=[],training=list(range(len(source))))}
    for k,(a,b) in enumerate(combinations(endpoints,2)):omissions['omit'+str(k)]=dict(endpoints=[a,b],training=[i for i,r in enumerate(source) if r['a'] not in [a,b] and r['b'] not in [a,b]])
    save(OUT/'omissions.json',omissions);save(OUT/'omission-freeze.json',dict(inputs={str(OUT/'omissions.json'):digest(OUT/'omissions.json')}))
    masks={v:masks_for(ff,o['training']) for v,o in omissions.items() if o['training']};save(OUT/'accepted-masks.json',masks);save(OUT/'mask-freeze.json',dict(inputs={str(OUT/'accepted-masks.json'):digest(OUT/'accepted-masks.json')}))
    y=load(ROOT/'iteration180/source-labels.json');reference=load(ROOT/'iteration180/models.json');models={};skipped={};cache={}
    for view,o in omissions.items():
        ix=o['training'];yy=[y[i] for i in ix]
        if len(set(yy))<2:skipped[view]=dict(training=len(ix),positives=sum(yy),reason='zero_or_oneclass');continue
        key=tuple(ix)
        if key not in cache:cache[key]={arm:(reference[arm] if view=='original' else fit_fixed([source[i]['values'] for i in ix],yy,cols,reference[arm])) for arm,cols in ARMS.items()}
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
    save(OUT/'ranges.json',ranges);save(OUT/'paired.json',paired);print(json.dumps(ranges),flush=True)
if __name__=='__main__':run()
