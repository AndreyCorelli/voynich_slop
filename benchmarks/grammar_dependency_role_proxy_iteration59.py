"""Learn token-role proxies and calibrate soft additions to frozen unit scores."""
from pathlib import Path
from collections import Counter
import copy,math
import numpy as np
from benchmarks.grammar_typed_predicate_units_iteration57 import OUT as UNIT,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest
from benchmarks.grammar_copular_head_oracle_iteration58 import OUT as PREVIOUS
from voynich_smt.typed_predicate_units import choices,matrix,select
from voynich_smt.dependency_role_proxy import MODES,ARMS,CLASSES,label,fit,probabilities,pos_prior,evidence,infer,calibrate
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration59'
ALL_ARMS=tuple(mode+'_'+arm for mode in MODES for arm in ARMS)


def calibration_frames(ids,data,prior_by_sid,unit_model,proxy):
    frames=[]
    for sid in ids:
        tokens=data[sid]['tokens'];p=probabilities(tokens,proxy)
        for r in prior_by_sid.get(sid,[]):
            gold=r['unit_gold']
            if gold is None:continue
            options=choices(tokens,gold[0],gold[2]);scores=matrix(tokens,gold[0],gold[2],options)@np.asarray(unit_model['weights']);head,typ=evidence(tokens,gold[2],options,p,proxy);frames.append(dict(gold=gold,options=options,scores=scores,head=head,type=typ))
    return frames


def evaluate(rows):
    result={};conditional={};by_kind={}
    arms=('baseline',)+ALL_ARMS
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        selected=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in selected if r['unit_gold'] is not None}
        for arm in arms:
            predictions={(r['sid'],*r['role_pipeline'][arm]) for r in selected if r['role_pipeline'][arm] is not None};result[scope+'/'+arm]=edge_metrics(gold,predictions)
            for kind in ('all','direct','cop','aux'):
                positive=[r for r in selected if r['unit_gold'] is not None and (kind=='all' or r['unit_gold'][3]==kind)];conditional[scope+'/'+arm+'/'+kind]=dict(n=len(positive),exact=sum(r['role_oracle_endpoint'][arm]==r['unit_gold'] for r in positive));by_kind[scope+'/'+arm+'/'+kind]=dict(n=len(positive),exact=sum(r['role_pipeline'][arm]==r['unit_gold'] for r in positive))
    return dict(unit_metrics=result,oracle_endpoint_accuracy=conditional,pipeline_by_gold_kind=by_kind)


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/dependency_role_proxy.py'),Path('src/voynich_smt/typed_predicate_units.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',UNIT/'models.json',UNIT/'frame-predictions.json',UNIT/'evaluation.json',UNIT/'verification-manifest.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},proxy='Four token labels dependent(amod/det/nmod/appos/flat/fixed/compound/case),cop,aux,other. Fit all source fit tokens only. Multinomial logistic, L2=.001, min featurecount3, fixed optimizer. pos: ±2POS and immediate POS pairs/flanks. lexical: also token and ±1 word identities plus2/3/4 target suffixes withPOS. Words normalized as source; no lemma/morphology/dependency features.',addition='Freeze57 learned unit scores and56 endpoint outputs. Head evidence log(nonDependent posterior/POS prior); type evidence log(carrier role posterior/POS prior) mapping direct toother. Clip probabilities1e-6. No hard mask or candidate changes, no head refitting/in-sample proxy features in a metamodel.',calibration='Per mode head-only/type-only/joint nonnegative weights0,.5,1,2,4; maximize exact unique calibration unit recovery at gold endpoints. Ties prefer lower totalweight then lower type/head weights; zero baseline included. Same true-endpoint conditioning as57 distance calibration. Actual pipeline uses frozen endpoints including mistakes.',scope='Same4070 source/five outer folds,3365 units/519 selected. Report oracle-endpoint vsactualpipeline, allroles/authors. Test labels only evaluate; no reserve/prior target query scoring. Extra lexical head-stage access explicit; POS-only proxy controls it.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];unit_models=load(UNIT/'models.json');prior=load(UNIT/'frame-predictions.json');by_sid={}
    for r in prior:by_sid.setdefault(r['sid'],[]).append(r)
    reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models={}
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);models[str(f)]={}
        for mode in MODES:
            proxy=fit((data[sid]['tokens'] for sid in part['fit']),mode);frames=calibration_frames(part['calibration'],data,by_sid,unit_models[str(f)]['model'],proxy);policies={arm:calibrate(frames,arm) for arm in ARMS};models[str(f)][mode]=dict(proxy=proxy,policies=policies)
            print('Fit/calibrated',f,mode,{a:r['selected'] for a,r in policies.items()},flush=True)
    save(OUT/'models.json',models);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));rows=[];token_metrics={mode:dict(n=0,correct=0,nll=0.,pos_prior_nll=0.,confusion=[[0]*4 for _ in range(4)]) for mode in MODES};mutation_checks=0;zero_replays=0
    for f in range(5):
        unit_model=unit_models[str(f)]['model']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];ps={mode:probabilities(tokens,models[str(f)][mode]['proxy']) for mode in MODES}
            for mode,p in ps.items():
                record=token_metrics[mode];proxy=models[str(f)][mode]['proxy']
                for i,t in enumerate(tokens):
                    y=CLASSES.index(label(t));predicted=int(np.argmax(p[i]));record['n']+=1;record['correct']+=predicted==y;record['nll']-=math.log(max(1e-12,float(p[i,y])));record['pos_prior_nll']-=math.log(float(pos_prior(proxy,t['pos'])[y]));record['confusion'][y][predicted]+=1
            selected=any(r['selected_sentence'] for r in by_sid.get(sid,[]))
            if selected:
                masked=[dict(t,head=None,rel='?',features={},lemma='?') for t in tokens]
                for mode in MODES:assert np.array_equal(probabilities(masked,models[str(f)][mode]['proxy']),ps[mode]);mutation_checks+=1
            for old in by_sid.get(sid,[]):
                r=copy.deepcopy(old);r['role_pipeline']={'baseline':old['unit_pipeline']['learned']};r['role_oracle_endpoint']={'baseline':old['unit_oracle_endpoint']['learned']};endpoint=r['arms']['carrierfit_carriercal']['f1'];gold=r['unit_gold']
                for field,v in (('role_pipeline',endpoint),('role_oracle_endpoint',gold[2] if gold is not None else None)):
                    if v is None:
                        for arm in ALL_ARMS:r[field][arm]=None
                        continue
                    options=choices(tokens,r['subject'],v);scores=matrix(tokens,r['subject'],v,options)@np.asarray(unit_model['weights'])
                    assert select(scores,options,r['subject'],v)==r[field]['baseline']
                    for mode in MODES:
                        record=models[str(f)][mode];head,typ=evidence(tokens,v,options,ps[mode],record['proxy']);assert infer(scores,options,r['subject'],v,head,typ,0,0)==r[field]['baseline'];zero_replays+=1
                        for arm in ARMS:
                            selected=record['policies'][arm]['selected'];r[field][mode+'_'+arm]=infer(scores,options,r['subject'],v,head,typ,selected['head_weight'],selected['type_weight'])
                rows.append(r)
    for r in token_metrics.values():r.update(accuracy=r['correct']/r['n'],mean_nll=r['nll']/r['n'],mean_pos_prior_nll=r['pos_prior_nll']/r['n'])
    save(OUT/'frame-predictions.json',rows);save(OUT/'token-metrics.json',token_metrics);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),role_models=10,selected_sentence_proxy_mutation_checks=mutation_checks,zero_weight_replays=zero_replays,head_models_and_endpoints_unchanged=True,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result['unit_metrics'].items():print(k,r)
if __name__=='__main__':run()
