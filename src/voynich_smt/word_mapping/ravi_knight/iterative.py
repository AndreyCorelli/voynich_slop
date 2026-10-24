"""Vocabulary expansion with confidence freezing or revisable channel transfer.

This sequential dense reference uses additive-smoothed LMs. It is not an exact
reproduction of the original LM backend or distributed sampling experiments.
"""
from collections import Counter
from dataclasses import dataclass
import math

from .em import EMResult, fit_channel, frequency_channel, random_channel
from .lm import UNKNOWN, SourceModel, _segments, train_bigram
from .reference import viterbi


@dataclass(frozen=True)
class Stage:
    requested_types: int
    source: SourceModel
    cipher_vocabulary: tuple[str, ...]
    frozen: tuple[tuple[str, str], ...]
    source_coverage: float
    cipher_coverage: float
    result: EMResult

    def decode(self, segments, *, channel_exponent=3):
        ids = {w: i for i, w in enumerate(self.cipher_vocabulary)}
        obs = tuple(tuple(ids.get(w, 0) for w in s) for s in _segments(segments))
        return tuple(tuple(self.source.vocabulary[i] for i in viterbi(
            self.result.model, s, channel_exponent=channel_exponent)[0]) for s in obs)


def confident_pairs(stage, *, threshold=0.5):
    """Freeze real-word pairs only, in direction P(cipher | plaintext).

    UNKNOWN is an aggregate whose meaning changes on expansion: neither its row
    nor assignments to its column are carried. This is an explicit interpretation
    of an underspecified edge case, not an assertion about the authors' code.
    Multiple source rows may map to one cipher type; no reciprocal exclusion.
    """
    if not 0.5 <= threshold < 1:
        raise ValueError('threshold must be at least 0.5 and below one')
    return tuple((word, stage.cipher_vocabulary[c])
                 for s, word in enumerate(stage.source.vocabulary) if s
                 for c, probability in enumerate(stage.result.model.channel[s])
                 if c and probability > threshold)


def transfer_channel(previous, source_vocabulary, cipher_vocabulary, cipher_counts,
                     fresh, *, exploration=0.05):
    """Transfer real source rows by identity, splitting old cipher UNKNOWN mass.

    New real cipher columns and remaining UNKNOWN share the old UNKNOWN mass in
    proportion to public ciphertext counts. New source rows and source UNKNOWN
    use fresh initialization because their aggregate identities have changed.
    Mix with fresh positive rows to reopen zero entries; this is initialization,
    not an EM prior or guaranteed monotone comparison across vocabulary stages.
    """
    if not math.isfinite(exploration) or not 0 < exploration < 1:
        raise ValueError('exploration must be finite and strictly between zero and one')
    old_source = {w: i for i, w in enumerate(previous.source.vocabulary)}
    old_cipher = {w: i for i, w in enumerate(previous.cipher_vocabulary)}
    if not set(old_source).issubset(source_vocabulary) or not set(old_cipher).issubset(cipher_vocabulary):
        raise ValueError('Warm start requires expanding vocabularies')
    remaining = sum(n for w, n in cipher_counts.items() if w not in cipher_vocabulary[1:])
    split = [remaining if c == 0 else cipher_counts.get(w, 0) if w not in old_cipher else 0
             for c, w in enumerate(cipher_vocabulary)]
    total = sum(split)
    if total == 0:
        split[0], total = 1, 1
    rows = []
    for s, word in enumerate(source_vocabulary):
        if s == 0 or word not in old_source:
            rows.append(fresh[s])
            continue
        old = previous.result.model.channel[old_source[word]]
        lifted = tuple(old[old_cipher[w]] if c and w in old_cipher
                       else old[0] * split[c] / total for c, w in enumerate(cipher_vocabulary))
        rows.append(tuple((1 - exploration) * p + exploration * q for p, q in zip(lifted, fresh[s])))
    return tuple(rows)


def fit_iterative(training, ciphertext, *, sizes=(100, 150, 200, 250, 300, 350),
                  seed=0, smoothing=0.1, max_iterations=100, tolerance=1e-7,
                  freeze=True, threshold=0.5, initialization='random', frequency_strength=0.5,
                  warm_start=False, exploration=0.05, cipher_order=None):
    """Retrain each expanded channel, carrying only confident fixed rows.

    Unfrozen rows receive fresh seeded initialization at every stage. Source and
    cipher ranks use their own data independently. Frozen pairs use word identity,
    never stage-local IDs. Likelihood histories are comparable only within stages.
    ``freeze=False`` retrains afresh unless ``warm_start=True`` explicitly
    transfers revisable rows. The UNKNOWN source row always initializes afresh.
    """
    if warm_start and freeze:
        raise ValueError('Revisable warm start requires freeze=False')
    if not math.isfinite(exploration) or not 0 < exploration < 1:
        raise ValueError('exploration must be strictly between zero and one')
    if initialization not in {'random', 'frequency'}:
        raise ValueError('Unknown initialization')
    training, ciphertext = _segments(training), _segments(ciphertext)
    sizes = tuple(sizes)
    if not sizes or any(type(k) is not int or k < 1 for k in sizes) or any(
            b <= a for a, b in zip(sizes, sizes[1:])):
        raise ValueError('sizes must be strictly increasing positive integers')
    if not 0.5 <= threshold < 1:
        raise ValueError('threshold must be at least 0.5 and below one')
    frequencies = Counter(w for s in ciphertext for w in s)
    ranked = sorted(frequencies, key=lambda w: (-frequencies[w], w))
    if cipher_order is not None:
        ranked = list(cipher_order)
        if not ranked or len(set(ranked)) != len(ranked) or any(w not in frequencies for w in ranked):
            raise ValueError('Fixed cipher order must contain unique observed words')
    source_types = len({w for s in training for w in s})
    stages, pairs = [], {}
    for index, size in enumerate(sizes):
        source = train_bigram(training, max_types=size, smoothing=smoothing)
        cipher_vocab = (UNKNOWN, *ranked[:size])
        source_ids = {w: i for i, w in enumerate(source.vocabulary)}
        cipher_ids = {w: i for i, w in enumerate(cipher_vocab)}
        observations = tuple(tuple(cipher_ids.get(w, 0) for w in s) for s in ciphertext)
        frozen = {source_ids[w]: cipher_ids[c] for w, c in pairs.items()}
        if initialization == 'frequency':
            channel = frequency_channel(len(source.vocabulary), len(cipher_vocab),
                                        seed=seed + index, strength=frequency_strength)
        else:
            channel = random_channel(len(source.vocabulary), len(cipher_vocab), seed=seed + index)
        if warm_start and stages:
            channel = transfer_channel(stages[-1], source.vocabulary, cipher_vocab,
                                       frequencies, channel, exploration=exploration)
        initial = source.hmm(channel)
        result = fit_channel(initial, observations, max_iterations=max_iterations,
                             tolerance=tolerance, frozen=frozen)
        stage = Stage(size, source, cipher_vocab, tuple(sorted(pairs.items())),
                      1 - source.counts[0] / sum(source.counts),
                      sum(frequencies[w] for w in cipher_vocab[1:]) / sum(frequencies.values()), result)
        stages.append(stage)
        if freeze:
            pairs.update(confident_pairs(stage, threshold=threshold))
        if size >= max(source_types, len(ranked)):
            break
    return tuple(stages)
