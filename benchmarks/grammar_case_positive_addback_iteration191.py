"""Exhaustive individual positive-source addbacks on frozen weak masks."""
from benchmarks.grammar_case_class_mass_iteration190_retry import *
OUT=ROOT/'iteration191'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_case_class_mass_iteration190_retry.py'),ROOT/'iteration190-retry/verification-manifest.json',ROOT/'iteration190-retry/models.json',ROOT/'iteration190-retry/predictions.json',ROOT/'iteration190-retry/summary.json',ROOT/'iteration189/cohorts.json',ROOT/'iteration188/omissions.json',ROOT/'iteration188/accepted-masks.json',ROOT/'iteration180/features.json',ROOT/'iteration180/source-labels.json',ROOT/'iteration180/models.json',ROOT/'iteration172/details.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='All EXACT21 historical188 weak masks from frozen189 weak_le7 cohort, even those improved190; no target-selected refinement. For each, baseline190 fixed-original-class-mass plus one-at-time addback of EVERY positive SOURCE example omitted by that mask (existing labels only). Freeze trial training indices before fitting. Fixed180 scales/features/ridge/columns and18/52positive34/52negative totalmass, same numerical gradient acceptance rule190. Base188 none/all19/entropy2 accepted masks FIXED per mask despite adding labeled example, isolating label/example information from changing range coverage. Baseline190 models/predictions copied; cache duplicate retained-index fits but report all trials. Freeze all models/predictions then trim/refill selections before target truth. Both rich/control and all policies, fixed.5/top10/top20/ties, all regressions retained. Primary per-mask distribution of rich entropy-refill10 applicability gains versus190 baseline; maxima diagnostic ORACLE over existing source addbacks, not deployable selection or new generalization. Report per-example across-mask effects/unique masks, full-target losses and feature coefficients retained, no chosen rescue model. Sameauthor/reused target/correlated trials; no new annotations/reserves/sealeddata/namedcase/POS/nuclei. Independent trial inventory/classmass/Newton/prediction/mask/metric/effect audit required.'))
    ff=load(ROOT/'iteration180/features.json');y=load(ROOT/'iteration180/source-labels.json');weak=load(ROOT/'iteration189/cohorts.json')['weak_le7'];om=load(ROOT/'iteration188/omissions.json');trials={}
    for mask in weak:
        base=om[mask]['training'];trials[mask+'/base']=dict(mask=mask,addback=None,training=base)
        for i,label in enumerate(y):
            if label and i not in base:trials[mask+'/add'+str(i)]=dict(mask=mask,addback=i,training=sorted(base+[i]))
    save(OUT/'trials.json',trials);save(OUT/'trial-freeze.json',dict(inputs={str(OUT/'trials.json'):digest(OUT/'trials.json')}))
    oldmodels=load(ROOT/'iteration190-retry/models.json');oldpred=load(ROOT/'iteration190-retry/predictions.json');reference=load(ROOT/'iteration180/models.json');cache={};models={}
    for view,t in trials.items():
        key=tuple(t['training'])
        if key not in cache:cache[key]=(oldmodels[t['mask']] if t['addback'] is None else {a:fit_mass([ff['earlier'][i]['values'] for i in key],[y[i] for i in key],cols,reference[a]) for a,cols in ARMS.items()})
        models[view]=cache[key]
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(OUT/'models.json'):digest(OUT/'models.json')}))
    predictions={v:(oldpred[t['mask']] if t['addback'] is None else {a:predict(ff['replication'],m) for a,m in models[v].items()}) for v,t in trials.items()};save(OUT/'predictions.json',predictions);save(OUT/'prediction-freeze.json',dict(inputs={str(OUT/'predictions.json'):digest(OUT/'predictions.json')}))
    masks=load(ROOT/'iteration188/accepted-masks.json');selections={}
    for v,arms in predictions.items():
        selections[v]={}
        for policy,accepted in masks[trials[v]['mask']].items():
            selections[v][policy]={}
            for arm,pp in arms.items():
                global_lists={'threshold':[i for i,p in enumerate(pp) if p>=.5]}
                for k in [10,20]:
                    cutoff=sorted(pp,reverse=True)[min(k,len(pp))-1];global_lists['top'+str(k)]=[i for i,p in enumerate(pp) if p>=cutoff]
                lists={'trim_'+name:[i for i in ix if i in accepted] for name,ix in global_lists.items()}
                for k in [10,20]:
                    cutoff=sorted([pp[i] for i in accepted],reverse=True)[min(k,len(accepted))-1] if accepted else None;lists['refill_top'+str(k)]=[i for i in accepted if cutoff is not None and pp[i]>=cutoff]
                selections[v][policy][arm]=lists
    save(OUT/'selections.json',selections);save(OUT/'selection-freeze.json',dict(inputs={str(OUT/'selections.json'):digest(OUT/'selections.json')}))
    rr=load(ROOT/'iteration172/details.json')['replication']['original']['all'];labels=[int(r['case_occurrence_pairs']>0) for r in rr];summary={}
    for v,policies in selections.items():
        summary[v]={}
        for policy,arms in policies.items():
            accepted=masks[trials[v]['mask']][policy];summary[v][policy]={a:dict(classification=evaluate([labels[i] for i in accepted],[predictions[v][a][i] for i in accepted]) if accepted else None,lists={label:metrics([rr[i] for i in ix],857) for label,ix in lists.items()}) for a,lists in arms.items()}
    save(OUT/'summary.json',summary);effects={};permask={}
    for v,t in trials.items():
        if t['addback'] is None:continue
        b=summary[t['mask']+'/base'];after=summary[v];effects[v]={}
        for arm in ARMS:
            bm=b['left_entropy'][arm]['lists']['refill_top10'];am=after['left_entropy'][arm]['lists']['refill_top10'];effects[v][arm]=dict(base_case_pairs=bm['case_edges'],after_case_pairs=am['case_edges'],change=am['case_edges']-bm['case_edges'],base_joint=bm['edge_joint_yield'],after_joint=am['edge_joint_yield'],base_nll=b['none'][arm]['classification']['nll'],after_nll=after['none'][arm]['classification']['nll'])
    for mask in weak:
        rows=[effects[v]['rich'] for v,t in trials.items() if t['mask']==mask and t['addback'] is not None];permask[mask]=dict(trials=len(rows),baseline=summary[mask+'/base']['left_entropy']['rich']['lists']['refill_top10']['case_edges'],min_applicable=min(r['after_case_pairs'] for r in rows),max_applicable=max(r['after_case_pairs'] for r in rows),improved=sum(r['change']>0 for r in rows),worsened=sum(r['change']<0 for r in rows),unchanged=sum(r['change']==0 for r in rows))
    perexample={}
    for i in sorted({t['addback'] for t in trials.values() if t['addback'] is not None}):
        vv=[v for v,t in trials.items() if t['addback']==i];changes=[effects[v]['rich']['change'] for v in vv];perexample[str(i)]=dict(trials=len(vv),distinct_base_masks=len({tuple(om[trials[v]['mask']]['training']) for v in vv}),improved=sum(c>0 for c in changes),worsened=sum(c<0 for c in changes),unchanged=sum(c==0 for c in changes),min_change=min(changes),max_change=max(changes),mean_change=sum(changes)/len(changes))
    save(OUT/'effects.json',effects);save(OUT/'per-mask.json',permask);save(OUT/'per-example.json',perexample);print(json.dumps(dict(masks=permask,examples=perexample)),flush=True)
if __name__=='__main__':run()
