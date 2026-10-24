"""Independent calibration/score replay and error attribution for iteration53."""
from collections import Counter
from benchmarks.grammar_none_gate_iteration53 import OUT,PREVIOUS,MORPH,SOURCE,BASES,ARMS,load,save,digest,prepare,make_frames,metrics
from voynich_smt.none_gate import best_edge,accept,calibrate


def run():
    hashes=0
    for filename in ('design-freeze.json','policy-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');models=load(PREVIOUS/'models.json');policies=load(OUT/'policies.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};old=load(PREVIOUS/'frame-predictions.json');oldlookup={(r['sid'],r['subject']):r for r in old};policy_replays=0;proposal_replays=0;decision_replays=0
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c)
        cache={};morph=morphs[str(f)]['expanded'];cal=prepare(part['calibration'],data,morph,cache)
        for base in BASES:
            proposals=[best_edge(frame,models[str(f)][base]['model']) for frame in cal]
            for mode in ('map','free'):
                assert calibrate(cal,proposals,mode)==policies[str(f)][base+'_'+mode];policy_replays+=1
        for sid in part['test']:
            frames,_=make_frames(sid,data[sid]['tokens'],morph,cache)
            for frame in frames:
                r=lookup[sid,frame['subject']];prior=oldlookup[sid,frame['subject']]
                for key in prior:
                    if key=='arms':
                        for arm,record in prior[key].items():assert record==r[key][arm]
                    else:assert prior[key]==r[key]
                for base in BASES:
                    proposal=best_edge(frame,models[str(f)][base]['model']);assert proposal==r['margins'][base];proposal_replays+=1
                    for mode in ('map','free'):
                        arm=base+'_'+mode
                        for policy in ('f1','precision90'):
                            decision=proposal['predicate'] if accept(proposal,policies[str(f)][arm][policy]['cutoff']) else None
                            assert decision==r['arms'][arm][policy];decision_replays+=1
    evaluation=load(OUT/'evaluation.json');metric_replays=0
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        chosen=[r for r in rows if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:
            for policy in ('f1','precision90'):assert metrics(chosen,arm,policy)==evaluation['edges'][scope+'/'+arm+'/'+policy];metric_replays+=1
    loss={};sentence_exact={};new_output={}
    for scope in ('selected_sentences','all_source'):
        chosen=[r for r in rows if scope=='all_source' or r['selected_sentence']]
        for base in BASES:
            counts=Counter()
            for r in chosen:
                gold=r['gold']
                if gold is None:continue
                proposal=r['margins'][base];decision=r['arms'][base+'_free']['f1']
                if gold not in r['candidate_predicates']:reason='missing_candidate'
                elif decision==gold:reason='correct'
                elif proposal['predicate'] is None:reason='edge_tie'
                elif proposal['predicate']!=gold:reason='wrong_predicate_ranks_first'
                else:reason='rejected_correct_best_edge'
                counts[reason]+=1
            loss[scope+'/'+base+'_free']=dict(counts)
        ids={r['sid'] for r in chosen}
        bysid={sid:[] for sid in ids}
        for r in chosen:bysid[r['sid']].append(r)
        for arm in ARMS:
            exact=0;multi=0
            for rs in bysid.values():
                gold={(r['subject'],r['gold']) for r in rs if r['gold'] is not None};pred={(r['subject'],r['arms'][arm]['f1']) for r in rs if r['arms'][arm]['f1'] is not None};exact+=gold==pred;multi+=len(pred)>1
            sentence_exact[scope+'/'+arm]=dict(sentences=len(ids),exact_edge_set=exact,multiple_predicted_links=multi)
        for base in BASES:
            counts=Counter()
            for r in chosen:
                before=r['arms'][base]['f1'];after=r['arms'][base+'_free']['f1']
                if before is None and after is not None:
                    counts['added_predictions']+=1;counts['correct_added']+=after==r['gold'];counts['was_raw_NONE_or_tie']+=r['proposals'][base]['predicate'] is None;counts['correct_from_raw_NONE_or_tie']+=after==r['gold'] and r['proposals'][base]['predicate'] is None
            new_output[scope+'/'+base]=dict(counts)
    save(OUT/'additional-audit.json',dict(loss_decomposition=loss,sentence_exact=sentence_exact,new_output=new_output))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,calibration_policies_reselected=policy_replays,best_edge_scores_replayed=proposal_replays,gate_decisions_replayed=decision_replays,aggregate_metrics_replayed=metric_replays,previous_predictions_unchanged=True,models_refitted=0,reserve_unscored=200,prior_queries_scored=0))
    print(loss);print({k:v for k,v in sentence_exact.items() if k.startswith('selected_sentences/')});print(new_output['selected_sentences/local_morph'])
if __name__=='__main__':run()
