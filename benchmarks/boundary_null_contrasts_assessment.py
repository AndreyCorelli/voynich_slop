"""Descriptive excess-gain conclusions; no mechanism classifier or dose selection."""
import json
from statistics import mean
from benchmarks import boundary_null_contrasts as b
from voynich_smt.data.corpus import write_json


def assess():
    p=b.prepare(); r=json.loads((b.OUT/'iteration-7.json').read_text()); grouped={}
    for kind in ('encoder','generator'):
        for dose in b.DOSES:
            rows=[r['contrasts'][b.name(kind,dose,seed)] for seed in b.SEEDS]; values=[v['excess_over_mean_null'] for v in rows]
            grouped[f'{kind}-{dose:g}']={'excess_gains':values,'mean':mean(values),'minimum':min(values),'maximum':max(values),'active_exceeds_all_three_shuffles':sum(v['exceeds_all_three_nulls'] for v in rows)}
    result={'grouped_excess':grouped,'old_null_contrasts':r['old_null_contrasts'],'all_contrasts':r['contrasts'],'structure':r['structure'],
            'assessment':'All12active weak fixtures exceed their3matchedshuffles. Old zero-preference generator excess shrinks to0.000245, showing why absolute gain is misleading. Marker-randomized encoder retains0.003114excess, consistent with remaining natural-prose ordering but not a causal decomposition. Both mechanisms can have excess gains; lower encoding dose approaches manuscript contrast scale while tested generator doses remain smaller. No mechanism identification.',
            'limitations':['Three shuffles per fixture and three keys/streams are descriptive, not a calibrated significance/power estimate.','Shuffles preserve folio/position-bin/length inventories and slot lengths; dependencies tied to preserved constraints can remain.','Null contrast includes refitting/regularization penalties, not a direct entropy or causal effect estimate.','Quarter/half prior cases not reselected; new doses fixed1/16and1/8. Encoder schedules and generator probabilities differ.','Generator uses manuscript word pool; encoder uses German113 prose. Structural contrast remains vocabulary-confounded.','No equal-effect match, heldout mechanism classifier, historical prior or language posterior.'],
            'next':'Stop tuning suffix gain. Equalize vocabulary access in a known-mechanism fixture comparison before testing whether one-edit/repetition features distinguish encoding from generation.'}
    write_json(b.OUT/'assessment.json',result); print(json.dumps({k:v for k,v in result.items() if k in ('grouped_excess','old_null_contrasts','assessment','next')},indent=2))

if __name__=='__main__': assess()
