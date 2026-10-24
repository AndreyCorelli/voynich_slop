"""Authoritative surface dictionary. Analyses never participate in rendering."""
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class WordMapping:
    forms: tuple[str, ...]
    assignments: dict[str, int | None]

    def __post_init__(self):
        if len(set(self.forms)) != len(self.forms) or any(
                not w or any(c.isspace() for c in w) for w in self.forms):
            raise ValueError('Forms must be unique nonempty surface words')
        for word, form in self.assignments.items():
            if not word or any(c.isspace() for c in word):
                raise ValueError('Invalid ciphertext word')
            if form is not None and (type(form) is not int or not 0 <= form < len(self.forms)):
                raise ValueError('Invalid surface form ID')

    def render(self, segments):
        return tuple(tuple(None if self.assignments.get(w) is None else
                           self.forms[self.assignments[w]] for w in segment)
                     for segment in segments)

    @property
    def collapse_penalty(self):
        counts = Counter(form for form in self.assignments.values() if form is not None)
        return sum(max(0, n - 1) for n in counts.values())

    def export(self, catalog=None):
        return [{'ciphertext': word, 'surface': None if form is None else self.forms[form],
                 'analyses': [] if form is None or catalog is None else
                 catalog.entries.get(self.forms[form], [])}
                for word, form in sorted(self.assignments.items())]


def occurrence_index(segments):
    positions = {}
    for segment_id, segment in enumerate(segments):
        for position, word in enumerate(segment):
            positions.setdefault(word, []).append((segment_id, position))
    return {word: tuple(rows) for word, rows in positions.items()}
