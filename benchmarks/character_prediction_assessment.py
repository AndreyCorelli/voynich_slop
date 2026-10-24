"""Descriptive assessment; no heldout reselection or additional model fitting."""
import json
import random
from statistics import mean
from benchmarks import character_prediction as p
from voynich_smt.data.corpus import write_json


def assess():
    prepared=p.prepare(); r=json.loads((p.OUT/'iteration-7.json').read_text()); m=r['models'][r['selected']]; folios=m['folios']; old=set(prepared['previously_evaluated_folios'])
    rng=random.Random(25004); values=[f['gain_position'] for f in folios]; samples=sorted(mean(rng.choices(values,k=len(values))) for _ in range(10000))
    diagnostic={}
    for d in r['diagnostic']:
        key=(d['folio'],d['seed']); bits,chars=diagnostic.get(key,(0,0)); diagnostic[key]=(bits+d['ordering_gain_bits'],chars+d['characters'])
    shuffle=mean(mean(bits/chars for (folio,seed),(bits,chars) in diagnostic.items() if folio==f['folio']) for f in folios)
    result={'selected':r['selected'],'bits_per_character':m['bits_per_character'],'gain_over_position':m['gain_position'],
        'positive_folios':sum(v>0 for v in values),'folios':len(values),'descriptive_folio_bootstrap_95':[samples[249],samples[9749]],
        'novel_words':m['novel_words'],'words':m['words'],'pooled_novel_gain_over_position':m['novel_gain_position'],
        'position_preserving_shuffle_loss_increase_bits_per_character':shuffle,
        'subgroups':{name:{'folios':len(group),'gain_over_position':mean(f['gain_position'] for f in group)} for name,group in
                    [('new_folios',[f for f in folios if f['folio'] not in old]),('previously_evaluated_folios',[f for f in folios if f['folio'] in old])]},
        'interpretation':'Small incremental predictive signal with open spellings; descriptive uncertainty, changed shorter-block cohort, atomic EVA and first-glyph-only external context. No mechanism/language identification. Independent replication and natural/cipher controls precede mechanism ranking.'}
    write_json(p.OUT/'assessment.json',result); print(json.dumps(result,indent=2))

if __name__=='__main__': assess()
