"""Training-only decoded frequency prior and explicit dictionary constraints."""
from collections import Counter
import math


def training_probabilities(model, forms):
    """Surface-only probabilities; exclude BOS/EOS and normalize over candidates."""
    counts = [model.unigram[model.form_ids.get(w, 2)] + model.config.alpha for w in forms]
    total = math.fsum(counts)
    return tuple(n / total for n in counts)


def frequency_term(count, total, probability):
    return count * math.log(count / (total * probability)) if count else 0.0


def frequency_penalty(model, segments, mapping):
    """N KL(decoded empirical frequencies || smoothed training frequencies).

    Aggregate token counts across ciphertext owners, including homophones.
    UNKNOWN tokens are excluded; the active mask is fixed throughout a search.
    """
    counts = Counter(form for segment in segments for word in segment
                     if (form := mapping.assignments.get(word)) is not None)
    total = sum(counts.values())
    probabilities = training_probabilities(model, mapping.forms)
    return math.fsum(frequency_term(n, total, probabilities[form]) for form, n in counts.items())


def objective_score(model, segments, mapping, *, collapse_weight=0.0,
                    frequency_weight=0.0, injective=False):
    if injective and mapping.collapse_penalty:
        raise ValueError('Dictionary violates injective constraint')
    likelihood = model.score(mapping.render(segments)).log_likelihood
    return (likelihood - collapse_weight * mapping.collapse_penalty
            - frequency_weight * frequency_penalty(model, segments, mapping))
