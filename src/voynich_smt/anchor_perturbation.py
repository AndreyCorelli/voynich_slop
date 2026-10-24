"""Type-consistent anchor errors without changing opaque equality identities."""
from collections import Counter


def source_patterns(sentences, anchors):
    frequency = Counter(t['word'] for s in sentences for t in s['tokens'])
    ranked = sorted(anchors, key=lambda w: (-frequency[w], w))
    adps = [w for w in ranked if anchors[w] == 'ADP']
    conjunctions = [w for w in ranked if anchors[w] == 'CCONJ']
    a, b = adps[:2]
    c = conjunctions[0]
    return {
        'correct': {},
        'missing_top1': {w: None for w in ranked[:1]},
        'missing_top5': {w: None for w in ranked[:5]},
        'missing_top_adp': {a: None},
        'swap_adps': {a: b, b: a},
        'swap_adp_conjunction': {a: c, c: a},
    }


def perturb(public, replacements, anchors):
    """Replace revealed anchor names/tags; never replace the underlying type ID."""
    result = []
    for sentence in public:
        tokens = []
        for token in sentence['tokens']:
            changed = dict(token)
            if token['anchor'] in replacements:
                name = replacements[token['anchor']]
                changed.update(anchor=name, tag=anchors[name] if name is not None else 'X')
            tokens.append(changed)
        result.append(dict(sentence, tokens=tokens))
    return result
