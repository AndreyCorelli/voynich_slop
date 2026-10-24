"""Post-result matched global-threshold control; no competition policy changes."""
from benchmarks.grammar_joint_subject_none_iteration65 import *
from voynich_smt.joint_subject_none import independent
CONTROL=OUT/'threshold-control'
CONTROL_ARMS=('threshold_carrier','threshold_unit')


def count_metrics(tp,predicted,gold):
    return dict(tp=int(tp),fp=int(predicted-tp),fn=int(gold-tp),predicted=int(predicted),gold=int(gold),precision=float(tp/predicted) if predicted else None,recall=float(tp/gold) if gold else None,f1=float(2*tp/(predicted+gold)) if predicted+gold else 0.)


def exact_thresholds(points,gold_n,original_cutoff):
    points=sorted(points,key=lambda r:r['margin']);margins=np.asarray([r['margin'] for r in points]);arrays={key:np.asarray([r[key] for r in points],dtype=int) for key in ('carrier_correct','unit_correct','unit_emitted')};prefix={key:np.concatenate(([0],np.cumsum(a))) for key,a in arrays.items()};grid=[]
    for cutoff in sorted(set([-1000000.,1000000.,float(original_cutoff)]+margins.tolist())):
        start=int(np.searchsorted(margins,cutoff+1e-10,side='right'));n=len(points)-start;totals={k:int(a[-1]-a[start]) for k,a in prefix.items()}
        grid.append(dict(cutoff=cutoff,carrier=count_metrics(totals['carrier_correct'],n,gold_n),unit=count_metrics(totals['unit_correct'],totals['unit_emitted'],gold_n)))
    selected={task:max(grid,key=lambda r:(r[task]['f1'],-r[task]['predicted'],-r['carrier']['predicted'],-abs(r['cutoff']-original_cutoff))) for task in ('carrier','unit')}
    return dict(selected=selected,grid=grid)


def calibrate_control(frames,data,model,original_cutoff):
    predictions,_=decode_sentences(frames,-1000000.,0.);up=unit_predictions(predictions,data,model,{});points=[]
    for r in frames:
        key=(r['sid'],r['subject']);v=predictions[key]
        if v is None:continue
        g=gold_unit(data[r['sid']]['tokens'],r['subject']);u=up[key]
        points.append(dict(margin=max(r['scores']),carrier_correct=r['gold'] is not None and v==r['gold'],unit_correct=g is not None and u==g,unit_emitted=u is not None))
    result=exact_thresholds(points,sum(r['gold'] is not None for r in frames),original_cutoff)
    # Verify chosen aggregate sweep metrics using actual predicted edge/unit sets.
    gold={(r['sid'],r['subject'],r['gold']) for r in frames if r['gold'] is not None};ug={(r['sid'],*gold_unit(data[r['sid']]['tokens'],r['subject'])) for r in frames if r['gold'] is not None}
    for task,selected in result['selected'].items():
        p,_=decode_sentences(frames,selected['cutoff'],0.);u=unit_predictions(p,data,model,{})
        assert selected['carrier']==edge_metrics(gold,{(sid,s,v) for (sid,s),v in p.items() if v is not None})
        assert selected['unit']==edge_metrics(ug,{(sid,*value) for (sid,s),value in u.items() if value is not None})
    return result


def run():
    assert not CONTROL.exists();CONTROL.mkdir()
    paths=[Path(__file__),Path('tests/test_subject_threshold_control.py'),OUT/'design-freeze.json',OUT/'lattice-freeze.json',OUT/'policy-freeze.json',OUT/'prediction-freeze.json',OUT/'evaluation.json']
    save(CONTROL/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},timing='Post-65-result control, specified before its own calibration/test evaluation. No modification to original competition policies.',design='Globally calibrate NONE cutoff over all unique calibration best margins plus extremes and frozen originalcutoff. Same frozen scorelattices/head models and besttie abstention. Primary carrierF1 and secondary exactunitF1, ties fewer task predictions then fewer carriers then closestoriginalcutoff. Allcalibration operating subsets covered up to1e-10 acceptanceband; no tests used tochoose cutoff. Compare with65 joint policies, not choose winner ontest.'))
    data=load(SOURCE);cal=load(OUT/'calibration-lattices.json');test=load(OUT/'test-lattices.json');base=load(OUT/'policies.json');units=load(UNIT/'models.json');policies={}
    for f in range(5):policies[str(f)]=calibrate_control(cal[str(f)],data,units[str(f)]['model'],base[str(f)]['cutoff'])
    save(CONTROL/'policies.json',policies);save(CONTROL/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in CONTROL.glob('*.json')}));rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows}
    for f in range(5):
        cache={}
        for arm in CONTROL_ARMS:
            task=arm.split('_')[1];p,_=decode_sentences(test[str(f)],policies[str(f)]['selected'][task]['cutoff'],0.);u=unit_predictions(p,data,units[str(f)]['model'],cache)
            for key,value in p.items():lookup[key]['competition_carrier'][arm]=value;lookup[key]['competition_unit'][arm]=u[key]
    for r in rows:
        if r['carrier_ambiguous']:
            for arm in CONTROL_ARMS:r['competition_carrier'][arm]=None;r['competition_unit'][arm]=None
    save(CONTROL/'frame-predictions.json',rows);save(CONTROL/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in CONTROL.glob('*.json')}))
    # evaluate() reads module-global ARMS, so explicitly supply a local evaluator.
    result={};roles={}
    for scope in ('all_source','selected_sentences','Cicero_selected','Palladius_selected'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None}
        for arm in ARMS+CONTROL_ARMS:
            predicted={(r['sid'],*r['competition_unit'][arm]) for r in rs if r['competition_unit'][arm] is not None};result[scope+'/'+arm]=edge_metrics(gold,predicted)
            for role in ('direct','cop','aux'):roles[scope+'/'+arm+'/'+role]=edge_metrics({u for u in gold if u[-1]==role},{u for u in predicted if u[-1]==role})
    save(CONTROL/'evaluation.json',dict(unit_metrics=result,per_role=roles));print('Cutoffs',{f:{t:r['cutoff'] for t,r in record['selected'].items()} for f,record in policies.items()})
    for k,r in result.items():print(k,r)
if __name__=='__main__':run()
