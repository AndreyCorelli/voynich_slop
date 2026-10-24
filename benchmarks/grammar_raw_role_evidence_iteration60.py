"""Raw vs POS-normalized role evidence, fixed proxies/head models/endpoints."""
from pathlib import Path
from collections import defaultdict,Counter
import copy
import numpy as np
from benchmarks.grammar_dependency_role_proxy_iteration59 import OUT as PREVIOUS,UNIT,MORPH,SOURCE,EXAMPLES,RESERVE,MODES,ARMS,load,save,digest
from voynich_smt.typed_predicate_units import choices,matrix,select
from voynich_smt.dependency_role_proxy import probabilities,evidence as normalized_evidence,infer,calibrate
from voynich_smt.raw_role_evidence import evidence as raw_evidence
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration60'
NORMALIZATIONS=('normalized','raw')
ALL_ARMS=tuple(n+'_'+m+'_'+a for n in NORMALIZATIONS for m in MODES for a in ARMS)


def calibration_frames(ids,data,by_sid,unit_model,proxy):
    result={n:[] for n in NORMALIZATIONS}
    for sid in ids:
        tokens=data[sid]['tokens'];p=probabilities(tokens,proxy)
        for r in by_sid.get(sid,[]):
            gold=r['unit_gold']
            if gold is None:continue
            options=choices(tokens,gold[0],gold[2]);scores=matrix(tokens,gold[0],gold[2],options)@np.asarray(unit_model['weights']);normalized=normalized_evidence(tokens,gold[2],options,p,proxy);raw=raw_evidence(gold[2],options,p)
            for n,(head,typ) in (('normalized',normalized),('raw',raw)):result[n].append(dict(gold=gold,options=options,scores=scores,head=head,type=typ))
    return result


def evaluate(rows):
    metrics={};conditional={};kinds={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in selected if r['unit_gold'] is not None}
        for arm in ('baseline',)+ALL_ARMS:
            predicted={(r['sid'],*r['ablation_pipeline'][arm]) for r in selected if r['ablation_pipeline'][arm] is not None};metrics[scope+'/'+arm]=edge_metrics(gold,predicted)
            for kind in ('all','direct','cop','aux'):
                positive=[r for r in selected if r['unit_gold'] is not None and (kind=='all' or r['unit_gold'][3]==kind)];conditional[scope+'/'+arm+'/'+kind]=dict(n=len(positive),exact=sum(r['ablation_oracle_endpoint'][arm]==r['unit_gold'] for r in positive));kinds[scope+'/'+arm+'/'+kind]=dict(n=len(positive),exact=sum(r['ablation_pipeline'][arm]==r['unit_gold'] for r in positive))
    return dict(unit_metrics=metrics,oracle_endpoint_accuracy=conditional,pipeline_by_gold_kind=kinds)


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/raw_role_evidence.py'),Path('src/voynich_smt/dependency_role_proxy.py'),Path('src/voynich_smt/typed_predicate_units.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',UNIT/'models.json',PREVIOUS/'models.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'evaluation.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},change='Only remove POS-prior subtraction from head logP(non-dependent) and carrier logP(role), direct=>other. Frozen59 proxies,57 learned head scores,56 endpoints, targets and domains. No refitting. Recalibrate normalized control and raw additions under identical conditions.',calibration='Same59 correct-endpoint exact-unit objective, ties lower total/type/head weight, grids0,.5,1,2,4; POS/lexical proxies, head/type/joint ablations. Zero baseline and all normalized policies must reproduce59 exactly. Calibration-only selection; no test labels choose weights.',scope='Same4070 source/five partitions,3365 units519 selected, ambiguous frame exclusion unchanged. Raw evidence is proposed after inspecting59 contrasts, so this is development follow-up, not fresh confirmation. No reserve/prior queries.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];unit_models=load(UNIT/'models.json');proxy_models=load(PREVIOUS/'models.json');prior=load(PREVIOUS/'frame-predictions.json');by_sid=defaultdict(list)
    for r in prior:by_sid[r['sid']].append(r)
    reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;policies={};normalized_policy_replays=0
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);policies[str(f)]={}
        for mode in MODES:
            frames=calibration_frames(part['calibration'],data,by_sid,unit_models[str(f)]['model'],proxy_models[str(f)][mode]['proxy'])
            for n in NORMALIZATIONS:
                for arm in ARMS:
                    key=n+'_'+mode+'_'+arm;policies[str(f)][key]=calibrate(frames[n],arm)
                    if n=='normalized':assert policies[str(f)][key]==proxy_models[str(f)][mode]['policies'][arm];normalized_policy_replays+=1
        print('Calibrated',f,{a:r['selected'] for a,r in policies[str(f)].items() if a.startswith('raw_')},flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));rows=[];normalized_decision_replays=0;zero_replays=0;mutation_checks=0
    for f in range(5):
        unit_model=unit_models[str(f)]['model']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];ps={m:probabilities(tokens,proxy_models[str(f)][m]['proxy']) for m in MODES}
            if any(r['selected_sentence'] for r in by_sid.get(sid,[])):
                masked=[dict(t,head=None,rel='?',features={},lemma='?') for t in tokens]
                for mode in MODES:assert np.array_equal(probabilities(masked,proxy_models[str(f)][mode]['proxy']),ps[mode]);mutation_checks+=1
            for old in by_sid.get(sid,[]):
                r=copy.deepcopy(old);r['ablation_pipeline']={'baseline':old['role_pipeline']['baseline']};r['ablation_oracle_endpoint']={'baseline':old['role_oracle_endpoint']['baseline']};endpoint=r['arms']['carrierfit_carriercal']['f1'];gold=r['unit_gold']
                for field,oldfield,v in (('ablation_pipeline','role_pipeline',endpoint),('ablation_oracle_endpoint','role_oracle_endpoint',gold[2] if gold else None)):
                    if v is None:
                        for arm in ALL_ARMS:r[field][arm]=None
                        continue
                    options=choices(tokens,r['subject'],v);scores=matrix(tokens,r['subject'],v,options)@np.asarray(unit_model['weights']);assert select(scores,options,r['subject'],v)==r[field]['baseline']
                    for mode,p in ps.items():
                        proxy=proxy_models[str(f)][mode]['proxy'];norm=normalized_evidence(tokens,v,options,p,proxy);raw=raw_evidence(v,options,p)
                        for n,(head,typ) in (('normalized',norm),('raw',raw)):
                            assert infer(scores,options,r['subject'],v,head,typ,0,0)==r[field]['baseline'];zero_replays+=1
                            for arm in ARMS:
                                key=n+'_'+mode+'_'+arm;weights=policies[str(f)][key]['selected'];prediction=infer(scores,options,r['subject'],v,head,typ,weights['head_weight'],weights['type_weight']);r[field][key]=prediction
                                if n=='normalized':assert prediction==old[oldfield][mode+'_'+arm];normalized_decision_replays+=1
                rows.append(r)
    save(OUT/'frame-predictions.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),models_refitted=0,normalized_policies_replayed=normalized_policy_replays,normalized_active_decisions_replayed=normalized_decision_replays,zero_weight_replays=zero_replays,selected_proxy_mutation_checks=mutation_checks,all_previous_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result['unit_metrics'].items():
        if k.startswith(('selected_sentences/','all_source/')):print(k,r)
if __name__=='__main__':run()
