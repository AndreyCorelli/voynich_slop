"""Typed head/carrier recovery with frozen endpoint predictions and explicit conditioning."""
from pathlib import Path
from collections import Counter
import copy
from benchmarks.grammar_predicate_carriers_iteration56 import OUT as PREVIOUS,MORPH,SOURCE,EXAMPLES,RESERVE,load,save,digest
from voynich_smt.typed_predicate_units import gold_unit,choices,matrix,fit,calibrate_distance,infer
from voynich_smt.multi_link_attachment import edge_metrics
OUT=PREVIOUS.parent/'iteration57'
ARMS=('prior_distance','learned')


def prepare(ids,data):
    rows=[];audit=Counter()
    for sid in ids:
        tokens=data[sid]['tokens']
        for s,t in enumerate(tokens):
            gold=gold_unit(tokens,s)
            if gold is None:continue
            options=choices(tokens,s,gold[2]);audit['gold_units']+=1;audit['gold_in_domain']+=tuple(gold[1::2]) in options
            rows.append(dict(sid=sid,gold=gold,options=options,x=matrix(tokens,s,gold[2],options),carrier_pos=tokens[gold[2]]['pos'],head_pos=tokens[gold[1]]['pos']))
    return rows,dict(audit)


def evaluate(rows):
    result={};conditional={};decomposition={}
    for scope in ('selected_sentences','all_source','Cicero_selected','Palladius_selected'):
        chosen=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))]
        gold={(r['sid'],*r['unit_gold']) for r in chosen if r['unit_gold'] is not None}
        for arm in ARMS:
            predicted={(r['sid'],*r['unit_pipeline'][arm]) for r in chosen if r['unit_pipeline'][arm] is not None};result[scope+'/'+arm]=edge_metrics(gold,predicted)
            for kind in ('all','direct','cop','aux'):
                positive=[r for r in chosen if r['unit_gold'] is not None and (kind=='all' or r['unit_gold'][3]==kind)];conditional[scope+'/'+arm+'/'+kind]=dict(n=len(positive),exact=sum(r['unit_oracle_endpoint'][arm]==r['unit_gold'] for r in positive),head_correct=sum(r['unit_oracle_endpoint'][arm] is not None and r['unit_oracle_endpoint'][arm][1]==r['unit_gold'][1] for r in positive),type_correct=sum(r['unit_oracle_endpoint'][arm] is not None and r['unit_oracle_endpoint'][arm][3]==r['unit_gold'][3] for r in positive),abstained=sum(r['unit_oracle_endpoint'][arm] is None for r in positive))
            positive=[r for r in chosen if r['unit_gold'] is not None];counts=Counter()
            for r in positive:
                endpoint=r['arms']['carrierfit_carriercal']['f1'];unit=r['unit_pipeline'][arm]
                if endpoint is None:reason='endpoint_abstained'
                elif endpoint!=r['carrier_gold']:reason='endpoint_wrong'
                elif unit==r['unit_gold']:reason='exact_unit'
                elif unit is None:reason='unit_tie'
                else:reason='head_or_type_wrong'
                counts[reason]+=1
            decomposition[scope+'/'+arm]=dict(counts)
    return dict(unit_metrics=result,oracle_endpoint_accuracy=conditional,pipeline_gold_loss=decomposition)


def run():
    assert not OUT.exists()
    previous=load(PREVIOUS/'verification-manifest.json')
    for p,h in previous['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/typed_predicate_units.py'),Path('src/voynich_smt/predicate_carriers.py'),Path('src/voynich_smt/multi_link_attachment.py'),SOURCE,EXAMPLES,RESERVE,MORPH/'manifest.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'evaluation.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},task='Same unique-carrier task56, ambiguity excluded only from expanded unit evaluation. Gold units (subject,governor,carrier,cop/aux) or (subject,carrier,carrier,direct). No new gold projection or coordination. Train head/type stage on fit gold endpoint units; oracle-endpoint testing is labeled diagnostic. Actual pipeline uses frozen56 carrierfit_carriercal F1 endpoints, including false endpoints.',inference='For any supplied subject/carrier positions, enumerate (carrier,direct) plus every other token except subject/carrier as cop or aux head. POS/positions only; no word/lemma, dependency, gold morphology or true type/head inputs. Unique score maxima only, ties abstain. All endpoint fields preserved.',estimators='Learned: conditional linear scorer, role-specific POS/distance/direction/boundary/neighbor features, L2=.01, same L-BFGS convergence criteria52. Prior-distance baseline: fit carrier-POS type prior and role-conditioned head-POS prior with addhalf smoothing; subtract weight*log(1+distance(head,carrier)). Weight0,.5,1,2,4 chosen by unique exact calibration unit recovery. Neither conditions on true role. No extra learned-stage confidence gate or endpoint reranking.',scope='Same4070 source and five outer partitions; primary304 selected sentences519 expanded units, all-source3365. Gold labels used only fitting/calibration/evaluation, never inference. Reused development data, readable Latin/oracle POS upstream. No reserve or prior target queries.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models={};domain_audit={}
    for f in range(5):
        part=parts[str(f)];a,b,c=(set(part[k]) for k in ('fit','calibration','test'));assert not (a&b or a&c or b&c);training,audit=prepare(part['fit'],data);model=fit(training);del training;calibration,cal_audit=prepare(part['calibration'],data);distance=calibrate_distance(calibration,{sid:data[sid]['tokens'] for sid in part['calibration']},model);models[str(f)]=dict(model=model,distance=distance);domain_audit[str(f)]=dict(fit=audit,calibration=cal_audit);print('Fit/calibrated',f,'distance',distance['selected'],flush=True)
    save(OUT/'models.json',models);save(OUT/'domain-audit.json',domain_audit);save(OUT/'model-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}))
    prior=load(PREVIOUS/'frame-predictions.json');by_sentence={}
    for r in prior:by_sentence.setdefault(r['sid'],[]).append(r)
    rows=[];mutation_checks=0;domain_checks=0
    for f in range(5):
        model=models[str(f)]['model'];weight=models[str(f)]['distance']['selected']['weight']
        for sid in parts[str(f)]['test']:
            tokens=data[sid]['tokens'];masked=[dict(t,word='?',lemma='?',head=None,rel='?',features={}) for t in tokens]
            for old in by_sentence.get(sid,[]):
                r=copy.deepcopy(old);s=r['subject'];gold=gold_unit(tokens,s);assert (gold[2] if gold is not None else None)==r['carrier_gold'];r['unit_gold']=gold;r['unit_pipeline']={};r['unit_oracle_endpoint']={};endpoint=r['arms']['carrierfit_carriercal']['f1']
                for arm,w in (('prior_distance',weight),('learned',None)):
                    r['unit_pipeline'][arm]=infer(tokens,s,endpoint,model,w) if endpoint is not None else None
                    r['unit_oracle_endpoint'][arm]=infer(tokens,s,gold[2],model,w) if gold is not None else None
                    if r['selected_sentence'] and endpoint is not None:
                        assert infer(masked,s,endpoint,model,w)==r['unit_pipeline'][arm];mutation_checks+=1
                if gold is not None:assert tuple(gold[1::2]) in choices(tokens,s,gold[2]);domain_checks+=1
                rows.append(r)
    save(OUT/'frame-predictions.json',rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(previous_hashes=len(previous['inputs']),head_models=5,gold_unit_domain_checks=domain_checks,selected_pipeline_inference_mutation_checks=mutation_checks,endpoint_predictions_unchanged=True,partitions_disjoint=True,reserve_unscored=200,prior_queries_scored=0))
    for k,r in result['unit_metrics'].items():print(k,r)
    print('Conditional selected',{k:v for k,v in result['oracle_endpoint_accuracy'].items() if k.startswith('selected_sentences/')})
if __name__=='__main__':run()
