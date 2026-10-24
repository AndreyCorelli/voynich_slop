"""Descriptive assessment and prior German short-form caveats; no new scoring."""
from collections import Counter
import json
from benchmarks import multilingual_character as m
from benchmarks import character_prediction as pred
from voynich_smt.data.corpus import write_json


def assess():
    p=m.prepare(); reports=[json.loads((m.OUT/f'iteration-{i}.json').read_text()) for i in range(1,8)]; summaries={n:s for r in reports for n,s in r['summary'].items()}
    short={}
    for name,case in p['cases'].items():
        if case['source'].startswith('german') and case['variant'] in ('primary','replication'):
            short[name]={split:dict(Counter(''.join(w) for b in case[split] for w in b['words'] if len(w)==1)) for split in ('train','heldout')}
    prior=json.loads((pred.OUT/'iteration-7.json').read_text()); manuscript=prior['models'][prior['selected']]
    result={'summary':summaries,'prior_manuscript_gain':manuscript['gain_position'],'coverage':p['coverage'],'german_one_letter_forms':short,
            'limitations':['Cached works differ in genre, orthography, vocabulary and word lengths; matched word counts do not match all statistical difficulty.','Copied manuscript layout and eight-word lines are artificial for comparators; Latin/German/Italian evaluation groups are not independent historical folios.','Seven source cases represent three language groups, not independent random samples of languages; Latin works share editorial pipeline and Italian comes from one collection.','Czech Bible excerpts too short, Dalimil verse not a prose comparator.','German uses earlier length-study normalization, not corrected solver-vocabulary quarantine: primary233 includes one unresolved v evaluation form, and other marked-form effects may remain. Primary133 contains no k/x; replications audited separately.','Raw-source checksums/parser hashes pinned, but source extraction reused rather than independently reimplemented.','Manuscript result reused; four tail replications disjoint within works, not independent authors. One refitted surrogate per source. No bootstrap or language posterior.'],
            'assessment':'Primary German gains are heterogeneous and smaller than reused manuscript gain. All seven primary novel-spelling gains are negative. Layout can reverse a German result. German113 replication stays positive; German133 turns negative. No language or historical mechanism ranking.',
            'next':'Replicate the manuscript signal on untouched eligible text with a frozen protocol and explicit layout sensitivity before treating its difference from prose as a stable property.'}
    write_json(m.OUT/'assessment.json',result); print(json.dumps({'assessment':result['assessment'],'german_one_letter_forms':short,'next':result['next']},indent=2))

if __name__=='__main__': assess()
