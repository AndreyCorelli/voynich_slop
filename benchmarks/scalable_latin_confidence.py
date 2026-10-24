"""Fit confidence on one independent work, confirm on another, then apply frozen to Caesar."""
import json
from pathlib import Path

from benchmarks.scalable_latin_classes import ROOT, RESOURCES, ORIGINAL
from benchmarks.scalable_latin_caesar import write,measure
from benchmarks.scalable_english_run import run
from voynich_smt.word_mapping.scalable.search import SearchConfig
from voynich_smt.word_mapping.scalable.inventory import Inventory
from voynich_smt.word_mapping.scalable.confidence import extract,truth_labels,fit,predict,evaluate
from voynich_smt.data.corpus import digest


def labels_for(public,fixture):
    truth=json.loads((fixture/'evaluation-only/truth.json').read_text())
    inventory=Inventory(RESOURCES/'inventory.sqlite')
    try:return truth_labels(public,truth,inventory)
    finally:inventory.close()


def main():
    gate=json.loads((ROOT/'gates.json').read_text())
    # Current formulation is rejected if gates fail; no forced class search.
    if gate['class_pass']:
        raise ValueError('Gate passed: run and assess coarse class stage before confidence comparison')
    write(ROOT/'class-decision.json',{'class_gate_pass':False,'word_gate_pass':gate['word_pass'],
          'action':'Stop learned-class inference; preserve model/gates; calibrate the unchanged baseline separately.'})
    result={}
    frozen=None;calibrator_digest=None
    for role in ('calibration','confirmation'):
        fixture=ROOT/role;output=ROOT/f'{role}-baseline'
        # A real public-only run: truth is unavailable at its usual path.
        private=fixture/'evaluation-only';unavailable=fixture/'private-unavailable-during-search'
        private.rename(unavailable)
        try:
            run(RESOURCES,fixture/'public/cipher.json',output,seeds=(3,5,7),
                config=SearchConfig(initialization='frequency',proposals=4000,budget_seconds=600,reserve_seconds=10),trace=True)
        finally:unavailable.rename(private)
        measured=measure(RESOURCES,fixture,output)
        public=extract(RESOURCES,output);write(output/'confidence-public.json',public)
        labels=labels_for(public,fixture)
        if role=='calibration':
            frozen=fit(public,labels);write(ROOT/'calibrator.json',frozen);calibrator_digest=digest(frozen)
        else:
            assert digest(frozen)==calibrator_digest
        probabilities=predict(frozen,public)
        report=evaluate(public,labels,probabilities)
        constant=evaluate(public,labels,[frozen['base_prevalence']]*len(labels))
        report['constant_calibration_prevalence_baseline']={k:constant[k] for k in ('brier','log_loss')}
        report['literal']=measured;report['calibrator_sha256']=calibrator_digest
        write(output/'confidence-evaluation.json',report);result[role]=report
        print(role,json.dumps({k:report[k] for k in ('candidate_types','positive_types','brier','top','thresholds')}),flush=True)
    confirmed=result['confirmation']['thresholds']['0.8']
    validated=confirmed['types']>=20 and confirmed['precision_wilson_95'][0]>=.8
    write(ROOT/'confirmation-decision.json',{'calibrator_sha256':calibrator_digest,'validated_high_trust':validated,
          'fixed_rule':'.8 score threshold; >=20 confirmation types; Wilson 95% precision lower bound >=.8',
          'observed':confirmed,'limits':'Only one reserved work; transfer to a manuscript is not established.'})
    # Frozen application only; Caesar truth is read after probabilities exist.
    public=extract(RESOURCES,ORIGINAL/'frequency');write(ROOT/'caesar-confidence-public.json',public)
    probabilities=predict(frozen,public)
    write(ROOT/'caesar-confidence-predictions.json',{'calibrator_sha256':calibrator_digest,
          'validated_on_confirmation':validated,'rows':[{'cipher':r['cipher'],'word_id':r['word_id'],'score':float(p)} for r,p in zip(public['rows'],probabilities)]})
    labels=labels_for(public,ORIGINAL/'fixture')
    report=evaluate(public,labels,probabilities);report['validated_on_confirmation']=validated
    report['calibrator_sha256']=calibrator_digest;write(ROOT/'caesar-confidence-evaluation.json',report)
    result['caesar']=report
    write(ROOT/'summary.json',{'class_gate':gate,'high_trust_validated':validated,'calibrator_sha256':calibrator_digest,
          'results':{role:{k:r[k] for k in ('candidate_types','positive_types','brier','top','usual_top','thresholds')} for role,r in result.items()},
          'limits':'Synthetic work-disjoint calibration; no target hints added. If confirmation fails, scores are an exploratory ranking, not validated probabilities.'})
    print('CAESAR',json.dumps({k:report[k] for k in ('candidate_types','positive_types','top','thresholds','validated_on_confirmation')}),flush=True)


if __name__=='__main__':main()
