"""Source-only cutoff refinement for frozen93 contextual class detector."""
from benchmarks.grammar_fixed_anchor_detector_iteration93 import *
from voynich_smt.anchor_thresholds import exact_policy
OUT=ROOT/'iteration94';PREVIOUS=ROOT/'iteration93'

def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text());paths=[Path(__file__),Path('src/voynich_smt/anchor_thresholds.py'),Path('src/voynich_smt/anchor_class_audit.py'),PREVIOUS/'verification-manifest.json',PREVIOUS/'models.json',PREVIOUS/'patterns.json']+list(PREVIOUS.glob('calibration-*.json'))+list(PREVIOUS.glob('*/predictions.json'))
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Refinement motivatedONLYby93sourcecal gridgap, prior93coarsepolicyOFFpreserved. Same93models/features/masking/support/5arms/referenceclasses. Replacegrid withALLattainable nonnegative source-calibration scorecutoffs plus0andOFF. Samecal correct+knownin/et ONLY, sameguard cleanFP<=1 andflaggedtokens<=5%, sameties. Freezeallpoliciesbeforeapplying ANYevaluationscores. Reuse alreadycached93sourcetest/authors all8patterns, developmentnotfreshconfirmation. Explicitcorrectfalsealarms anddirection-specificdetections. No modelsrefit/thresholdselectionfromevaluation, no PPintegration/correction/newannotations/reserve/sealedtest.'))
    clean=load(PREVIOUS/'calibration-correct.json')['records'];corrupted=load(PREVIOUS/'calibration-rehearsed_in_et.json')['records'];policies={}
    for arm in DETECTOR_ARMS:
        chosen,curve=exact_policy(clean[arm],corrupted[arm]);policies[arm]=chosen;save(OUT/('calibration-curve-'+arm+'.json'),curve);print('policy',arm,chosen,flush=True)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json']+list(OUT.glob('calibration-curve-*.json'))}));summary={};details={}
    for name in ('source','Jerome','Caesar'):
        for pattern in load(PREVIOUS/'patterns.json'):
            pred=load(PREVIOUS/(name.lower()+'-'+pattern)/'predictions.json');result={};detail={}
            for arm,rows in pred['records'].items():
                threshold=float('inf') if policies[arm]['threshold'] is None else policies[arm]['threshold'];result[arm]=metrics(rows,threshold);detail[arm]=dict(true_flags=[pred['identities'][r['anchor_id']] for r in rows if flagged(r,threshold) and r['class_wrong']],false_flags=[pred['identities'][r['anchor_id']] for r in rows if flagged(r,threshold) and not r['class_wrong']],missed=[pred['identities'][r['anchor_id']] for r in rows if not flagged(r,threshold) and r['class_wrong']])
            summary[name+'/'+pattern]=result;details[name+'/'+pattern]=detail
    save(OUT/'evaluation.json',summary);save(OUT/'flag-details.json',details)
if __name__=='__main__':run()
