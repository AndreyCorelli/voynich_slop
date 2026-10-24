"""Replay restriction, calibration and blind evaluation against frozen caches."""
from benchmarks.grammar_core_uncertainty_iteration103 import *
from voynich_smt.pair_uncertainty import selected


def run():
    hashes=0
    for manifest in [OUT/'design-freeze.json',OUT/'policy-freeze.json',PREVIOUS/'verification-manifest.json']:
        for path,h in load(manifest)['inputs'].items():assert digest(Path(path))==h,path;hashes+=1
    cases=load(OUT/'calibration-cases.json');assert build_calibration()==cases
    prior={(c['block'],c['case']):c for c in load(PREVIOUS/'calibration-cases.json')};replayed=0
    for c in cases:
        original=prior[c['block'],c['case']];indices=c['source_pair_indices'];assert c['pairs']==[original['pairs'][j] for j in indices]
        draws=np.load(PREVIOUS/c['block']/(c['case']+'.npz'))['draws'][:,indices];assert summarize(c['pairs'],draws)==c['features'];assert c['reference']==original['reference'];replayed+=1
    policies=load(OUT/'policies.json')
    for arm in ['stability','lower']:
        chosen,curve=calibrate102(cases,arm);assert chosen['policy']==policies[arm];assert curve==load(OUT/('curve-'+arm+'.json'))
    for arm,gap in [('gain',False),('gain_gap',True)]:
        chosen,curve=calibrate_baseline(cases,gap);assert dict(arm='baseline',threshold=chosen['threshold'],gap=chosen['gap'])==policies[arm];assert curve==load(OUT/('curve-'+arm+'.json'))
    assert {a:evaluate102(cases,p) for a,p in policies.items()}==load(OUT/'calibration-summary.json')
    evaluation=load(PREVIOUS/'evaluation-cases.json');assert len(evaluation)==162
    assert {a:evaluate102(evaluation,p) for a,p in policies.items()}==load(OUT/'evaluation-summary.json')
    actions={a:{c['block']+'/'+c['case']:selected(c['features'],p) for c in evaluation} for a,p in policies.items()};assert actions==load(OUT/'evaluation-actions.json')
    # All original gains/choices survive restriction unchanged on the already-core evaluation.
    expected=load(PREVIOUS/'evaluation-summary.json')['frozen95'];assert expected==load(OUT/'evaluation-summary.json')['frozen95']
    save(OUT/'audit.json',dict(input_hashes_verified=hashes,calibration_restrictions_replayed=replayed,evaluation_cases_replayed=len(evaluation),all_four_calibrations_reproduced=True,original95_evaluation_unchanged=True,no_new_annotations_or_reserve=True))
    print(load(OUT/'audit.json'))
if __name__=='__main__':run()
