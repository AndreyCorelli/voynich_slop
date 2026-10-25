"""Replay balanced-loss training, masked predictions and structural metrics."""
from benchmarks.grammar_balanced_training_iteration124 import *
from scipy.optimize import check_grad

def run():
    hashes=0
    for name in ['design-freeze','model-freeze','class-predictions-freeze','pp-input-freeze','pp-predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    # Finite-difference check on an imbalanced multiclass fixture.
    x=ag.matrix([['a','b'],['b'],['a'],['c']],{'a':0,'b':1,'c':2});y=np.array([0,0,0,1]);weight=np.array([1/6,1/6,1/6,1/2]);w=np.linspace(-.3,.4,6);err=check_grad(lambda z:weighted_objective(z,x,y,weight)[0],lambda z:weighted_objective(z,x,y,weight)[1],w);assert err<1e-6
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];split=load(ROOT/'iteration116/type-split.json');train=split['training'];targets=load(ROOT/'iteration93/types.json')['candidates'];assert not set(train)&set(targets);data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(part['fit'])&reserved
    fit=ag.public_sentences([dict(sent_id=i,tokens=[dict(word=t['word']) for t in data[i]['tokens']]) for i in part['fit']],anchors,'fit116');lookup={t['anchor']:t['id'] for s in fit for t in s['tokens'] if t['anchor'] is not None};hidden={lookup[w] for w in targets};models=load(OUT/'models.json');prov=load(OUT/'training-provenance.json');oldprov=load(ROOT/'iteration116/training-provenance.json');oof={}
    for key in ['0','1','2','final']:
        held=[] if key=='final' else [w for w in train if split['oof_folds'][w]==int(key)];tr=[w for w in train if w not in held];hid=hidden|{lookup[w] for w in held};m,p=train_balanced(fit,tr,hid,lookup,anchors);assert p==({k:v for k,v in prov[key].items() if k not in ['train','held']});assert p['sampled_rows']==(oldprov[key] if key=='final' else oldprov[key]['sampled_rows']);assert np.allclose(m['weights'],models[key]['weights'],rtol=1e-4,atol=1e-4);assert np.allclose(p['class_weight_mass'],[.5,.5]);oof.update(grouped_profile(fit,held,lookup,hid,models[key]))
    assert all(np.allclose(oof[w]['profile'],load(OUT/'oof-profiles.json')[w]['profile'],rtol=1e-12,atol=1e-12) for w in train);cal=fit_offset([oof[w]['mean'] for w in train],[int(anchors[w]=='CCONJ') for w in train],True);assert abs(cal['offset']-load(OUT/'calibrator.json')['offset'])<1e-10
    public=load(ROOT/'iteration118/public.json');assert [s['sent_id'] for s in public]==part['test'];assert not set(part['test'])&(set(part['fit'])|set(part['calibration'])|reserved);rows=load(OUT/'predictions.json');lookup={r['type']:r['opaque'] for r in rows};hidden=set(lookup.values());profiles=grouped_profile(public,targets,lookup,hidden,models['final']);assert all(np.allclose(profiles[w]['profile'],load(OUT/'profiles.json')[w]['profile'],rtol=1e-12,atol=1e-12) for w in targets);assert len(rows)==16
    for r in rows:assert abs(r['probabilities']['balanced']-float(apply_offset([profiles[r['type']]['mean']],cal)[0]))<1e-12
    # Independent type-level accuracy/NLL, and rank-order comparison.
    summary=load(OUT/'class-summary.json');y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);ranks={}
    for arm in ['raw','balanced','previous','prior']:
        p=np.array([r['probabilities'][arm] for r in rows]);assert summary[arm]['correct']==int(((p>.5)==y).sum());assert abs(summary[arm]['nll']-float(-np.mean(np.log(np.where(y,p,1-p)))))<1e-12;ranks[arm]=p
    tags={r['opaque']:('CCONJ' if r['probabilities']['balanced']>.5 else 'ADP') for r in rows};view=load(OUT/'public.json');assert view==inject(public,hidden,tags);assert tags==load(OUT/'assignments.json');labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];scores=load(OUT/'scores.json');old=load(ROOT/'iteration120/scores-predicted.json');unknown=load(ROOT/'iteration120/scores-unknown.json');settings=load(ROOT/'iteration120/settings.json');cohorts=load(ROOT/'iteration120/cohorts.json');evaluation=load(OUT/'evaluation.json');checks=0
    for name,m in [('original',load(BASE/'models.json')),('augmented',load(ROOT/'iteration89/models.json'))]:
        expected=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),m)];assert np.allclose(expected,scores[name],rtol=1e-12,atol=1e-12)
        for policy,cut in settings[name].items():
            for c,ii in cohorts.items():
                a=np.array(scores[name])[ii]>=cut;t=np.array([labels[i]['labels']['pp'] for i in ii],bool);e=evaluation[name][policy][c];assert [e['metrics'][k] for k in ['tp','fp','fn','tn']]==[int((a&t).sum()),int((a&~t).sum()),int((~a&t).sum()),int((~a&~t).sum())]
                for key,base in [('previous',old),('unknown',unknown)]:
                    b=np.array(base[name])[ii]>=cut;assert e['changes_from_'+key]==dict(new_tp=int((a&~b&t).sum()),new_fp=int((a&~b&~t).sum()),lost_tp=int((~a&b&t).sum()),removed_fp=int((~a&b&~t).sum()))
                checks+=1
    flips=[dict(type=r['type'],previous='CCONJ' if r['probabilities']['previous']>.5 else 'ADP',balanced=tags[r['opaque']],reference=anchors[r['type']]) for r in rows if (r['probabilities']['previous']>.5)!=(r['probabilities']['balanced']>.5)];save(OUT/'class-changes.json',flips);save(OUT/'audit.json',dict(input_hashes_verified=hashes,gradient_check_error=err,models_retrained=4,same_sampled_rows_as116=True,oof_profiles_replayed=13,test_profiles_replayed=16,pp_score_vectors_recomputed=2,independent_metric_transition_groups=checks,all_checks_passed=True));print(load(OUT/'audit.json'));print('CHANGES',flips)
if __name__=='__main__':run()
