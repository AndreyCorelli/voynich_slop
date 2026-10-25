"""Independent anchor masking, class and PP score replay."""
from benchmarks.grammar_anchor_dependence_iteration129 import *
from voynich_smt.paired_anchor_class import target_features

def run():
    hashes=0
    for folder,names in [(OUT,['design-freeze','input-freeze','all-scores-freeze'])]+[(OUT/('budget-'+str(n)),['input-freeze','predictions-freeze']) for n in BUDGETS]:
        for name in names:
            for p,h in load(folder/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];words=load(ROOT/'iteration93/types.json')['candidates'];part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];cache=load(ROOT/'iteration44/annotations-truth.json');counts=Counter(t['word'] for sid in part['fit'] for t in cache[sid]['tokens']);ranked=sorted(set(anchors)-set(words),key=lambda w:(-counts[w],w));assert load(OUT/'anchor-ranking.json')==[dict(type=w,fit_count=counts[w],given_class=anchors[w]) for w in ranked];public=load(ROOT/'iteration118/public.json');oldrows=load(ROOT/'iteration124/predictions.json');lookup={r['type']:r['opaque'] for r in oldrows};targets=set(lookup.values());predictions=load(OUT/'predictions.json');selection=load(OUT/'selection.json');probs=load(OUT/'probabilities.json');summary=load(OUT/'class-summary.json');evaluation=load(OUT/'evaluation.json');classmodel=load(ROOT/'iteration124/models.json')['final'];cal=load(ROOT/'iteration124/calibrator.json');ppmodel=load(BASE/'models.json');labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(BASE/'predictions.json')];cohorts=load(ROOT/'iteration120/cohorts.json');cut=load(ROOT/'iteration128/chosen.json')['threshold'];vectors=checks=types=0
    reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};assert not set(part['fit']+part['test'])&reserved
    for n in BUDGETS:
        key=str(n);allowed=set(ranked[:n]);view=load(OUT/('public-'+key+'.json'));assert selection[key]['allowed']==ranked[:n]
        for s,t in zip(public,view):
            assert s['sent_id']==t['sent_id'] and len(s['tokens'])==len(t['tokens'])
            for a,b in zip(s['tokens'],t['tokens']):
                expected=dict(a)
                if a['id'] in targets or a['anchor'] not in allowed:expected.update(anchor=None,tag='X')
                assert expected==b
        assert selection[key]['given_anchor_tokens']==sum(t['anchor'] is not None for s in view for t in s['tokens']);rr=target_features(view,targets);q=ag.predict([r['features'] for r in rr],classmodel);rows=predictions[key];assert len(rows)==16
        for r in rows:
            ix=[i for i,t in enumerate(rr) if t['word']==r['opaque']];raw=float(q[ix,1].mean());assert abs(raw-r['probabilities']['raw'])<1e-12;assert abs(float(apply_offset([raw],cal)[0])-r['probabilities']['balanced124'])<1e-12;assert probs[key][r['opaque']]==r['probabilities']['balanced124'];types+=1
        for arm,m in summary[key].items():
            p=np.array([r['probabilities'][arm] for r in rows]);y=np.array([anchors[r['type']]=='CCONJ' for r in rows]);assert m['correct']==int(((p>.5)==y).sum());assert abs(m['nll']-float(-np.log(np.where(y,p,1-p)).mean()))<1e-12;assert m['auc']==float(np.mean((p[y,None]>p[~y][None,:])+.5*(p[y,None]==p[~y][None,:])))
        folder=OUT/('budget-'+key);assign=load(folder/'assignments.json');scores=load(folder/'scores.json');ids=sorted(probs[key]);u=qmc.Sobol(d=16,scramble=True,seed=12700).random_base2(5)
        for arm,tags in assign.items():
            expected={} if arm=='unknown' else {i:('CCONJ' if probs[key][i]>.5 else 'ADP') for i in ids} if arm=='hard' else {i:('CCONJ' if u[int(arm[4:]),j]<probs[key][i] else 'ADP') for j,i in enumerate(ids)};assert expected==tags;v=inject(view,targets,tags);p=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(v,labels),ppmodel)];assert np.allclose(p,scores[arm],rtol=1e-12,atol=1e-12);vectors+=1
        assert np.allclose(scores['posterior'],np.mean([scores['draw'+str(j)] for j in range(32)],axis=0),rtol=1e-12,atol=1e-12)
        for arm in ['unknown','hard','posterior']:
            for c in [cut,.8]:
                for co,ii in cohorts.items():
                    a=np.array(scores[arm])[ii]>=c;b=np.array(scores['unknown'])[ii]>=c;y=np.array([labels[i]['labels']['pp'] for i in ii],bool);e=evaluation[key][arm][str(c)][co];m=e['metrics'];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert e['changes_from_matching_unknown']==dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()));checks+=1
        if n==179:
            for r in rows:assert abs(r['probabilities']['balanced124']-next(z['probabilities']['balanced'] for z in oldrows if z['type']==r['type']))<1e-12
            old=load(ROOT/'iteration127/test/scores.json');assert all(np.allclose(scores[a],old[a],rtol=1e-12,atol=1e-12) for a in ['unknown','hard','posterior'])
        print('audited',n,flush=True)
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,budgets_replayed=6,type_probabilities_recomputed=types,pp_vectors_recomputed=vectors,metric_transition_groups=checks,full_budget_reproduces_previous=True,source_only_ranking_verified=True,reserve_absent=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
