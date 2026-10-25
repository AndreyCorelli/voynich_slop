"""Replay factorial inputs, oracle privilege boundaries, scores and effects."""
from benchmarks.grammar_sparse_factorial_iteration131 import *

def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];allowed={r['type'] for r in load(ROOT/'iteration129/anchor-ranking.json')[:5]};contexts={'source':load(ROOT/'iteration118/public.json')};contexts.update({a+'-'+v:load(p)[:100] for a,paths in INPUTS.items() for v,p in paths.items()});labels={'source':load(BASE/'predictions.json')};labels.update({a+'-'+v:load(p) for a,p in LABELS.items() for v in ['base','expanded']});sparse={'source':load(ROOT/'iteration129/predictions.json')['5'],**load(ROOT/'iteration130/predictions.json')};full={'source':load(ROOT/'iteration124/predictions.json')};full.update({k.replace('/','-'):v['rows'] for k,v in load(ROOT/'iteration125/predictions.json').items()});assign=load(OUT/'assignments.json');cohorts=load(OUT/'cohorts.json');scores=load(OUT/'scores.json');evaluation=load(OUT/'evaluation.json');model=load(BASE/'models.json');reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};vectors=checks=0
    for key,public in contexts.items():
        assert not {s['sent_id'] for s in public}&reserved;lookup={r['type']:r['opaque'] for r in sparse[key]};targets=set(lookup.values());fullarm='balanced' if key=='source' else 'balanced124';expected=dict(unknown={},class5={r['opaque']:('CCONJ' if r['probabilities']['balanced124']>.5 else 'ADP') for r in sparse[key]},classfull={r['opaque']:('CCONJ' if r['probabilities'][fullarm]>.5 else 'ADP') for r in full[key]},oracle={i:anchors[w] for w,i in lookup.items()});assert assign[key]==expected
        for budget in ['5','full']:
            permitted=allowed if budget=='5' else set(anchors)-set(lookup)
            for arm,tags in expected.items():
                name='pp'+budget+'-'+arm;view=load(OUT/('public-'+key+'-'+name+'.json'));assert len(view)==len(public)
                for s,t in zip(public,view):
                    assert s['sent_id']==t['sent_id'] and len(s['tokens'])==len(t['tokens'])
                    for a,b in zip(s['tokens'],t['tokens']):
                        exp=dict(a)
                        if a['id'] in targets:exp.update(anchor=None,tag=tags.get(a['id'],'X'))
                        elif a['anchor'] not in permitted:exp.update(anchor=None,tag='X')
                        assert b==exp
                p=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels[key]),model)];assert np.allclose(p,scores[key][name],rtol=1e-12,atol=1e-12);vectors+=1
                for co,ii in cohorts[key].items():
                    a=np.array(p)[ii]>=.8;y=np.array([labels[key][i]['labels']['pp'] for i in ii],bool);e=evaluation[key][name][co];m=e['metrics'];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert m['precision']==(m['tp']/(m['tp']+m['fp']) if m['tp']+m['fp'] else None)
                    for comp,basearm in [('matching_unknown','unknown'),('same_pp_class5','class5')]:
                        b=np.array(scores[key]['pp'+budget+'-'+basearm])[ii]>=.8;assert e['changes_from_'+comp]==dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()))
                    checks+=1
        if key=='source':
            assert cohorts[key]==load(ROOT/'iteration120/cohorts.json');old5=load(ROOT/'iteration129/budget-5/scores.json');assert all(np.allclose(scores[key][a],old5[b],rtol=1e-12,atol=1e-12) for a,b in [('pp5-unknown','unknown'),('pp5-class5','hard')]);assert np.allclose(scores[key]['ppfull-classfull'],load(ROOT/'iteration124/scores.json')['original'],rtol=1e-12,atol=1e-12)
        else:
            author=key.split('-')[0];assert cohorts[key]==load(ROOT/'iteration130/cohorts.json')[author];old=load(ROOT/'iteration130/scores.json')[key];assert all(np.allclose(scores[key][a],old[b],rtol=1e-12,atol=1e-12) for a,b in [('pp5-unknown','unknown'),('pp5-class5','hard')])
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,contexts_replayed=5,pp_vectors_recomputed=vectors,metric_transition_groups=checks,all_target_names_hidden_including_oracle=True,previous_sparse_and_source_full_reproduced=True,fixed_cohorts_and_reserve_checked=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
