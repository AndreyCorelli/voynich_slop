"""Independently reconstruct selected-model shuffle and bootstrap diagnostics."""
import json
import random
from statistics import mean
from benchmarks import context_prediction as experiment
from benchmarks.context_prediction_validation import manual
from voynich_smt.data.corpus import digest, write_json


def run():
    p=experiment.prepare(); report=json.loads((experiment.OUT/'iteration-7.json').read_text()); selection=json.loads((experiment.OUT/'iteration-6.json').read_text())
    assert report['selected']==selection['selected']
    for row in report['shuffle_diagnostic']:
        block=next(b for b in p['heldout'] if b['folio']==row['folio'] and b['start']==row['start'])
        permuted=list(block['words']); random.Random(row['seed']+block['start']).shuffle(permuted)
        original=manual(p['development'],block,selection['selected_spec'])[0]
        shuffled=manual(p['development'],{**block,'words':permuted},selection['selected_spec'])[0]
        assert abs(original-row['original_bits'])<1e-12 and abs(shuffled-row['shuffled_bits'])<1e-12
        assert abs(shuffled-original-row['ordering_gain'])<1e-12
        base=manual(p['development'],block,experiment.MODELS['unigram'])[0]
        base_shuffled=manual(p['development'],{**block,'words':permuted},experiment.MODELS['unigram'])[0]
        assert abs(base-base_shuffled)<1e-12
    selected=report['models'][report['selected']]; gains=[r['gain'] for r in selected['folios']]
    rng=random.Random(p['bootstrap_seed']); sample=sorted(mean(rng.choices(gains,k=len(gains))) for _ in range(p['bootstrap_repetitions']))
    assert report['selected_gain_bootstrap_95']==[sample[50],sample[1949]]
    result={'prepared_sha256':digest(p),'selected':report['selected'],'folio_mean_gain_bits':selected['folio_mean_gain'],
            'known_word_gain_bits':selected['known_token_gain'],'unknown_tokens':selected['unknown_tokens'],'tokens':selected['tokens'],
            'positive_folios':sum(g>0 for g in gains),'folios':len(gains),'bootstrap_95_bits':report['selected_gain_bootstrap_95'],
            'mean_shuffle_ordering_gain_bits':mean(r['ordering_gain'] for r in report['shuffle_diagnostic']),
            'verified_order_and_bootstrap':True,'scope':'Predictive order signal on seven previously heldout folios/new blocks, not semantic decipherment or a causal mechanism ranking. UNKNOWN class conflates novel spellings; known-word score is reported separately.'}
    path=experiment.OUT/'assessment.json'
    if path.exists(): assert json.loads(path.read_text())==result
    else: write_json(path,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__': run()
