"""Frozen-score audit of Case, phrase and clause evidence for copular heads."""
from pathlib import Path
from collections import Counter,defaultdict
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT as PREVIOUS,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest
from voynich_smt.typed_predicate_units import choices,matrix,prior_scores,select
from voynich_smt.copular_head_oracle import CUES,MASKS,flags,indices
import numpy as np
OUT=PREVIOUS.parent/'iteration58'
ARMS=('prior_distance','learned')


def fold(sid):
    from voynich_smt.crossfit_morphology import sentence_fold
    return sentence_fold(sid)


def choose(scores,options,kept,subject,carrier):
    return select(scores[kept],[options[j] for j in kept],subject,carrier) if kept else None


def summary(rows):
    results={};survival={};competition={}
    for cohort in ('all_source','selected_sentences','Cicero_all','Palladius_all','reachable_all','reachable_selected'):
        chosen=[r for r in rows if cohort=='all_source' or cohort=='selected_sentences' and r['selected_sentence'] or cohort.endswith('_all') and r['author']==cohort[:-4] or cohort=='reachable_all' and r['endpoint_correct'] or cohort=='reachable_selected' and r['selected_sentence'] and r['endpoint_correct']]
        for mask,cues in MASKS.items():
            exclusions=[r for r in chosen if not all(r['gold_flags'][cue] for cue in cues)];survival[cohort+'/'+mask]=dict(n=len(chosen),gold_kept=len(chosen)-len(exclusions),excluded=[[r['sid'],r['gold'][0]] for r in exclusions])
            for arm in ARMS:
                for mode in ('free_type','cop_type'):
                    predictions=[r['predictions'][arm][mode][mask] for r in chosen];results[cohort+'/'+arm+'/'+mode+'/'+mask]=dict(n=len(chosen),exact=sum(p==r['gold'] for p,r in zip(predictions,chosen)),head_correct=sum(p is not None and p[1]==r['gold'][1] for p,r in zip(predictions,chosen)),type_correct=sum(p is not None and p[3]=='cop' for p in predictions),abstained=sum(p is None for p in predictions))
        for arm in ARMS:
            counts=Counter()
            for r in chosen:counts.update(r['competition'][arm])
            competition[cohort+'/'+arm]=dict(counts)
    return dict(conditional_accuracy=results,gold_head_survival=survival,competition=competition,warning='All rows are oracle diagnostics on gold copular endpoints. cop_type additionally reveals true type. Reachable subsets reveal true endpoint correctness. No metric is unanchored restoration performance.')


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/copular_head_oracle.py'),Path('src/voynich_smt/typed_predicate_units.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',PREVIOUS/'models.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'evaluation.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Pure diagnostic on same650 gold copular units,32 selected. Frozen57 scores/choices/models/endpoints, no fitting or cutoff changes. No reserve/prior query scoring.',masks='All16 subsets of4 cues. Case: Nom or unknown permitted; known otherCase excluded. ADP: reject a token in a case-ADP-headed phrase, including paths through nominal dependent relations. Phrase: reject amod/det/nmod/appos/flat/fixed/compound/case dependents. Clause: require same gold clause anchor as carrier; roots/ccomp/xcomp/advcl/acl/parataxis/csubj or finite/copular conjuncts delimit anchors; unknown/cycles permissive. These are annotation masks, not observable inference.',evaluation='Score both prior_distance and learned options at gold subject/carrier. free_type retains all roles, cop_type reveals correctcoptype. Masks apply consistently to each candidate head, no candidate injection or rescoring. Report truehead survival, exact/head/type recovery, abstentions and higher-scoring samecop competitors. Reachable subset uses frozen56 correct endpoints as another oracle condition.',limitations='Clause anchoring follows the gold carrier dependency to its head and can directly encode target attachment; it is an ideal parse oracle, not evidence that marker detection alone suffices. Nominal Case and PP/phrase exclusions may reject legitimate predicative constructions. Reused development partitions; descriptive comparisons only.'))
    data=load(SOURCE);reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models=load(PREVIOUS/'models.json');prior=load(PREVIOUS/'frame-predictions.json');rows=[];baseline_replays=0;subset_checks=0
    for old in prior:
        gold=old['unit_gold']
        if gold is None or gold[3]!='cop':continue
        sid=old['sid'];tokens=data[sid]['tokens'];s,h,v,role=gold;record=models[str(fold(sid))];model=record['model'];weight=record['distance']['selected']['weight'];options=choices(tokens,s,v);head_flags={head:flags(tokens,head,v) for head,_ in options};gold_flags=head_flags[h];predictions={};competition={};candidate_rows=[]
        for arm in ARMS:
            scores=matrix(tokens,s,v,options)@np.asarray(model['weights']) if arm=='learned' else prior_scores(tokens,v,options,model,weight);assert select(scores,options,s,v)==old['unit_oracle_endpoint'][arm];baseline_replays+=1;predictions[arm]={}
            for mode in ('free_type','cop_type'):
                predictions[arm][mode]={}
                for mask in MASKS:
                    kept=indices(options,head_flags,mask,mode);assert set(kept)<=set(range(len(options)));subset_checks+=1;predictions[arm][mode][mask]=choose(scores,options,kept,s,v)
            gold_index=options.index((h,'cop'));counts=Counter()
            for j,(head,kind) in enumerate(options):
                if kind!='cop' or head==h:continue
                counts['competing_heads']+=1
                outranks=bool(scores[j]>scores[gold_index]+1e-10);counts['outranking_heads']+=outranks
                if outranks:
                    for cue in CUES:counts[cue+'_blocks_outranker']+=not head_flags[head][cue];counts[cue+'_blocks_outranker_preserving_gold']+=gold_flags[cue] and not head_flags[head][cue]
            competition[arm]=dict(counts)
            if arm=='learned':
                for j,(head,kind) in enumerate(options):
                    if kind!='cop':continue
                    t=tokens[head];candidate_rows.append(dict(head=head,word=t['word'],pos=t['pos'],case=t['features'].get('Case',''),rel=t['rel'],flags=head_flags[head],score=float(scores[j]),gold=head==h))
        rows.append(dict(sid=sid,author=old['author'],selected_sentence=old['selected_sentence'],gold=gold,endpoint_correct=old['arms']['carrierfit_carriercal']['f1']==v,gold_flags=gold_flags,predictions=predictions,competition=competition,candidates=candidate_rows,sentence=' '.join(t['word'] for t in tokens)))
    save(OUT/'copular-audit.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=summary(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),copular_units=len(rows),baseline_conditional_replays=baseline_replays,mask_subset_checks=subset_checks,models_refitted=0,previous_outputs_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    for cohort in ('all_source','selected_sentences'):
        print(cohort,{mask:dict(accuracy=result['conditional_accuracy'][cohort+'/learned/cop_type/'+mask],gold_survival=result['gold_head_survival'][cohort+'/'+mask]['gold_kept']) for mask in MASKS});print('Competition',result['competition'][cohort+'/learned'])
if __name__=='__main__':run()
