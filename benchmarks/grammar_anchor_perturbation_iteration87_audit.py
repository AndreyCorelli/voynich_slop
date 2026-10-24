"""Replay every perturbation, baseline and annotation-free inference invariant."""
from benchmarks.grammar_anchor_perturbation_iteration87 import *

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    data=load(ROOT/'iteration44/annotations-truth.json');part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];catalogue=load(ROOT/'iteration85/anchor-budgets.json');source=lambda split:[dict(sent_id=sid,**data[sid]) for sid in part[split]]
    patterns=load(OUT/'patterns.json');assert patterns==source_patterns(source('fit'),catalogue['20']);datasets={'source':source('test')};cache=load(CACHE);decl=load(DECLARATION)['split_ids'];datasets.update({a:cached_sentences(cache,decl[a]) for a in AUTHORS});summary={};checked=0
    for name,sentences in datasets.items():
        for budget,kind in SETTINGS.items():
            base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');public,labels=transfer_rows(sentences,catalogue[budget],'stress87-'+name,models['pos_classes']);baseline=None
            for pattern,replacements in patterns.items():
                folder=OUT/(name.lower()+'-'+budget+'-'+pattern)
                for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
                changed=perturb(public,replacements,catalogue[budget]);assert changed==load(folder/'public.json');rows=load(folder/'predictions.json');q=query_rows(changed,labels)
                # Inference receives no reference POS, head, relation or Case.
                assert all(set(r)=={'sid','index','word','anchor_tag','features','labels','masked_center'} for r in q)
                replay=infer85(q,models)
                for r,t in zip(rows,replay):
                    assert all(r[k]==t[k] for k in ('sid','index','word','visible','labels'))
                    for arm in ARMS:assert math.isclose(r['scores'][arm]['pp'],t['scores'][arm]['pp'],rel_tol=1e-10,abs_tol=1e-12)
                assert [t['id'] for s in public for t in s['tokens']]==[t['id'] for s in changed for t in s['tokens']]
                if pattern=='correct':
                    baseline=rows
                    oldpath=base/'predictions.json' if name=='source' else ROOT/'iteration86'/(name.lower()+'-'+budget)/'predictions.json'
                    old=load(oldpath);assert len(old)==len(rows)
                    for r,t in zip(rows,old):
                        assert (r['sid'],r['index'],r['labels'])==(t['sid'],t['index'],t['labels'])
                        for arm in ARMS:assert math.isclose(r['scores'][arm]['pp'],t['scores'][arm]['pp'],rel_tol=1e-10,abs_tol=1e-12)
                result=eval_transfer(rows,pol,kind);assert result['threshold']==(.81 if budget=='20' else .8);result['transitions']=transitions(rows,baseline,result['threshold']);result['changed_anchor_tokens']=sum(x!=y for s,t in zip(public,changed) for x,y in zip(s['tokens'],t['tokens']));assert result==load(folder/'evaluation.json');summary[name+'/'+budget+'/'+pattern]=result
    assert summary==load(OUT/'evaluation.json')
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all_36_conditions_replayed=True,baseline_reproduces_85_86=True,opaque_ids_preserved=True,source_only_pattern_selection=True,fixed_thresholds=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('Audit passed;',checked,'prior hashes')
if __name__=='__main__':run()
