"""Fixed interpretation of independently tested adjacency feature."""
from collections import Counter
import json
from benchmarks import adjacent_order_replication as m
from voynich_smt.data.corpus import write_json


def assess():
    p=m.prepare(); r=json.loads((m.OUT/'iteration-7.json').read_text()); rows=r['grouped']
    short={s:{split:dict(Counter(''.join(w) for b in data[key] for w in b['words'] if len(w)==1)) for split,key in (('train','training'),('heldout','heldout'))} for s,data in p['sources'].items() if s.startswith('german')}
    result={'summary':rows,'source_one_letter_forms':short,'assessment':'All4prose excerpts suppress adjacent repetition relative to the exact constrained-frequency null. Uniform/mapped generators are near zero or mildly signed; repeat preference positive; greedy avoidance negative in all4sources. Prose suppression is stronger than avoidance in these runs: shared negative sign is not overlap of every numerical range. Sign-only specificity fails; no classification threshold or mechanism inference follows.',
            'limitations':['Fourselectedexcerpts,3keys/order streams, not representative language samples or power estimate.','Prose keys are relabelings/common schedules on same words, not independent prose observations.','Generators receive heldout block inventories and do not invent forms; avoid strategy greedy, not globally optimized.','Conditional expectation adjusts finite word inventories/position/length, not all genre/orthographic/editorial effects.','Feature tested on source-order fixtures only; no new manuscript score or joint predictive classifier.','Raw historical parser reused; short/marked forms retain previous normalization caveats.'],
            'next':'Test a fixed stronger repeat-avoidance generator and a suffix-conditioned generator with avoidance jointly. If they reproduce both frozen ordering signals, park these features as descriptive constraints and shift to an independent mechanism prediction instead of further classifier tuning.'}
    write_json(m.OUT/'assessment.json',result); print(json.dumps({'summary':rows,'source_one_letter_forms':short,'assessment':result['assessment'],'next':result['next']},indent=2))

if __name__=='__main__': assess()
