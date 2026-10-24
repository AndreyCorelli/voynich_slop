"""Replay cached-author transfer, frozen thresholds and opaque-input invariance."""
from benchmarks.grammar_anchor_transfer_iteration86 import *

def run():
    for p,h in load(OUT/'design-freeze.json')['inputs'].items():assert digest(p)==h,p
    selected=load(OUT/'selected-ids.json');declaration=load(DECLARATION)['split_ids'];cache=load(CACHE);catalogue=load(ROOT/'iteration85/anchor-budgets.json');source={sid for ids in load(ROOT/'iteration49/manifest.json')['partitions']['0'].values() for sid in ids};reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};evaluation={};details={}
    for author in AUTHORS:
        assert selected[author]==declaration[author] and len(selected[author])==100;assert not set(selected[author])&(source|reserved);sentences=cached_sentences(cache,selected[author])
        for budget,kind in SETTINGS.items():
            folder=OUT/(author.lower()+'-'+budget)
            for p,h in load(folder/'prediction-freeze.json')['inputs'].items():assert digest(p)==h,p
            base=ROOT/('iteration85/budget-'+budget);models=load(base/'models.json');pol=load(base/'policies.json');pub,q=transfer_rows(sentences,catalogue[budget],'transfer86-'+author,models['pos_classes']);assert pub==load(folder/'public.json');rows=load(folder/'predictions.json');replay=infer85(q,models);assert len(rows)==sum(len(s['tokens']) for s in sentences)
            for x,y in zip(rows,replay):
                assert all(x[k]==y[k] for k in ('sid','index','word','visible','labels'))
                for arm in ARMS:assert math.isclose(x['scores'][arm]['pp'],y['scores'][arm]['pp'],abs_tol=1e-12,rel_tol=1e-10)
            result=eval_transfer(rows,pol,kind);assert result==load(folder/'evaluation.json');evaluation[author+'/'+budget]=result
            assert result['threshold']==(.81 if budget=='20' else .8)
            altered=[dict(s,tokens=[dict(t,pos='X',head=None,rel='root') for t in s['tokens']]) for s in sentences];_,changedq=transfer_rows(altered,catalogue[budget],'differentKEY',models['pos_classes']);changed=infer85(changedq,models)
            for x,y in zip(rows,changed):
                for arm in ARMS:assert math.isclose(x['scores'][arm]['pp'],y['scores'][arm]['pp'],abs_tol=1e-12,rel_tol=1e-10)
            mcut=pol['pooled_pos']['standard']['f1']['threshold'];lcut=pol['left']['standard']['f1']['threshold'];mp={(r['sid'],r['index']) for r in rows if r['scores']['pooled_pos']['pp']>=mcut};lp={(r['sid'],r['index']) for r in rows if r['scores']['left']['pp']>=lcut};p=result['threshold'];sp={(r['sid'],r['index']) for r in rows if r['scores']['pooled_pos']['pp']>=p}
            details[author+'/'+budget]=dict(model_f1_equals_nearest_predictions=mp==lp,selected_outside_nearest_f1=len(sp-lp),model_f1_only=len(mp-lp),nearest_f1_only=len(lp-mp),hidden_selected=sum(not r['visible'] and r['scores']['pooled_pos']['pp']>=p for r in rows))
    assert evaluation==load(OUT/'evaluation.json')
    checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    result=dict(cached_author_sentences={a:len(ids) for a,ids in selected.items()},all_predictions_replayed=True,private_annotation_and_rekey_invariance=True,no_source_overlap=True,reserve_unscored=True,prior_input_hashes_verified=checked,comparison=details);save(OUT/'audit.json',result);print(result)
if __name__=='__main__':run()
