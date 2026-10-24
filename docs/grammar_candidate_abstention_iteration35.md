# Iteration 35: candidate-quality flags and abstention

**A background-calibrated outside-mass threshold identifies a small, useful subset of missing-candidate errors.** At the primary settings, query flag precision is 85.0% at 10% class deletion and 94.1% at 50%; recall is 16.2/19.3%. Abstaining on those flags raises retained word-tag accuracy from 68.92% to 69.89% at 98.31% coverage, and from 32.30% to 35.45% at 89.94% coverage. No tag is corrected, and the retained high-deletion tags remain mostly wrong. This is candidate-quality filtering, not grammatical restoration.

## Frozen design and information limits

This experiment reuses iteration34-v2's scalar outside-mass signals and ordinary predictions. Thresholds are calibrated on the 200 old background sentences (1,579 tokens); results use the disjoint 40 old query sentences (473 tokens). Both deletion levels and all five perturbation seeds are pooled within each arm/fallback setting during calibration. The policy receives no deletion-rate label at application.

The underlying chain and candidate inventories remain oracle-derived, and emission parameters were transductively fitted on this corpus. These queries were inspected in previous experiments. Consequently this is an internal development check, not a new held-out result or demonstrated candidate filtering on an unknown cipher. No fresh targets or reserved sentences are scored.

The primary score is cavity probability mass outside the supplied candidate inventory. The control score is ordinary posterior uncertainty, `1 − max p(class)`, which does not consult candidate membership. Both are computed without target labels or oracle neighboring states. Primary fallback epsilon remains .01; .30 is a sensitivity condition. No new model is fitted and no class prediction changes.

## Threshold calibration

For each arm/epsilon/score, enumerate whole tied-score groups and select a scalar `score >= threshold` rule that detects the largest number of excluded-class calibration tokens while falsely flagging at most a fixed fraction of **baseline-correct covered tags**. The primary false-flag budget is 1%; 5% and 10% are frozen sensitivity settings. Ties favor fewer flags; no positive detection gain means the rule is disabled. No query label chooses thresholds or budgets.

There are 24 policies: two arms × two epsilon settings × two scores × three budgets. All policies enable. Each fits 10 background scenarios (two deletion levels × five perturbations), or 15,790 scenario-token exposures from 200 unique sentences. Counts across perturbations are correlated copies, not independent samples.

At primary epsilon .01 and 1% budget, outside-mass thresholds are .973364 for word and.973400 for ending. Word calibration flags 1,154 exposures, including 1,032 excluded tags and 84 baseline-correct covered tags (84/8,566 protected calibration tags). The ending threshold flags 1,161, including 1,039 excluded and 86/8,615 protected tags. These are empirical calibration constraints, not a guarantee of the same error rate on queries.

The ordinary-uncertainty control is calibrated under the same budget/rule. Its selected thresholds are about .476/.475 for word/ending. It flags many fewer excluded calibration tags: 85/87, versus 1,032/1,039 for outside mass.

## Primary query flag quality

The following counts pool the five perturbation scenarios at each deletion level: 2,365 query-token exposures, still only 40 unique query sentences. Both arms produce the same primary outside-mass flag decisions on these queries.

| Query deletion rate | Flagged | Flagged excluded tags | Total excluded tags | Flag precision | Flag recall | Correct covered tags falsely flagged |
|---|---:|---:|---:|---:|---:|---:|
| 10% | 40 | 34 | 210 | 85.00% | 16.19% | 5 |
| 50% | 238 | 224 | 1158 | 94.12% | 19.34% | 10 |

These detect candidate exclusion, not necessarily every incorrect predicted tag. At10% deletion, 35/40 flags are actually incorrect tags (87.5% error precision); at 50%,228/238 (95.8%). Some covered tokens also have wrong predictions, explaining why error precision and excluded-class precision differ.

The empirical primary false-flag rate on baseline-correct covered query tags is 0.31% at low deletion and 1.31% at high deletion. The latter exceeds the 1% calibration budget; the budget does not transfer as a hard bound. Word/ending protected-tag denominators differ slightly but give nearly identical rates.

Most missing-class tokens are not flagged: 83.8% at low deletion and 80.7% at high deletion remain. The result is a relatively precise, low-recall flag, not complete candidate-error detection.

## Retained-tag accuracy versus coverage

Abstention keeps original tag predictions for unflagged tokens and removes flagged claims. It cannot create correct tags. Here “retained accuracy” is correct class predictions divided by retained tokens; it is not dependency precision or recovered grammatical structure.

| Arm | Query deletion | Original tag accuracy | Retained tag accuracy | Retained token coverage | Correct tags discarded |
|---|---:|---:|---:|---:|---:|
| Word | 10% | 68.92% | 69.89% | 98.31% | 5 |
| Ending | 10% | 69.30% | 70.28% | 98.31% | 5 |
| Word | 50% | 32.30% | 35.45% | 89.94% | 10 |
| Ending | 50% | 32.26% | 35.40% | 89.94% | 10 |

For the word arm, the fraction of **all** query tokens still carrying a correct asserted tag falls from 68.92% to 68.71% at low deletion and 32.30% to 31.88% at high deletion. Conditional accuracy rises because proportionally more wrong claims are removed. The retained-correct count never increases; this is an explicitly selective result.

A paired sentence-cluster bootstrap resamples the 40 query sentence IDs jointly across all five perturbations (1,000 replicates). Word-arm 95% intervals for retained-minus-original accuracy are [+0.706,+1.259] percentage points at low deletion and [+2.569,+3.770] at high deletion. Ending intervals are similar. These describe this finite reused query set; they do not account for prior inspection, oracle upstream signals, or transfer to new material.

![Abstention accuracy and coverage](../experiments/results/grammar-restoration/iteration35/abstention-accuracy-coverage.svg)

## Controls

At the same **calibration** 1% budget, ordinary uncertainty is much less useful for detecting missing classes:

| Arm | Query deletion | Outside-mass precision / recall | Ordinary-uncertainty precision / recall |
|---|---:|---:|---:|
| Word | 10% | 85.00 / 16.19% | 7.14 / 0.48% |
| Ending | 10% | 85.00 / 16.19% | 6.25 / 0.48% |
| Word | 50% | 94.12 / 19.34% | 44.83 / 1.12% |
| Ending | 50% | 94.12 / 19.34% | 51.85 / 1.21% |

The uncertainty control retains 98.77–99.41% of word-query tokens, with retained accuracy 69.12% at low deletion and 32.45% at high deletion. It therefore makes fewer abstentions as well as catching fewer candidate failures. These are matched calibration-budget comparisons, not claims that both controls operate at identical query risk or coverage.

For random abstention at the outside-mass policy's exact per-perturbation coverage, expected retained word accuracy is 68.91% at low deletion and 32.27% at high deletion. Actual retained accuracy is 69.89/35.45%. The analytic random control accounts for varying numbers retained in each scenario; no random mask is selected by query outcomes.

## Sensitivity to the false-flag budget

Primary word arm, epsilon .01; all thresholds calibrated before scoring:

| Calibration budget | Query deletion | Flag precision / recall | Query false-flag rate on correct covered tags | Retained accuracy | Coverage |
|---|---:|---:|---:|---:|---:|
| 1% | 10% | 85.00 / 16.19% | 0.31% | 69.89% | 98.31% |
| 5% | 10% | 49.76 / 50.00% | 4.79% | 72.05% | 91.08% |
| 10% | 10% | 37.43 / 63.81% | 10.25% | 72.89% | 84.86% |
| 1% | 50% | 94.12 / 19.34% | 1.31% | 35.45% | 89.94% |
| 5% | 50% | 85.96 / 51.81% | 8.77% | 41.81% | 70.49% |
| 10% | 50% | 79.79 / 65.80% | 16.49% | 45.25% | 59.62% |

Higher calibration budgets trade coverage and correct claims for recall. In particular, false-flag risk on high-deletion queries can substantially exceed the calibration budget; the policy is not calibrated for a new corruption distribution by this experiment. Even the aggressive high-deletion operating point leaves most retained tags incorrect.

At epsilon .30 and primary 1% budget, word-arm flag precision/recall is 67.80/38.10% at low deletion and 94.09/38.51% at high deletion. Retained accuracies are 72.10% at 95.01% coverage and 42.41% at 79.96% coverage, compared with 70.15/36.28% full-tag accuracy for those different upstream models. Correct-covered false-flag rates are 1.82/2.67%, again exceeding the calibration budget. These are sensitivity results, not a query-selected replacement for the .01 primary setting. Ending results and all operating points are retained in the artifacts.

## What this establishes and what to try next

Outside mass provides a usable candidate-quality ranking and, under a frozen scalar rule, a small high-precision subset worth flagging in this oracle-controlled development setting. It outperforms ordinary model uncertainty for identifying missing-class tokens. It does not make the remaining tags reliable enough to claim grammatical restoration, repair the candidate inventory, or validate a threshold on fresh ciphertext.

The next concrete repair diagnostic is **limited candidate expansion for flagged words**: propose a small fixed number of outside classes from cavity context, measure reference-class coverage gained and false classes introduced, then evaluate downstream decoding with the same frozen flag thresholds. Do not assume the cavity top class is correct—the previous override failed. Keep abstention available while evaluating repair, and separate coverage improvement from new ranking errors. Fresh confirmation would require a new declared slice; the reserved 200 sentences should remain untouched.

## Artifacts and checks

Artifacts: `experiments/results/grammar-restoration/iteration35/` contains frozen score observations, manifest, 24 calibrated policies and evaluation freeze, 240 per-scenario query flag audits, 48 pooled/clustered summaries, a standalone accuracy–coverage curve, and validation report. Previous verified files remain unchanged.

```
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_candidate_abstention_iteration35
OPENBLAS_NUM_THREADS=1 MPLCONFIGDIR=/tmp/voynich-matplotlib .venv/bin/python -m benchmarks.grammar_candidate_abstention_iteration35_evaluate
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_candidate_abstention_iteration35_validate
```

Runners preserve outputs. Four new tests independently enumerate threshold choices, verify tie-group/risk behavior and disabled zero-gain flags, and check abstention accounting including removal of correct tags and empty retained sets. Validation replays all 24 policies and independently verifies optimality by grouped-score counts, audits all 240 query flags, confirms source-score projections and disjoint 200/40 sentence IDs, checks all 48 pooled/bootstrap summaries, verifies original tag predictions are unchanged, and checks prior hashes. The combined relevant suite passes 321 tests. The 200 reserved sentences remain unscored.
