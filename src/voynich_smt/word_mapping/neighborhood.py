"""Evaluation-only exhaustive single-replacement and pair-swap oracle audit."""
from collections import Counter
from itertools import combinations
import math

from .incremental import IncrementalScorer
from .mapping import WordMapping
from .ngram import BOS, EOS
from .objective import objective_score


def audit_neighborhood(model, candidates, public, truth, *, top=10, progress=None):
    if public.identity != truth.public_sha256:
        raise ValueError('Truth belongs to another fixture')
    if len(public.segments) != len(truth.plaintext) or any(
            len(a) != len(b) for a, b in zip(public.segments, truth.plaintext)):
        raise ValueError('Truth layout differs from public ciphertext')
    if type(top) is not int or top < 1:
        raise ValueError('top must be positive')
    ids = {w: i for i, w in enumerate(candidates.forms)}
    owners = {}
    for ciphertext, plaintext in zip(public.segments, truth.plaintext):
        for cipher, plain in zip(ciphertext, plaintext):
            owners.setdefault(cipher, set()).add(plain)
    if any(len(forms) != 1 for forms in owners.values()):
        raise ValueError('Neighborhood requires a deterministic true dictionary')
    missing = sorted({next(iter(forms)) for forms in owners.values()} - ids.keys())
    if missing:
        raise ValueError('Neighborhood requires fully covered truth; no candidates will be added')
    mapping = WordMapping(candidates.forms, {w: ids[next(iter(forms))] for w, forms in owners.items()})
    scorer = IncrementalScorer(model, public.segments, mapping)
    words = tuple(sorted(mapping.assignments))
    used = set(mapping.assignments.values())
    occurrences = Counter(w for s in public.segments for w in s)
    counters = {name: Counter() for name in ('replacement', 'injective_replacement', 'swap')}
    best = {name: [] for name in counters}
    per_type = []
    tolerance = 1e-8

    def record(kind, proposal):
        delta = scorer.delta(proposal)
        bucket = 'improving' if delta > tolerance else 'worsening' if delta < -tolerance else 'tied'
        counters[kind][bucket] += 1
        if len(best[kind]) == top and delta <= best[kind][-1][0]:
            return
        best[kind].append((delta, dict(proposal.changes)))
        best[kind].sort(key=lambda row: (-row[0], tuple(sorted(row[1].items()))))
        del best[kind][top:]

    for index, word in enumerate(words):
        highest = highest_injective = -math.inf
        improving = improving_injective = 0
        for form in range(len(candidates.forms)):
            if form == mapping.assignments[word]:
                continue
            proposal = scorer.propose({word: form})
            delta = scorer.delta(proposal)
            record('replacement', proposal)
            highest = max(highest, delta)
            improving += delta > tolerance
            if not mapping.collapse_penalty and form not in used:
                record('injective_replacement', proposal)
                highest_injective = max(highest_injective, delta)
                improving_injective += delta > tolerance
        per_type.append({'ciphertext': word, 'true_form': candidates.forms[mapping.assignments[word]],
            'occurrences': occurrences[word], 'improving_replacements': improving,
            'improving_injective_replacements': improving_injective,
            'best_replacement_delta': highest if math.isfinite(highest) else None,
            'best_injective_replacement_delta': highest_injective if math.isfinite(highest_injective) else None})
        if progress and ((index + 1) % 25 == 0 or index + 1 == len(words)):
            progress(index + 1, len(words))
    for first, second in combinations(words, 2):
        if mapping.assignments[first] != mapping.assignments[second]:
            record('swap', scorer.propose({first: mapping.assignments[second], second: mapping.assignments[first]}))

    def term(term, changes):
        if term == BOS:
            return '<BOS>'
        if term == EOS:
            return '<EOS>'
        return candidates.forms[changes.get(term, mapping.assignments[term])]

    examples = {}
    for kind, rows in best.items():
        examples[kind] = []
        for delta, changes in rows:
            proposal = scorer.propose(changes)
            neighbor = WordMapping(mapping.forms, {**mapping.assignments, **changes})
            # Independent full computation validates each retained example.
            expected = objective_score(model, public.segments, neighbor) - scorer.objective
            if not math.isclose(expected, delta, rel_tol=1e-10, abs_tol=1e-8):
                raise ValueError('Neighborhood delta differs from full recomputation')
            terms = [{'before': [term(t, {}) for t in scorer.events[i]],
                'after': [term(t, changes) for t in scorer.events[i]],
                'log_delta': score - scorer.event_scores[i]}
                for i, score in proposal.event_scores.items()]
            examples[kind].append({'objective_delta': delta,
                'changes': [{'ciphertext': w, 'before': candidates.forms[mapping.assignments[w]],
                    'after': candidates.forms[form], 'occurrences': occurrences[w]} for w, form in changes.items()],
                'terms': sorted(terms, key=lambda row: -abs(row['log_delta']))})
    scorer.validate()
    return {'public_sha256': public.identity, 'model_sha256': model.identity,
        'tokens': sum(map(len, public.segments)), 'active_types': len(words),
        'candidate_forms': len(candidates.forms), 'true_objective': scorer.objective,
        'truth_injective': not mapping.collapse_penalty,
        'counts': {kind: {**dict(counts), 'evaluated': sum(counts.values())} for kind, counts in counters.items()},
        'types_with_improving_replacement': sum(row['improving_replacements'] > 0 for row in per_type),
        'types_with_improving_injective_replacement': sum(row['improving_injective_replacements'] > 0 for row in per_type),
        'per_type': per_type, 'examples': examples,
        'scope': 'evaluation only; exhaustive radius-one replacements and pair swaps; truth never seeds search'}
