# Iteration 185 — influential negative example adjusts entropy-based ranking

**Diagnostic finding:** restoring weight to source negative pair21 gradually recovers the original target shortlist rather than producing a single all-or-nothing switch. Rich top10 applicability rises5→6→7→8→9; weights.5 through1 give the same9/10 list. The largest standardized coefficient changes concern mean left-context entropy and the endpoint entropy difference, suppressing four non-case pairs. No intermediate weight is chosen as an algorithm change.

## Frozen weight path

Use source pair21, already identified by183/184, with fixed weights0,.1,…,1 and all51 other examples at unit weight. Normalize weighted loss by51+w, preserving the objective scale and ridge.1: weight0 numerically matches184's fixed-scale omission, weight1 matches180. Keep original full-source scales, feature projection, rich19/control3 columns, intercept, optimizer and threshold/top10/top20 tie rules unchanged.

Freeze every fit and then all source/target probabilities before target scoring. Primary output is the entire path, coefficients, source-pair probability and adjacent-grid top10 entrants/leavers, not selection of a successful weight. Endpoint logit contributions are recorded for every target pair using the same fixed standardized coordinates. These are algebraic contributions with correlated features, not causal feature importance. Grid intervals bracket observed rank changes; they are not exact continuous breakpoints.

## Rich-model path

| Negative example weight | Target NLL | Target AUC | Top10 applicable pairs | Top10 joint yield | Probability predicted for negative sourcepair21 |
|---|---:|---:|---:|---:|---:|
| 0.0 | .5286 | .7824 | 5/10 | 39.58% | 95.09% |
| 0.1 | .5094 | .7898 | 6/10 | 49.58% | 92.50% |
| 0.2 | .4933 | .7978 | 7/10 | 59.58% | 89.08% |
| 0.3 | .4803 | .8086 | 7/10 | 59.58% | 84.97% |
| 0.4 | .4701 | .8173 | 8/10 | 64.58% | 80.45% |
| 0.5 | .4621 | .8222 | 9/10 | 74.58% | 75.84% |
| 0.6 | .4558 | .8281 | 9/10 | 74.58% | 71.38% |
| 0.7 | .4509 | .8336 | 9/10 | 74.58% | 67.20% |
| 0.8 | .4470 | .8361 | 9/10 | 74.58% | 63.36% |
| 0.9 | .4438 | .8386 | 9/10 | 74.58% | 59.87% |
| 1.0 | .4411 | .8417 | 9/10 | 74.58% | 56.70% |

The original rich top10 set is identical at all six tested weights.5–1.0. This is a local training-influence observation, not a recommendation to use.5, a validated confidence bound, or a repair for completely absent source examples. The full-weight model still predicts the negative example above.5; its influence helps target ranking without correctly classifying that source example itself.

The frequency/support control changes much less: targetNLL.6082→.5958, AUC.6102→.6265, with top10 applicability3–4/10 and no consistent monotonic shortlist improvement. Both full paths, all threshold/top10/top20 selections and calibration bins remain in the artifacts. Joint yield is diagnostic agreement over all selected pairs, not named-case/token/word recovery accuracy.

## What moves in the model

Endpoint standardized-coefficient changes (weight0 to1) are largest for:

| Coordinate | Coefficient change |
|---|---:|
| Absolute difference in left-context entropy | −.2362 |
| Mean left-context entropy | +.2128 |
| Log shared-frame support | −.0995 |
| Mean left-neighbor log frequency | +.0989 |
| Mean right-neighbor log frequency | +.0807 |

Sourcepair21 is extreme on the first two entropy coordinates: standardized mean left entropy−4.75 and difference+5.01 relative to full-source scales. Its retained outside-query counts are222 and51, so it is not simply an entropy estimate based on one observation. This is descriptive geometry, not a label-based feature selection rule.

The four rich top10 exchanges, by target row index, are:

| Grid interval | Non-case pair leaving | Case-comparable pair entering |
|---|---:|---:|
| 0.0–0.1 | 69 | 77 |
| 0.1–0.2 | 21 | 45 |
| 0.3–0.4 | 92 | 118 |
| 0.4–0.5 | 82 | 105 |

Indices identify frozen target rows, not recovered word identities; target row21 is distinct from sourcepair21. The two left-entropy coordinates contribute large negative endpoint logit changes to the four departing non-case pairs (combined about−2.19,−1.96,−2.28,−2.25). Total logit changes are−3.02,−1.82,−2.33,−2.78, respectively; other correlated coordinates partly reinforce or offset those terms. One entering pair also loses probability slightly: ranks change comparatively, not just through raising all positive examples.

## Implication and next audit

The original case-applicability signal remains promising, while one negative example teaches the linear model about a sparsely represented entropy regime. This path explains which directions change; it does not prove that a particular nonlinear feature, clipping rule or extra source example will repair robustness. No model, training weight or confidence threshold is adopted from target outcomes.

Next proposed diagnostic: compare the departing non-case pairs' entropy coordinates against source feature ranges with and without pair21, retaining every target row and all coordinates. Determine whether these false positives are extrapolations outside the retained source support. Freeze range definitions and comparisons before evaluation; any later abstention or source-only range-aware model must be assessed separately, without selecting favorable target exclusions. This tests coverage of the training feature regime before modifying the scoring model.

Both passages remain reused Cicero development data with extensive vocabulary overlap. This is an explanation of a supervised grammatical interface, not named-case/POS assignment, lexical nuclei, syntactic restoration or Voynich validation.

## Verification

Independent weighted Newton solves verified all22 fits, fixed scales, weighted normalization and gradients below1e-6. Weight endpoints match180 and184 predictions within1e-6. All source/target probabilities, classification/calibration,66 list metric groups, every adjacent-grid crossing and252 target logit decompositions passed independent checks. Frozen input/model/prediction hashes passed. The broader test suite was not rerun for this reference-only diagnostic; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_weight_path_iteration185.py`; reviewer: `benchmarks/grammar_case_weight_path_iteration185_review.py`. Frozen proposal/design, complete coefficients/predictions/selections/summaries, grid crossings, logit contributions, audit and verification manifest: `experiments/results/grammar-restoration/iteration185/`.
