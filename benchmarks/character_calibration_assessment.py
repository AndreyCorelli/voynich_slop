"""Transformation audits and descriptive calibration contrasts, without refitting."""
from collections import defaultdict
import json
import random
from statistics import mean
from benchmarks import character_calibration as c
from benchmarks import character_prediction as p
from voynich_smt.data.corpus import write_json


def assess():
    prepared=c.prepare(); reports=[json.loads((c.OUT/f'iteration-{i}.json').read_text()) for i in range(1,8)]; results={n:r for report in reports for n,r in report['results'].items()}
    for name,case in prepared['cases'].items():
        kind=case['kind']
        if kind not in ('mono','expand','homophonic','positive'): continue
        if kind=='positive':
            for split in ('train','heldout'):
                original=p.prepare()['development' if split=='train' else 'heldout']
                for a,b in zip(original,case[split],strict=True):
                    for i,w in enumerate(b['words']):
                        if i and b['line_ids'][i]==b['line_ids'][i-1]: assert w[0]==b['words'][i-1][-1] and w[1:]==a['words'][i][1:]
                        else: assert w==a['words'][i]
            continue
        original=prepared['cases'][f"latin-{case['seed']}"]; decoder={}; forward=defaultdict(set)
        for split in ('train','heldout'):
            for a,b in zip(original[split],case[split],strict=True):
                for plain,cipher in zip(a['words'],b['words'],strict=True):
                    width=1 if kind=='mono' else 2; chunks=[''.join(cipher[i:i+width]) for i in range(0,len(cipher),width)]
                    for letter,code in zip(plain,chunks,strict=True):
                        assert code not in decoder or decoder[code]==letter; decoder[code]=letter; forward[letter].add(code)
                    assert list(plain)==[decoder[code] for code in chunks]
        assert all(len(codes)<=(2 if kind=='homophonic' else 1) for codes in forward.values())
    prior=json.loads((p.OUT/'iteration-7.json').read_text()); manuscript=prior['models'][prior['selected']]; surrogate=results['eva-shuffle']
    diffs=[a['gain_position']-b['gain_position'] for a,b in zip(manuscript['folios'],surrogate['folios'],strict=True)]
    rng=random.Random(26003); boot=sorted(mean(rng.choices(diffs,k=len(diffs))) for _ in range(10000))
    result={'summary':{n:c.summarize(r) for n,r in results.items()},'prior_manuscript':c.summarize(manuscript),
            'manuscript_minus_refitted_shuffle_gain_per_character':mean(diffs),'descriptive_paired_folio_bootstrap_95':[boot[249],boot[9749]],
            'transformation_decoding_audits':'passed: shared reversible code inventories and positive-control boundaries',
            'limitations':['One author and language; two contiguous excerpts, not independent corpora.','Copied manuscript folio/line slots are artificial layout for Latin; folio uncertainty is not a historical sampling interval.','Expansion doubles word lengths; the same frozen order-two model spans a different plaintext scale in each representation.','Random code-choice RNG restarts at the same seed for training and evaluation, reusing the choice stream; these are not independent random streams.','Surrogates use one permutation per corpus and preserve word inventories/position bins, not every source dependency.','Positive control is strong and artificial; it calibrates detection, not sensitivity at the manuscript effect size.','Manuscript evaluation is reused, not independent replication. No historical mechanism likelihood ratio or language inference.']}
    write_json(c.OUT/'assessment.json',result); print(json.dumps(result,indent=2))

if __name__=='__main__': assess()
