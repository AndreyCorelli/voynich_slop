"""Evaluate frozen surface dictionaries without proposing or changing entries."""
from collections import Counter


def recovery(public, truth, mapping, *, morphology=None):
    if public.identity != truth.public_sha256:
        raise ValueError('Truth belongs to another fixture')
    if (len(public.segments) != len(truth.plaintext) or any(
            len(a) != len(b) for a, b in zip(public.segments, truth.plaintext))):
        raise ValueError('Fixture layout differs from truth')
    rendered = mapping.render(public.segments)
    exact = covered = lemma_correct = lemma_eligible = feature_correct = feature_eligible = 0
    type_hits = Counter()
    type_counts = Counter()
    for cipher_segment, predicted, expected in zip(public.segments, rendered, truth.plaintext):
        for cipher, guess, gold in zip(cipher_segment, predicted, expected):
            type_counts[cipher] += 1
            type_hits[cipher] += guess == gold
            exact += guess == gold
            covered += guess is not None
            if morphology is not None:
                gold_lemmas = morphology.lemma_ids(gold)
                if gold_lemmas:
                    lemma_eligible += 1
                    lemma_correct += bool(gold_lemmas & morphology.lemma_ids(guess))
                gold_features = feature_sets(morphology, gold)
                if len(gold_features) == 1:
                    feature_eligible += 1
                    feature_correct += bool(gold_features & feature_sets(morphology, guess))
    total = sum(type_counts.values())
    return {'tokens': total, 'types': len(type_counts), 'coverage': covered / total,
        'exact_token_accuracy': exact / total,
        'exact_type_accuracy': sum(type_hits[w] == n for w, n in type_counts.items()) / len(type_counts),
        'lemma_token_accuracy': lemma_correct / lemma_eligible if lemma_eligible else None,
        'lemma_eligible_tokens': lemma_eligible,
        'unambiguous_feature_accuracy': feature_correct / feature_eligible if feature_eligible else None,
        'feature_eligible_tokens': feature_eligible,
        'deterministic_accuracy_ceiling': truth.deterministic_accuracy_ceiling}


def feature_sets(catalog, surface):
    return {tuple(sorted({'part_of_speech': inflection['part_of_speech'],
                          **inflection['features']}.items()))
            for analysis in catalog.entries.get(surface, [])
            for inflection in analysis['inflections']}


def frozen_holdout(model, mapping, ciphertext_segments):
    return model.score(mapping.render(ciphertext_segments))
