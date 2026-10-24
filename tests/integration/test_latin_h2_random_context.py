import json
from pathlib import Path
import random
from benchmarks.latin_h2_random_context import OUT


def test_frozen_extension_preserves_key_training_cipher_and_holdouts():
    p=json.loads((OUT/'prepared.json').read_text())
    assert len(p['jobs'])==14
    for short,long in zip(p['jobs'][::2],p['jobs'][1::2]):
        assert long['full_held_cipher']==short['full_held_cipher']
        assert long['fixture']['truth']['key']==short['fixture']['truth']['key']
        assert long['fixture']['inventory']==short['fixture']['inventory']
        if long['fixture']['arms']:
            assert long['fixture']['arms']['positive'][-48:]==short['fixture']['arms']['positive']
            rng=random.Random(long['prefix_choice_seed']); key=long['fixture']['truth']['key']
            expected=[[key[l][rng.randrange(2)] for l in w] for w in long['fixture']['truth']['train'][:48]]
            assert long['fixture']['arms']['positive'][:48]==expected


def test_missing_numeral_case_is_retained_not_relaxed():
    p=json.loads((OUT/'prepared.json').read_text())
    case=next(j for j in p['jobs'] if j['job']=='passage-4-words-96')
    assert not case['admitted']
    assert 'xii' in case['coverage']['through-medieval-rare']['missing_training']
    assert len(case['fixture']['truth']['train'])==96
