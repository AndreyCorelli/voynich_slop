"""Replay the best-carrier-only competition ablation."""
from benchmarks.grammar_joint_subject_none_iteration65_ablation import *


def run():
    hashes=0
    for name in ('design-freeze.json','policy-freeze.json','prediction-freeze.json'):
        for p,h in load(ABLATION/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);units=load(UNIT/'models.json');carrier=load(CARRIER/'models.json');cal=load(OUT/'calibration-lattices.json');test=load(OUT/'test-lattices.json');base=load(OUT/'policies.json');policies=load(ABLATION/'policies.json');rows=load(ABLATION/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};checks=0
    for f in range(5):
        assert calibration(restrict(cal[str(f)]),data,carrier[str(f)]['carrierfit_carriercal'],units[str(f)]['model'])==policies[str(f)];cache={}
        for arm in DROP_ARMS:
            task=arm.split('_')[1];p,_=decode_sentences(restrict(test[str(f)]),base[str(f)]['cutoff'],policies[str(f)]['selected'][task]['penalty']);u=unit_predictions(p,data,units[str(f)]['model'],cache)
            for key,v in p.items():assert v==lookup[key]['competition_carrier'][arm];assert u[key]==lookup[key]['competition_unit'][arm];checks+=1
    for r in load(CONTROL/'frame-predictions.json'):
        saved=lookup[(r['sid'],r['subject'])]
        for k,value in r.items():
            if k in ('competition_unit','competition_carrier'):assert all(saved[k][a]==v for a,v in value.items())
            else:assert saved[k]==value
    result=load(ABLATION/'evaluation.json')['unit_metrics']
    for scope in ('all_source','selected_sentences','Cicero_selected','Palladius_selected'):
        rs=[r for r in rows if not r['carrier_ambiguous'] and (scope=='all_source' or r['selected_sentence'] and (scope=='selected_sentences' or r['author']==scope.split('_')[0]))];gold={(r['sid'],*r['unit_gold']) for r in rs if r['unit_gold'] is not None}
        for arm in ARMS+CONTROL_ARMS+DROP_ARMS:assert edge_metrics(gold,{(r['sid'],*r['competition_unit'][arm]) for r in rs if r['competition_unit'][arm] is not None})==result[scope+'/'+arm]
    save(ABLATION/'independent-validation.json',dict(freeze_hashes=hashes,calibration_policies_replayed=5,assignment_replays=checks,original_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0));print('Ablation audit passed',checks)
if __name__=='__main__':run()
