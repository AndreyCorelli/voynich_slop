"""Serializable, smoothed surface n-grams and an independent full scorer."""
from collections import Counter
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

from voynich_smt.data.corpus import digest, write_json

BOS, EOS, OOV = 0, 1, 2


@dataclass(frozen=True)
class NgramConfig:
    min_count: int = 1
    alpha: float = 0.1
    backoff_strength: float = 1.0
    bigram_weight: float = 0.5
    trigram_weight: float = 0.5
    unigram_weight: float = 0.0

    def __post_init__(self):
        if type(self.min_count) is not int or self.min_count < 1:
            raise ValueError('min_count must be positive')
        values = (self.alpha, self.backoff_strength, self.bigram_weight, self.trigram_weight, self.unigram_weight)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite model parameter')
        if self.alpha <= 0 or self.backoff_strength <= 0:
            raise ValueError('Smoothing must be positive')
        if min(self.bigram_weight, self.trigram_weight, self.unigram_weight) < 0 or not math.isclose(
                self.bigram_weight + self.trigram_weight + self.unigram_weight, 1.0):
            raise ValueError('Conditional mixture weights must sum to one')


@dataclass(frozen=True)
class Score:
    log_likelihood: float
    covered_tokens: int
    total_tokens: int
    prediction_events: int
    oov_tokens: int

    @property
    def coverage(self):
        return self.covered_tokens / self.total_tokens if self.total_tokens else 0.0

    @property
    def per_token(self):
        return self.log_likelihood / self.covered_tokens if self.covered_tokens else None


class NgramModel:
    def __init__(self, vocabulary, unigram, bigram, trigram, config, training_sha256):
        self.vocabulary = tuple(vocabulary)
        self.form_ids = {word: index + 3 for index, word in enumerate(vocabulary)}
        if len(self.form_ids) != len(self.vocabulary):
            raise ValueError('Duplicate forms')
        self.unigram = Counter(unigram)
        self.bigram = Counter(bigram)
        self.trigram = Counter(trigram)
        self.config = config
        self.training_sha256 = training_sha256
        self.bigram_totals = Counter()
        self.trigram_totals = Counter()
        for (a, _), count in self.bigram.items():
            self.bigram_totals[a] += count
        for (a, b, _), count in self.trigram.items():
            self.trigram_totals[a, b] += count
        self.total = sum(self.unigram.values())

    @classmethod
    def train(cls, segments, config=NgramConfig(), *, training_sha256=None):
        segments = tuple(tuple(segment) for segment in segments)
        if any(not isinstance(w, str) or not w or any(c.isspace() for c in w)
               for segment in segments for w in segment):
            raise ValueError('Training segments require nonempty surface words')
        counts = Counter(w for segment in segments for w in segment)
        if not counts:
            raise ValueError('Empty training corpus')
        vocabulary = sorted(w for w, count in counts.items() if count >= config.min_count)
        ids = {w: i + 3 for i, w in enumerate(vocabulary)}
        unigram, bigram, trigram = Counter(), Counter(), Counter()
        for segment in segments:
            if not segment:
                continue
            a = b = BOS
            for c in [ids.get(w, OOV) for w in segment] + [EOS]:
                unigram[c] += 1
                bigram[b, c] += 1
                trigram[a, b, c] += 1
                a, b = b, c
        return cls(vocabulary, unigram, bigram, trigram, config,
                   training_sha256 or digest(segments))

    def probability(self, a, b, c):
        # BOS is context only. EOS and OOV belong to the predictive vocabulary.
        if c < EOS or c >= len(self.vocabulary) + 3:
            raise ValueError('Invalid prediction ID')
        cfg = self.config
        p1 = (self.unigram[c] + cfg.alpha) / (
            self.total + cfg.alpha * (len(self.vocabulary) + 2))
        p2 = (self.bigram[b, c] + cfg.backoff_strength * p1) / (
            self.bigram_totals[b] + cfg.backoff_strength)
        p3 = (self.trigram[a, b, c] + cfg.backoff_strength * p2) / (
            self.trigram_totals[a, b] + cfg.backoff_strength)
        return cfg.unigram_weight * p1 + cfg.bigram_weight * p2 + cfg.trigram_weight * p3

    def score(self, segments):
        """None splits a run; it is UNKNOWN, not an LM OOV word.

        EOS is scored only for nonempty runs. Per-token likelihood includes EOS
        events; prediction_events exposes the separate event denominator.
        """
        likelihood = 0.0
        covered = total = events = oov = 0
        for segment in segments:
            a = b = BOS
            active = False
            for word in segment:
                total += 1
                if word is None:
                    if active:
                        likelihood += math.log(self.probability(a, b, EOS))
                        events += 1
                    a = b = BOS
                    active = False
                    continue
                c = self.form_ids.get(word, OOV)
                likelihood += math.log(self.probability(a, b, c))
                covered += 1
                oov += c == OOV
                events += 1
                a, b = b, c
                active = True
            if active:
                likelihood += math.log(self.probability(a, b, EOS))
                events += 1
        return Score(likelihood, covered, total, events, oov)

    def artifact(self):
        config = asdict(self.config)
        # Keep existing zero-unigram model identities/loaders compatible.
        if not config['unigram_weight']:
            del config['unigram_weight']
        return {'format_version': 1, 'config': config,
            'training_sha256': self.training_sha256, 'vocabulary': list(self.vocabulary),
            'unigram': [[k, n] for k, n in sorted(self.unigram.items())],
            'bigram': [[*k, n] for k, n in sorted(self.bigram.items())],
            'trigram': [[*k, n] for k, n in sorted(self.trigram.items())],
            'boundary_policy': 'two BOS contexts; EOS per nonempty run; UNKNOWN splits',
            'score_denominator': 'covered tokens, including EOS in numerator'}

    @property
    def identity(self):
        return digest(self.artifact())

    def save(self, path):
        write_json(path, {**self.artifact(), 'sha256': self.identity})

    @classmethod
    def load(cls, path):
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        if value['format_version'] != 1:
            raise ValueError('Unsupported n-gram model version')
        model = cls(value['vocabulary'], dict(value['unigram']),
            {tuple(r[:2]): r[2] for r in value['bigram']},
            {tuple(r[:3]): r[3] for r in value['trigram']},
            NgramConfig(**value['config']), value['training_sha256'])
        if model.identity != value['sha256']:
            raise ValueError('N-gram checksum mismatch')
        return model
