"""Matched-coverage random contextual-head control for Number transfer."""
import numpy as np
from benchmarks.grammar_cipher_relations_iteration23 import OUT,load,save
from voynich_smt.cipher_relations import RADIUS


def calculate(data,predictions):
    majority=int(np.argmax(np.bincount([y for s in data['train'] for p,y in s['numbers']],minlength=2)))
    result={}
    for row in predictions:
        lookup={s['sent_id']:s for s in data[row['split']]};expected=[];actual=[];targets=[];covered=[]
        for r in row['records']:
            s=lookup[r['sent_id']];c=r['position'];target=r['target'];targets.append(target);covered.append(r['covered']);actual.append(r['guess']==target)
            if not r['covered']:expected.append(float(majority==target));continue
            alternatives=[number for p,number in s['numbers'] if p!=c and abs(p-c)<=RADIUS and s['tokens'][p]!=s['tokens'][c]]
            assert alternatives
            expected.append(sum(v==target for v in alternatives)/len(alternatives))
        expected=np.asarray(expected);actual=np.asarray(actual);targets=np.asarray(targets);covered=np.asarray(covered,dtype=bool)
        result[row['split']+'/'+row['arm']]=dict(queries=len(targets),covered_queries=int(covered.sum()),
            observed_covered_accuracy=float(actual[covered].mean()) if covered.any() else None,
            random_context_expected_covered_accuracy=float(expected[covered].mean()) if covered.any() else None,
            observed_full_balanced_accuracy=float(np.mean([actual[targets==v].mean() for v in (0,1)])),
            random_context_expected_full_balanced_accuracy=float(np.mean([expected[targets==v].mean() for v in (0,1)])))
    return result

if __name__=='__main__':
    if (OUT/'agreement-transfer-control.json').exists():raise ValueError('Preserve previous control')
    result=calculate(load(OUT/'datasets.json'),load(OUT/'agreement-transfer-predictions.json'));save(OUT/'agreement-transfer-control.json',result)
    for key,value in result.items():print(key,round(value['observed_full_balanced_accuracy'],3),round(value['random_context_expected_full_balanced_accuracy'],3))
