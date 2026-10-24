"""Known-error rehearsal for PP inference; POS models remain frozen."""
from benchmarks.grammar_anchor_stability_iteration88 import *
OUT=ROOT/'iteration89';BASE=ROOT/'iteration85/budget-195'
TRAIN_VIEWS=('correct','missing_top5','swap_adp_conjunction')

def robust_policy(by_pattern,required_clean_tp):
    curve=[]
    for i in range(101):
        threshold=i/100;stats={k:counts(rows,'pp','pooled_pos',threshold) for k,rows in by_pattern.items()}
        types={k:len({r['word'] for r in rows if r['scores']['pooled_pos']['pp']>=threshold}) for k,rows in by_pattern.items()}
        eligible=stats['correct']['tp']>=required_clean_tp and all(r['predicted']>=10 and types[k]>=10 and (r['precision'] or 0)>=.9 for k,r in stats.items())
        curve.append(dict(threshold=threshold,eligible=eligible,stats=stats,types=types))
    candidates=[r for r in curve if r['eligible']]
    selected=max(candidates,key=lambda r:(sum(v['tp'] for v in r['stats'].values()),r['threshold'])) if candidates else None
    return selected,curve

def score(rows,threshold):
    if threshold is None:return None
    return counts(rows,'pp','pooled_pos',threshold)

def run():
    assert not OUT.exists();OUT.mkdir()
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]]
    patterns=load(ROOT/'iteration87/patterns.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];old=load(BASE/'models.json');classes=old['pos_classes'];oldpol=load(BASE/'policies.json');save(OUT/'patterns.json',patterns)
    (OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),ROOT/'iteration44/annotations-truth.json',ROOT/'iteration49/manifest.json',BASE/'models.json',BASE/'policies.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration88/verification-manifest.json',CACHE,DECLARATION,OUT/'patterns.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Focus195inventory: frozen85POSmodels, retrain only3PP/headmodels using equallyweighted clean,missingtop5,in/etswap sourceFITviews. Rehearsal of known87errors, not generalrobustness/discoveredanchors. Labels unchanged, IDs preserved. Per-view OOFcontextPOS uses matching sourcefold POSmodel, corruptedpublictagoverride thenstrictfoldlocaltypepool; neverpoolacrossviews. PPfoldexcludes allviews ofheldsentences. SameL2,solver,3ensemble. No hyperparametersearch. Calibration ALLsix87patterns for old/newmodels. Robustthreshold fixedgrid0..1step.01: eachpattern>=90%empiricalprecision,10calls,10types,cleanTP>=50% original85cal463 =>232. ChoosemaxsummedTP,thentiehigherthreshold; none=>notqualified, no relaxedguard. Clean-only empirical90 calibration policy secondary. Freezeallpoliciesbeforetest/transfer. Reportnewoldfixed.8, clean90androbustpolicies, samecalibrationoldcontrol, nearestleftF1and88strictendpoint. Cachedsource/Jerome/Caesar reused, noreserve/newannotations/sealedtest.'))
    public,labels=prepare84(source('fit'),anchors,'fit89',classes);allrows=[];allsoft=[];provenance={}
    for view in TRAIN_VIEWS:
        changed=perturb(public,patterns[view],anchors);rows=query_rows(changed,labels)
        for r,l in zip(rows,labels):r['structure_gold']=l['structure_gold']
        q=np.zeros((len(rows),len(classes)))
        for f in range(3):
            ids=[i for i,r in enumerate(rows) if fold(r['sid'])==f];q[ids]=ag.predict([rows[i]['features'] for i in ids],old['pos'][str(f)])
        q=ag.anchor_override(rows,q,classes);pooled=fold_pool(rows,q);allrows.extend(rows);allsoft.append(pooled);provenance[view]=dict(n=len(rows),fold_counts={str(f):sum(fold(r['sid'])==f for r in rows) for f in range(3)})
        print('prepared fit view',view,flush=True)
    soft=np.concatenate(allsoft);xx=[r['features'] for r in allrows];pp={}
    for f in range(3):
        ids=[i for i,r in enumerate(allrows) if fold(r['sid'])!=f];pp[str(f)]=ag.fit([xx[i] for i in ids],[allrows[i]['structure_gold'] for i in ids],list(CLASSES),soft[ids]);print('trained PP fold',f,flush=True)
    models=dict(old,pp=pp);save(OUT/'models.json',models);save(OUT/'training-provenance.json',dict(views=provenance,fold_excluded_sids={str(f):sorted(s['sent_id'] for s in source('fit') if fold(s['sent_id'])==f) for f in range(3)}));save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in (OUT/'models.json',OUT/'training-provenance.json')}))
    calpublic,callabels=transfer_rows(source('calibration'),anchors,'cal89',classes);cal={a:{} for a in ('original','augmented')}
    for pattern,replacements in patterns.items():
        changed=perturb(calpublic,replacements,anchors);queries=query_rows(changed,callabels)
        for arm,model in (('original',old),('augmented',models)):
            folder=OUT/('calibration-'+arm+'-'+pattern);folder.mkdir();rows=infer85(queries,model);save(folder/'predictions.json',rows);cal[arm][pattern]=rows
    policies={}
    for arm,by_pattern in cal.items():
        selected,curve=robust_policy(by_pattern,232);clean=select_policy(by_pattern['correct'],'pp','pooled_pos')['precision90'];policies[arm]=dict(robust_threshold=selected['threshold'] if selected else None,clean_threshold=clean['threshold'] if clean else None);save(OUT/('calibration-curve-'+arm+'.json'),curve);print('calibration policy',arm,policies[arm],flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json']+list(OUT.glob('calibration-*/predictions.json'))+list(OUT.glob('calibration-curve-*.json'))}))
    datasets={'source':source('test')};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={}
    for name,sentences in datasets.items():
        public,labels=transfer_rows(sentences,anchors,'eval89-'+name,classes)
        for pattern,replacements in patterns.items():
            changed=perturb(public,replacements,anchors);queries=query_rows(changed,labels);folder=OUT/(name.lower()+'-'+pattern);folder.mkdir();rows=infer85(queries,models);save(folder/'predictions.json',rows);save(folder/'prediction-freeze.json',dict(inputs={str(folder/'predictions.json'):digest(folder/'predictions.json')}));oldrows=load(ROOT/'iteration87'/(name.lower()+'-195-'+pattern)/'predictions.json');result={}
            for arm,rr in (('original',oldrows),('augmented',rows)):
                result[arm]=dict(fixed_80=score(rr,.8),clean_policy=score(rr,policies[arm]['clean_threshold']),robust_policy=score(rr,policies[arm]['robust_threshold']))
            result['nearest_f1']=counts(rows,'pp','left',oldpol['left']['standard']['f1']['threshold']);result['strict88']=load(ROOT/'iteration88/evaluation-tradeoff-grid.json')[name+'/195/'+pattern]['0.0']['selected'];save(folder/'evaluation.json',result);summary[name+'/'+pattern]=result
        print('evaluated',name,flush=True)
    save(OUT/'evaluation.json',summary)
if __name__=='__main__':run()
