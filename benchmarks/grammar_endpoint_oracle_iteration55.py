"""Frozen-score endpoint-eligibility audit, all interventions explicitly oracle."""
from pathlib import Path
from collections import Counter,defaultdict
import copy
from benchmarks.grammar_none_gate_iteration53 import OUT as BASELINE,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest,make_frames,metrics
from benchmarks.grammar_crossfit_attachment_iteration54 import OUT as PREVIOUS
from voynich_smt.none_gate import best_edge,accept
from voynich_smt.endpoint_oracle import MASKS,flags,allows,masked_frame,false_positive_class
OUT=PREVIOUS.parent/'iteration55'
ARMS=tuple(phase+'_'+mask for phase in ('postfilter','rerank') for mask in MASKS)


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/endpoint_oracle.py'),SOURCE,EXAMPLES,RESERVE,BASELINE/'models.json',BASELINE/'frame-predictions.json',BASELINE/'verification-manifest.json',MORPH/'models.json',MORPH/'manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md',BASELINE.parent/'iteration52/models.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths if p.exists()},scope='Oracle diagnostic only; frozen iteration53 local_morph_free F1 baseline. Same4070 source,304 selected sentences470 edges326 references. No fitting, cutoff recalibration, candidate injection or reserve/prior query scoring.',taxonomy='Baseline false positives cross subject true finite-subject role and Case with predicate VerbForm; finite_subject_wrong_attachment / nominative_not_finite_subject / non_nominative_not_finite_subject / unknown_or_ambiguous_case_not_finite_subject, crossed with finite/nonfinite/unknown_or_ambiguous predicate. Include nonexclusive Case/finiteness/role overlaps.',masks=MASKS,semantics='Known Case excludingNom/VerbForm excludingFin blocks; missing values permit and ambiguity containing required value permits. Role uses gold direct nominal finite-nsubj target from52. Exact edge permits only target head. Postfilter removes disallowed baseline outputs without reranking. Rerank masks candidates before choosing unchanged linear-score best edge and frozen53 cutoff. Exact-edge-no-gate bypasses cutoff only to expose candidate ceiling. These are oracle upper-bound probes, not deployable changes or guaranteed mathematical upper bounds for each fixed cutoff.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');models=load(BASELINE.parent/'iteration52/models.json');policies=load(BASELINE/'policies.json');previous_rows=load(BASELINE/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in previous_rows};reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve
    output=[];false_positives=[];replays=0;subset_checks=0
    for f in range(5):
        morph=morphs[str(f)]['expanded'];model=models[str(f)]['local_morph']['model'];cutoff=policies[str(f)]['local_morph_free']['f1']['cutoff'];cache={}
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];frames,_=make_frames(sid,tokens,morph,cache)
            for raw in frames:
                prior=lookup[sid,raw['subject']];frame=dict(raw,gold=prior['gold']);original=prior['arms']['local_morph_free']['f1'];proposal=best_edge(frame,model);assert (proposal['predicate'] if accept(proposal,cutoff) else None)==original;replays+=1;r=copy.deepcopy(prior);r['oracle_masks']={}
                for mask in MASKS:
                    filtered=masked_frame(frame,tokens,mask);assert set(filtered['predicates'])<=set(frame['predicates']);subset_checks+=1
                    reranked=best_edge(filtered,model);rerank_decision=reranked['predicate'] if (reranked['predicate'] is not None and (mask=='exact_edge_no_gate' or accept(reranked,cutoff))) else None
                    post=original if original is not None and allows(mask,tokens,frame['subject'],original,frame['gold']) else None
                    r['arms']['rerank_'+mask]={'f1':rerank_decision};r['arms']['postfilter_'+mask]={'f1':post};r['oracle_masks'][mask]=dict(remaining_predicates=filtered['predicates'],best=reranked)
                assert r['arms']['rerank_baseline']['f1']==r['arms']['postfilter_baseline']['f1']==original
                if original is not None and original!=frame['gold']:
                    s=tokens[frame['subject']];v=tokens[original];false_positives.append(dict(sid=sid,author=r['author'],selected_sentence=r['selected_sentence'],subject=frame['subject'],predicate=original,gold=frame['gold'],category=false_positive_class(tokens,frame['subject'],original,frame['gold']),flags=flags(tokens,frame['subject'],original,frame['gold']),subject_word=s['word'],subject_pos=s['pos'],subject_case=s['features'].get('Case',''),subject_rel=s['rel'],subject_head=s['head'],predicate_word=v['word'],predicate_form=v['features'].get('VerbForm',''),sentence=' '.join(t['word'] for t in tokens)))
                output.append(r)
    save(OUT/'frame-predictions.json',output);save(OUT/'false-positive-audit.json',false_positives);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result={};taxonomy={};overlaps={};references={};gold_losses={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in output if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])];errors=[r for r in false_positives if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        taxonomy[scope]=dict(Counter(r['category'] for r in errors));counts=Counter()
        for r in errors:
            c=not r['flags']['case_allowed'];v=not r['flags']['finite_allowed'];role=not r['flags']['subject_role'];counts['total']+=1;counts['case_excluded']+=c;counts['finite_excluded']+=v;counts['role_excluded']+=role;counts['case_and_finite_excluded']+=c and v;counts['case_or_finite_excluded']+=c or v;counts['both_eligible_still_wrong']+=not c and not v;counts['case_annotation_missing']+=r['flags']['case_state']=='unknown';counts['finite_annotation_missing']+=r['flags']['finite_state']=='unknown'
        overlaps[scope]=dict(counts)
        for arm in ARMS:result[scope+'/'+arm]=metrics(selected,arm,'f1')
        for mask in MASKS:
            lost=[]
            for r in selected:
                if r['gold'] is not None and not allows(mask,data[r['sid']]['tokens'],r['subject'],r['gold'],r['gold']):lost.append([r['sid'],r['subject'],r['gold']])
            gold_losses[scope+'/'+mask]=lost
    selected=[r for r in output if r['selected_reference'] is not None]
    for arm in ARMS:references[arm]=dict(n=len(selected),correct=sum(r['arms'][arm]['f1']==r['selected_reference'] for r in selected),wrong=sum(r['arms'][arm]['f1'] is not None and r['arms'][arm]['f1']!=r['selected_reference'] for r in selected),abstained=sum(r['arms'][arm]['f1'] is None for r in selected))
    save(OUT/'evaluation.json',dict(edges=result,taxonomy=taxonomy,overlaps=overlaps,selected_references=references,oracle_gold_exclusions=gold_losses,warning='Every intervention depends on test annotations; none is restoration performance. Postfilter exact_edge_no_gate intentionally equals exact_edge; only rerank version exposes ungated candidate ceiling.'))
    save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),baseline_frame_replays=replays,mask_candidate_subset_checks=subset_checks,models_refitted=0,cutoffs_recalibrated=0,reserve_unscored=200,prior_queries_scored=0))
    print('Taxonomy selected',taxonomy['selected_sentences']);print('Overlaps',overlaps['selected_sentences'])
    for k,r in result.items():
        if k.startswith('selected_sentences/'):print(k,r)
if __name__=='__main__':run()
