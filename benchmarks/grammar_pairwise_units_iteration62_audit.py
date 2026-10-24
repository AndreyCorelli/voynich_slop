"""Refit models and replay calibration and predictions from frozen inputs."""
from collections import defaultdict
import numpy as np
from benchmarks.grammar_pairwise_units_iteration62 import *
from voynich_smt.type_balanced_units import fit as softmax_fit


def run():
    hashes=0
    for name in ('design-freeze.json','model-freeze.json','prediction-freeze.json'):
        for p,h in load(OUT/name)['inputs'].items():
            assert digest(p)==h,p
            hashes+=1
    data=load(SOURCE);parts=load(MORPH/'manifest.json')['partitions'];models=load(OUT/'models.json');rows=load(OUT/'frame-predictions.json');prior=load(UNIT/'frame-predictions.json');lookup={(r['sid'],r['subject']):r for r in prior};by_sid=defaultdict(list)
    for r in rows:by_sid[r['sid']].append(r)
    refits=calibrations=decisions=0
    for f in range(5):
        part=parts[str(f)];training,_=prepare(part['fit'],data);cal,_=prepare(part['calibration'],data)
        for loss in LOSSES:
            record=models[str(f)][loss];base=models[str(f)]['unweighted']['model'];fitted=softmax_fit(training,balanced=False) if loss=='unweighted' else fit(training,loss,base['weights'])
            np.testing.assert_allclose(fitted['weights'],record['model']['weights'],rtol=1e-6,atol=1e-7);refits+=1
            if loss!='unweighted':assert fitted==record['model']
            frames=[dict(gold=r['gold'],options=r['options'],scores=r['x']@np.asarray(fitted['weights'])) for r in cal]
            for policy in ('micro',):
                assert calibrate(frames,policy)==record['policies'][policy];calibrations+=1
        for sid in part['test']:
            tokens=data[sid]['tokens']
            for r in by_sid[sid]:
                old=lookup[(sid,r['subject'])]
                assert all(r[k]==v for k,v in old.items())
                for field,v in (('pairwise_pipeline',r['arms']['carrierfit_carriercal']['f1']),('pairwise_oracle_endpoint',r['unit_gold'][2] if r['unit_gold'] else None)):
                    options=choices(tokens,r['subject'],v) if v is not None else []
                    x=matrix(tokens,r['subject'],v,options) if options else None
                    for loss in LOSSES:
                        record=models[str(f)][loss];scores=x@np.asarray(record['model']['weights']) if x is not None else None
                        for policy in POLICIES:
                            offsets=ZERO if policy=='zero' else record['policies'][policy]['selected']['offsets']
                            prediction=infer(scores,options,r['subject'],v,offsets) if scores is not None else None
                            assert prediction==r[field][loss+'_'+policy];decisions+=1
                        if field=='pairwise_oracle_endpoint':
                            gold=r['unit_gold'];kept=[j for j,(_,role) in enumerate(options) if role==gold[3]] if gold else []
                            prediction=select(scores[kept],[options[j] for j in kept],r['subject'],v) if kept else None
                            assert prediction==r['pairwise_true_type'][loss]
    assert evaluate(rows)==load(OUT/'evaluation.json')
    paired={}
    for candidate in ('pair_all_zero','pair_all_micro','pair_hard_zero','pair_hard_micro'):
        for baseline in ('unweighted_zero','unweighted_micro'):
            counts=Counter()
            for r in rows:
                if r['carrier_ambiguous']:continue
                a=r['pairwise_pipeline'][baseline];b=r['pairwise_pipeline'][candidate];g=r['unit_gold']
                if a!=b:
                    counts['changed']+=1
                    if g is not None and a==g:counts['lost_exact']+=1
                    if g is not None and b==g:counts['gained_exact']+=1
            paired[candidate+'/'+baseline]=dict(counts)
    save(OUT/'additional-audit.json',dict(paired=paired))
    save(OUT/'independent-validation.json',dict(freeze_hashes=hashes,refitted_models=refits,calibration_replays=calibrations,prediction_replays=decisions,evaluation_replayed=True,prior_fields_unchanged=True,reserve_unscored=200,prior_queries_scored=0))
    print('Audit passed',refits,calibrations,decisions,paired)
if __name__=='__main__':run()
