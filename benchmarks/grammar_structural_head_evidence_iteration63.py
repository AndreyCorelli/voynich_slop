"""Learn candidate-conditioned phrase/clause cues; keep unit scores/endpoints fixed."""
from pathlib import Path
from collections import defaultdict
import copy
import numpy as np
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT as UNIT,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest,prepare
from benchmarks.grammar_pairwise_units_iteration62 import OUT as PREVIOUS
from voynich_smt.typed_predicate_units import ROLES,choices,matrix,select
from voynich_smt.structural_head_evidence import MODES,ARMS,TASKS,fit,probabilities,evidence,infer,calibrate
from voynich_smt.copular_head_oracle import flags
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration63'
ALL_ARMS=('baseline',)+tuple(m+'_'+a for m in MODES for a in ARMS)


def calibration_frames(frames,data,unit_model,proxy):
    return [dict(gold=r['gold'],options=r['options'],scores=r['x']@np.asarray(unit_model['weights']),cues=evidence(data[r['sid']]['tokens'],r['gold'][2],r['options'],proxy)) for r in frames]


def evaluate(rows):
    metrics={};per_role={};conditional={};true_type={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        chosen=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))]
        gold={(r['sid'],*r['unit_gold']) for r in chosen if r['unit_gold'] is not None}
        for arm in ALL_ARMS:
            pred={(r['sid'],*r['structure_pipeline'][arm]) for r in chosen if r['structure_pipeline'][arm] is not None};metrics[scope+'/'+arm]=edge_metrics(gold,pred)
            for role in ROLES:
                per_role[scope+'/'+arm+'/'+role]=edge_metrics({g for g in gold if g[-1]==role},{p for p in pred if p[-1]==role})
                positive=[r for r in chosen if r['unit_gold'] is not None and r['unit_gold'][3]==role]
                conditional[scope+'/'+arm+'/'+role]=dict(n=len(positive),exact=sum(r['structure_oracle_endpoint'][arm]==r['unit_gold'] for r in positive))
                true_type[scope+'/'+arm+'/'+role]=dict(n=len(positive),exact=sum(r['structure_true_type'][arm]==r['unit_gold'] for r in positive))
    return dict(unit_metrics=metrics,per_role=per_role,oracle_endpoint_accuracy=conditional,true_endpoint_and_type_accuracy=true_type)


def cue_metrics(records):
    result={}
    for mode in MODES:
        for task in TASKS:
            candidates=[(c['probabilities'][mode][TASKS.index(task)],int(c['flags'][task])) for r in records for c in r['candidates']]
            result[mode+'/'+task]=dict(n=len(candidates),correct=sum((p>=.5)==bool(y) for p,y in candidates),brier=float(np.mean([(p-y)**2 for p,y in candidates])),nll=float(np.mean([-np.log(max(1e-12,p if y else 1-p)) for p,y in candidates])))
            for subset in ('all_wrong','baseline_outrankers','oracle_blockable_outrankers'):
                comparison=[]
                for r in records:
                    gold=next(c for c in r['candidates'] if c['head']==r['gold'][1])
                    for c in r['candidates']:
                        if c is gold:continue
                        if subset!='all_wrong' and c['score']<=gold['score']+1e-10:continue
                        if subset=='oracle_blockable_outrankers' and not (gold['flags'][task] and not c['flags'][task]):continue
                        delta=gold['probabilities'][mode][TASKS.index(task)]-c['probabilities'][mode][TASKS.index(task)];comparison.append(delta)
                result[mode+'/'+task+'/'+subset]=dict(n=len(comparison),gold_higher=sum(d>1e-10 for d in comparison),tied=sum(abs(d)<=1e-10 for d in comparison),gold_lower=sum(d< -1e-10 for d in comparison))
    return result


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_structural_head_evidence_iteration63_audit.py'),Path('src/voynich_smt/structural_head_evidence.py'),Path('src/voynich_smt/copular_head_oracle.py'),Path('src/voynich_smt/dependency_role_proxy.py'),Path('src/voynich_smt/typed_predicate_units.py'),Path('tests/test_structural_head_evidence.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',UNIT/'models.json',UNIT/'frame-predictions.json',UNIT/'evaluation.json',UNIT/'verification-manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070 sentences/five fit-cal-test partitions,3365 goldunits519 selected; frozen57 unit weights and56 endpoints/candidates. No reserve or prior target queries.',probes='Two independent binary logistic outputs phrase-not-dependent and same gold clause anchor, from58 flags. Fit only goldendpoint fitframe head/carrier pairs, heads deduplicated across candidate roles. Each frame totalweight1; losses averaged over2tasks; L2=.001/minfeaturecount3/fixed optimizer. coarse: head/carrier POS, interaction, distancebucket/order. context adds ±2 POS windows/pairs and interval counts. No words, morphology or dependency input. Clause reflexivity h=v set toprobability1 at inference. All inference scores computed before diagnostic flags.',addition='Primary context_joint; coarse_joint controls coarse cues, phrase/clause-only ablations isolate targets. Original scores plus nonnegative weights times log phrase/clause probabilities, floor1e-6; same additions for all roles sharinghead. No hard masking or typeoffset tuning, no refit of unit score.',calibration='Each mode phrase-only/clause-only/joint grid weights0,.5,1,2,4, zero included; maximize exact unique unit count at gold calibration endpoints. Prefer smaller totals then clause/phrase weights. No test-based policy selection.',diagnostics='Report full pipeline exactunit pertype F1 and goldendpoint/true-type ranking. On650goldcopframes record every competinghead flags/probabilities/frozen scores; compare goldvswrong on allwrong/baselineoutrankers/oracleblockableoutrankers. Token/candidate accuracy alone is insufficient. Annotation clause anchors can encode target attachment; these are auxiliary training labels, not available inference masks.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];unit_models=load(UNIT/'models.json');prior=load(UNIT/'frame-predictions.json');by_sid=defaultdict(list)
    for r in prior:by_sid[r['sid']].append(r)
    reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve
    models={}
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not(a&b or a&c or b&c);training,_=prepare(part['fit'],data);cal,_=prepare(part['calibration'],data);models[str(f)]={}
        for mode in MODES:
            proxy=fit(training,data,mode);frames=calibration_frames(cal,data,unit_models[str(f)]['model'],proxy);policies={arm:calibrate(frames,arm) for arm in ARMS};models[str(f)][mode]=dict(proxy=proxy,policies=policies)
            print('Fit/calibrated',f,mode,{a:r['selected'] for a,r in policies.items()},flush=True)
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));rows=[];cue_rows=[];mutations=zero_replays=0
    for f in range(5):
        w=np.asarray(unit_models[str(f)]['model']['weights'])
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];masked=[dict(t,word='?',lemma='?',head=None,rel='?',features={}) for t in tokens]
            for old in by_sid.get(sid,[]):
                r=copy.deepcopy(old);r['structure_pipeline']={'baseline':old['unit_pipeline']['learned']};r['structure_oracle_endpoint']={'baseline':old['unit_oracle_endpoint']['learned']};r['structure_true_type']={}
                gold=r['unit_gold'];endpoint=r['arms']['carrierfit_carriercal']['f1']
                for field,v in (('structure_pipeline',endpoint),('structure_oracle_endpoint',gold[2] if gold else None)):
                    if v is None:
                        for arm in ALL_ARMS:r[field][arm]=None
                        continue
                    options=choices(tokens,r['subject'],v);scores=matrix(tokens,r['subject'],v,options)@w;assert select(scores,options,r['subject'],v)==r[field]['baseline']
                    if field=='structure_oracle_endpoint':
                        kept=[j for j,(_,role) in enumerate(options) if role==gold[3]];r['structure_true_type']['baseline']=select(scores[kept],[options[j] for j in kept],r['subject'],v)
                    for mode in MODES:
                        record=models[str(f)][mode];cues=evidence(tokens,v,options,record['proxy'])
                        if r['selected_sentence']:
                            assert np.array_equal(cues,evidence(masked,v,options,record['proxy']));mutations+=1
                        assert infer(scores,options,r['subject'],v,cues,0,0)==r[field]['baseline'];zero_replays+=1
                        for arm in ARMS:
                            policy=record['policies'][arm]['selected'];name=mode+'_'+arm;r[field][name]=infer(scores,options,r['subject'],v,cues,policy['phrase_weight'],policy['clause_weight'])
                            if field=='structure_oracle_endpoint':r['structure_true_type'][name]=infer(scores[kept],[options[j] for j in kept],r['subject'],v,cues[kept],policy['phrase_weight'],policy['clause_weight'])
                if gold is None:
                    for arm in ALL_ARMS:r['structure_true_type'][arm]=None
                if gold and gold[3]=='cop':
                    s,h,v,_=gold;options=choices(tokens,s,v);scores=matrix(tokens,s,v,options)@w;heads=[j for j,(_,role) in enumerate(options) if role=='cop'];hs=[options[j][0] for j in heads];ps={m:probabilities(tokens,v,hs,models[str(f)][m]['proxy']) for m in MODES}
                    candidates=[dict(head=head,score=float(scores[j]),flags=flags(tokens,head,v),probabilities={m:ps[m][i].tolist() for m in MODES}) for i,(head,j) in enumerate(zip(hs,heads))]
                    cue_rows.append(dict(sid=sid,subject=s,gold=gold,selected_sentence=r['selected_sentence'],candidates=candidates))
                rows.append(r)
    save(OUT/'frame-predictions.json',rows);save(OUT/'cue-predictions.json',cue_rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'cue-metrics.json',cue_metrics(cue_rows));save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),models=10,selected_inference_mutation_checks=mutations,zero_weight_replays=zero_replays,endpoints_unchanged=True,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result['unit_metrics'].items():
        if k.startswith(('selected_sentences/','all_source/')):print(k,r)
if __name__=='__main__':run()
