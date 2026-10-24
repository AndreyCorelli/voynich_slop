"""Abstain when PP support disappears after hiding one uncertain anchor type."""
import numpy as np

SLACKS = (0., .05, .1, .2, .4, 1.)


def stable_scores(baseline, hidden_scores, threshold, slack):
    baseline = np.asarray(baseline)
    hidden = np.asarray(hidden_scores)
    assert hidden.ndim == 2 and hidden.shape[1] == len(baseline)
    return np.where(hidden.min(axis=0) >= threshold - slack, baseline, -1.)


def select_slack(curve):
    """Source-calibration choice; preserve half clean TP and ten calls per pattern."""
    original = curve['1.0']['correct']['tp']
    eligible = []
    for slack, patterns in curve.items():
        clean = patterns['correct']
        if clean['tp'] < .5 * original or clean['predicted'] < 20 or (clean['precision'] or 0) < .9:
            continue
        if any(v['predicted'] < 10 for v in patterns.values()):
            continue
        worst = min(v['precision'] for v in patterns.values())
        eligible.append((worst, sum(v['tp'] for v in patterns.values()), float(slack)))
    if not eligible:
        return dict(slack=1., qualified=False, reason='No candidate satisfies clean coverage/precision and per-pattern support guards; baseline fallback.')
    worst, _, slack = max(eligible)
    return dict(slack=slack, qualified=True, worst_calibration_precision=worst)
