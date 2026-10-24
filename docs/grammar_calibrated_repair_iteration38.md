# Iteration 38: background-calibrated repair budgets

**Background calibration selects a 10% repair-channel budget for context proposals under a 1% spoil allowance.** On the reused query scenarios, this gains about 1.9 accuracy points pooled across deletion levels, while spoiling 0.96% /0.92% of originally correct tags (word/ending). In the severe-deletion subgroup alone, spoil rates rise to 1.57% /1.31%. The pooled constraint therefore does not guarantee protection within each corruption condition. No-update is selected under the stricter 0.1% allowance.

This is a selection audit of frozen models, not an independent confirmation: iteration37 already reported these budgets' query outcomes. The new selector uses only background labels, but the query set is not newly held out.

## Frozen selection rule

The observations, iteration35 flags, iteration36 context/random K2 proposals, and iteration37 fixed-base repair fits remain unchanged. No HMM or repair-channel model is retrained. All original seed selections still maximize the unlabeled within-budget objective.

Calibration uses the 200 old background sentences (1,579 tokens); application uses the disjoint 40 old queries (473 tokens). The same sentences recur across five perturbation seeds and two deletion levels. Calibration is pooled within each old-model arm and proposal strategy, so the selected policy does not receive the deletion rate at application.

Available repair budgets are 0/.001/.01/.05/.10. Budget 0 is an actual unchanged-model prediction, not a refit. For each candidate budget, count background corrections and spoils relative to the original frozen model. Choose the largest **net corrected-minus-spoiled** count subject to:

`spoiled background tags <= risk × originally correct background tags`

The denominator includes all originally correct background tags, not only candidate-covered tags. Ties prefer fewer spoils, then a smaller repair budget. The primary risk allowance is .01; .001/.005 are fixed sensitivity settings. The no-update option is always available and wins if no feasible update improves net accuracy. Objectives are not compared across repair budgets, and query labels do not enter this new selection function.

This creates 12 policies: two old-model arms × two proposal strategies × three risk allowances. Model outputs and choices were frozen before applying the selections in this iteration's query evaluator. Upstream oracle candidate/chain information, transductive parameter fits, repeated development inspection, and already-known budget query results remain material limitations. No fresh or reserved material is scored.

## Background choices

| Allowed background spoil rate | Context proposals, both arms | Random proposals, both arms |
|---|---:|---:|
| 0.1% | No update | No update |
| 0.5% | 1% repair budget | 1% repair budget |
| **1% primary** | **10% repair budget** | **5% repair budget** |

Word-arm context calibration has 15,790 scenario-token exposures and 8,582 originally correct predictions. These represent 200 unique sentences, not 15,790 independent observations.

| Repair budget | Corrected background tags | Spoiled background tags | Net gain | Spoil rate |
|---|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0% |
| .001 | 65 | 10 | +55 | 0.12% |
| .01 | 214 | 28 | +186 | 0.33% |
| .05 | 364 | 54 | +310 | 0.63% |
| .10 | 456 | 79 | +377 | 0.92% |

Thus even the smallest nonzero budget violates the 0.1% allowance; at 0.5%, .01 is the highest-gain feasible option; at 1%, .10 is feasible and gives the most gain. For the ending arm, .10 corrects 463 and spoils 81/8,631 originally correct background tags (0.94%), net +382.

Under the primary constraint, random proposals select .05, with word-arm 217 corrections/67 spoils (net+150) and ending 238/68 (net+170). Comparisons with context are therefore matched **calibration risk rules**, not identical repair masses.

## Primary query outcomes

Counts pool five perturbations at each deletion level: 2,365 query-token exposures over 40 unique query sentences. The primary context policies select .10 in both arms.

| Arm | Query deletion | Corrected | Spoiled | Net gain | Missing-class tags recovered | Accuracy before → after | Query spoil rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Word | 10% | 26 | 11 | +15 | 20 | 68.92 →69.56% | 0.67% |
| Ending | 10% | 24 | 12 | +12 | 20 | 69.30 →69.81% | 0.73% |
| Word | 50% | 88 | 12 | +76 | 71 | 32.30 →35.52% | **1.57%** |
| Ending | 50% | 87 | 10 | +77 | 72 | 32.26 →35.52% | **1.31%** |

The empirical primary 1% background bound transfers reasonably in the pooled query mixture, but does not hold in every subgroup. Query spoil rates use originally correct query predictions as their denominator: 11/1,630 and 12/764 for word; 12/1,639 and 10/763 for ending. The harder condition has fewer originally correct tags, so comparable spoil counts imply higher rates.

Pooled across both deletion levels (4,730 scenario-token exposures):

| Arm | Corrected | Spoiled | Net gain | Missing-class tags recovered | Accuracy before → after | Pooled spoil rate |
|---|---:|---:|---:|---:|---:|---:|
| Word | 114 | 23 | +91 | 91 | 50.61 →52.54% | 0.96% |
| Ending | 111 | 22 | +89 | 92 | 50.78 →52.66% | 0.92% |

These pooled accuracy levels average deliberately different corruption conditions; they are not estimates of performance on an unknown natural corpus. Recovery of missing classes and net correctness are also distinct: covered tags can improve or deteriorate. The coincidence of 91 recovered and +91 net in the pooled word row is not an accounting identity.

Paired sentence-cluster bootstrap intervals jointly resample the 40 query IDs across perturbations and both deletion levels (1,000 replicates). Pooled primary accuracy gains are +1.92 points for word (95% interval [+1.35,+2.51]) and +1.88 for ending ([+1.36,+2.40]). These finite reused-query intervals do not establish fresh generalization, compensate for prior inspection, or certify the spoil constraint out of sample.

## Stricter risk and no-update controls

The 0.1% allowance chooses no update for every arm/strategy; query predictions, accuracy, and spoils remain exactly unchanged. This shows that the selector can refuse a tempting correction when the declared cost is too tight.

At 0.5%, context chooses the previous .01 repair budget. Word queries correct 36 tags and spoil 4 pooled across conditions, net+32; ending corrects 36 and spoils 5, net+31. Pooled query spoil rates are 0.17/0.21%. Accuracy gains are+0.68/+0.66 points. Severe-condition spoil rates are about 0.39% for either arm, below the 0.5% calibration allowance in this sample. These are frozen sensitivity results, not a newly promoted primary risk setting.

Risk here is an empirical average over scenario-token exposures, not a confidence-bound guarantee. Repeated word types, repeated sentences across corruptions, and distribution shifts can all affect transfer. If protection is required per subgroup, that must be declared and calibrated explicitly; pooling does not provide it automatically.

## Matched random proposals and fixed abstention

Under the primary risk rule, the random-proposal policies select .05. Query accuracies are 68.96/34.04% at low/high deletion for word and 69.39/33.62% for ending. Context's selected-policy advantage is +0.59/+1.48 points for word and +0.42/+1.90 for ending. All paired sentence intervals in this finite query comparison are positive, but repair budgets differ and query results were already known from iteration37. This is a policy comparison, not an isolated proof that context proposal quality caused the entire gain.

Keeping the **original** abstention flags after selected context repair gives retained accuracy 70.15/36.62% at low/high deletion for word and 70.41/36.62% for ending, at unchanged 98.31/89.94% coverage. The flags are not recalibrated for the repaired model. Most severe-condition retained tags are still wrong; neither selective reporting nor budget calibration establishes grammatical restoration.

## Interpretation and next step

The repair procedure now has an explicit, background-label-based decision about how much existing accuracy it may spend, including refusal to update. The chosen budget gives a moderate pooled recovery gain while keeping empirical pooled spoils near the requested 1% allowance. Subgroup exceedances and the heavily reused oracle-controlled development setup prevent a stronger protection claim.

The next necessary confirmation is a **new declared, non-reserved slice with the complete policy frozen**, including candidate/flag rules, proposal cap, repair-budget selection rule, and risk reporting. It should report worst-subgroup spoils as well as pooled gain. More tuning on the same 40 query sentences cannot provide independent evidence. Such confirmation would still validate only the controlled mechanism unless the upstream candidate support and grammatical context can be obtained without oracle labels; that larger problem remains unresolved. The 200 reserved sentences should remain unscored.

## Artifacts and verification

Artifacts: `experiments/results/grammar-restoration/iteration38/` contains cached predictions from frozen models, manifest, 12 background-selected policies and evaluation freeze, 120 query-policy audits, pooled/risk/abstention summaries, clustered comparisons, and validation report. No new model fits occur; earlier verified files remain unchanged.

```
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_calibrated_repair_iteration38
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_calibrated_repair_iteration38_evaluate
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_calibrated_repair_iteration38_validate
```

Runners preserve outputs. Four new tests check spoil feasibility, tie preferences, positive gains, pooling, exact correction accounting, and no-update selection. Validation replays 200 frozen-model prediction vectors, all 12 selectors plus independent exhaustive budget optimality checks, 120 query decisions, 40 pooled/clustered comparisons, split-ID disjointness, zero-update identities, and prior hashes. The combined relevant suite passes 333 tests. No fresh targets or reserved sentences are scored.
