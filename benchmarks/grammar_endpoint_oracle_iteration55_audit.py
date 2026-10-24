"""Independent oracle-mask replay and finite-subject task-scope audit."""
from collections import Counter,defaultdict
from benchmarks.grammar_endpoint_oracle_iteration55 import OUT,BASELINE,MORPH,SOURCE,MASKS,ARMS,load,save,digest,make_frames,metrics
from voynich_smt.none_gate import best_edge,accept
from voynich_smt.endpoint_oracle import flags,allows,masked_frame,false_positive_class


def projected_scope(tokens,s,v):
    subject=tokens[s];predicate=tokens[v];head=subject['head'];tags=[]
    if subject['rel']=='nsubj' and head is not None:
        if predicate['rel']=='cop' and predicate['head']==head:tags.append('copular_projection')
        if predicate['rel']=='aux' and predicate['head']==head:tags.append('finite_auxiliary_projection')
        # Only xcomp links: do not project arbitrary ccomp/relative-clause subjects.
        seen=set();current=head
        while current is not None and current not in seen and tokens[current]['rel']=='xcomp':
            seen.add(current);current=tokens[current]['head']
            if current==v:tags.append('xcomp_governor_projection');break
    if subject['rel']=='conj':
        seen=set();current=s
        while current is not None and current not in seen and tokens[current]['rel']=='conj':
            seen.add(current);current=tokens[current]['head']
        if current is not None and tokens[current]['rel']=='nsubj' and tokens[current]['head']==v:tags.append('coordinated_subject_projection')
    return tags


def run():
    hashes=0
    for name in ('design-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');models=load(BASELINE.parent/'iteration52/models.json');policies=load(BASELINE/'policies.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};prior={(r['sid'],r['subject']):r for r in load(BASELINE/'frame-predictions.json')};decisions=0;vector_checks=0;counterfactual_pairs=0
    errors=[]
    for f in range(5):
        cache={};model=models[str(f)]['local_morph']['model'];cutoff=policies[str(f)]['local_morph_free']['f1']['cutoff']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];frames,_=make_frames(sid,tokens,morphs[str(f)]['expanded'],cache)
            for raw in frames:
                r=lookup[sid,raw['subject']];old=prior[sid,raw['subject']]
                for key in old:
                    if key=='arms':
                        for arm,value in old[key].items():assert r[key][arm]==value
                    else:assert r[key]==old[key]
                frame=dict(raw,gold=r['gold']);original=old['arms']['local_morph_free']['f1']
                for mask in MASKS:
                    filtered=masked_frame(frame,tokens,mask)
                    for arm,values in filtered['vectors'].items():
                        for v,x in zip(filtered['predicates'],values):assert x==frame['vectors'][arm][frame['predicates'].index(v)];vector_checks+=1
                    proposal=best_edge(filtered,model);assert proposal==r['oracle_masks'][mask]['best'];assert filtered['predicates']==r['oracle_masks'][mask]['remaining_predicates'];counterfactual_pairs+=len(filtered['predicates'])
                    expected=proposal['predicate'] if proposal['predicate'] is not None and (mask=='exact_edge_no_gate' or accept(proposal,cutoff)) else None;assert r['arms']['rerank_'+mask]['f1']==expected;decisions+=1
                    expected=original if original is not None and allows(mask,tokens,frame['subject'],original,frame['gold']) else None;assert r['arms']['postfilter_'+mask]['f1']==expected;decisions+=1
                if original is not None and original!=r['gold']:
                    errors.append(dict(sid=sid,subject=frame['subject'],predicate=original,selected_sentence=r['selected_sentence'],category=false_positive_class(tokens,frame['subject'],original,r['gold']),subject_rel=tokens[frame['subject']]['rel'],projections=projected_scope(tokens,frame['subject'],original)))
    audit=load(OUT/'false-positive-audit.json');assert {(e['sid'],e['subject'],e['predicate'],e['category']) for e in errors}=={(e['sid'],e['subject'],e['predicate'],e['category']) for e in audit};evaluation=load(OUT/'evaluation.json');metric_replays=0;scope_audit={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in rows if scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0])]
        for arm in ARMS:assert metrics(selected,arm,'f1')==evaluation['edges'][scope+'/'+arm];metric_replays+=1
    for scope in ('selected_sentences','all_source'):
        selected=[e for e in errors if scope=='all_source' or e['selected_sentence']];nom=[e for e in selected if e['category'].startswith('nominative_not')];counts=Counter(tag for e in selected for tag in e['projections']);scope_audit[scope]=dict(baseline_false_positives=len(selected),nominative_not_finite_subject_relations=dict(Counter(e['subject_rel'] for e in nom)),projection_tags=dict(counts),any_projection=sum(bool(e['projections']) for e in selected),note='Gold-edge pattern matches outside current direct finite-nsubj task. These tags are scope diagnostics, not adjudicated alternative gold edges; xcomp projection in particular can involve control/raising ambiguities.')
    excluded=[]
    for sid,s,v in evaluation['oracle_gold_exclusions']['all_source/case']:
        tokens=data[sid]['tokens'];excluded.append(dict(sid=sid,subject=s,predicate=v,subject_token=tokens[s],predicate_token=tokens[v],baseline_predicted=prior[sid,s]['arms']['local_morph_free']['f1'],sentence=' '.join(t['word'] for t in tokens)))
    save(OUT/'scope-audit.json',dict(scopes=scope_audit,projection_examples=[e for e in errors if e['projections']],gold_case_exclusion_examples=excluded))
    save(OUT/'independent-validation.json',dict(hash_checks=hashes,mask_decisions_replayed=decisions,preserved_vector_checks=vector_checks,masked_candidate_pairs=counterfactual_pairs,aggregate_metrics_replayed=metric_replays,false_positive_taxonomy_replayed=len(errors),previous_prediction_fields_unchanged=True,models_refitted=0,cutoffs_recalibrated=0,reserve_unscored=200,prior_queries_scored=0))
    print(scope_audit);print('Metrics replayed',metric_replays)
if __name__=='__main__':run()
