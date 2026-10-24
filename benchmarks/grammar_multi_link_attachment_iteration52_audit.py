"""Refit/replay and loss attribution for frozen multi-link predictions."""
import numpy as np
from collections import Counter
from benchmarks.grammar_multi_link_attachment_iteration52 import OUT,MORPH,SOURCE,EXAMPLES,ARMS,load,save,digest,prepare,make_frames,add_targets,metrics
from voynich_smt.multi_link_attachment import fit,propose,distance_proposal,calibrate,accept


def run():
    hashes=0
    for filename in ('design-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');models=load(OUT/'models.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};replayed=0;models_refit=0;calibrations=0;decomposition={};rank_only={}
    for f in range(5):
        morph=morphs[str(f)]['expanded'];p=parts[str(f)];cache={};training=prepare(p['fit'],data,morph,cache);calibration=prepare(p['calibration'],data,morph,cache)
        for arm in ARMS:
            record=models[str(f)][arm]
            if arm!='distance':
                refit=fit(training,arm);assert np.allclose(refit['weights'],record['model']['weights'],rtol=1e-8,atol=1e-9);models_refit+=1
            proposals=[propose(frame,record['model']) if arm!='distance' else distance_proposal(frame) for frame in calibration]
            assert calibrate(calibration,proposals,arm=='distance')==record['thresholds'];calibrations+=1
        for sid in p['test']:
            frames,_=make_frames(sid,data[sid]['tokens'],morph,cache)
            for frame in add_targets(frames,data[sid]['tokens']):
                r=lookup[sid,frame['subject']]
                for arm in ARMS:
                    record=models[str(f)][arm];proposal=propose(frame,record['model']) if arm!='distance' else distance_proposal(frame)
                    assert proposal==r['proposals'][arm]
                    for policy in ('f1','precision90'):
                        accepted=proposal['predicate'] if accept(proposal,record['thresholds'][policy]['threshold'],arm=='distance') else None
                        assert accepted==r['arms'][arm][policy];replayed+=1
                    if frame['gold'] is None:continue
                    scope='selected_sentences' if r['selected_sentence'] else 'other_source_sentences'
                    for population in (scope,'all_source'):
                        counts=decomposition.setdefault(population+'/'+arm,Counter());gold=frame['gold']
                        if gold not in frame['predicates']:reason='missing_candidate'
                        elif r['arms'][arm]['f1']==gold:reason='correct'
                        elif proposal['predicate'] is None:reason='none_or_tie'
                        elif proposal['predicate']!=gold:reason='wrong_predicate_wins'
                        else:reason='threshold_rejection'
                        counts[reason]+=1
                    if arm!='distance' and frame['predicates']:
                        scores=np.asarray(frame['vectors'][arm])@np.asarray(record['model']['weights']);winners=np.flatnonzero(np.isclose(scores,scores.max(),rtol=0,atol=1e-10));counts=rank_only.setdefault(scope+'/'+arm,Counter());counts['gold_subjects_with_predicates']+=1;counts['unique_correct_ignoring_none']+=len(winners)==1 and frame['predicates'][int(winners[0])]==frame['gold']
    evaluation=load(OUT/'evaluation.json');metric_replays=0
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in rows if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:
            for policy in ('f1','precision90'):
                assert metrics(selected,arm,policy)==evaluation['edges'][scope+'/'+arm+'/'+policy];metric_replays+=1
    selected=[r for r in rows if r['selected_sentence']];sentence_exact={}
    for arm in ARMS:
        for policy in ('f1','precision90'):
            ids={r['sid'] for r in selected};exact=0;multi=0
            for sid in ids:
                rs=[r for r in selected if r['sid']==sid];gold={(r['subject'],r['gold']) for r in rs if r['gold'] is not None};pred={(r['subject'],r['arms'][arm][policy]) for r in rs if r['arms'][arm][policy] is not None};exact+=gold==pred;multi+=len(pred)>1
            sentence_exact[arm+'/'+policy]=dict(sentences=len(ids),exact_edge_set=exact,multiple_predicted_links=multi)
    save(OUT/'additional-audit.json',dict(gold_loss_decomposition={k:dict(v) for k,v in decomposition.items()},known_gold_subject_ranking_ignoring_none={k:dict(v) for k,v in rank_only.items()},sentence_exact=sentence_exact,note='Ignoring NONE supplies oracle subject eligibility and is only a diagnostic; not an unanchored restoration result.'))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,models_refitted=models_refit,calibration_policies_reselected=calibrations,frame_policy_predictions_replayed=replayed,aggregate_metrics_replayed=metric_replays,reserve_unscored=200,prior_queries_scored=0))
    print({k:dict(v) for k,v in decomposition.items() if k.startswith('selected_sentences/')});print(sentence_exact)
if __name__=='__main__':run()
