"""Training-only candidate sets; lemma ambiguity contributes fractional counts."""
from collections import Counter
from dataclasses import dataclass
import random

from .mapping import WordMapping


@dataclass(frozen=True)
class CandidateCatalog:
    forms: tuple[str, ...]
    form_counts: dict
    lemma_counts: dict
    lemma_forms: dict
    training_sha256: str
    morphology_sha256: str

    @classmethod
    def build(cls, segments, morphology, *, training_sha256, min_count=1):
        if morphology.training_sha256 != training_sha256:
            raise ValueError('Morphology and candidate training inputs differ')
        if type(min_count) is not int or min_count < 1:
            raise ValueError('min_count must be positive')
        counts = Counter(w for s in segments for w in s)
        counts = {w: n for w, n in counts.items() if n >= min_count}
        if not counts:
            raise ValueError('Empty candidate vocabulary')
        missing = set(counts) - morphology.entries.keys()
        if missing:
            raise ValueError('Morphology catalog must explicitly include unrecognized forms')
        lemmas = Counter()
        for word, n in counts.items():
            analyses = morphology.lemma_ids(word)
            for lemma in analyses:
                lemmas[lemma] += n / len(analyses)
        groups = {lemma: tuple(w for w in words if w in counts)
                  for lemma, words in morphology.form_groups().items()}
        return cls(tuple(sorted(counts, key=lambda w: (-counts[w], w))),
                   counts, dict(sorted(lemmas.items())),
                   {k: v for k, v in groups.items() if v}, training_sha256, morphology.identity)

    def initialize(self, ciphertext_segments, *, active_types, seed, mode='frequency'):
        """Seed diverse dictionaries. All attested forms remain in the catalog."""
        if type(active_types) is not int or active_types < 1:
            raise ValueError('active_types must be positive')
        if mode not in {'frequency', 'random', 'lemma-aware'}:
            raise ValueError('Unknown initialization mode')
        rng = random.Random(seed)
        counts = Counter(w for s in ciphertext_segments for w in s)
        active = sorted(counts, key=lambda w: (-counts[w], w))[:active_types]
        ids = {word: i for i, word in enumerate(self.forms)}
        assignments = {}
        lemmas = sorted(self.lemma_counts, key=lambda k: (-self.lemma_counts[k], k))
        for rank, word in enumerate(active):
            if mode == 'random':
                form = rng.choice(self.forms)
            elif mode == 'lemma-aware' and lemmas:
                lemma = lemmas[rank % len(lemmas)]
                choices = self.lemma_forms[lemma]
                form = rng.choices(choices, weights=[self.form_counts[w] for w in choices])[0]
            else:
                form = self.forms[rank % len(self.forms)]
            assignments[word] = ids[form]
        return WordMapping(self.forms, assignments)
