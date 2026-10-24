"""Replay all deletions, policy selection and baseline identity."""
from benchmarks.grammar_anchor_stability_iteration88 import *

def run():
    for freeze in ('design-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]]
    catalogue=load(ROOT/'iteration85/anchor-budgets.json');patterns=load(OUT/'patterns.json');assert patterns==source_patterns(source('fit'),catalogue['20']);uncertain=list(patterns['missing_top5']);policies=load(OUT/'policies.json');cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets={'calibration':source('calibration'),'source':source('test')};datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={};curves={b:{str(s):{} for s in SLACKS} for b in SETTINGS};conditions=0
    for name,sentences in datasets.items():
        for budget in SETTINGS:
            base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');threshold=.81 if budget=='20' else .8;salt='cal88' if name=='calibration' else 'eval88-'+name;public,labels=transfer_rows(sentences,catalogue[budget],salt,models['pos_classes'])
            for pattern,replacements in patterns.items():
                folder=OUT/(name.lower()+'-'+budget+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                stored=load(folder/'scores.json');changed=perturb(public,replacements,catalogue[budget]);rows,hidden=stability_predictions(changed,labels,catalogue[budget],models,uncertain)
                assert np.allclose(hidden,stored['hidden'],rtol=1e-10,atol=1e-12)
                for r,t in zip(rows,stored['rows']):
                    assert all(r[k]==t[k] for k in ('sid','index','word','visible','labels'))
                    for arm in ARMS:assert math.isclose(r['scores'][arm]['pp'],t['scores'][arm]['pp'],rel_tol=1e-10,abs_tol=1e-12)
                rows=stored['rows'];hidden=stored['hidden'];assert apply(rows,hidden,threshold,1.)==rows
                if name=='calibration':
                    for slack in SLACKS:curves[budget][str(slack)][pattern]=counts(apply(rows,hidden,threshold,slack),'pp','pooled_pos',threshold)
                else:
                    old=load(ROOT/'iteration87'/(name.lower()+'-'+budget+'-'+pattern)/'predictions.json')
                    for r,t in zip(rows,old):
                        assert (r['sid'],r['index'],r['labels'])==(t['sid'],t['index'],t['labels'])
                        for arm in ARMS:assert math.isclose(r['scores'][arm]['pp'],t['scores'][arm]['pp'],rel_tol=1e-10,abs_tol=1e-12)
                    result=evaluate(rows,hidden,threshold,policies[budget]['slack'],pol);assert result==load(folder/'evaluation.json');assert result['transitions']['new_tp']==result['transitions']['new_fp']==0;summary[name+'/'+budget+'/'+pattern]=result
                conditions+=1
            print('replayed',name,budget,flush=True)
    for b,curve in curves.items():assert curve==load(OUT/('calibration-curve-'+b+'.json'));assert select_slack(curve)==policies[b]
    assert summary==load(OUT/'evaluation.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    for p,h in load(OUT/'tradeoff-reporting-freeze.json')['inputs'].items():assert digest(p)==h,p
    grid=load(OUT/'evaluation-tradeoff-grid.json');hidden_diagnostic=load(OUT/'strict-hidden-diagnostic.json')
    for key,curve in grid.items():
        name,b,pattern=key.split('/');stored=load(OUT/(name.lower()+'-'+b+'-'+pattern)/'scores.json');pol=load(ROOT/('iteration85/budget-'+b)/'policies.json');threshold=.81 if b=='20' else .8
        for slack,result in curve.items():assert result==evaluate(stored['rows'],stored['hidden'],threshold,float(slack),pol)
        if key in hidden_diagnostic:
            strict=apply(stored['rows'],stored['hidden'],threshold,0.)
            assert hidden_diagnostic[key]==counts([r for r in strict if not r['visible']],'pp','pooled_pos',threshold)
    save(OUT/'audit.json',dict(tradeoff_grid_and_hidden_diagnostics_verified=True,conditions_replayed=conditions,deletion_inferences_replayed=conditions*5,baseline_reproduces_iteration87=True,calibration_policy_replayed=True,only_abstains=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
