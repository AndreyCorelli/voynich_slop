"""Carrier task definition, recalibration and supervised training, with dual metrics."""
from pathlib import Path
from collections import Counter
import copy
from benchmarks.grammar_none_gate_iteration53 import OUT as BASELINE,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest,make_frames,metrics
from benchmarks.grammar_endpoint_oracle_iteration55 import OUT as PREVIOUS
from voynich_smt.multi_link_attachment import fit
from voynich_smt.none_gate import best_edge,accept,calibrate
from voynich_smt.predicate_carriers import target,relabel
OUT=PREVIOUS.parent/'iteration56'
ARMS=tuple(fit_task+'fit_'+cal_task+'cal' for fit_task in ('direct','carrier') for cal_task in ('direct','carrier'))


def prepare(ids,data,morph,task):
    frames=[];counts=Counter();positive=0;retrievable=0;cache={}
    for sid in ids:
        tokens=data[sid]['tokens'];base,_=make_frames(sid,tokens,morph,cache);rows,audit=relabel(base,tokens,task);frames.extend(rows);counts.update(r['kind'] for r in audit)
        positive+=sum(r['gold'] is not None for r in rows);retrievable+=sum(r['gold'] is not None and r['gold'] in r['predicates'] for r in rows)
    return frames,dict(target_kinds=dict(counts),scored_frames=len(frames),gold=positive,retrievable=retrievable)


def evaluate(rows):
    result={};reference={};baseline={}
    for task in ('direct','carrier'):
        for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
            selected=[dict(r,gold=r[task+'_gold']) for r in rows if (task=='direct' or not r['carrier_ambiguous']) and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))]
            for arm in ARMS:
                for policy in ('f1','precision90'):result[task+'/'+scope+'/'+arm+'/'+policy]=metrics(selected,arm,policy)
            baseline[task+'/'+scope]=metrics(selected,'local_morph_free','f1')
    selected=[r for r in rows if r['selected_reference'] is not None]
    for arm in ARMS:
        for policy in ('f1','precision90'):reference[arm+'/'+policy]=dict(n=len(selected),correct=sum(r['arms'][arm][policy]==r['selected_reference'] for r in selected),wrong=sum(r['arms'][arm][policy] is not None and r['arms'][arm][policy]!=r['selected_reference'] for r in selected),abstained=sum(r['arms'][arm][policy] is None for r in selected))
    return dict(edges=result,frozen_baseline_on_each_task=baseline,original_references=reference)


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/predicate_carriers.py'),Path('src/voynich_smt/multi_link_attachment.py'),Path('src/voynich_smt/none_gate.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'models.json',MORPH/'manifest.json',BASELINE.parent/'iteration52/models.json',BASELINE/'policies.json',BASELINE/'frame-predictions.json',BASELINE/'verification-manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},task='Original direct finite VERB/AUX nsubj target wins unchanged. Otherwise, for nominal/pronominal nsubj with nonverbal or known nonfinite governor, use its unique finite VERB/AUX child with rel cop/aux as carrier. Multiple such children => ambiguous and unscored only on expanded task; no choice => NONE. Unknown/nonatomic verbal governor form stays NONE with separate audit. Coordination not projected. Annotation-derived labels only, never inference.',scope='Same4070 source sentences/five partitions. Primary304 selected sentences plus all-source/author breakdowns; old326 references retained. Readable words and supplied POS; no reserve/prior query scoring.',controls='Freeze candidates and local_morph features from49/50/52. Reuse direct-trained52 models; fit carrier targets with same L2/optimizer and in-sample morphology features as baseline. For both models recalibrate on direct AND carrier calibration labels using unchanged53 MAP-free grid/F1/precision90 objectives. Main expanded-task comparison uses carrier calibration for both models. Frozen53 predictions scored on both tasks separately. No gold head/morphology/carrier selection at inference. Carrier head is not predicted separately: this tests finite-carrier endpoint edges, not recovery of an entire predicate unit.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');direct_models=load(BASELINE.parent/'iteration52/models.json');reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models={};fit_audit={}
    # Fit target coverage is frozen before attachment fitting/test annotation inspection.
    for f in range(5):
        p=parts[str(f)];a,b,c=(set(p[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c)
        _,audit=prepare(p['fit'],data,morphs[str(f)]['expanded'],'carrier');fit_audit[str(f)]=audit
    save(OUT/'fit-target-audit.json',fit_audit);save(OUT/'target-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    for f in range(5):
        p=parts[str(f)];outer=morphs[str(f)]['expanded'];training,_=prepare(p['fit'],data,outer,'carrier');learned=fit(training,'local_morph');fitted={'direct':direct_models[str(f)]['local_morph']['model'],'carrier':learned};calibrations={task:prepare(p['calibration'],data,outer,task)[0] for task in ('direct','carrier')};models[str(f)]={}
        for fit_task,model in fitted.items():
            for cal_task,frames in calibrations.items():
                proposals=[best_edge(frame,model) for frame in frames];models[str(f)][fit_task+'fit_'+cal_task+'cal']=dict(model=model,policies=calibrate(frames,proposals,'free'))
        print('Fit/calibrated',f,{arm:dict(cutoff=r['policies']['f1']['cutoff'],cal_f1=r['policies']['f1']['f1']) for arm,r in models[str(f)].items()},flush=True)
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));prior=load(BASELINE/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in prior};rows=[];target_audit=[];mutation_checks=0
    for f in range(5):
        cache={};outer=morphs[str(f)]['expanded']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];frames,_=make_frames(sid,tokens,outer,cache)
            if any(lookup[sid,frame['subject']]['selected_sentence'] for frame in frames):
                masked=[dict(t,head=None,rel='?',features={},lemma='?') for t in tokens];other,_=make_frames(sid,masked,outer,cache);assert frames==other;mutation_checks+=1
            for frame in frames:
                old=lookup[sid,frame['subject']];r=copy.deepcopy(old);truth=target(tokens,frame['subject']);assert truth['direct']==old['gold'];assert r['candidate_predicates']==frame['predicates'];r.update(direct_gold=truth['direct'],carrier_gold=truth['carrier'],carrier_ambiguous=truth['ambiguous'],carrier_kind=truth['kind'],carrier_proposals={});target_audit.append(dict(sid=sid,subject=frame['subject'],selected_sentence=r['selected_sentence'],**truth,retrievable=truth['carrier'] is not None and truth['carrier'] in frame['predicates']))
                for arm,record in models[str(f)].items():
                    proposal=best_edge(frame,record['model']);r['carrier_proposals'][arm]=proposal;r['arms'][arm]={policy:proposal['predicate'] if accept(proposal,record['policies'][policy]['cutoff']) else None for policy in ('f1','precision90')}
                assert r['arms']['directfit_directcal']==old['arms']['local_morph_free']
                rows.append(r)
    save(OUT/'target-audit.json',target_audit);save(OUT/'frame-predictions.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);opportunity={}
    for scope in ('selected_sentences','all_source'):
        selected=[r for r in target_audit if scope=='all_source' or r['selected_sentence']];counts=Counter(r['kind'] for r in selected);opportunity[scope]=dict(target_kinds=dict(counts),direct_gold=sum(r['direct'] is not None for r in selected),carrier_gold=sum(r['carrier'] is not None for r in selected),carrier_retrievable=sum(r['retrievable'] for r in selected),new_projected_gold=sum(r['kind'] in ('copula','auxiliary') for r in selected),new_projected_retrievable=sum(r['kind'] in ('copula','auxiliary') and r['retrievable'] for r in selected),ambiguous=sum(r['ambiguous'] for r in selected))
    result['opportunity']=opportunity;save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),new_attachment_models=5,direct_targets_replayed=len(rows),frozen_baseline_policies_reproduced=len(rows),selected_sentence_inference_mutation_checks=mutation_checks,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    print(opportunity)
    for k,r in result['edges'].items():
        if '/selected_sentences/' in k and k.endswith('/f1'):print(k,r)
if __name__=='__main__':run()
