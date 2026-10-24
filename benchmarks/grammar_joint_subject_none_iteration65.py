"""Joint optional subject/carrier assignment with soft occupancy competition."""
from pathlib import Path
from collections import Counter,defaultdict
import copy
import numpy as np
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT as UNIT,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest
from benchmarks.grammar_predicate_carriers_iteration56 import OUT as CARRIER,prepare
from benchmarks.grammar_joint_unit_oracle_iteration64b import OUT as PREVIOUS
from benchmarks.grammar_multi_link_attachment_iteration52 import make_frames
from voynich_smt.joint_subject_none import PENALTIES,decode
from voynich_smt.typed_predicate_units import gold_unit,infer
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration65'
ARMS=('baseline','carrier_cal','unit_cal')


def scored(frames,model):
    return [dict(sid=r['sid'],subject=r['subject'],predicates=r['predicates'],scores=(np.asarray(r['vectors'][model['arm']])@np.asarray(model['weights'])).tolist() if r['predicates'] else [],gold=r.get('gold')) for r in frames]


def decode_sentences(frames,cutoff,penalty):
    by_sid=defaultdict(list);predictions={};stats=Counter()
    for r in frames:by_sid[r['sid']].append(r)
    for sid,rs in by_sid.items():
        result,st=decode(rs,cutoff,penalty)
        predictions.update({(sid,s):v for s,v in result.items()});stats.update(st)
    return predictions,dict(stats)


def unit_predictions(predictions,data,unit_model,cache):
    result={}
    for (sid,s),v in predictions.items():
        key=(sid,s,v)
        if key not in cache:cache[key]=infer(data[sid]['tokens'],s,v,unit_model) if v is not None else None
        result[(sid,s)]=cache[key]
    return result


def calibration(frames,data,record,unit_model):
    cutoff=record['policies']['f1']['cutoff'];gold={(r['sid'],r['subject'],r['gold']) for r in frames if r['gold'] is not None};units={(r['sid'],*gold_unit(data[r['sid']]['tokens'],r['subject'])) for r in frames if r['gold'] is not None};grid=[];cache={}
    for penalty in PENALTIES:
        predictions,stats=decode_sentences(frames,cutoff,penalty);up=unit_predictions(predictions,data,unit_model,cache)
        edges={(sid,s,v) for (sid,s),v in predictions.items() if v is not None};pred={(sid,*u) for (sid,s),u in up.items() if u is not None}
        grid.append(dict(penalty=penalty,carrier=edge_metrics(gold,edges),unit=edge_metrics(units,pred),solver=stats))
    selected={}
    for task in ('carrier','unit'):
        selected[task]=max(grid,key=lambda r:(r[task]['f1'],-r[task]['predicted'],-r['penalty']))
    return dict(cutoff=cutoff,selected=selected,grid=grid)


def evaluate(rows):
    metrics={};carriers={};per_role={}
    for scope in ('all_source','selected_sentences','Cicero_selected','Palladius_selected'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None};cg={(r['sid'],r['subject'],r['carrier_gold']) for r in rs if r['carrier_gold'] is not None}
        for arm in ARMS:
            pred={(r['sid'],*r['competition_unit'][arm]) for r in rs if r['competition_unit'][arm] is not None};cp={(r['sid'],r['subject'],r['competition_carrier'][arm]) for r in rs if r['competition_carrier'][arm] is not None};metrics[scope+'/'+arm]=edge_metrics(gold,pred);carriers[scope+'/'+arm]=edge_metrics(cg,cp)
            for role in ('direct','cop','aux'):per_role[scope+'/'+arm+'/'+role]=edge_metrics({u for u in gold if u[-1]==role},{u for u in pred if u[-1]==role})
    return dict(unit_metrics=metrics,carrier_metrics=carriers,per_role=per_role)


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_joint_subject_none_iteration65_audit.py'),Path('src/voynich_smt/joint_subject_none.py'),Path('tests/test_joint_subject_none.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',MORPH/'models.json',CARRIER/'models.json',UNIT/'models.json',UNIT/'frame-predictions.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070 source/fivepartitions/3365units519selected. Frozen56 carrier scores/candidate lattice and57 head scorer. No training/newfeatures/gold inference. Ambiguous frame excluded fromcompetition. Reserve200unscored, priorqueries0.',decoder='Maximize sum(score-cutoff) over optional subject-carrier assignments minus penalty*sum_v(max(0,n_subjects(v)-1)); NONEutility0. No hardcap, positiveutility alternatives only, original best-edge ties remainabstained. Signed-incidence network LP with integralbounds; assertintegrality. If an assigned edge can be removed without reducing optimal objective within1e-8, abstain that subject as globallyambiguous. Zero penalty must reproduce frozen56 gates/57 units. No annotation, coordination or morphology beyond existing predicted features.',calibration='Fixed56 cutoffs reused (-1 or-.5). Penalty grid0,.25,.5,1,2,4,8. Primary carrier_cal maximizes calibration carrier F1, secondary unit_cal exactunitF1, ties fewerpredictions then smallerpenalty. Same goldcalibration labels/partitions asprior. Report both without test-based choice. Original lambda0 control retains samecutoff; no additional threshold tuning.',success='Require meaningful full-source exactunit gain with selected-sentence and pertype checks, rather than carrier precision alone. If no encouraging result, continue to predicate-complement/annotation diagnostic.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');carrier_models=load(CARRIER/'models.json');unit_models=load(UNIT/'models.json');prior=load(UNIT/'frame-predictions.json');old={(r['sid'],r['subject']):r for r in prior};reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;cal_frames={};test_frames={};mutations=0
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not(a&b or a&c or b&c);record=carrier_models[str(f)]['carrierfit_carriercal'];morph=morphs[str(f)]['expanded'];cal,_=prepare(part['calibration'],data,morph,'carrier');cal_frames[str(f)]=scored(cal,record['model']);test,_=prepare(part['test'],data,morph,'carrier');test_frames[str(f)]=scored(test,record['model'])
        for sid in part['test']:
            if not any(r['sid']==sid and r['selected_sentence'] for r in prior):continue
            tokens=data[sid]['tokens'];masked=[dict(t,head=None,rel='?',features={},lemma='?') for t in tokens];original,_=make_frames(sid,tokens,morph,{});other,_=make_frames(sid,masked,morph,{});assert original==other;mutations+=1
        print('Prepared',f,len(cal),len(test),flush=True)
    save(OUT/'calibration-lattices.json',cal_frames);save(OUT/'test-lattices.json',test_frames);save(OUT/'lattice-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));policies={}
    for f in range(5):
        policies[str(f)]=calibration(cal_frames[str(f)],data,carrier_models[str(f)]['carrierfit_carriercal'],unit_models[str(f)]['model']);print('Calibrated',f,policies[str(f)]['selected'],flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));rows=[];solver={};replays=0
    for f in range(5):
        record=policies[str(f)];frames=test_frames[str(f)];cache={};predictions={};up={}
        for arm in ARMS:
            penalty=0 if arm=='baseline' else record['selected'][arm.split('_')[0]]['penalty'];predictions[arm],solver[str(f)+'/'+arm]=decode_sentences(frames,record['cutoff'],penalty);up[arm]=unit_predictions(predictions[arm],data,unit_models[str(f)]['model'],cache)
        for frame in frames:
            key=(frame['sid'],frame['subject']);r=copy.deepcopy(old[key]);r['competition_carrier']={a:predictions[a][key] for a in ARMS};r['competition_unit']={a:up[a][key] for a in ARMS};assert r['competition_carrier']['baseline']==r['arms']['carrierfit_carriercal']['f1'];assert r['competition_unit']['baseline']==r['unit_pipeline']['learned'];replays+=1;rows.append(r)
    # Preserve the one ambiguous prior frame without allowing it to affect groups.
    for r in prior:
        if r['carrier_ambiguous']:
            item=copy.deepcopy(r);item['competition_carrier']={a:None for a in ARMS};item['competition_unit']={a:None for a in ARMS};rows.append(item)
    save(OUT/'frame-predictions.json',rows);save(OUT/'solver-statistics.json',solver);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));evaluation=evaluate(rows);save(OUT/'evaluation.json',evaluation);save(OUT/'validation.json',dict(models_refitted=0,baseline_replays=replays,selected_inference_mutation_checks=mutations,prior_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in evaluation['unit_metrics'].items():print(k,r,flush=True)
if __name__=='__main__':run()
