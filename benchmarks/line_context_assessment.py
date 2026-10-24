"""Freeze the interpretation of independently validated line controls."""
from statistics import mean
import json
from pathlib import Path
from benchmarks import line_context_prediction as experiment
from voynich_smt.data.corpus import digest, write_json


def run():
    p=experiment.prepare(); report=json.loads((experiment.OUT/'iteration-7.json').read_text()); selection=json.loads((experiment.OUT/'iteration-6.json').read_text())
    controlled=report['models'][selection['controlled_context']]
    overall=report['models'][selection['selected']]
    strata={s:sum(t['stratum']==s for row in controlled['rows'] for t in row['tokens']) for s in ('within','cross','block-start')}
    result={'prepared_sha256':digest(p),'selected':selection['selected'],'selected_gain_unigram':overall['gain_unigram'],
        'controlled_context':selection['controlled_context'],'controlled_gain_position':controlled['gain_position'],
        'controlled_known_gain_position':controlled['known_gain_position'],
        'controlled_positive_folios':sum(f['gain_position']>0 for f in controlled['folios']),'folios':len(controlled['folios']),
        'unknown_tokens':controlled['unknown_tokens'],'tokens':controlled['tokens'],'strata':strata,
        'controlled_shuffle_ordering_gain':mean(row['ordering_gain'] for row in report['diagnostic']),
        'assessment':'Raw suffix signal replicates against global frequency, but the development-selected within-line suffix adds no reliable advantage over its position baseline in this new cohort. Shuffled loss can worsen even when the controlled model underperforms its baseline. Positional effects and sparse-context overfitting are not causally separated; no claim that position explains all language-like structure.'}
    path=experiment.OUT/'assessment.json'
    if path.exists(): assert json.loads(path.read_text())==result
    else: write_json(path,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__': run()
