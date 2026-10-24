"""Pairwise unit ranking with unchanged features, endpoints and offset controls."""
from pathlib import Path
from collections import Counter,defaultdict
import copy
import numpy as np
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT as UNIT,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest,prepare
from benchmarks.grammar_type_balanced_units_iteration61 import OUT as PREVIOUS
from voynich_smt.typed_predicate_units import ROLES,choices,matrix,select
from voynich_smt.type_balanced_units import calibrate,infer
from voynich_smt.pairwise_units import fit
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration62'
LOSSES=('unweighted','pair_all','pair_hard')
POLICIES=('zero','micro')
ARMS=tuple(loss+'_'+policy for loss in LOSSES for policy in POLICIES)
ZERO={r:0. for r in ROLES}


def evaluate(rows):
    metrics={};per_role={};macro={};conditional={};true_type={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in selected if r['unit_gold'] is not None}
        for arm in ARMS:
            predicted={(r['sid'],*r['pairwise_pipeline'][arm]) for r in selected if r['pairwise_pipeline'][arm] is not None};metrics[scope+'/'+arm]=edge_metrics(gold,predicted);recalls=[];f1=[]
            for role in ROLES:
                g={u for u in gold if u[-1]==role};p={u for u in predicted if u[-1]==role};score=edge_metrics(g,p);per_role[scope+'/'+arm+'/'+role]=score;recalls.append(score['recall']);f1.append(score['f1'])
                positive=[r for r in selected if r['unit_gold'] is not None and r['unit_gold'][3]==role];conditional[scope+'/'+arm+'/'+role]=dict(n=len(positive),exact=sum(r['pairwise_oracle_endpoint'][arm]==r['unit_gold'] for r in positive))
            macro[scope+'/'+arm]=dict(macro_f1=float(np.mean(f1)),macro_recall=float(np.mean([v for v in recalls if v is not None])))
        for loss in LOSSES:
            for role in ROLES:
                positive=[r for r in selected if r['unit_gold'] is not None and r['unit_gold'][3]==role];true_type[scope+'/'+loss+'/'+role]=dict(n=len(positive),exact=sum(r['pairwise_true_type'][loss]==r['unit_gold'] for r in positive))
    return dict(unit_metrics=metrics,per_role=per_role,macro=macro,oracle_endpoint_accuracy=conditional,true_endpoint_and_type_accuracy=true_type)


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('benchmarks/grammar_pairwise_units_iteration62_audit.py'),Path('tests/test_pairwise_units.py'),Path('src/voynich_smt/pairwise_units.py'),Path('src/voynich_smt/type_balanced_units.py'),Path('src/voynich_smt/typed_predicate_units.py'),Path('src/voynich_smt/multi_link_attachment.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',UNIT/'models.json',UNIT/'frame-predictions.json',UNIT/'evaluation.json',UNIT/'verification-manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},training='Same57 features/candidates and fit/cal/test sentence partitions. Primary pair_all: average logistic gold-minus-wrong-candidate loss within each frame, then average across frames; no type weights. Secondary pair_hard: strongest wrong opponents under original57 fit model, all tied opponents equally weighted, every fit frame included even when original correct. Mining uses fit frames only; no test/cal errors. Fixed L2=.01 and same optimizer. Original57 softmax control reused. No tuning of loss blend or regularization.',calibration='Original and both pairwise models receive identical micro-exact conditional unit calibration of cop/aux type offsets (-2,-1,-.5,0,.5,1,2), direct0; zero included; ties smaller absoluteoffset. Report zero and micro arms with no test-based choice. Gold endpoints used for calibration only and oracle diagnostics; inference POS/position only. True-type head ranking isolates localization.',scope='Same4070 source/five sentencepartitions/3365 gold units519 selected, same ambiguity handling and frozen56 endpoints. Report uncalibrated/zero, micro/macro policies, per-type precision/recall/F1, macroF1, and full pipeline. Reused development data, no reserve or prior target queries. POS/positions only in unit stage.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];original=load(UNIT/'models.json');reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models={}
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);training,_=prepare(part['fit'],data);base=original[str(f)]['model'];fitted={loss:fit(training,loss,base['weights']) for loss in LOSSES if loss!='unweighted'};del training;cal,_=prepare(part['calibration'],data);models[str(f)]={}
        for loss,model in [('unweighted',base)]+list(fitted.items()):
            frames=[dict(gold=r['gold'],options=r['options'],scores=r['x']@np.asarray(model['weights'])) for r in cal];policies={p:calibrate(frames,p) for p in ('micro',)};models[str(f)][loss]=dict(model=model,policies=policies)
        print('Fit/calibrated',f,{loss:{p:r['selected'] for p,r in record['policies'].items()} for loss,record in models[str(f)].items()},flush=True)
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));prior=load(UNIT/'frame-predictions.json');by_sid=defaultdict(list)
    for r in prior:by_sid[r['sid']].append(r)
    rows=[];baseline_replays=0;mutation_checks=0;type_invariance_checks=0
    for f in range(5):
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];masked=[dict(t,word='?',lemma='?',head=None,rel='?',features={}) for t in tokens]
            for old in by_sid.get(sid,[]):
                r=copy.deepcopy(old);r['pairwise_pipeline']={};r['pairwise_oracle_endpoint']={};r['pairwise_true_type']={};endpoint=r['arms']['carrierfit_carriercal']['f1'];gold=r['unit_gold']
                for field,v in (('pairwise_pipeline',endpoint),('pairwise_oracle_endpoint',gold[2] if gold else None)):
                    if v is None:
                        for arm in ARMS:r[field][arm]=None
                        continue
                    options=choices(tokens,r['subject'],v);x=matrix(tokens,r['subject'],v,options)
                    if r['selected_sentence'] and field=='pairwise_pipeline':assert np.array_equal(x,matrix(masked,r['subject'],v,choices(masked,r['subject'],v)));mutation_checks+=1
                    for loss,record in models[str(f)].items():
                        scores=x@np.asarray(record['model']['weights'])
                        for policy in POLICIES:
                            offsets=ZERO if policy=='zero' else record['policies'][policy]['selected']['offsets'];prediction=infer(scores,options,r['subject'],v,offsets);r[field][loss+'_'+policy]=prediction
                        if loss=='unweighted':assert r[field]['unweighted_zero']==old['unit_pipeline' if field=='pairwise_pipeline' else 'unit_oracle_endpoint']['learned'];baseline_replays+=1
                        if field=='pairwise_oracle_endpoint':
                            kept=[j for j,(_,role) in enumerate(options) if role==gold[3]];true_type=select(scores[kept],[options[j] for j in kept],r['subject'],v);r['pairwise_true_type'][loss]=true_type
                            for p in ('micro',):
                                offsets=record['policies'][p]['selected']['offsets'];revised=scores+np.asarray([offsets[role] for _,role in options]);assert select(revised[kept],[options[j] for j in kept],r['subject'],v)==true_type;type_invariance_checks+=1
                if gold is None:
                    for loss in LOSSES:r['pairwise_true_type'][loss]=None
                rows.append(r)
    save(OUT/'frame-predictions.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),pairwise_models=10,zero_unweighted_active_replays=baseline_replays,selected_pipeline_inference_mutation_checks=mutation_checks,true_type_offset_invariance_checks=type_invariance_checks,endpoints_unchanged=True,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result['unit_metrics'].items():
        if k.startswith(('selected_sentences/','all_source/')):print(k,r,'macro',result['macro'][k])
if __name__=='__main__':run()
