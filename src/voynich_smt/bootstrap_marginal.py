"""Marginalize ambiguous local agreement readings rather than average signs."""
import hashlib
import math
from pathlib import Path

from .bootstrap_mapping import AgreementModel, BootstrapSearch
from .data.corpus import digest


class MarginalAgreementModel(AgreementModel):
    def __init__(self, morphology, strength=2.0):
        if not math.isfinite(strength) or strength <= 0:
            raise ValueError('Marginal strength must be finite and positive')
        super().__init__(morphology)
        self.strength = strength

    def pair(self, left, right):
        key = (left, right)
        if key not in self.cache:
            a, b = self.signatures.get(left, ()), self.signatures.get(right, ())
            if a and b:
                counts = {-1.0: 0, 0.0: 0, 1.0: 0}
                for x in a:
                    for y in b:
                        counts[self.compatible(x, y)] += 1
                largest = max(sign for sign, count in counts.items() if count)
                scaled = math.fsum(count * math.exp(self.strength * (sign - largest)) for sign, count in counts.items() if count)
                value = largest + (math.log(scaled) - math.log(len(a) * len(b))) / self.strength
            else:
                value = 0.0
            if len(self.cache) >= 100000:
                self.cache.clear()
            self.cache[key] = value
        return self.cache[key]


class MarginalBootstrapSearch(BootstrapSearch):
    def __init__(self, model, candidates, morphology, segments, config, options, *, input_sha256=None):
        self.marginal_morphology = morphology
        super().__init__(model, candidates, morphology, segments, config, options, input_sha256=input_sha256)
        self.protocol = {**self.protocol, 'agreement_reduction': 'log mean exp(2 * signed compatibility) / 2',
            'marginal_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        self.identity = digest(self.protocol)

    def _archive(self):
        if not isinstance(self.agreement, MarginalAgreementModel):
            self.agreement = MarginalAgreementModel(self.marginal_morphology, strength=2)
        super()._archive()
