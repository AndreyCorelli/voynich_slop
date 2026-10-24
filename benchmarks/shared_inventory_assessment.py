"""Descriptive paired conclusions; no classifier or manuscript model selection."""
import json
from statistics import mean
from benchmarks import shared_inventory_mechanisms as m
from voynich_smt.data.corpus import write_json


def assess():
    p=m.prepare(); r=json.loads((m.OUT/'iteration-7.json').read_text()); structure=json.loads((m.OUT/'iteration-6.json').read_text())['structure']; pairs={}
    for source in m.SOURCES:
        rows=[]
        for seed in m.SEEDS:
            prose=f'{source}-prose-{seed}'; local=f'{source}-local-{seed}'; a=r['contrasts'][prose]; b=r['contrasts'][local]
            rows.append({'seed':seed,'prose_excess':a['excess'],'local_excess':b['excess'],'local_minus_prose':b['excess']-a['excess'],
                         'prose_adjacent_repeat':structure[prose]['encoded']['adjacent_repeat'],'local_adjacent_repeat':structure[local]['encoded']['adjacent_repeat'],
                         'prose_one_edit_pair_fraction':structure[prose]['encoded']['one_edit_pair_fraction'],'local_one_edit_pair_fraction':structure[local]['encoded']['one_edit_pair_fraction']})
        pairs[source]={'rows':rows,'mean_prose_excess':mean(v['prose_excess'] for v in rows),'mean_local_excess':mean(v['local_excess'] for v in rows),'prose_excess_larger_pairs':sum(v['local_minus_prose']<0 for v in rows)}
    result={'paired_sources':pairs,'structure':structure,'assessment':'Exact inventory matching removes the payload global-word-family distinction by construction; encoded one-edit density stays close. Original prose has higher excess suffix gain in all6pairs. Local reordered text has more adjacent repetition. These are source-order/calibration observations, not general encoding-versus-generation signatures. Both sources share reversible encoding, demonstrating composability rather than exclusive causes.',
            'limitations':['Two cached German sources;3keys/streams and3nulls each, no power/classification estimate.','Local generator receives each heldout block public word inventory and cannot create new lexical forms; not independent-vocabulary generation.','Conditional sampling uses only one preset rule/strength; it may destroy natural-order associations even while adding its chosen mapping.','Same public encoding schedule/keys and slot lengths; prefix identities/frequencies and resulting encoded lexical counts can differ.','Source-dependent chronology, normalization and artificial layout remain; raw source parsing reused.','No manuscript classification or mechanism probability inferred.'],
            'next':'Predeclare frequency-adjusted adjacent repetition as a candidate source-order statistic, then test it on disjoint excerpts and other ordering generators under the same representation before applying it to manuscript mechanisms.'}
    write_json(m.OUT/'assessment.json',result); print(json.dumps({'paired_sources':pairs,'assessment':result['assessment'],'next':result['next']},indent=2))

if __name__=='__main__': assess()
