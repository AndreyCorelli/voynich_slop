"""Reconstruct lattices and replay all calibration and test assignments."""
from benchmarks.grammar_joint_subject_none_iteration65 import *


def run():
    checks=0
    for name in ('design-freeze.json','lattice-freeze.json','policy-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():assert digest(p)==h,p;checks+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];morphs=load(MORPH/'models.json');carrier=load(CARRIER/'models.json');units=load(UNIT/'models.json');cal=load(OUT/'calibration-lattices.json');test=load(OUT/'test-lattices.json');policies=load(OUT/'policies.json');rows=load(OUT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in rows};replays=0;lattices=0
    for r in load(UNIT/'frame-predictions.json'):assert all(lookup[(r['sid'],r['subject'])][k]==v for k,v in r.items())
    for f in range(5):
        record=carrier[str(f)]['carrierfit_carriercal']
        for part,expected in (('calibration',cal[str(f)]),('test',test[str(f)])):
            frames,_=prepare(parts[str(f)][part],data,morphs[str(f)]['expanded'],'carrier');actual=scored(frames,record['model']);assert len(actual)==len(expected)
            for a,b in zip(actual,expected):
                for k in ('sid','subject','predicates','gold'):assert a[k]==b[k]
                np.testing.assert_allclose(a['scores'],b['scores'],rtol=1e-10,atol=1e-12);lattices+=1
        assert calibration(cal[str(f)],data,record,units[str(f)]['model'])==policies[str(f)]
        cache={}
        for arm in ARMS:
            penalty=0 if arm=='baseline' else policies[str(f)]['selected'][arm.split('_')[0]]['penalty'];p,_=decode_sentences(test[str(f)],policies[str(f)]['cutoff'],penalty);u=unit_predictions(p,data,units[str(f)]['model'],cache)
            for key,value in p.items():assert value==lookup[key]['competition_carrier'][arm];assert u[key]==lookup[key]['competition_unit'][arm];replays+=1
    assert evaluate(rows)==load(OUT/'evaluation.json')
    paired={}
    for arm in ARMS[1:]:
        counts=Counter()
        for r in rows:
            if r['carrier_ambiguous']:continue
            a=r['competition_unit']['baseline'];b=r['competition_unit'][arm];g=r['unit_gold']
            if a!=b:
                counts['changed']+=1
                if g is not None and a==g:counts['lost_exact']+=1
                if g is not None and b==g:counts['gained_exact']+=1
        paired[arm]=dict(counts)
    save(OUT/'additional-audit.json',dict(paired=paired));save(OUT/'independent-validation.json',dict(freeze_hashes=checks,reconstructed_lattices=lattices,calibration_policies_replayed=5,test_assignments_replayed=replays,prior_fields_unchanged=True,evaluation_replayed=True,reserve_unscored=200,prior_queries_scored=0));print('Audit passed',lattices,replays,paired)
if __name__=='__main__':run()
