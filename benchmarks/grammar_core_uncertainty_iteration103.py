"""Candidate-budget-matched calibration, reusing iteration102 bootstrap evidence."""
from benchmarks.grammar_pair_uncertainty_iteration102 import *
from voynich_smt.core_pair_uncertainty import restrict
from voynich_smt.repair_abstention import calibrate as calibrate_baseline
OUT=ROOT/'iteration103';PREVIOUS=ROOT/'iteration102'


def build_calibration():
    data=load(ROOT/'iteration44/annotations-truth.json');anchors=load(ROOT/'iteration85/anchor-budgets.json')['195'];core=load(ROOT/'iteration100/core.json');bank=load(ROOT/'iteration98/calibration-bank.json');allowed={}
    for block,ids in load(ROOT/'iteration98/blocks.json')['scored'].items():
        public=ag.public_sentences([dict(sent_id=sid,**data[sid]) for sid in ids],anchors,'cal98-'+block);allowed[block]={t['id'] for s in public for t in s['tokens'] if t['anchor'] in core}
    cases=[]
    for c in load(PREVIOUS/'calibration-cases.json'):
        if c['case'].startswith('swap_') and not set(bank[c['case']])<=set(core):continue
        draws=np.load(PREVIOUS/c['block']/(c['case']+'.npz'))['draws'];cases.append(restrict(c,draws,allowed[c['block']]))
    assert len(cases)==162
    return cases


def run():
    assert not OUT.exists();OUT.mkdir();(OUT/'proposal-design.md').write_text(Path('docs/grammar_algorithm_proposals.md').read_text())
    paths=[Path(__file__),Path('src/voynich_smt/core_pair_uncertainty.py'),Path('src/voynich_smt/pair_uncertainty.py'),Path('src/voynich_smt/repair_abstention.py'),PREVIOUS/'verification-manifest.json',ROOT/'iteration100/core.json',ROOT/'iteration98/blocks.json',ROOT/'iteration98/calibration-bank.json',ROOT/'iteration85/anchor-budgets.json',ROOT/'iteration44/annotations-truth.json']
    save(OUT/'design-freeze.json',dict(inputs={str(p):digest(p) for p in paths},design='Frozen8core from99/100, not reselected; all15corecrossswaps+3controls x full829+8x100=162SOURCECALcases. All195suppliedcontextanchors retained. Restrict cached102paircolumns using original public-IDmap; RECOMPUTE originaltop/stability/lowerbounds againstONLYcorecompetitors, do notfilter onreferenceavailability. 256sentencebootstrap draws/counteligibility/classifier unchanged. Same102gain+stabilityPRIMARY/lowerboundSECONDARY thresholds,90percentprecisioneachfull/sparse,10full20sparsecalls,zeroclean/sameclasscalls,zerounavailablewrong; same tiechoice/OFF. Matched8coregain/gap baselines calibrated with98helper andSAMEguards; frozen95baseline. Freeze allpolicies before reading102evaluationcases. EvaluateALL162existing100corecases(9blocks), unchangedcore/errors/controls. No policy chosen fromtargetoutcomes; reusedsourceTESTdevelopmentnotfreshconfirmation. Coreselectedoncalibration99so calibratedresultsnotindependent. No PP integration inthiscalibrationexperiment; exactpairrepair evaluated,no newgrammar/nucleusclaim. No newannotations/reserve/sealedtest/authorqueries.'))
    cases=build_calibration();save(OUT/'calibration-cases.json',cases);policies={}
    for arm in ['stability','lower']:
        chosen,curve=calibrate102(cases,arm);policies[arm]=chosen['policy'];save(OUT/('curve-'+arm+'.json'),curve);print('CHOSEN',arm,chosen,flush=True)
    for arm,gap in [('gain',False),('gain_gap',True)]:
        chosen,curve=calibrate_baseline(cases,gap);policies[arm]=dict(arm='baseline',threshold=chosen['threshold'],gap=chosen['gap']);save(OUT/('curve-'+arm+'.json'),curve);print('BASELINE',arm,chosen,flush=True)
    policies['frozen95']=dict(arm='baseline',threshold=load(ROOT/'iteration95/policies.json')['joint_context']['threshold'],gap=0.)
    save(OUT/'policies.json',policies);save(OUT/'policy-freeze.json',dict(inputs={str(p):digest(p) for p in [OUT/'policies.json',OUT/'calibration-cases.json']+list(OUT.glob('curve-*.json'))}));save(OUT/'calibration-summary.json',{a:evaluate102(cases,p) for a,p in policies.items()})
    # The target already has exactly this core, so reuse its features unchanged.
    evaluation=load(PREVIOUS/'evaluation-cases.json');save(OUT/'evaluation-summary.json',{a:evaluate102(evaluation,p) for a,p in policies.items()});save(OUT/'evaluation-actions.json',{a:{c['block']+'/'+c['case']:__import__('voynich_smt.pair_uncertainty',fromlist=['selected']).selected(c['features'],p) for c in evaluation} for a,p in policies.items()})
    print('EVALUATION',json.dumps(load(OUT/'evaluation-summary.json')),flush=True)
if __name__=='__main__':run()
