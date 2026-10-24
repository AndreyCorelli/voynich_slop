"""Experimental normalized n-gram model with vocabulary-neutral fallback."""
from .ngram import EOS, NgramModel


class UniformBackoffModel(NgramModel):
    """Retain observed conditional counts; replace unigram backoff with uniform mass.

    Uniformity includes EOS/OOV to preserve normalization over the original
    predictive vocabulary. Observed bigram/trigram evidence remains informative.
    This is an experimental ablation, not a changed decoder default.
    """
    def probability(self, a, b, c):
        if c < EOS or c >= len(self.vocabulary) + 3:
            raise ValueError('Invalid prediction ID')
        cfg = self.config
        p1 = 1 / (len(self.vocabulary) + 2)
        p2 = (self.bigram[b, c] + cfg.backoff_strength * p1) / (
            self.bigram_totals[b] + cfg.backoff_strength)
        p3 = (self.trigram[a, b, c] + cfg.backoff_strength * p2) / (
            self.trigram_totals[a, b] + cfg.backoff_strength)
        return cfg.unigram_weight*p1 + cfg.bigram_weight*p2 + cfg.trigram_weight*p3

    def artifact(self):
        return {**super().artifact(), 'experimental_backoff': 'uniform-predictive-vocabulary-v1'}

    @classmethod
    def from_model(cls, model):
        return cls(model.vocabulary, model.unigram, model.bigram, model.trigram,
                   model.config, model.training_sha256)
