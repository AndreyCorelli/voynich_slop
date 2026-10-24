"""Independent target/refit/calibration replay and carrier-specific learning audit."""
import numpy as np
from collections import defaultdict,Counter
from benchmarks.grammar_predicate_carriers_iteration56 import OUT,BASELINE,MORPH,SOURCE,ARMS,load,save,digest,prepare,make_frames,evaluate
from voynich_smt.predicate_carriers import target
from voynich_smt.multi_link_attachment import fit
from voynich_smt.none_gate import best_edge,accept,calibrate


def run():
    hashes=0
    for filename in ('design-freeze.json','target-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/filename)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');models=load(OUT/'models.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};old={(r['sid'],r['subject']):r for r in load(BASELINE/'frame-predictions.json')};fit_audits=load(OUT/'fit-target-audit.json');target_audits={(r['sid'],r['subject']):r for r in load(OUT/'target-audit.json')};refits=0;policy_replays=0;score_replays=0;decisions=0;truth_replays=0
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);outer=morphs[str(f)]['expanded'];training,audit=prepare(part['fit'],data,outer,'carrier');assert audit==fit_audits[str(f)];refit=fit(training,'local_morph');assert np.allclose(refit['weights'],models[str(f)]['carrierfit_carriercal']['model']['weights'],rtol=1e-8,atol=1e-9);refits+=1
        assert models[str(f)]['carrierfit_directcal']['model']==models[str(f)]['carrierfit_carriercal']['model']
        for task in ('direct','carrier'):
            frames,_=prepare(part['calibration'],data,outer,task)
            for fit_task in ('direct','carrier'):
                arm=fit_task+'fit_'+task+'cal';record=models[str(f)][arm];proposals=[best_edge(frame,record['model']) for frame in frames];assert calibrate(frames,proposals,'free')==record['policies'];policy_replays+=1
        cache={}
        for sid in part['test']:
            tokens=data[sid]['tokens'];frames,_=make_frames(sid,tokens,outer,cache)
            for frame in frames:
                r=lookup[sid,frame['subject']];prior=old[sid,frame['subject']]
                for key in prior:
                    if key=='arms':
                        for arm,value in prior[key].items():assert r[key][arm]==value
                    else:assert r[key]==prior[key]
                truth=target(tokens,frame['subject']);assert truth['direct']==r['direct_gold']==prior['gold'];assert truth['carrier']==r['carrier_gold'];assert truth['ambiguous']==r['carrier_ambiguous'];assert truth['kind']==r['carrier_kind'];audit=target_audits[sid,frame['subject']]
                for k,v in truth.items():assert audit[k]==v
                truth_replays+=1
                for arm,record in models[str(f)].items():
                    proposal=best_edge(frame,record['model']);assert proposal==r['carrier_proposals'][arm];score_replays+=1
                    for policy in ('f1','precision90'):
                        decision=proposal['predicate'] if accept(proposal,record['policies'][policy]['cutoff']) else None;assert decision==r['arms'][arm][policy];decisions+=1
    evaluation=load(OUT/'evaluation.json');replayed=evaluate(rows)
    for k,value in replayed.items():assert evaluation[k]==value
    baseline=load(BASELINE/'evaluation.json')
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        for policy in ('f1','precision90'):assert evaluation['edges']['direct/'+scope+'/directfit_directcal/'+policy]==baseline['edges'][scope+'/local_morph_free/'+policy]
    groups={};paired={};exact={}
    arms=('directfit_directcal','directfit_carriercal','carrierfit_directcal','carrierfit_carriercal')
    for scope in ('selected_sentences','all_source'):
        chosen=[r for r in rows if (scope=='all_source' or r['selected_sentence']) and not r['carrier_ambiguous']]
        for kind in ('direct','copula','auxiliary','none'):
            selected=[r for r in chosen if (kind=='none' and r['carrier_gold'] is None) or r['carrier_kind']==kind]
            groups[scope+'/'+kind]=dict(frames=len(selected),gold=sum(r['carrier_gold'] is not None for r in selected),retrievable=sum(r['carrier_gold'] is not None and r['carrier_gold'] in r['candidate_predicates'] for r in selected),arms={arm:dict(correct=sum(r['carrier_gold'] is not None and r['arms'][arm]['f1']==r['carrier_gold'] for r in selected),wrong=sum(r['arms'][arm]['f1'] is not None and r['arms'][arm]['f1']!=r['carrier_gold'] for r in selected)) for arm in arms})
        counts=Counter()
        for r in chosen:
            a=r['arms']['directfit_carriercal']['f1'];b=r['arms']['carrierfit_carriercal']['f1'];gold=r['carrier_gold'];ac=a is not None and a==gold;bc=b is not None and b==gold;aw=a is not None and a!=gold;bw=b is not None and b!=gold
            counts['correct_added']+=bc and not ac;counts['correct_removed']+=ac and not bc;counts['wrong_added']+=bw and not aw;counts['wrong_removed']+=aw and not bw
        paired[scope]=dict(counts)
        bysid=defaultdict(list)
        for r in chosen:bysid[r['sid']].append(r)
        for arm in arms:
            exact[scope+'/'+arm]=dict(sentences=len(bysid),exact_edge_sets=sum({(r['subject'],r['carrier_gold']) for r in rs if r['carrier_gold'] is not None}=={(r['subject'],r['arms'][arm]['f1']) for r in rs if r['arms'][arm]['f1'] is not None} for rs in bysid.values()))
    ambiguous=[dict(sid=r['sid'],subject=r['subject'],choices=target_audits[r['sid'],r['subject']]['choices'],sentence=' '.join(t['word'] for t in data[r['sid']]['tokens'])) for r in rows if r['carrier_ambiguous']]
    save(OUT/'additional-audit.json',dict(by_kind=groups,paired_expanded_task_retraining_vs_recalibration=paired,expanded_task_sentence_exact=exact,ambiguous_examples=ambiguous))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,carrier_attachment_models_refitted=refits,calibration_policies_reselected=policy_replays,targets_replayed=truth_replays,best_edge_scores_replayed=score_replays,gate_decisions_replayed=decisions,aggregate_edge_metrics_replayed=len(replayed['edges']),frozen_baseline_metrics_replayed=8,previous_candidate_prediction_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    print(paired);print({k:v for k,v in groups.items() if k.startswith('selected_sentences/')});print(ambiguous)
if __name__=='__main__':run()
