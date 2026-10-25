"""Audit fixed-author inference, masking, metrics, and common-type comparisons."""
from benchmarks.grammar_balanced_transfer_iteration125 import *
from voynich_smt.paired_anchor_class import target_features
from scipy.special import expit


def run():
    hashes=0
    for name in ['design-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    selection=load(OUT/'selection.json');predictions=load(OUT/'predictions.json');details=load(OUT/'reference-details.json');summary=load(OUT/'summary.json');volume=load(OUT/'volume-comparison.json');words=load(ROOT/'iteration93/types.json')['candidates'];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];model=load(ROOT/'iteration124/models.json')['final'];offset=load(ROOT/'iteration124/calibrator.json')['offset'];split=load(ROOT/'iteration116/type-split.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};typechecks=0;metricchecks=0;poisons=0
    for author,paths in INPUTS.items():
        publics={v:load(p) for v,p in paths.items()};assert publics['expanded'][:100]==publics['base'];lookup=selection[author]['lookup'];hidden=set(lookup.values());assert not set(words)&set(split['training'])
        for view,p in publics.items():
            key=author+'/'+view;assert not {s['sent_id'] for s in p}&reserved;meta=selection[author]['views'][view];assert meta['sids']==[s['sent_id'] for s in p] and meta['tokens']==sum(len(s['tokens']) for s in p);rr=target_features(p,hidden);q=ag.predict([r['features'] for r in rr],model);rows=predictions[key]['rows'];assert {r['type'] for r in rows}|set(predictions[key]['missing_types'])==set(words)
            for r in rows:
                ii=[i for i,t in enumerate(rr) if t['word']==r['opaque']];n=len(ii);ns=len({rr[i]['sid'] for i in ii});raw=float(q[ii,1].mean());cal=float(expit(math.log((raw+1e-12)/(1-raw+1e-12))+offset));assert n==r['n'] and ns==r['sentences'] and r['supported']==(n>=5 and ns>=3);assert abs(raw-r['probabilities']['raw'])<1e-12 and abs(cal-r['probabilities']['balanced124'])<1e-12;typechecks+=1
            poisoned=[dict(s,tokens=[dict(t,anchor='POISON',tag='POISON') if t['id'] in hidden else dict(t) for t in s['tokens']]) for s in p];assert target_features(poisoned,hidden)==rr;poisons+=1
            previous={r['type']:r for r in load(ROOT/'iteration119/predictions.json')[key]['rows']};assert all(r['probabilities']['previous']==previous[r['type']]['probabilities']['balanced13'] for r in rows)
            assert details[key]==[dict(r,**{'class':anchors[r['type']]}) for r in rows]
            for g,ms in summary[key]['metrics'].items():
                selected=[r for r in details[key] if g=='all' or g=='supported' and r['supported'] or g=='unsupported' and not r['supported'] or g in ['ADP','CCONJ'] and r['class']==g or g=='earlier_calibration8' and r['type'] in split['calibration'] or g=='earlier_evaluation8' and r['type'] in split['evaluation']]
                for arm,m in ms.items():
                    assert m['n']==len(selected)
                    if not selected:assert m['accuracy'] is None;continue
                    pp=np.array([r['probabilities'][arm] for r in selected]);yy=np.array([r['class']=='CCONJ' for r in selected]);pred=pp>.5;correct=int((pred==yy).sum());assert m['correct']==correct and m['accuracy']==correct/len(selected);assert abs(m['nll']-float(-np.log(np.where(yy,pp,1-pp)).mean()))<1e-12 and abs(m['brier']-float(((pp-yy)**2).mean()))<1e-12
                    nn=np.array([r['n'] for r in selected]);assert abs(m['token_weighted_accuracy']-float(np.dot(nn,pred==yy)/nn.sum()))<1e-12
                    if yy.any() and (~yy).any():
                        pos=pp[yy];neg=pp[~yy];auc=float(np.mean((pos[:,None]>neg[None,:])+.5*(pos[:,None]==neg[None,:])));assert m['auc']==auc
                    else:assert m['auc'] is None
                    assert m['confusion']==dict(ADP_as_ADP=int((~yy&~pred).sum()),ADP_as_CCONJ=int((~yy&pred).sum()),CCONJ_as_ADP=int((yy&~pred).sum()),CCONJ_as_CCONJ=int((yy&pred).sum()));metricchecks+=1
        before={r['type']:r for r in details[author+'/base']};after={r['type']:r for r in details[author+'/expanded']};common=sorted(set(before)&set(after));assert volume[author]['common_types']==common and volume[author]['new_types']==sorted(set(after)-set(before))
        for arm in ['raw','balanced124','previous']:
            correct=lambda r:(r['probabilities'][arm]>.5)==(r['class']=='CCONJ');tr=volume[author]['transitions'][arm];assert tr['gained']==[w for w in common if not correct(before[w]) and correct(after[w])];assert tr['lost']==[w for w in common if correct(before[w]) and not correct(after[w])];new=sorted(set(after)-set(before));assert tr['new_correct']==[w for w in new if correct(after[w])];assert tr['new_wrong']==[w for w in new if not correct(after[w])]
            for phase,rr in [('before',before),('after',after)]:
                selected=[rr[w] for w in common];expected=volume[author]['common_metrics'][arm][phase];assert expected['correct']==sum(correct(r) for r in selected);assert expected['n']==len(common)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,independent_type_probabilities_verified=typechecks,independent_metric_groups_verified=metricchecks,target_poison_invariance_views=poisons,common_type_volume_comparisons_replayed=2,original_prefixes_unchanged=True,reserve_ids_absent=True,no_refit_or_policy_change=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
