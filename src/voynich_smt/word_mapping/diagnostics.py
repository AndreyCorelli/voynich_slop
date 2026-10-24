"""Evaluation-only oracle comparisons on identical masks and candidate domains."""
from collections import Counter
from dataclasses import asdict
import math

from .mapping import WordMapping
from .objective import frequency_penalty


def dictionary_score(model, public, mapping, collapse_weight, frequency_weight=0.0, injective=False):
    if injective and mapping.collapse_penalty:
        raise ValueError('Dictionary violates injective constraint')
    score = model.score(mapping.render(public.segments))
    result = {**asdict(score), 'collapse_penalty': mapping.collapse_penalty,
              'objective': score.log_likelihood - collapse_weight * mapping.collapse_penalty}
    if frequency_weight:
        penalty = frequency_penalty(model, public.segments, mapping)
        result.update(frequency_penalty=penalty, frequency_weight=frequency_weight)
        result['objective'] -= frequency_weight * penalty
    return result


def truth_diagnostic(model, candidates, public, truth, archive, *, collapse_weight=0.0,
                     frequency_weight=0.0, injective=False):
    """Never feeds oracle assignments back into search.

    Missing true candidates cannot be inserted into the optimizer's domain.
    Compare projected dictionaries on exactly the same ciphertext-type mask;
    label partial-domain evidence separately from complete-active comparisons.
    Lossy ciphertext owners with conflicting plaintext forms are not treated as
    a deterministic true dictionary.
    """
    if public.identity != truth.public_sha256:
        raise ValueError('Truth belongs to another fixture')
    if (len(public.segments) != len(truth.plaintext) or any(
            len(a) != len(b) for a, b in zip(public.segments, truth.plaintext))):
        raise ValueError('Truth layout differs from public ciphertext')
    if not archive:
        raise ValueError('Diagnostic requires an archived search result')
    if not math.isfinite(collapse_weight) or collapse_weight < 0:
        raise ValueError('Invalid collapse weight')
    if not math.isfinite(frequency_weight) or frequency_weight < 0 or type(injective) is not bool:
        raise ValueError('Invalid objective configuration')
    owners = {}
    for cipher_segment, plain_segment in zip(public.segments, truth.plaintext):
        for cipher, plain in zip(cipher_segment, plain_segment):
            owners.setdefault(cipher, Counter())[plain] += 1
    forms = candidates.forms
    ids = {form: index for index, form in enumerate(forms)}
    active = {w for w, form in archive[0]['assignments'].items() if form is not None}
    if not active or not active <= owners.keys():
        raise ValueError('Archive has no active words or includes unobserved ciphertext')
    for row in archive:
        if {w for w, form in row['assignments'].items() if form is not None} != active:
            raise ValueError('Archive active vocabulary changed')
        WordMapping(forms, row['assignments'])
    missing = {}
    conflicting = []
    assignments = {}
    for word in sorted(active):
        if len(owners[word]) != 1:
            conflicting.append(word)
            continue
        gold = next(iter(owners[word]))
        if gold not in ids:
            missing[word] = gold
        else:
            assignments[word] = ids[gold]
    total = sum(map(len, public.segments))
    active_tokens = sum(sum(owners[word].values()) for word in active)
    comparable_tokens = sum(sum(owners[word].values()) for word in assignments)
    # Evaluation-only, candidate-constrained deterministic ceiling (also valid
    # for lossy stress tests). Inactive types contribute zero correct tokens.
    attainable = sum(max((n for form, n in owners[w].items() if form in ids), default=0)
                     for w in active)
    result = {'active_types': len(active), 'active_tokens': active_tokens,
        'total_tokens': total, 'comparable_types': len(assignments),
        'comparable_tokens': comparable_tokens,
        'comparable_fraction_of_active_tokens': comparable_tokens / active_tokens,
        'missing_true_candidates': missing, 'conflicting_plaintext_types': conflicting,
        'active_truth_feasible': len(assignments) == len(active),
        'candidate_constrained_token_accuracy_ceiling': attainable / total,
        'full_plaintext_score_noncomparable': asdict(model.score(truth.plaintext)),
        'comparison_scope': 'complete_active_dictionary' if len(assignments) == len(active)
            else 'candidate-covered_unambiguous_subset',
        'truth_score': None, 'best_comparable_score': None,
        'best_incorrect_comparable_objective': None, 'best_minus_truth': None,
        'diagnosis': 'no_comparable_truth', 'comparison_archive_index': None}
    if not assignments:
        return result
    oracle = WordMapping(forms, assignments)
    if injective and oracle.collapse_penalty:
        result.update(active_truth_feasible=False, diagnosis='truth_violates_injective_constraint')
        return result
    truth_score = dictionary_score(model, public, oracle, collapse_weight, frequency_weight, injective)
    compared = []
    for index, row in enumerate(archive):
        projected = WordMapping(forms, {w: row['assignments'][w] for w in assignments})
        score = dictionary_score(model, public, projected, collapse_weight, frequency_weight, injective)
        if (score['covered_tokens'], score['prediction_events']) != (
                truth_score['covered_tokens'], truth_score['prediction_events']):
            raise ValueError('Oracle and searched dictionaries use different scoring masks')
        compared.append((score['objective'], index, projected.assignments != assignments, score))
    best = max(compared, key=lambda row: (row[0], -row[1]))
    wrong = [row[0] for row in compared if row[2]]
    wrong_best = max(wrong) if wrong else None
    tolerance = 1e-8
    true_objective = truth_score['objective']
    if wrong_best is not None and wrong_best > true_objective + tolerance:
        diagnosis = 'incorrect_mapping_outranks_truth'
    elif wrong_best is not None and abs(wrong_best - true_objective) <= tolerance:
        diagnosis = 'incorrect_mapping_ties_truth'
    elif best[0] < true_objective - tolerance:
        diagnosis = 'search_below_truth'
    else:
        diagnosis = 'truth_recovered_in_comparison'
    result.update(truth_score=truth_score, best_comparable_score=best[3],
        best_incorrect_comparable_objective=wrong_best, best_minus_truth=best[0] - true_objective,
        diagnosis=diagnosis, comparison_archive_index=best[1])
    return result
