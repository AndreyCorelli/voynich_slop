# Iteration 103: matching the candidate budget does not rescue sparse uncertainty calibration

Both uncertainty policies still select OFF with the frozen eight-candidate pool. A matched gain-plus-gap baseline qualifies on calibration but fails the 90% precision target on short source-test blocks. The candidate-pool mismatch was therefore not the only obstacle. Preserve iteration 102's small clean screening signal; this iteration establishes no new grammatical restoration or nucleus recovery.

## Frozen comparison

Keep the existing eight types (`a, ad, de, et, ex, in, que, sed`), all fifteen cross-class errors and three clean/same-class controls. Use all nine source-calibration blocks from iteration 98: full 829 sentences and eight 100-sentence blocks, making 162 cases. All 195 supplied context anchors remain visible as before. The core is not reselected and unsupported true partners are not filtered out.

Restrict iteration 102's cached bootstrap columns to pairs whose opaque IDs belong to the core, then recompute the top pair, top-rank stability and lower bounds against the restricted competitors. Keep all 256 sentence resamples, original count eligibility, classifier and joint masking unchanged. This is different from retaining the old sixteen-candidate winner and merely filtering its recommendation.

Keep the exact iteration-102 grids, guards and selection tie breakers: at least 90% empirical precision in both full and sparse regimes, at least ten full and twenty sparse calls, no clean/same-class false calls, and no wrong call with an absent or unsupported true partner. Calibrate matched gain-only and gain-plus-gap baselines using iteration 98's procedure and the same guards. Freeze all policies before loading the previously computed source-test features. The core itself was selected using calibration data in iteration 99, so calibration results are development evidence, not independent confirmation.

## Calibration

| Rule / descriptive subset | Full correct / wrong | Sparse correct / wrong | Outcome |
|---|---:|---:|---|
| Frozen iteration 95 cutoff | 12 / 0 | 70 / 21 | Baseline; one sparse control error |
| Largest zero-wrong stability subset | 15 / 0 | 8 / 0 | Stability ≥0.90, gain ≥0; insufficient sparse calls |
| Best stability policy with required call counts | 11 / 0 | 32 / 4 | 88.89% sparse precision; fails |
| Largest zero-wrong lower-bound subset | 15 / 0 | 2 / 0 | Insufficient sparse calls |
| Matched gain-plus-gap baseline | 11 / 0 | 56 / 6 | 90.32% sparse precision; qualifies |

Of 852 gain/stability policies, 102 meet call-count minima and none meets the precision guard, before additional clean/unavailable checks. None of the 84 lower-bound policies meets the call-count minima. Both uncertainty policies remain OFF, as does gain-only calibration.

The qualifying gain-plus-gap baseline has gain cutoff 0.6554007527202013 and runner-up gap at least 0.25. It has no calibration control errors or wrong repairs with unavailable true partners. This is a calibration success for a simpler baseline, not evidence that bootstrap uncertainty improves the algorithm.

## Frozen source-test evaluation

Use all 162 existing fixed-core cases from iteration 100, through iteration 102's unchanged features. Both uncertainty policies and the calibrated gain-only policy abstain everywhere. Compare the active matched gain-plus-gap baseline with the original frozen cutoff:

| Sentence count | Original correct / wrong | Matched gain-plus-gap correct / wrong |
|---|---:|---:|
| 100 (four blocks) | 28 / 10 | 18 / 4 |
| 200 (two blocks) | 9 / 11 | 2 / 1 |
| 400 | 7 / 4 | 4 / 0 |
| 700 | 10 / 0 | 6 / 0 |
| 770 | 10 / 0 | 6 / 0 |

Short-block precision improves from 73.68% to 81.82%, while correct repairs fall from 28 to 18; it remains below 90%. Three of the four remaining short-block wrong repairs have unsupported true partners. In the designated bad 200-sentence merge, eleven wrong repairs fall to one wrong repair with zero correct repairs: suppression, not successful restoration. The other 200 block falls from nine correct to two. Clean and same-class controls all abstain on evaluation.

The blocks overlap across lengths and reuse development data. Do not pool them as independent observations, adopt the baseline, or change cutoffs using these outcomes. No PP integration was performed in this calibration comparison.

## Verification and next proposal

Replay all 162 restricted calibration cases and 162 evaluation cases; reproduce all four calibrations and actions; verify unchanged original-cutoff evaluation and 1,582 input hashes. All 55 focused tests pass, including a restriction test that checks recomputing the winner and stability when an outside competitor is removed. Frozen evidence, curves, policies, actions, audits and the prior tracker snapshot are in `experiments/results/grammar-restoration/iteration103/`.

Further cutoff tuning has diminishing value here. The next proposed test is to add existing cached unlabeled Caesar context while keeping the scored 100 annotated sentences fixed, the mapping global, and all model parameters and policies fixed. Compare the original context and expanded context for exact pair recovery and uncertainty; do not choose the added context or thresholds based on target outcomes. Establish normalization, type-ID consistency and exclusion of sealed Gallic I–IV material before running. This tests whether more occurrences can resolve unsupported or unstable evidence without adding target annotations. It may still fail under author shift or systematic classifier bias. The grammatical reserve and sealed lexical test remain unscored.
