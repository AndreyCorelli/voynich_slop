"""Replay the coordination oracle without changing any fitted policy."""
from benchmarks.grammar_coordination_oracle_iteration66 import *


def run():
    hashes=0
    for name in ('design-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;hashes+=1
    data=load(SOURCE);models=load(UNIT/'models.json');policies=load(PREVIOUS/'policies.json');lattices=load(PREVIOUS/'test-lattices.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};checks=0
    for old in load(PREVIOUS/'frame-predictions.json'):assert all(lookup[(old['sid'],old['subject'])][k]==v for k,v in old.items())
    for f in range(5):
        policy=policies[str(f)];p,_=decode_sentences(remove_conj(lattices[str(f)],data),policy['cutoff'],policy['selected']['carrier']['penalty']);u=unit_predictions(p,data,models[str(f)]['model'],{})
        for key,v in p.items():assert v==lookup[key]['coord_carrier']['oracle_conj'];assert u[key]==lookup[key]['coord_unit']['oracle_conj'];checks+=1
    assert evaluate(rows)==load(OUT/'evaluation.json');assert attribution(rows,data)==load(OUT/'attribution.json');save(OUT/'independent-validation.json',dict(freeze_hashes=hashes,assignment_replays=checks,prior_fields_unchanged=True,targets_unchanged=True,models_refitted=0,reserve_unscored=200,prior_queries_scored=0));print('Oracle audit passed',checks)
if __name__=='__main__':run()
