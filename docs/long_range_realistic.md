# Longer-range prediction with sparse and shared-state controls

Seven stages stress-tested the frozen seven-lag probability mixture with a larger alphabet, uneven emissions, variable word lengths, line boundaries and limited training. These remain synthetic controls, not a historically calibrated corpus or manuscript experiment.

## Protocol

Words use 26 lowercase letters. Initial and final emissions have Zipf-like rank weights `1/(rank^1.2)`; a weighted choice among five middle forms creates uneven repeated word frequencies and lengths of three or four letters. Every 32-word block contains two artificial 16-word lines. Context resets at line boundaries. Only positions 8–15 in each line are scored, ensuring that lags 2–8 never cross a line.

Training uses 32 blocks (1,024 words, 512 eligible prediction events). Evaluation uses 89 independent blocks (2,848 words, 1,424 eligible events). Three preset generator seeds replicate each primary case. Baseline features are half of the scored line segment, current word length, and immediate predecessor's final letter. Current length is supplied publicly, so this is prediction of an initial letter conditional on length, not unrestricted full-word prediction.

The baseline has global/position/immediate count backoff, pseudocount 0.5 per letter and fixed strength 20. Each lag extension additionally conditions on one final letter at distances 2–8, backing off to the baseline. The primary predictor averages all seven probability distributions; no lag or smoothing selection occurs. Gains are bits per eligible initial-letter event.

Primary generators:

- Independent emissions.
- Local-only copying of the preceding final letter with probability 0.6; final letters remain independently sampled.
- Planted copying at lag 4 or lag 8 with probability 0.6.
- Weak planted lag-4 copying with probability 0.25.
- Shared-state independent emissions: two hidden emission states switch with probability 0.1 per word and reset at line starts. Each favors a different half of the alphabet, with leakage into the other half.
- Shared-state local copying, adding the same 0.6 adjacent rule.

Shared-state controls have no explicit distant-copy operation, but common hidden state can create distant associations. They are confounding challenges, not guaranteed statistical independence negatives.

Three refitted controls independently permute each distant feature within baseline position/length/immediate groups, separately in training and evaluation. Targets and baseline features remain unchanged. These are conditional feature controls; they need not form coherent texts and do not provide a claimed permutation p-value. Primary excess subtracts the mean control gain.

## Seven stages

1. Freeze generators, predictor, contexts, seeds and three null streams.
2. Score seven generators with seed 37001.
3. Replicate with seed 37002.
4. Replicate with seed 37003.
5. Expose the true hidden state to baseline features for both state generators and all three seeds; also test 128 training blocks for preset local, weak-lag-4 and state-local generators with seed 37001.
6. Score matched refitted feature controls for all 30 active cases.
7. Assess separation and sparsity; stop without manuscript scoring.

The larger-training check uses the same evaluation sample as its smaller-training counterpart. Its training sample is independently generated from the same distribution, not a nested extension. Oracle state is diagnostic information unavailable in manuscript experiments. Plans are saved before scoring with preparation and preceding-result digests.

## Results

Matched-null excess, bits per eligible initial-letter event:

| Primary generator | Range across three seeds |
|---|---:|
| Independent | −0.002398 to 0.004993 |
| Local only | −0.000720 to 0.002780 |
| Strong lag 4 | 0.040063 to 0.046723 |
| Strong lag 8 | 0.039103 to 0.052783 |
| Weak lag 4 | 0.001702 to 0.012088 |
| Shared-state independent | −0.006421 to 0.002634 |
| Shared-state local | −0.001636 to 0.002080 |

Strong planted effects exceed every tested negative or state-control excess. Weak effects are inconsistent in magnitude: the smallest weak result lies within the negative-control range. These runs therefore do not establish adequate sensitivity to weak effects at the 1,024-word training budget.

For the predetermined larger-training check, weak lag-4 excess increases from 0.001702 to 0.023119 on the same evaluation sample. Local-only excess is −0.001334 and state-local excess is 0.002043 with larger training. This supports a sparsity concern, but one independently resampled training comparison is not a learning curve or a power estimate.

Oracle-state excesses are near zero: state-independent −0.003847 to −0.000607; state-local −0.002628 to −0.000371. The non-oracle state controls were also near zero in these runs. Thus this particular challenge did not produce a large confound; it does not rule out other hidden-state processes.

Raw gain is unreliable: local-only raw gains are approximately 0.0266–0.0273, despite near-zero matched excess. Conversely, weak planted raw gains are negative despite positive matched excess. The refitted contrast removes substantial baseline/model effects. Positive excess alone is not a mechanism discriminator, and no decision threshold, false-positive rate or statistical equivalence claim is fitted.

## Verification

Two tests check line-reset/oracle feature construction and finite normalized predictions for unseen contexts. Independent validation rebuilds every feature row from stored words and independently reconstructs counts and all baseline, per-lag and mixture losses. It checks refitted controls, conditional inventories, unchanged baseline losses, plan digests and final summaries. The generator itself is reused; this is not independent historical source validation.

```sh
.venv/bin/python -m benchmarks.long_range_realistic --run
.venv/bin/python -m benchmarks.long_range_realistic_validation
.venv/bin/python -m pytest -q tests/integration/test_long_range_realistic.py
```

Records: `experiments/results/long-range-realistic/`. Benchmark and reused prior code are hashed at preparation; further variants need a new module/output directory.

## Assessment and next priority

The test is ready to detect strong planted distant effects in this setting, but weak-effect calibration remains inadequate. Before real-text application, reduce sparsity with a pooled/backoff lag predictor and training-only smoothing calibration, then evaluate on untouched positive and local/shared-state control seeds. Freeze the comparison and cap this at one bounded follow-up. If weak effects still overlap negatives, report a sensitivity limit and move to a different prediction rather than extending estimator tuning indefinitely.

No Voynich language, decryption or historical mechanism conclusion follows from this calibration.

Verification passed: both focused tests and 1,537,920 independently reconstructed probability/loss checks across 30 active cases and 90 refitted controls. All saved feature rows, contrasts and grouped summaries passed the audit.
