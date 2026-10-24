"""Seeded surface proposals; every frozen candidate remains reachable."""


def injective_changes(assignments, changes):
    """Convert a single occupied-form replacement into an owner swap."""
    changes = dict(changes)
    if len(changes) == 1:
        word, form = next(iter(changes.items()))
        owner = next((w for w, f in assignments.items() if f == form and w != word), None)
        if owner is not None:
            changes[owner] = assignments[word]
    return changes


class MutationCatalog:
    def __init__(self, mapping, candidates):
        self.active = tuple(sorted(w for w, form in mapping.assignments.items() if form is not None))
        if not self.active:
            raise ValueError('No active ciphertext types')
        ids = {form: i for i, form in enumerate(mapping.forms)}
        self.groups = {lemma: tuple(ids[w] for w in forms)
                       for lemma, forms in candidates.lemma_forms.items()}
        self.lemmas = tuple(sorted(self.groups))
        self.form_lemmas = {}
        for lemma, forms in self.groups.items():
            for form in forms:
                self.form_lemmas.setdefault(form, set()).add(lemma)
        self.related = {}
        self.form_count = len(mapping.forms)

    def propose(self, scorer, rng, kind):
        word = rng.choice(self.active)
        current = scorer.assignments[word]
        if kind == 'swap' and len(self.active) >= 2:
            index = rng.randrange(len(self.active) - 1)
            own = self.active.index(word)
            other = self.active[index + (index >= own)]
            return kind, {word: scorer.assignments[other], other: current}
        if kind in {'inflection', 'lemma'}:
            lemmas = self.form_lemmas.get(current, set())
            if kind == 'inflection':
                if current not in self.related:
                    self.related[current] = tuple(sorted({form for lemma in lemmas
                        for form in self.groups[lemma] if form != current}))
                choices = self.related[current]
                if choices:
                    return kind, {word: rng.choice(choices)}
            elif self.lemmas:
                for _ in range(16):
                    lemma = rng.choice(self.lemmas)
                    if lemma in lemmas:
                        continue
                    form = rng.choice(self.groups[lemma])
                    if not (self.form_lemmas.get(form, set()) & lemmas):
                        return kind, {word: form}
        if kind not in {'replace', 'swap', 'inflection', 'lemma'}:
            raise ValueError('Unknown mutation operator')
        return 'replace', {word: rng.randrange(self.form_count)}
