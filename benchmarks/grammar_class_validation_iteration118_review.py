"""Independent masked inference, projection, and class-metric verification."""
from benchmarks.grammar_class_validation_iteration118 import *
from voynich_smt.paired_anchor_class import target_features
from scipy.special import expit


def run():
    hashes=0
    for name in ['design-freeze','context-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    selection=load(OUT/'selection.json');ids=selection['ids'];part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert ids==part['test'] and not set(ids)&(set(part['fit'])|set(part['calibration'])|reserved)
    cache=load(ROOT/'iteration44/annotations-truth.json');words=load(OUT/'input-words.json');assert words==[dict(sent_id=i,author=cache[i]['author'],tokens=[dict(word=t['word']) for t in cache[i]['tokens']]) for i in ids];anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];public=ag.public_sentences(words,anchors,'class118');assert public==load(OUT/'public.json');byid={s['sent_id']:s for s in public};targets=selection['types'];lookup={w:hashlib.sha256(('class118|'+w).encode()).hexdigest() for w in targets};hidden=set(lookup.values());model=load(ROOT/'iteration116/class-models.json')['final'];offset=load(ROOT/'iteration117/models.json')['balanced13']['offset'];predictions=load(OUT/'predictions.json');details=load(OUT/'reference-details.json');summary=load(OUT/'summary.json');profiles=load(OUT/'profiles.json');comparisons=0;inferences=0
    for view,vids in selection['views'].items():
        p=[byid[i] for i in vids];rr=target_features(p,hidden);q=ag.predict([r['features'] for r in rr],model);rows=predictions[view]['rows'];assert {r['type'] for r in rows}|set(predictions[view]['missing_types'])==set(targets)
        for r in rows:
            ii=[i for i,s in enumerate(rr) if s['word']==r['opaque']];mean=float(q[ii,1].mean());ns=len({rr[i]['sid'] for i in ii});assert len(ii)==r['n'] and ns==r['sentences'] and r['supported']==(len(ii)>=5 and ns>=3);assert abs(mean-r['probabilities']['raw'])<1e-12;cal=float(expit(math.log((mean+1e-12)/(1-mean+1e-12))+offset));assert abs(cal-r['probabilities']['balanced13'])<1e-12;inferences+=1
        reference={r['type']:r for r in details[view]};assert all(reference[r['type']]==dict(r,**{'class':anchors[r['type']]}) for r in rows)
        split=load(ROOT/'iteration116/type-split.json')
        for name,ms in summary[view]['metrics'].items():
            selected=[reference[r['type']] for r in rows if name=='all' or name=='supported' and r['supported'] or name=='unsupported' and not r['supported'] or name in ['ADP','CCONJ'] and anchors[r['type']]==name or name=='earlier_calibration8' and r['type'] in split['calibration'] or name=='earlier_evaluation8' and r['type'] in split['evaluation']]
            for arm,m in ms.items():
                n=len(selected);assert m['n']==n
                if not n:assert m['accuracy'] is None;continue
                ys=np.array([r['class']=='CCONJ' for r in selected]);ps=np.array([r['probabilities'][arm] for r in selected]);pred=ps>.5;correct=int((pred==ys).sum());loss=float(-np.mean(np.log(np.where(ys,ps,1-ps))));assert m['correct']==correct and m['accuracy']==correct/n and abs(m['nll']-loss)<1e-12;assert abs(m['brier']-float(np.mean((ps-ys)**2)))<1e-12
                nwords=np.array([r['n'] for r in selected]);assert abs(m['token_weighted_accuracy']-float(np.dot(nwords,pred==ys)/nwords.sum()))<1e-12
                if ys.any() and (~ys).any():
                    pos=ps[ys];neg=ps[~ys];auc=float(np.mean((pos[:,None]>neg[None,:])+.5*(pos[:,None]==neg[None,:])));assert m['auc']==auc
                else:assert m['auc'] is None
                expected=dict(ADP_as_ADP=int((~ys&~pred).sum()),ADP_as_CCONJ=int((~ys&pred).sum()),CCONJ_as_ADP=int((ys&~pred).sum()),CCONJ_as_CCONJ=int((ys&pred).sum()));assert expected==m['confusion'];comparisons+=1
    # Poisoning target identities/classes must not alter inference features.
    poison=[dict(s,tokens=[dict(t,anchor='POISON',tag='POISON') if t['id'] in hidden else dict(t) for t in s['tokens']]) for s in public];a=target_features(public,hidden);b=target_features(poison,hidden);assert a==b
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,source_split_and_preprojection_reserve_exclusion_verified=True,word_only_cache_projection_reconstructed=True,public_inputs_reconstructed=True,independent_type_probabilities_verified=inferences,independent_metric_groups_verified=comparisons,target_identity_and_class_poison_invariance=True,no_training_or_policy_changes=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
