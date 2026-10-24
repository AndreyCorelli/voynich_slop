"""Descriptive conclusions for frozen mapped-boundary calibration."""
import json
from statistics import mean
from benchmarks import mapped_boundary_calibration as w
from benchmarks import character_prediction as pred
from voynich_smt.data.corpus import write_json


def strata(model):
    tokens=[t for row in model['rows'] for t in row['tokens']]
    return {s:{'words':len(group),'pooled_gain_bits_per_character':sum(t['gain_position'] for t in group)/sum(t['characters'] for t in group)} for s in ('block-start','within','cross') if (group:=[t for t in tokens if t['stratum']==s])}


def assess():
    p=w.prepare(); validation=json.loads((w.OUT/'validation.json').read_text()); original=pred.prepare(); r=json.loads((pred.OUT/'iteration-7.json').read_text()); manuscript=r['models'][r['selected']]
    eligible=matched=0
    for b in original['heldout']:
        for i in range(1,len(b['words'])):
            if b['line_ids'][i]==b['line_ids'][i-1]: eligible+=1; matched+=b['words'][i][0]==p['mapping'].get(b['words'][i-1][-1])
    strong=json.loads((w.OUT/'iteration-4.json').read_text())['results'][w.name(w.SEEDS[0],1)]
    result={'mapping':p['mapping'],'dose_response':validation['dose_response'],'manuscript_gain':validation['prior_manuscript_gain'],
            'original_heldout_mapped_match_fraction':matched/eligible,'original_stratum_gains':strata(manuscript),'seed_28001_strong_stratum_gains':strata(strong),
            'assessment':'All nine nonzero-dose realizations gain over the invariant position baseline; three strongest controls span0.00863–0.00935 bits/character, comparable to manuscript0.00915. Nulls all slightly negative. This is an initial sensitivity check for the specific injected relationship, not a power estimate or identification of its cause.',
            'next':'Park calibration tuning. Compare the frozen statistic with several independent natural-prose corpora/languages using explicit normalization and matched sample sizes, before ranking mechanisms.'}
    write_json(w.OUT/'assessment.json',result); print(json.dumps(result,indent=2))

if __name__=='__main__': assess()
