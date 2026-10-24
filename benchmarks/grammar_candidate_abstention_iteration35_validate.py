"""Independent threshold optimality and retained-accuracy audits."""
import numpy as np
from benchmarks.grammar_candidate_abstention_iteration35 import OUT,PREVIOUS,DATA,PROBES,EPSILONS,BUDGETS,SCORES,load,save,digest
from benchmarks.grammar_candidate_abstention_iteration35_evaluate import pooled,bootstrap
from voynich_smt.candidate_abstention import calibrate_flag,flag,abstention_metrics


def run():
    for path in (OUT/'evaluation-freeze.json',OUT/'manifest.json',PREVIOUS/'verification-manifest.json',PROBES/'verification-manifest.json'):
        for p,h in load(path)['inputs'].items():assert digest(p)==h,p
    obs=load(DATA/'observations.json')['calibration'];data=load(DATA/'datasets.json');background={s['sent_id'] for s in data['background_calibration']};queryids={s['sent_id'] for s in data['calibration']};assert len(background)==200 and len(queryids)==40 and not background&queryids
    offset=sum(map(len,obs['sequences'][:obs['offset']]));records=load(OUT/'observations.json');truth=load(PREVIOUS/'feature-truth.json');old=load(PREVIOUS/'features.json');policies=load(OUT/'policies.json');evaluation=load(OUT/'evaluation.json')
    for r,original,filename in zip(records,old,load(PROBES/'probe-index.json')):
        assert r['scores']['outside_mass']==original['features']['outside_mass'];assert r['predicted']==original['features']['old'];p=load(PROBES/filename)
        np.testing.assert_allclose(r['scores']['ordinary_uncertainty'],1-np.array(p['probabilities']['ordinary_hmm']).max(axis=1))
    checks=0
    for arm in ('word','ending'):
        for eps in EPSILONS:
            rows=[(r,y) for r,y in zip(records,truth) if r['arm']==arm and r['epsilon']==eps]
            excluded=np.concatenate([np.array(y['excluded'])[:offset] for r,y in rows]);protected=np.concatenate([(np.array(r['predicted'])[:offset]==np.array(y['gold'])[:offset])&~np.array(y['excluded'])[:offset] for r,y in rows])
            for score in SCORES:
                s=np.concatenate([r['scores'][score][:offset] for r,y in rows]);unique,inverse=np.unique(s,return_inverse=True);positive=np.bincount(inverse,weights=excluded,minlength=len(unique));negative=np.bincount(inverse,weights=protected,minlength=len(unique));total=np.bincount(inverse,minlength=len(unique));tp=np.cumsum(positive[::-1])[::-1];fp=np.cumsum(negative[::-1])[::-1];nflag=np.cumsum(total[::-1])[::-1]
                for budget in BUDGETS:
                    p=policies[f'{arm}/{eps}/{score}/{budget}'];assert p==calibrate_flag(s,excluded,protected,budget);options=[(int(tp[i]),-int(nflag[i]),float(t)) for i,t in enumerate(unique) if tp[i]>0 and fp[i]<=budget*protected.sum()]
                    assert p['enabled']==bool(options)
                    if options:assert p['threshold']==max(options)[2]
                    selected=flag(s,p);assert (selected&protected).sum()<=budget*protected.sum();assert p['calibration']['flagged_excluded']==int((selected&excluded).sum());checks+=1
    for cell in evaluation['cells']:
        i=next(i for i,r in enumerate(records) if all(r[k]==cell[k] for k in ('mask_seed','rate','epsilon','arm')));r=records[i];y=truth[i];pred=np.array(r['predicted'])[offset:];gold=np.array(y['gold'])[offset:];excluded=np.array(y['excluded'])[offset:];p=policies[f"{r['arm']}/{r['epsilon']}/{cell['score']}/{cell['budget']}"];selected=flag(r['scores'][cell['score']][offset:],p)
        np.testing.assert_array_equal(selected,cell['flagged']);m=abstention_metrics(pred,gold,excluded,selected);assert m==cell['metrics'];correct=pred==gold
        assert m['retained_correct']+m['correct_tags_discarded']==m['baseline_correct'];assert m['retained']+m['flagged']==m['tokens'];assert m['retained_correct']<=m['baseline_correct']
        assert m['flagged_excluded']==int((selected&excluded).sum()) and m['false_flags_protected']==int((selected&correct&~excluded).sum())
        assert sum(cell['sentence_counts']['retained_correct'])==m['retained_correct'];assert sum(cell['sentence_counts']['retained'])==m['retained']
    for summary in evaluation['summary']:
        rows=[r for r in evaluation['cells'] if all(r[k]==summary[k] for k in ('arm','epsilon','rate','score','budget'))];assert len(rows)==5;assert summary['pooled']==pooled(rows);assert summary['bootstrap']==bootstrap(rows)
    report=dict(threshold_replays=checks,independent_threshold_optimality_checks=checks,query_flag_audits=len(evaluation['cells']),pooled_and_bootstrap_checks=len(evaluation['summary']),source_score_projections=len(records),calibration_query_ids_disjoint=True,tag_predictions_unchanged=True,prior_hashes_valid=True,scope='Reused internal background200/query40 split; upstream oracle/transductive channels retained; reserved200 unscored')
    save(OUT/'validation.json',report);print(report)

if __name__=='__main__':run()
