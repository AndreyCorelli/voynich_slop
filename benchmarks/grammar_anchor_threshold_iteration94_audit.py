"""Replay exact source-only cutoffs and every cached evaluation decision."""
from benchmarks.grammar_anchor_threshold_iteration94 import *

def run():
    for freeze in ('design-freeze.json','policy-freeze.json'):
        for p,h in load(OUT/freeze)['inputs'].items():assert digest(p)==h,p
    clean=load(PREVIOUS/'calibration-correct.json')['records'];corrupt=load(PREVIOUS/'calibration-rehearsed_in_et.json')['records'];policies=load(OUT/'policies.json');summary={};details={}
    for arm in DETECTOR_ARMS:
        chosen,curve=exact_policy(clean[arm],corrupt[arm]);assert chosen==policies[arm];assert curve==load(OUT/('calibration-curve-'+arm+'.json'));assert chosen['clean']['fp']<=1;assert chosen['clean']['flagged_tokens']<=.05*sum(r['n'] for r in clean[arm])
    for name in ('source','Jerome','Caesar'):
        for pattern in load(PREVIOUS/'patterns.json'):
            pred=load(PREVIOUS/(name.lower()+'-'+pattern)/'predictions.json');result={};detail={}
            for arm,rows in pred['records'].items():
                threshold=float('inf') if policies[arm]['threshold'] is None else policies[arm]['threshold'];result[arm]=metrics(rows,threshold);detail[arm]=dict(true_flags=[pred['identities'][r['anchor_id']] for r in rows if flagged(r,threshold) and r['class_wrong']],false_flags=[pred['identities'][r['anchor_id']] for r in rows if flagged(r,threshold) and not r['class_wrong']],missed=[pred['identities'][r['anchor_id']] for r in rows if not flagged(r,threshold) and r['class_wrong']])
            summary[name+'/'+pattern]=result;details[name+'/'+pattern]=detail
    assert summary==load(OUT/'evaluation.json') and details==load(OUT/'flag-details.json');checked=0
    for path in ROOT.glob('iteration*/verification-manifest.json'):
        if path.parent==OUT:continue
        for p,h in load(path).get('inputs',{}).items():assert digest(p)==h,(path,p);checked+=1
    save(OUT/'audit.json',dict(all5policies_and24scenarios_replayed=True,source_only_cutoffs=True,unchanged_models_and_false_alarm_guards=True,prior_input_hashes_verified=checked,reserve_unscored=True));print('audit passed',checked,'prior hashes')
if __name__=='__main__':run()
