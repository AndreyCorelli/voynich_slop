"""Descriptive folio uncertainty for the frozen manuscript replication."""
import json
import random
from statistics import mean
from benchmarks import manuscript_character_replication as m
from voynich_smt.data.corpus import write_json


def assess():
    p=m.prepare(); reports=[json.loads((m.OUT/f'iteration-{i}.json').read_text()) for i in range(1,8)]; results={n:r for report in reports for n,r in report['results'].items()}
    values=[f['gain_position'] for n in ('A','B') for f in results[n]['folios']]; rng=random.Random(30004)
    samples=sorted(mean(rng.choices(values,k=len(values))) for _ in range(10000))
    summary={n:s for report in reports for n,s in report['summary'].items()}
    result={'primary_combined_folio_equal_gain':mean(values),'positive_folios':sum(v>0 for v in values),'folios':len(values),'primary_words':3712,
            'descriptive_folio_bootstrap_95':[samples[249],samples[9749]],'combined_artificial_layout_gain':mean(summary[n]['gain_position_per_character'] for n in ('A-eight-lines','B-eight-lines')),
            'refitted_null_gains':[summary[f'shuffle-{seed}']['gain_position_per_character'] for seed in (30001,30002,30003)],
            'additional_words':summary['additional-blocks']['words'],'additional_folios':summary['additional-blocks']['folios'],'summary':summary,
            'assessment':'Frozen suffix gain replicates on116previously unscored statistical folios in two cohorts, survives artificial layout, is mainly within-line and retains positive novel-spelling gain. Three refitted nulls near zero. Additional disjoint words on56of these folios also positive. Descriptive bootstrap only, source exclusions/cohort constraints retained; no mechanism/language inference.',
            'next':'Compare matched synthetic boundary-conditioned encoding and local-generation mechanisms with the frozen predictive statistic plus spelling/frequency checks; the replicated gain alone cannot distinguish them.'}
    write_json(m.OUT/'assessment.json',result); print(json.dumps({k:v for k,v in result.items() if k!='summary'},indent=2))

if __name__=='__main__': assess()
