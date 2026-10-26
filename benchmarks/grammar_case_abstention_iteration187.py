"""Fixed range-abstention controls across all frozen endpoint omissions."""
from benchmarks.grammar_case_feature_ranges_iteration186 import *
OUT=ROOT/'iteration187'
POLICIES=['none','all_coordinates','left_entropy']
ENTROPY=[COLS.index('mean_left_entropy'),COLS.index('difference_left_entropy')]

def masks_for(features,indices):
    raw=np.array([features['earlier'][i]['values'] for i in indices]);target=np.array([r['values'] for r in features['replication']]);outside=(target<raw.min(0)-1e-12)|(target>raw.max(0)+1e-12)
    return dict(none=list(range(len(target))),all_coordinates=[i for i,row in enumerate(outside) if not any(row)],left_entropy=[i for i,row in enumerate(outside) if not any(row[ENTROPY])])

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration186/verification-manifest.json',ROOT/'iteration184/omissions.json',ROOT/'iteration184/predictions.json',ROOT/'iteration184/selections.json',ROOT/'iteration184/summary.json',ROOT/'iteration180/features.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen184 models/predictions and all53 omission masks plus original; NO refitting or target-based selection. Coordinate ranges from retained SOURCE raw features only, tolerance1e-12; none/all19/leftentropymean-and-difference policies fixed from186. Freeze all accepted-index masks before labels. Both rich/control arms, retain all54fits including duplicate47omission training sets. Select original global threshold/top10/top20 then intersect masks (trim); independently refill top10/top20 from accepted indices with original fixed probabilities/all boundary ties. All candidates accepted/rejected coverage, applicable pairs lost, noncase rejected, accepted probability calibration/NLL/Brier/AUC, and list172 frame-consistency/jointyield/type diversity. Retain empty acceptedsets/thresholdlists and oneclass cases; no abstentions counted as correct, no comparing conditional losses without coverage. Primary rich leftentropy refill-top10 across all53 omissions versus noabstention, along with applicable-evidence loss; all-coordinate comparator no winner selection or adoption. Freeze selections before summaries, report all per-fit outcomes and ranges; exact184 none baselines. Sameauthor reused development and hypothesis from known target errors, not fresh validation or calibrated confidence. Independent retained-source bounds/masks/ties/metrics/coverage/range audit required.'))
    ff=load(ROOT/'iteration180/features.json');omissions=load(ROOT/'iteration184/omissions.json');masks={v:masks_for(ff,o['training']) for v,o in omissions.items()};save(OUT/'accepted-masks.json',masks);save(OUT/'mask-freeze.json',dict(inputs={str(OUT/'accepted-masks.json'):digest(OUT/'accepted-masks.json')}))
    predictions=load(ROOT/'iteration184/predictions.json');oldsel=load(ROOT/'iteration184/selections.json');selections={}
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
