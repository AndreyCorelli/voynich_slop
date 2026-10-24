"""Independent mask replay, paired changes and genuine-head exclusions."""
from collections import Counter,defaultdict
import numpy as np
from benchmarks.grammar_copular_head_oracle_iteration58 import OUT,PREVIOUS,SOURCE,load,save,digest,summary,fold,choose
from voynich_smt.typed_predicate_units import choices,matrix,prior_scores,select
from voynich_smt.copular_head_oracle import CUES,MASKS,flags,indices


def run():
    hashes=0
    for name in ('design-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);models=load(PREVIOUS/'models.json');prior={(r['sid'],r['subject']):r for r in load(PREVIOUS/'frame-predictions.json')};rows=load(OUT/'copular-audit.json');replays=0;score_replays=0;paired=defaultdict(Counter);mistakes=defaultdict(Counter);gold_profile=Counter();exclusions=defaultdict(list)
    for r in rows:
        sid=r['sid'];tokens=data[sid]['tokens'];s,h,v,_=r['gold'];old=prior[sid,s];assert r['gold']==old['unit_gold'];record=models[str(fold(sid))];model=record['model'];weight=record['distance']['selected']['weight'];options=choices(tokens,s,v);hf={head:flags(tokens,head,v) for head,_ in options};assert hf[h]==r['gold_flags'];gold_profile[tokens[h]['features'].get('Case','')]+=1
        for cue in CUES:
            if not hf[h][cue]:exclusions[cue].append(dict(sid=sid,subject=s,head=h,carrier=v,token=tokens[h],sentence=r['sentence']))
        for arm in ('prior_distance','learned'):
            scores=matrix(tokens,s,v,options)@np.asarray(model['weights']) if arm=='learned' else prior_scores(tokens,v,options,model,weight);assert select(scores,options,s,v)==old['unit_oracle_endpoint'][arm];score_replays+=1
            for mode in ('free_type','cop_type'):
                baseline=r['predictions'][arm][mode]['none'];expected_baseline=choose(scores,options,indices(options,hf,'none',mode),s,v);assert baseline==expected_baseline
                for mask in MASKS:
                    kept=indices(options,hf,mask,mode);expected=choose(scores,options,kept,s,v);assert expected==r['predictions'][arm][mode][mask];replays+=1
                    for scope in (('all_source','selected_sentences') if r['selected_sentence'] else ('all_source',)):
                        key=scope+'/'+arm+'/'+mode+'/'+mask;counts=paired[key];counts['correct_added']+=expected==r['gold'] and baseline!=r['gold'];counts['correct_removed']+=baseline==r['gold'] and expected!=r['gold']
                if mode=='cop_type' and baseline!=r['gold']:
                    for scope in (('all_source','selected_sentences') if r['selected_sentence'] else ('all_source',)):
                        counts=mistakes[scope+'/'+arm];counts['wrong_or_tied']+=1
                        if baseline is None:counts['tie']+=1
                        else:
                            for cue in CUES:counts[cue+'_rejects_chosen_wrong_head']+=not hf[baseline[1]][cue]
        # Stored per-candidate scores and annotation flags must replay verbatim.
        learned_scores=matrix(tokens,s,v,options)@np.asarray(model['weights'])
        for c in r['candidates']:
            j=options.index((c['head'],'cop'));assert c['flags']==hf[c['head']];assert c['score']==float(learned_scores[j])
    assert summary(rows)==load(OUT/'evaluation.json')
    save(OUT/'additional-audit.json',dict(paired={k:dict(v) for k,v in paired.items()},baseline_wrong_head_flags={k:dict(v) for k,v in mistakes.items()},gold_head_case_counts=dict(gold_profile),excluded_gold_examples=dict(exclusions),note='Counts are descriptive oracle contrasts; no score or policy is fitted/selected on these outcomes.'))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,frozen_score_replays=score_replays,oracle_mask_predictions_replayed=replays,aggregate_accuracy_groups_replayed=len(load(OUT/'evaluation.json')['conditional_accuracy']),prior_predictions_unchanged=True,models_refitted=0,reserve_unscored=200,prior_queries_scored=0))
    print({k:dict(v) for k,v in paired.items() if k.startswith('all_source/learned/cop_type/') and k.endswith(('case','adp','phrase','clause'))});print(dict(gold_profile));print({k:dict(v) for k,v in mistakes.items() if k.startswith('all_source/')})
if __name__=='__main__':run()
