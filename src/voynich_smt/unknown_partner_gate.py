"""Contrast a jointly masked swap with independently masked singleton alternatives."""
import math
from voynich_smt.pair_uncertainty import sentence_totals
from voynich_smt.combined_repair_gate import select


def singleton_scores(public, candidates, model):
    result = {}
    for opaque in sorted(candidates):
        # sentence_totals supports a one-element target set as well as pairs.
        n, q = sentence_totals(public, [opaque], model)
        total = float(n[:, 0].sum())
        ns = int((n[:, 0] > 0).sum())
        if not total:
            continue
        tag = next(t['tag'] for s in public for t in s['tokens'] if t['id'] == opaque)
        p = float(q[:, 0].sum()) / total
        gain = math.log((p + 1e-12) / (1 - p + 1e-12)) * (1 if tag == 'ADP' else -1)
        result[opaque] = dict(gain=gain, n=int(total), sentences=ns, supported=total >= 5 and ns >= 3)
    return result


def contrast(features, singletons):
    alternative = max([0.] + [r['gain'] for r in singletons.values() if r['supported']])
    return None if features['pair'] is None else features['gain'] - alternative


def choose(features, singletons, base_policy, cutoff):
    pair = select(features, base_policy)
    value = contrast(features, singletons)
    return pair if cutoff is not None and pair is not None and value is not None and value >= cutoff else None
