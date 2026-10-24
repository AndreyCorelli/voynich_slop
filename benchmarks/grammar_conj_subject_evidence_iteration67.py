"""Learn soft nominal conjunct eligibility to preserve subject phrase heads."""
from pathlib import Path
from collections import defaultdict,Counter
import copy
import numpy as np
from benchmarks.grammar_coordination_oracle_iteration66 import OUT as PREVIOUS
from benchmarks.grammar_joint_subject_none_iteration65 import OUT as BASE,UNIT,MORPH,SOURCE,RESERVE,load,save,digest,decode_sentences,unit_predictions
from voynich_smt.conj_subject_evidence import MODES,WEIGHTS,fit,probabilities,adjust
from voynich_smt.typed_predicate_units import gold_unit
from voynich_smt.multi_link_attachment import edge_metrics
OUT=BASE.parent/'iteration67'
ARMS=('baseline','competition65','oracle_conj')+MODES


def adjusted(frames,data,model,weight):
    grouped=defaultdict(list);result=[]
    for r in frames:grouped[r['sid']].append(r)
    for sid,rs in grouped.items():result.extend(adjust(rs,data[sid]['tokens'],model,weight))
    return result


def calibrate(frames,data,record,unit_model,model):
    gold={(r['sid'],r['subject'],r['gold']) for r in frames if r['gold'] is not None};units={(r['sid'],*gold_unit(data[r['sid']]['tokens'],r['subject'])) for r in frames if r['gold'] is not None};cache={};grid=[];penalty=record['selected']['carrier']['penalty']
    for weight in WEIGHTS:
        p,stats=decode_sentences(adjusted(frames,data,model,weight),record['cutoff'],penalty);u=unit_predictions(p,data,unit_model,cache)
        grid.append(dict(weight=weight,carrier=edge_metrics(gold,{(sid,s,v) for (sid,s),v in p.items() if v is not None}),unit=edge_metrics(units,{(sid,*value) for (sid,s),value in u.items() if value is not None}),solver=stats))
    selected=max(grid,key=lambda r:(r['carrier']['f1'],-r['carrier']['predicted'],-r['weight']))
    return dict(selected=selected,grid=grid,cutoff=record['cutoff'],competition_penalty=penalty)


def unit(r,arm):return r['coord_unit'][arm] if arm not in MODES else r['conj_unit'][arm]


def evaluate(rows):
    metrics={};roles={};cohort={}
    for scope in ('all_source','selected_sentences','Cicero_all','Palladius_all','Cicero_selected','Palladius_selected'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or scope=='selected_sentences' and r['selected_sentence'] or scope.endswith('_all') and r['author']==scope[:-4] or scope.endswith('_selected') and scope!='selected_sentences' and r['selected_sentence'] and r['author']==scope[:-9])];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None}
        for arm in ARMS:
            pred={(r['sid'],*unit(r,arm)) for r in rs if unit(r,arm) is not None};metrics[scope+'/'+arm]=edge_metrics(gold,pred)
            for role in ('direct','cop','aux'):roles[scope+'/'+arm+'/'+role]=edge_metrics({u for u in gold if u[-1]==role},{u for u in pred if u[-1]==role})
            positives=[r for r in rs if r['coordination_subject'] and r['unit_gold'] is not None];cohort[scope+'/'+arm]=dict(n=len(positives),exact=sum(unit(r,arm)==r['unit_gold'] for r in positives))
    return dict(unit_metrics=metrics,per_role=roles,coordination=cohort)


def run():
    assert not OUT.exists()
    for p,h in load(PREVIOUS/'verification-manifest.json')['inputs'].items():assert digest(p)==h,p
    OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('benchmarks/grammar_conj_subject_evidence_iteration67_audit.py'),Path('src/voynich_smt/conj_subject_evidence.py'),Path('src/voynich_smt/dependency_role_proxy.py'),Path('src/voynich_smt/joint_subject_none.py'),Path('tests/test_conj_subject_evidence.py'),SOURCE,RESERVE,MORPH/'manifest.json',BASE/'calibration-lattices.json',BASE/'test-lattices.json',BASE/'policies.json',UNIT/'models.json',PREVIOUS/'frame-predictions.json',PREVIOUS/'verification-manifest.json',OUT/'proposal-design.md']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},scope='Same4070source/fivepartitions/3365units519selected; keep65primary penalty/cutoff, frozen56edge57unit scores and alltargets. No reserve or prior queries. Primarycontext, POS-only control.',probe='Binary nominal token relbaseconj on outerfit source tokens only, no carrier/goldsubject inputs. Sparse logistic meanBCE L2=.001/minfeaturecount3. pos: bias andnominalPOS. context adds59POS±2/pairs, nearest left/rightCCONJ distancebucket, nearestnominalPOS/markerbetween andinteractions. No words/lemma/parse/morph input.',addition='Subtract soft logprobnonconj * nonnegative weight from everycarrier edge of a nominal; same evidence across alternatives. No hard mask or newtargets, no conjunctprojection. Adjusted subjects stillchoose carrier/alternative/NONE under65softcompetition. Goldconj oracle66 onlyreference.',calibration='Fixed65primary cutoff andcompetitionpenalty. Weightgrid0,.5,1,2,4,8; maximizecarrierF1, tie fewerpredictions then smallerweight. No testchoice/retuninglambda. Weight0 mustreplay65primary. Primary success: coordinationrecovery>39/122, no loss of65 overallunitF1/correctunit count and no selectedF1regression; report allauthors/types and controls.'))
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];cal=load(BASE/'calibration-lattices.json');test=load(BASE/'test-lattices.json');base=load(BASE/'policies.json');units=load(UNIT/'models.json');reserve={r['sent_id'] for rs in load(RESERVE)['authors'].values() for r in rs};assert not set(data)&reserve;models={}
    for f in range(5):
        p=parts[str(f)];a,b,c=(set(p[k]) for k in ('fit','calibration','test'));assert not(a&b or a&c or b&c);models[str(f)]={}
        for mode in MODES:
            model=fit((data[sid]['tokens'] for sid in p['fit']),mode);policy=calibrate(cal[str(f)],data,base[str(f)],units[str(f)]['model'],model);models[str(f)][mode]=dict(model=model,policy=policy);print('Fit/calibrated',f,mode,policy['selected'],flush=True)
    save(OUT/'models.json',models);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));rows=load(PREVIOUS/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};probe_rows=[];mutations=replays=0
    for r in rows:r['conj_unit']={m:None for m in MODES};r['conj_carrier']={m:None for m in MODES}
    for f in range(5):
        for mode in MODES:
            record=models[str(f)][mode];weight=record['policy']['selected']['weight'];frames=adjusted(test[str(f)],data,record['model'],weight);p,_=decode_sentences(frames,base[str(f)]['cutoff'],base[str(f)]['selected']['carrier']['penalty']);u=unit_predictions(p,data,units[str(f)]['model'],{})
            zero,_=decode_sentences(test[str(f)],base[str(f)]['cutoff'],base[str(f)]['selected']['carrier']['penalty'])
            for key,v in p.items():lookup[key]['conj_carrier'][mode]=v;lookup[key]['conj_unit'][mode]=u[key];assert zero[key]==lookup[key]['coord_carrier']['competition65'];replays+=1
        grouped=defaultdict(list)
        for r in test[str(f)]:grouped[r['sid']].append(r)
        for sid,rs in grouped.items():
            tokens=data[sid]['tokens'];subjects=[r['subject'] for r in rs];ps={m:probabilities(tokens,subjects,models[str(f)][m]['model']) for m in MODES}
            if any(lookup[(sid,s)]['selected_sentence'] for s in subjects):
                masked=[dict(t,word='?',lemma='?',head=None,rel='?',features={}) for t in tokens]
                for m in MODES:np.testing.assert_allclose(probabilities(masked,subjects,models[str(f)][m]['model']),ps[m],rtol=0,atol=0);mutations+=1
            for j,s in enumerate(subjects):probe_rows.append(dict(sid=sid,subject=s,label=tokens[s]['rel'].split(':')[0]=='conj',probabilities={m:float(ps[m][j]) for m in MODES}))
    save(OUT/'frame-predictions.json',rows);save(OUT/'probe-predictions.json',probe_rows);save(OUT/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in OUT.glob('*.json')}));result=evaluate(rows);save(OUT/'evaluation.json',result);save(OUT/'validation.json',dict(fitted_models=10,zero_weight_replays=replays,selected_probe_mutation_checks=mutations,targets_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    for k,v in result['unit_metrics'].items():
        if k.startswith(('all_source/','selected_sentences/')):print(k,v,flush=True)
    print('Coordination',result['coordination'],flush=True)
if __name__=='__main__':run()
