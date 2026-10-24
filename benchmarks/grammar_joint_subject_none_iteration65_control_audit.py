"""Replay post-result exact global-threshold control independently of run()."""
from benchmarks.grammar_joint_subject_none_iteration65_control import *


def run():
    hashes=0
    for name in ('design-freeze.json','policy-freeze.json','prediction-freeze.json'):
        for p,h in load(CONTROL/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);units=load(UNIT/'models.json');cal=load(OUT/'calibration-lattices.json');test=load(OUT/'test-lattices.json');base=load(OUT/'policies.json');policies=load(CONTROL/'policies.json');rows=load(CONTROL/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};checks=0
    for r in load(OUT/'frame-predictions.json'):
        saved=lookup[(r['sid'],r['subject'])]
        for k,value in r.items():
            if k in ('competition_unit','competition_carrier'):assert all(saved[k][a]==v for a,v in value.items())
            else:assert saved[k]==value
    for f in range(5):
        assert calibrate_control(cal[str(f)],data,units[str(f)]['model'],base[str(f)]['cutoff'])==policies[str(f)]
        cache={}
        for arm in CONTROL_ARMS:
            task=arm.split('_')[1];p,_=decode_sentences(test[str(f)],policies[str(f)]['selected'][task]['cutoff'],0.);u=unit_predictions(p,data,units[str(f)]['model'],cache)
            for key,v in p.items():assert v==lookup[key]['competition_carrier'][arm];assert u[key]==lookup[key]['competition_unit'][arm];checks+=1
    result=load(CONTROL/'evaluation.json')
    for scope in ('all_source','selected_sentences','Cicero_selected','Palladius_selected'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None}
        for arm in ARMS+CONTROL_ARMS:
            pred={(r['sid'],*r['competition_unit'][arm]) for r in rs if r['competition_unit'][arm] is not None};assert result['unit_metrics'][scope+'/'+arm]==edge_metrics(gold,pred)
    save(CONTROL/'independent-validation.json',dict(freeze_hashes=hashes,calibration_policies_replayed=5,assignment_replays=checks,original_competition_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0));print('Control audit passed',checks)
if __name__=='__main__':run()
