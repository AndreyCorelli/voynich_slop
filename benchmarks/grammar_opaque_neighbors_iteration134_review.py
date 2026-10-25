"""Replay frozen opaque-neighbor features, held-type training and utility."""
from benchmarks.grammar_opaque_neighbors_iteration134 import *

def run():
    hashes=0
    for name in ['design-freeze','model-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    public,lookup,anchors,split,words,allowed=training_inputs();train=split['training'];assert not set(train)&set(words);models=load(OUT/'models.json');oof=load(OUT/'oof-profiles.json');prov=load(OUT/'training-provenance.json');oldprov=load(ROOT/'iteration132/training-provenance.json');cal=load(OUT/'calibrators.json');maxloss=maxpdiff=0.
    for arm in ARMS:
        rows=feature_rows(public,arm)
        for key in ['0','1','2','final']:
            held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key)];tr=[w for w in train if w not in held];m,p=fit_rows(rows,tr,lookup,anchors);assert p==prov[arm][key]==oldprov[key]['sampled_rows'];assert m['vocabulary']==models[arm][key]['vocabulary'];ld=abs(m['loss']-models[arm][key]['loss']);xx=[r['features'] for w in tr for r in cap_rows([r for r in rows if r['word']==lookup[w]])];pd=float(np.max(np.abs(ag.predict(xx,m)-ag.predict(xx,models[arm][key]))));maxloss=max(maxloss,ld);maxpdiff=max(maxpdiff,pd);assert ld<1e-8 and pd<1e-4
            expected=profiles_rows(rows,held,lookup,models[arm][key]);assert all(abs(expected[w]['mean']-oof[arm][w]['mean'])<1e-12 for w in held)
        expected=fit_offset([oof[arm][w]['mean'] for w in train],[int(anchors[w]=='CCONJ') for w in train],True);assert abs(expected['offset']-cal[arm]['offset'])<1e-10
    contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p) for a,vv in INPUTS.items() for v,p in vv.items()});old=load(ROOT/'iteration132/predictions.json');pred=load(OUT/'predictions.json');scores=load(OUT/'scores.json');summary=load(OUT/'class-summary.json');evaluation=load(OUT/'evaluation.json');oldpp=load(ROOT/'iteration132/scores.json');labels={'source':load(BASE/'predictions.json')};labels.update({a+'-'+v:load(p) for a,p in LABELS.items() for v in ['base','expanded']});cohorts={'source':load(ROOT/'iteration120/cohorts.json')};cohorts.update({a+'-'+v:load(ROOT/'iteration130/cohorts.json')[a] for a in INPUTS for v in ['base','expanded']});reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not {s['sent_id'] for s in public}&reserved;types=checks=invariance=0
    for key,context in contexts.items():
        assert not {s['sent_id'] for s in context}&reserved;lookup={r['type']:r['opaque'] for r in old[key]};targets=set(lookup.values());masked=mask_budget(context,targets,allowed)
        identities=sorted({t['id'] for s in context for t in s['tokens']});rename={w:str(i) for i,w in enumerate(identities)};poison=[dict(s,tokens=[dict(id=rename[t['id']],anchor='POISON',tag='POISON') for t in s['tokens']]) for s in masked]
        for arm in ARMS:
            extras=neighbor_features(masked,arm=='recurrence');assert extras==neighbor_features(poison,arm=='recurrence');invariance+=1;rr=feature_rows(masked,arm);q=ag.predict([r['features'] for r in rr],models[arm]['final']);rows=pred[key][arm];tags={};previous={r['type']:r for r in old[key]};assert len(rows)==len(previous)
            for r in rows:
                ix=[i for i,t in enumerate(rr) if t['word']==r['opaque']];raw=float(q[ix,1].mean());assert r['n']==len(ix) and r['sentences']==len({rr[i]['sid'] for i in ix});assert abs(raw-r['probabilities']['raw'])<1e-12;assert abs(float(apply_offset([raw],cal[arm])[0])-r['probabilities']['new'])<1e-12;assert r['probabilities']['previous']==previous[r['type']]['probabilities']['matched'];tags[r['opaque']]='CCONJ' if r['probabilities']['new']>.5 else 'ADP';types+=1
            for name,m in summary[key][arm].items():
                p=np.array([r['probabilities'][name] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);assert m['correct']==int(((p>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12;assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])))
            view=load(OUT/('public-'+key+'-'+arm+'.json'));assert view==inject(masked if key=='source' else masked[:100],targets,tags);assert [(s['sent_id'],i) for s in view for i,t in enumerate(s['tokens'])]==[(r['sid'],r['index']) for r in labels[key]];expected=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels[key]),load(BASE/'models.json'))];assert np.allclose(expected,scores[key][arm],rtol=1e-12,atol=1e-12)
            for co,ii in cohorts[key].items():
                a=np.array(expected)[ii]>=.8;b=np.array(oldpp[key])[ii]>=.8;y=np.array([labels[key][i]['labels']['pp'] for i in ii],bool);e=evaluation[key][arm][co];m=e['metrics'];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert e['changes_from132']==dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));checks+=1
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,models_retrained=8,maximum_retrain_loss_difference=maxloss,maximum_retrain_training_probability_difference=maxpdiff,identical_sampled_rows_verified=True,oof_profiles_replayed=26,target_probabilities_recomputed=types,opaque_renaming_and_private_field_poison_invariance_views=invariance,pp_vectors_recomputed=10,metric_transition_groups=checks,strict_type_and_reserve_exclusion_checked=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
