"""Independent inner-exclusion/refit/score audit for iteration54."""
import numpy as np
from collections import Counter
from benchmarks.grammar_crossfit_attachment_iteration54 import OUT,PREVIOUS,MORPH,SOURCE,VARIANTS,ARMS,load,save,digest,prepare,make_frames,training_frames,metrics
from voynich_smt.crossfit_morphology import inner_plan,sentence_fold
from voynich_smt.factor_morphology import fit as fit_morph
from voynich_smt.multi_link_attachment import fit as fit_attachment
from voynich_smt.none_gate import best_edge,accept,calibrate


def run():
    hashes=0
    for name in ('design-freeze.json','inner-fit-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];outer=load(MORPH/'models.json');plans=load(OUT/'inner-plans.json');inner=load(OUT/'inner-morphology-models.json');models=load(OUT/'models.json');diagnostics=load(OUT/'training-role-diagnostics.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};prior={(r['sid'],r['subject']):r for r in load(PREVIOUS/'frame-predictions.json')};morph_refits=0;attachment_refits=0;policy_replays=0;score_replays=0;decision_replays=0;size_audit={}
    for f in range(5):
        p=parts[str(f)];fitids,calids,testids=(set(p[k]) for k in ('fit','calibration','test'));assert not (fitids&calids or fitids&testids or calids&testids);assert inner_plan(p['fit'])==plans[str(f)];size_audit[str(f)]={}
        for excluded in plans[str(f)]:
            ids=[sid for sid in p['fit'] if sentence_fold(sid)!=int(excluded)];assert not set(ids)&(calids|testids);refit=fit_morph((data[sid]['tokens'] for sid in ids),'expanded');assert refit==inner[str(f)][excluded];morph_refits+=1
        for g,record in plans[str(f)].items():
            held=set(record['held_ids']);cross={sid for sid in fitids if sentence_fold(sid)!=record['crossfit_excluded']};exposed={sid for sid in fitids if sentence_fold(sid)!=record['exposed_excluded']};assert not cross&held and held<=exposed
            size_audit[str(f)][g]=dict(held=len(held),crossfit_training=len(cross),exposed_training=len(exposed))
        frames,diagnostic,_=training_frames(p['fit'],data,outer[str(f)]['expanded'],plans[str(f)],inner[str(f)]);assert diagnostic==diagnostics[str(f)];cal=prepare(p['calibration'],data,outer[str(f)]['expanded'],{})
        for variant in VARIANTS:
            record=models[str(f)][variant];refit=fit_attachment(frames[variant],'local_morph');assert np.allclose(refit['weights'],record['model']['weights'],rtol=1e-8,atol=1e-9);attachment_refits+=1
            proposals=[best_edge(frame,record['model']) for frame in cal]
            for mode in ('map','free'):assert calibrate(cal,proposals,mode)==record['policies'][mode];policy_replays+=1
        cache={}
        for sid in p['test']:
            frames,_=make_frames(sid,data[sid]['tokens'],outer[str(f)]['expanded'],cache)
            for frame in frames:
                r=lookup[sid,frame['subject']];old=prior[sid,frame['subject']]
                for key in old:
                    if key=='arms':
                        for arm,record in old[key].items():assert r[key][arm]==record
                    else:assert r[key]==old[key]
                for variant in VARIANTS:
                    record=models[str(f)][variant];proposal=best_edge(frame,record['model']);assert proposal==r['crossfit_proposals'][variant];score_replays+=1
                    for mode in ('map','free'):
                        for policy in ('f1','precision90'):
                            decision=proposal['predicate'] if accept(proposal,record['policies'][mode][policy]['cutoff']) else None;assert decision==r['arms'][variant+'_'+mode][policy];decision_replays+=1
    evaluation=load(OUT/'evaluation.json');metric_replays=0
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        chosen=[r for r in rows if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:
            for policy in ('f1','precision90'):assert metrics(chosen,arm,policy)==evaluation['edges'][scope+'/'+arm+'/'+policy];metric_replays+=1
    details={};exact={}
    for scope in ('selected_sentences','all_source'):
        chosen=[r for r in rows if scope=='all_source' or r['selected_sentence']]
        for variant in VARIANTS:
            counts=Counter()
            for r in chosen:
                gold=r['gold']
                if gold is None:continue
                proposal=r['crossfit_proposals'][variant];decision=r['arms'][variant+'_free']['f1']
                if gold not in r['candidate_predicates']:reason='missing_candidate'
                elif decision==gold:reason='correct'
                elif proposal['predicate'] is None:reason='edge_tie'
                elif proposal['predicate']!=gold:reason='wrong_predicate_ranks_first'
                else:reason='rejected_correct_best_edge'
                counts[reason]+=1
            details[scope+'/'+variant]=dict(counts)
        bysid={r['sid']:[] for r in chosen}
        for r in chosen:bysid[r['sid']].append(r)
        for arm in ('local_morph_free','inner_exposed_free','crossfit_free'):
            count=0
            for rs in bysid.values():
                gold={(r['subject'],r['gold']) for r in rs if r['gold'] is not None};pred={(r['subject'],r['arms'][arm]['f1']) for r in rs if r['arms'][arm]['f1'] is not None};count+=gold==pred
            exact[scope+'/'+arm]=dict(sentences=len(bysid),exact_edge_sets=count)
    save(OUT/'additional-audit.json',dict(inner_training_sizes=size_audit,loss_decomposition=details,sentence_exact=exact));save(OUT/'independent-validation.json',dict(hash_checks=hashes,inner_morphology_models_refitted=morph_refits,attachment_models_refitted=attachment_refits,calibration_policies_reselected=policy_replays,best_edge_scores_replayed=score_replays,gate_decisions_replayed=decision_replays,aggregate_metrics_replayed=metric_replays,previous_candidate_and_prediction_fields_unchanged=True,inner_sentence_exclusion_verified=True,reserve_unscored=200,prior_queries_scored=0))
    print(exact);print({k:v for k,v in details.items() if k.startswith('selected_sentences/')})
if __name__=='__main__':run()
