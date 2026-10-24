"""Plaintext-derived morphology tolerance; diagnostic, not a blind grammar scorer."""
from collections import Counter

CONTENT = frozenset({'N', 'ADJ', 'V', 'VPAR', 'SUPINE', 'ADV'})
FUNCTION = frozenset({'PREP', 'CONJ', 'PRON', 'NUM', 'INTERJ'})


def signatures(entries):
    """Keep every analysis, including enclitics; omit lexical identity only."""
    return frozenset((i['part_of_speech'], a.get('enclitic'),
                      tuple(sorted(i['features'].items())))
                     for a in entries for i in a['inflections'])


class StructuralOracle:
    def __init__(self, entries, decoding):
        self.profiles = {w: signatures(a) for w, a in entries.items()}
        self.decoding = dict(decoding)

    def kind(self, word):
        profile = self.profiles.get(word, frozenset())
        if not profile:
            return 'unknown'
        if any(s[0] in FUNCTION or s[0] not in CONTENT for s in profile):
            return 'fixed'
        return 'content'

    def status(self, cipher, proposed, *, permissive=False):
        gold = self.decoding[cipher]
        if proposed == gold:
            return 'compatible'
        if self.kind(gold) == 'fixed':
            return 'error'
        if self.kind(gold) == 'unknown' or not self.profiles.get(proposed):
            return 'unknown'
        a, b = self.profiles[gold], self.profiles[proposed]
        return 'compatible' if (bool(a & b) if permissive else a == b) else 'error'

    def evaluate(self, segments, proposed, *, permissive=False):
        counts = Counter(w for segment in segments for w in segment)
        if set(counts) != set(self.decoding):
            raise ValueError('Oracle key must exactly cover observed ciphertext')
        result = Counter()
        exact = 0
        for cipher, count in counts.items():
            result[self.status(cipher, proposed.get(cipher), permissive=permissive)] += count
            exact += count * (proposed.get(cipher) == self.decoding[cipher])
        total = sum(counts.values())
        return {k: result[k] for k in ('compatible', 'error', 'unknown')} | {
            'tokens': total, 'exact_accuracy': exact/total,
            'error_lower_bound': result['error']/total,
            'error_upper_bound': (result['error']+result['unknown'])/total}
