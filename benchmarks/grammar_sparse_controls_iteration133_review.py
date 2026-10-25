"""Audit fixed sparse nulls, sentence-local proximity and all scored cohorts."""
from benchmarks.grammar_sparse_controls_iteration133 import *

def run():
    hashes=0
    for name in ['design-freeze','input-freeze','predictions-freeze']:
        for p,h in load(OUT/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    predictions=load(ROOT/'iteration132/predictions.json');assign=load(OUT/'assignments.json');scores=load(OUT/'scores.json');evaluation=load(OUT/'evaluation.json');summary=load(OUT/'shuffle-summary.json');comparisons=load(OUT/'proximity-comparisons.json');mass=load(OUT/'class-mass.json');labels={'source':load(BASE/'predictions.json')};labels.update({a+'-'+v:load(p) for a,p in LABELS.items() for v in ['base','expanded']});cohorts={'source':load(ROOT/'iteration120/cohorts.json')};cohorts.update({a+'-'+v:load(ROOT/'iteration130/cohorts.json')[a] for a in INPUTS for v in ['base','expanded']});model=load(BASE/'models.json');vectors=checks=0;reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr}
    for key,rows in predictions.items():
        public=load(ROOT/'iteration132'/('public-'+key+'.json'));assert not {s['sent_id'] for s in public}&reserved;actual={r['opaque']:('CCONJ' if r['probabilities']['matched']>.5 else 'ADP') for r in rows};ids=sorted(actual);assert assign[key]['actual']==actual;assert len(assign[key])==20
        for arm,tags in assign[key].items():
            if arm.startswith('shuffle'):
                seed=int(arm[7:]);expected=dict(zip(ids,np.random.default_rng(seed).permutation([actual[i] for i in ids]).tolist()));assert tags==expected;assert Counter(tags.values())==Counter(actual.values())
            elif arm=='all_ADP':assert tags=={i:'ADP' for i in ids}
            elif arm=='all_CCONJ':assert tags=={i:'CCONJ' for i in ids}
            elif arm=='unknown':assert tags=={}
            view=inject(public,set(ids),tags);assert all(t['anchor'] is None for s in view for t in s['tokens'] if t['id'] in ids);pp=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels[key]),model)];assert np.allclose(pp,scores[key][arm]['pp'],rtol=1e-12,atol=1e-12);vectors+=1
            if arm=='actual':assert np.allclose(pp,load(ROOT/'iteration132/scores.json')[key],rtol=1e-12,atol=1e-12)
            assert mass[key][arm]['type_counts']==dict(Counter(tags.values()));assert mass[key][arm]['target_token_counts']==dict(Counter(t['tag'] for s in view for t in s['tokens'] if t['id'] in ids))
            for width in [1,2]:
                expected=[]
                for s in view:
                    for i,t in enumerate(s['tokens']):expected.append(float(any(i-d>=0 and s['tokens'][i-d]['tag']=='ADP' for d in range(1,width+1))))
                assert scores[key][arm]['left'+str(width)]==expected
            for method,p in scores[key][arm].items():
                for co,ii in cohorts[key].items():
                    a=np.array(p)[ii]>=(.8 if method=='pp' else .5);y=np.array([labels[key][i]['labels']['pp'] for i in ii],bool);m=evaluation[key][arm][method][co];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert m['precision']==(m['tp']/(m['tp']+m['fp']) if m['tp']+m['fp'] else None);assert m['f1']==(2*m['tp']/(2*m['tp']+m['fp']+m['fn']) if 2*m['tp']+m['fp']+m['fn'] else 0.);checks+=1
        for co,ii in cohorts[key].items():
            r=summary[key][co];null=[evaluation[key]['shuffle'+str(seed)]['pp'][co] for seed in SEEDS];a=evaluation[key]['actual']['pp'][co];assert r['actual']==a;assert r['null_f1_at_least_actual']==sum(m['f1']>=a['f1'] for m in null);assert r['descriptive_rank_fraction']==(1+r['null_f1_at_least_actual'])/17;assert r['null_min_f1']==min(m['f1'] for m in null) and r['null_max_f1']==max(m['f1'] for m in null)
            for k in ['tp','fp','f1']:assert abs(r['null_mean'][k]-np.mean([m[k] for m in null]))<1e-12
            for method in ['left1','left2']:
                p=np.array(scores[key]['actual']['pp'])[ii]>=.8;b=np.array(scores[key]['actual'][method])[ii]>=.5;y=np.array([labels[key][i]['labels']['pp'] for i in ii],bool);assert comparisons[key][co][method]==dict(new_tp=int((p&~b&y).sum()),new_fp=int((p&~b&~y).sum()),lost_tp=int((~p&b&y).sum()),removed_fp=int((~p&b&~y).sum()))
        print('audited',key,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,pp_vectors_recomputed=vectors,confusion_groups_verified=checks,all80_type_permutations_and_class_counts_verified=True,sentence_local_proximity_replayed=True,actual132scores_reproduced=True,reserve_absent=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
