"""Training-attested pair proposals and bounded exhaustive mapping audits."""
import bisect
import hashlib
import itertools
import math
from pathlib import Path

from .bootstrap_mapping import BootstrapSearch, coordinated_changes
from .data.corpus import digest
from .word_mapping.mapping import WordMapping
from .word_mapping.objective import objective_score


class PhraseSearch(BootstrapSearch):
    """Replace independent joint draws with count-weighted training bigrams.

    No development plaintext is used. Original single-word operators retain
    full vocabulary support. This is heuristic annealing, not MCMC sampling.
    """
    def __init__(self, model, candidates, morphology, segments, config, options, *, input_sha256=None):
        ids = {model.form_ids[w]: i for i, w in enumerate(candidates.forms)}
        rows = sorted((ids[a], ids[b], n) for (a, b), n in model.bigram.items()
                      if a in ids and b in ids and a != b and n > 0)
        if not rows:
            raise ValueError('No distinct training-attested candidate pairs')
        self.phrase_pairs = tuple((a, b) for a, b, _ in rows)
        self.phrase_cumulative = tuple(itertools.accumulate(n for _, _, n in rows))
        super().__init__(model, candidates, morphology, segments, config, options,
                         input_sha256=input_sha256)
        self.protocol = {**self.protocol, 'phrase_policy': 'training-bigram count weighted; no boundary pairs',
                         'phrase_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        self.identity = digest(self.protocol)

    def _joint(self):
        if not self.active_joint_edges:
            return super()._joint()
        left, right = self.rng.choice(self.active_joint_edges)
        index = bisect.bisect_right(self.phrase_cumulative,
                                   self.rng.randrange(self.phrase_cumulative[-1]))
        first, second = self.phrase_pairs[index]
        return 'joint', coordinated_changes(self.scorer.assignments, {left: first, right: second})


def exact_mapping_audit(model, segments, forms, *, max_states=100000):
    """Enumerate every injective mapping in a declared small candidate set.

    Certifies only this restricted problem. Uses the independent full scorer.
    Counts ties with numerical tolerance; retains a deterministic optimum.
    """
    segments = tuple(tuple(s) for s in segments)
    forms = tuple(forms)
    words = tuple(sorted({w for s in segments for w in s}))
    if not words or len(set(forms)) != len(forms) or len(forms) < len(words):
        raise ValueError('Nonempty types and enough unique candidate forms required')
    states = math.perm(len(forms), len(words))
    if type(max_states) is not int or max_states < 1 or states > max_states:
        raise ValueError('Exact audit exceeds state budget')
    best, assignments, ties = -math.inf, None, 0
    scores = []
    for permutation in itertools.permutations(range(len(forms)), len(words)):
        current = dict(zip(words, permutation))
        score = objective_score(model, segments, WordMapping(forms, current), injective=True)
        scores.append(score)
        if score > best + 1e-9:
            best, assignments, ties = score, current, 1
        elif math.isclose(score, best, rel_tol=0, abs_tol=1e-9):
            ties += 1
    return {'states': states, 'best_score': best, 'best_assignments': assignments,
            'optimal_ties': ties, 'scores': scores}
