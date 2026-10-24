"""Post-result ablation: carrier competition without alternative-edge rerouting."""
from benchmarks.grammar_joint_subject_none_iteration65_control import *
from voynich_smt.joint_subject_none import independent
ABLATION=OUT/'drop-only-control'
DROP_ARMS=('drop_carrier_cal','drop_unit_cal')


def restrict(frames):
    rows=[]
    for r in frames:
        p,_=independent([r],-1000000.);v=p[r['subject']];other=dict(r)
        other['predicates']=[v] if v is not None else [];other['scores']=[r['scores'][r['predicates'].index(v)]] if v is not None else [];rows.append(other)
    return rows


def run():
    assert not ABLATION.exists();ABLATION.mkdir();paths=[Path(__file__),OUT/'design-freeze.json',OUT/'lattice-freeze.json',OUT/'policy-freeze.json',OUT/'prediction-freeze.json',CONTROL/'design-freeze.json',CONTROL/'evaluation.json']
    save(ABLATION/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},timing='Post-result ablation; no changes to65 primary policies or threshold controls.',design='Restrict each subject to original unique best carrier orNONE. Same optional occupancy objective/penalty grid/cutoffs and carrier/unit calibration. Tests whether rerouting alternatives adds benefit beyond competition-gated abstention. Zero penalty must preserve original baseline. No annotations at inference.'))
    data=load(SOURCE);units=load(UNIT/'models.json');carrier=load(CARRIER/'models.json');cal=load(OUT/'calibration-lattices.json');test=load(OUT/'test-lattices.json');base=load(OUT/'policies.json');policies={}
    for f in range(5):policies[str(f)]=calibration(restrict(cal[str(f)]),data,carrier[str(f)]['carrierfit_carriercal'],units[str(f)]['model'])
    save(ABLATION/'policies.json',policies);save(ABLATION/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in ABLATION.glob('*.json')}));rows=load(CONTROL/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};replays=0
    for f in range(5):
        frames=restrict(test[str(f)]);baseline,_=decode_sentences(frames,base[str(f)]['cutoff'],0);cache={}
        for key,v in baseline.items():assert v==lookup[key]['competition_carrier']['baseline'];replays+=1
        for arm in DROP_ARMS:
            task=arm.split('_')[1];penalty=policies[str(f)]['selected'][task]['penalty'];p,_=decode_sentences(frames,base[str(f)]['cutoff'],penalty);u=unit_predictions(p,data,units[str(f)]['model'],cache)
            for key,v in p.items():lookup[key]['competition_carrier'][arm]=v;lookup[key]['competition_unit'][arm]=u[key]
    for r in rows:
        if r['carrier_ambiguous']:
            for arm in DROP_ARMS:r['competition_carrier'][arm]=None;r['competition_unit'][arm]=None
    save(ABLATION/'frame-predictions.json',rows);save(ABLATION/'prediction-freeze.json',dict(inputs={str(p):digest(p) for p in ABLATION.glob('*.json')}));result={}
    for scope in ('all_source','selected_sentences','Cicero_selected','Palladius_selected'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None}
        for arm in ARMS+CONTROL_ARMS+DROP_ARMS:
            p={(r['sid'],*r['competition_unit'][arm]) for r in rs if r['competition_unit'][arm] is not None};result[scope+'/'+arm]=edge_metrics(gold,p)
    save(ABLATION/'evaluation.json',dict(unit_metrics=result));save(ABLATION/'validation.json',dict(baseline_replays=replays,models_refitted=0,reserve_unscored=200,prior_queries_scored=0));print('Penalties',{f:{t:v['penalty'] for t,v in r['selected'].items()} for f,r in policies.items()})
    for k,r in result.items():print(k,r)
if __name__=='__main__':run()
