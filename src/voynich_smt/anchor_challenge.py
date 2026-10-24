"""Source-frequency challenge pairs disjoint from rehearsed swap identities."""
from collections import Counter
from itertools import product


def challenge_patterns(sentences, anchors, excluded=('in', 'et')):
    frequency = Counter(t['word'] for s in sentences for t in s['tokens'])
    ranked = sorted((w for w in anchors if w not in excluded), key=lambda w: (-frequency[w], w))
    adps = [w for w in ranked if anchors[w] == 'ADP'][:2]
    conjunctions = [w for w in ranked if anchors[w] == 'CCONJ'][:2]
    assert len(adps) == len(conjunctions) == 2
    result = {'correct': {}, 'rehearsed_in_et': {'in': 'et', 'et': 'in'}}
    for a, c in product(adps, conjunctions):
        result['unseen_' + a + '_' + c] = {a: c, c: a}
    a, b = adps
    result['same_adp'] = {a: b, b: a}
    a, b = conjunctions
    result['same_conjunction'] = {a: b, b: a}
    return result
