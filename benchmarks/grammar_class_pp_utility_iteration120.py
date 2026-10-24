"""Do frozen inferred classes improve structure when identities remain opaque?"""
from benchmarks.grammar_class_transfer_iteration119 import *
from voynich_smt.opaque_class_tags import inject
OUT=ROOT/'iteration120'
SETTINGS={'original':{'fixed80':.8,'source_f1':.55},'augmented':{'selected71':.71,'fixed80':.8}}


def confusion(labels,probabilities,cut,indices):
    tp=fp=fn=tn=0
    for i in indices:
        positive=probabilities[i]>=cut;gold=labels[i]['labels']['pp'];tp+=positive and gold;fp+=positive and not gold;fn+=not positive and gold;tn+=not positive and not gold
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.)


def changes(labels,before,after,cut,indices):
    d=dict(new_tp=0,new_fp=0,lost_tp=0,removed_fp=0)
    for i in indices:
        b=before[i]>=cut;a=after[i]>=cut;gold=labels[i]['labels']['pp']
        if a and not b:d['new_tp' if gold else 'new_fp']+=1
        if b and not a:d['lost_tp' if gold else 'removed_fp']+=1
    return d


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/opaque_class_tags.py'),ROOT/'iteration118/verification-manifest.json',ROOT/'iteration118/public.json',ROOT/'iteration118/predictions.json',ROOT/'iteration118/selection.json',ROOT/'iteration116/class-models.json',ROOT/'iteration117/models.json',BASE/'models.json',BASE/'predictions.json',BASE/'policies.json',ROOT/'iteration89/models.json',ROOT/'iteration89/policies.json',Path('experiments/holdouts/grammar-construction-next.json')]
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='SOURCE-ONLY structuralutility test, exact118test770/9956publicpositions; alreadycached85PPlabels reusedONLY, nonewannotations/author/reserve/sealedtest. NewclassscoresEXACT118frozen116/117balanced13,no refit/recalibration. ALL16targetlexicalnames hidden(None) inEVERYarm, IDs/positions/content/other179suppliedanchorsunchanged. Arms unknown(X),predictedhardclass(q>.5CCONJ,elseADP),oracle suppliedmodalclasses asprivilegedceiling,allADP,allCCONJ,3type-consistentshufflesofpredictedtags seed12000/12001/12002. ShufflespreservetypeclasscountsNOTtokenweightedclassmass; reportboth. Hardtags feedexisting85anchor_overrideonehotPOS, NOTsoftprobabilityfusion; inferredclassvisibilitydoesNOTcreateplaintextidentity. Freezeinputs/classes beforePPinference. FixedPPmodels85originaland89augmented,no training; primaryoriginal.80,secondaryoriginalsourceF1.55(assert85policy)/aug.71and.80,reportall,no winningcutoffchoice. Fixedcohorts all9956,originalunmappedcontentpositions,target16positions,othergivenanchors; doNOTcomparechangingvisibleflagcohorts. FreezeALLPPscoresbeforemetrics. Structuralutilityprimarygate: predictedTP>unknownTP,F1>unknownF1,precision>=.90 ANDF1>mean3shuffleF1 at original.80 allpositions. No default adoption evenifgatepasses; gatefailure preservedwithallgrossnewTP/newFP/lostTP/removedFP,oracle/allADPcontrols. Constantmodalclasses notnewtokenPOSoracle; PPmodelpreviouslytrainedwithtargettypes butlexicaltargetnames neveravailableatest. Source-testadaptivelyreused elsewhere, notfreshconfirmation. No nucleus/fullgrammar/expandedcleanPPclaim withoutactualmetrics.'))
    public=load(ROOT/'iteration118/public.json');assert len(public)==770;reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in public}&reserved;pred=load(ROOT/'iteration118/predictions.json')['full']['rows'];ids={r['opaque'] for r in pred};assert len(ids)==16;anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];wordbyid={r['opaque']:r['type'] for r in pred};assigned={r['opaque']:('CCONJ' if r['probabilities']['balanced13']>.5 else 'ADP') for r in pred};oracle={i:anchors[wordbyid[i]] for i in ids};assignments=dict(unknown={},predicted=assigned,oracle=oracle,all_ADP={i:'ADP' for i in ids},all_CCONJ={i:'CCONJ' for i in ids})
    orderedids=sorted(ids)
    for seed in range(3):assignments['shuffle'+str(seed)]=dict(zip(orderedids,np.random.default_rng(12000+seed).permutation([assigned[i] for i in orderedids]).tolist()))
    views={a:inject(public,ids,tags) for a,tags in assignments.items()};labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];positions=[(s['sent_id'],i) for s in public for i,t in enumerate(s['tokens'])];assert positions==[(r['sid'],r['index']) for r in labels] and len(labels)==9956
    flat=[t for s in public for t in s['tokens']];cohorts=dict(all=list(range(len(flat))),original_unmapped=[i for i,t in enumerate(flat) if t['anchor'] is None],targets=[i for i,t in enumerate(flat) if t['id'] in ids],other_given_anchors=[i for i,t in enumerate(flat) if t['anchor'] is not None and t['id'] not in ids]);assert len(cohorts['original_unmapped'])+len(cohorts['targets'])+len(cohorts['other_given_anchors'])==9956;save(OUT/'cohorts.json',cohorts);save(OUT/'assignments.json',assignments);save(OUT/'settings.json',SETTINGS);save(OUT/'input-class-summary.json',{a:dict(type_counts=dict(Counter(tags.values())),target_token_counts=dict(Counter(t['tag'] for s in views[a] for t in s['tokens'] if t['id'] in ids))) for a,tags in assignments.items()})
    for arm,view in views.items():
        assert all(t['anchor'] is None for s in view for t in s['tokens'] if t['id'] in ids);save(OUT/('public-'+arm+'.json'),view)
    save(OUT/'input-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'assignments.json',OUT/'cohorts.json',OUT/'settings.json',OUT/'input-class-summary.json']+list(OUT.glob('public-*.json'))}));assert load(BASE/'policies.json')['pooled_pos']['standard']['f1']['threshold']==.55
    models={'original':load(BASE/'models.json'),'augmented':load(ROOT/'iteration89/models.json')};scores={}
    for arm,view in views.items():
        scores[arm]={name:[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),m)] for name,m in models.items()};save(OUT/('scores-'+arm+'.json'),scores[arm]);print('inferred',arm,flush=True)
    save(OUT/'predictions-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('scores-*.json')}));evaluation={}
    for arm,by_model in scores.items():
        evaluation[arm]={}
        for name,cuts in SETTINGS.items():
            evaluation[arm][name]={}
            for policy,cut in cuts.items():
                evaluation[arm][name][policy]={c:dict(metrics=confusion(labels,by_model[name],cut,ii),changes_from_unknown=changes(labels,scores['unknown'][name],by_model[name],cut,ii),probability_l1_from_unknown=sum(abs(by_model[name][i]-scores['unknown'][name][i]) for i in ii)) for c,ii in cohorts.items()}
    save(OUT/'evaluation.json',evaluation);u=evaluation['unknown']['original']['fixed80']['all']['metrics'];p=evaluation['predicted']['original']['fixed80']['all']['metrics'];sf=float(np.mean([evaluation['shuffle'+str(i)]['original']['fixed80']['all']['metrics']['f1'] for i in range(3)]));gate_result=dict(passed=bool(p['tp']>u['tp'] and p['f1']>u['f1'] and p['precision'] is not None and p['precision']>=.90 and p['f1']>sf),unknown=u,predicted=p,mean_shuffle_f1=sf);save(OUT/'utility-gate.json',gate_result);print('GATE',gate_result,flush=True)
if __name__=='__main__':run()
