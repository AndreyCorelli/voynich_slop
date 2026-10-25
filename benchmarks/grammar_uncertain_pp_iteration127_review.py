"""Audit posterior assignment averaging, source selection, and fixed-cohort metrics."""
from benchmarks.grammar_uncertain_pp_iteration127 import *

def run():
    hashes=0
    for folder,names in [(OUT,['design-freeze','policy-freeze']),(OUT/'calibration',['input-freeze','predictions-freeze']),(OUT/'test',['input-freeze','predictions-freeze'])]:
        for name in names:
            for p,h in load(folder/(name+'.json'))['inputs'].items():assert digest(p)==h,p;hashes+=1
    reserved={r['sent_id'] for rr in load('experiments/holdouts/grammar-construction-next.json')['authors'].values() for r in rr};part=load(ROOT/'iteration49/manifest.json')['partitions']['0'];model=load(BASE/'models.json');vectors=checks=0
    for phase,pubpath,labelpath in [('calibration',ROOT/'iteration122/calibration-public-original.json',BASE/'calibration-predictions.json'),('test',ROOT/'iteration118/public.json',BASE/'predictions.json')]:
        public=load(pubpath);assert [s['sent_id'] for s in public]==part[phase];assert not {s['sent_id'] for s in public}&reserved;labels=[dict(sid=r['sid'],index=r['index'],labels=r['labels']) for r in load(labelpath)];assert [(s['sent_id'],i) for s in public for i,t in enumerate(s['tokens'])]==[(r['sid'],r['index']) for r in labels];prob=load(OUT/(phase+'-probabilities.json'));ids=sorted(prob);hidden=set(ids);folder=OUT/phase;assignments=load(folder/'assignments.json');scores=load(folder/'scores.json');assert len(ids)==16;u=qmc.Sobol(d=16,scramble=True,seed=12700).random_base2(5)
        if phase=='test':assert prob=={r['opaque']:r['probabilities']['balanced'] for r in load(ROOT/'iteration124/predictions.json')}
        else:
            words=load(ROOT/'iteration93/types.json')['candidates'];lookup={w:hashlib.sha256(('cal122|'+w).encode()).hexdigest() for w in words};pp=grouped_profile(public,words,lookup,hidden,load(ROOT/'iteration124/models.json')['final']);cal=load(ROOT/'iteration124/calibrator.json');assert all(abs(prob[lookup[w]]-float(apply_offset([pp[w]['mean']],cal)[0]))<1e-12 for w in words)
        for arm,tags in assignments.items():
            expected={} if arm=='unknown' else {i:('CCONJ' if p>.5 else 'ADP') for i,p in prob.items()} if arm=='hard' else {i:('CCONJ' if u[int(arm[4:]),k]<prob[i] else 'ADP') for k,i in enumerate(ids)};assert tags==expected;view=inject(public,hidden,tags)
            assert all(t['anchor'] is None for s in view for t in s['tokens'] if t['id'] in hidden);q=[r['scores']['pooled_pos']['pp'] for r in infer85(query_rows(view,labels),model)];assert np.allclose(q,scores[arm],rtol=1e-12,atol=1e-12);vectors+=1
        posterior=np.mean([scores['draw'+str(j)] for j in range(32)],axis=0);assert np.allclose(posterior,scores['posterior'],rtol=1e-12,atol=1e-12)
        for alpha in ALPHAS:assert np.allclose((1-alpha)*np.array(scores['unknown'])+alpha*posterior,scores['alpha'+str(alpha)],rtol=1e-12,atol=1e-12)
        if phase=='test':
            assert np.allclose(scores['hard'],load(ROOT/'iteration124/scores.json')['original'],rtol=1e-12,atol=1e-12);assert np.allclose(scores['unknown'],load(ROOT/'iteration120/scores-unknown.json')['original'],rtol=1e-12,atol=1e-12)
            ev=load(OUT/'evaluation.json');cohorts=load(ROOT/'iteration120/cohorts.json');old=load(ROOT/'iteration120/scores-predicted.json')['original']
            for arm,policies in ev.items():
                for policy,groups in policies.items():
                    for c,e in groups.items():
                        ii=cohorts[c];a=np.array(scores[arm])[ii]>=float(policy);y=np.array([labels[i]['labels']['pp'] for i in ii],bool);m=e['metrics'];assert [m[k] for k in ['tp','fp','fn','tn']]==[int((a&y).sum()),int((a&~y).sum()),int((~a&y).sum()),int((~a&~y).sum())];assert m['precision']==(m['tp']/(m['tp']+m['fp']) if m['tp']+m['fp'] else None)
                        for key,base in [('hard',scores['hard']),('unknown',scores['unknown']),('previous',old)]:
                            b=np.array(base)[ii]>=float(policy);assert e['changes_from_'+key]==dict(new_tp=int((a&~b&y).sum()),new_fp=int((a&~b&~y).sum()),lost_tp=int((~a&b&y).sum()),removed_fp=int((~a&b&~y).sum()))
                        checks+=1
        else:
            curve=load(OUT/'calibration-curve.json');minimum=math.ceil(.8*curve['hard_baseline']['tp']);eligible=[];y=np.array([r['labels']['pp'] for r in labels],bool)
            for r in curve['rows']:
                a=np.array(scores['alpha'+str(r['alpha'])])>=.8;tp=int((a&y).sum());fp=int((a&~y).sum());assert (tp,fp)==(r['metrics']['tp'],r['metrics']['fp']);ok=tp+fp>0 and tp/(tp+fp)>=.9 and tp>=minimum;assert ok==r['qualified'];checks+=1
                if ok:eligible.append(r)
            expected=max(eligible,key=lambda r:(r['metrics']['tp'],-r['metrics']['fp'],r['alpha'])) if eligible else dict(alpha=None,qualified=False);assert expected==load(OUT/'chosen.json')
    result=load(OUT/'result.json');chosen=load(OUT/'chosen.json');assert result['selected_arm']==('alpha'+str(chosen['alpha']) if chosen['qualified'] else 'hard');m=result['selected'];assert result['passed']==bool(chosen['qualified'] and m['precision'] is not None and m['precision']>=.9 and m['tp']>=max(188,math.ceil(.8*result['hard_baseline']['tp'])))
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,pp_vectors_recomputed=vectors,independent_metric_transition_groups=checks,source_selection_replayed=True,type_consistent_draws_verified=True,hard_and_unknown_baselines_reproduced=True,reserve_absent=True));print(load(OUT/'audit.json'))
if __name__=='__main__':run()
