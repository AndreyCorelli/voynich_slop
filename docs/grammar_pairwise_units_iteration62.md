# Iteration 62: correct-versus-competing unit training

Pairwise training does not improve grammatical-unit restoration with the existing features. The primary all-candidate variant, after matched calibration, lowers full-source exact-unit F1 from **56.86% to 55.01%** and selected-sentence F1 from **64.85% to 63.73%**. Copular recovery also declines. Retain the original iteration-57 scorer.

## Frozen design

The experiment keeps the same 4,070 Cicero/Palladius source sentences, five sentence partitions, 96 POS/position features, candidate domains and iteration-56 carrier endpoints. The expanded target is `(subject, head, finite carrier, type)`: 3,365 gold units overall, 519 in the 304 selected sentences. One carrier-ambiguous frame remains excluded. Words, lemmas, morphology and dependency labels are unavailable to the unit scorer.

The control is the original conditional-softmax model. Two pairwise logistic models use the same gold training frames:

- **All candidates (primary):** compare the gold unit against every wrong candidate, average comparisons within each frame, then average frames. Thus long sentences do not acquire more training weight simply because they contain more candidates.
- **Fixed hard opponents (secondary):** compare against the strongest wrong candidates under the original model fitted on that fold's training sentences. All tied strongest opponents share the frame weight. Every training frame is used, including those the original model gets right. No test or calibration errors enter mining.

Each comparison minimizes `log(1 + exp(score(wrong) − score(gold)))`. Both models retain fixed L2 0.01 and the original optimizer settings. There is no type balancing, regularization search or mixing of losses. Equal mean loss weighting does not make the pairwise and softmax objectives mathematically equivalent; the change in how they weight competing candidates is the intended intervention.

All three models receive both zero offsets and the same micro-exact calibration grid: direct offset zero; copular/auxiliary offsets independently in {−2, −1, −0.5, 0, 0.5, 1, 2}. Calibration uses true subject/carrier endpoints, following the previous conditional task. Ties prefer smaller total absolute offset. No grid extension or model change followed test evaluation. The primary calibrated all-candidate auxiliary offset reaches +2 in two folds; fixed-hard calibration reaches −2 for both non-direct types in four folds. These boundary choices limit claims about optimal calibration, but constant offsets cannot repair the within-type head-ranking regressions below.

The pre-evaluation proposal is copied into `proposal-design.md`; design, models and predictions have separate hash freezes.

## Pipeline results

| Model / offsets | Full-source exact | Full-source F1 | Selected exact | Selected F1 | Full-source macro F1 |
|---|---:|---:|---:|---:|---:|
| Original / zero | 2,098 | 56.86% | 346 | 64.85% | 48.36% |
| Original / micro | 2,084 | 56.48% | 345 | 64.67% | 47.62% |
| All candidates / zero | 1,906 | 51.65% | 340 | 63.73% | 33.12% |
| All candidates / micro | 2,030 | 55.01% | 340 | 63.73% | 45.25% |
| Fixed hard / zero | 1,636 | 44.34% | 319 | 59.79% | 22.13% |
| Fixed hard / micro | 1,713 | 46.42% | 329 | 61.67% | 19.61% |

All arms emit the same 4,015 full-source and 548 selected predictions; endpoints do not change. A wrong unit counts as a false positive and false negative. The calibrated all-candidate model gains 34 exact units but loses 102 relative to original zero: net −68. Against the equally calibrated original it gains 38 and loses 92: net −54. Its selected F1 declines for both authors: Cicero 65.98%→65.07%, Palladius 59.57%→57.45%.

| Full-source type | Original zero: correct / F1 | All candidates micro: correct / F1 |
|---|---:|---:|
| Direct (2,423 gold) | 1,690 / 63.51% | 1,648 / 63.12% |
| Copular (650 gold) | 259 / 37.48% | 214 / 32.30% |
| Auxiliary (292 gold) | 149 / 44.08% | 168 / 40.34% |

More auxiliary units are recovered at the cost of precision; this is not an auxiliary F1 improvement. Neither the overall nor copular success condition is met.

## Localization diagnostic

Supply the true endpoints and true type, so constant type offsets cannot affect the head ranking:

| Type | Original | All candidates | Fixed hard |
|---|---:|---:|---:|
| Direct | 2,423 / 2,423 | 2,423 / 2,423 | 2,423 / 2,423 |
| Copular | 420 / 650 | 387 / 650 | 42 / 650 |
| Auxiliary | 269 / 292 | 264 / 292 | 13 / 292 |

Direct heads are automatic once the true direct type/carrier is given. The other rows show that the failure extends beyond calibration. With true endpoints but unknown type, calibrated all-candidate recovery is 2,781/3,365, versus 2,870 for original zero. None of these oracle figures is pipeline restoration performance.

## Why fixed hard opponents fail

A post-evaluation diagnostic evaluates only the existing training frames, without changing models or policies. On its selected comparisons, the fixed-hard model improves weighted pair accuracy in every fold: original 85.27–86.33%, fitted hard model 89.41–90.83%. Yet full-candidate training accuracy falls from 85.27–86.33% to 67.03–69.19%.

It therefore learns the sampled comparisons while failing against candidates that its frozen opponent set did not constrain. This is evidence against replacing the complete competition with a fixed hard-opponent set; it does not rule out adaptive mining or a hard-negative term added to a complete objective. The all-candidate variant also regresses, so correcting that sampling problem alone would not establish a useful gain. The diagnostic is explicitly post hoc in `training-diagnostics.json`.

## Verification and decision

The replay audit refits 15 models (five originals and ten pairwise), replays all 15 calibration policies and 212,100 prediction fields, preserves prior prediction fields and recomputes evaluation. The first audit's metadata assertion compared in-memory tuple feature names with their JSON list representation; `grammar_pairwise_units_iteration62_replay.py` corrects that comparison. The frozen initial audit remains preserved, and no experimental weights, policies or predictions changed. Use the replay module for reproducibility.

Inference mutation checks mask lexical and annotation fields while preserving POS, and true-type offset invariance is checked. **88 relevant tests pass.** Artifacts are under `experiments/results/grammar-restoration/iteration62/`; earlier frozen manifests remain unchanged.

Do not adopt either pairwise model. This rules out these particular loss replacements, not every possible scoring function or the availability of a better structural representation. Next prioritize learning the phrase-role/clause distinctions that helped the earlier head oracles, with candidate-level evaluation and a downstream unit test. Avoid treating high aggregate token-role accuracy as sufficient evidence, as iteration 59 already showed.

These are reused development partitions with source POS available, not fresh confirmation or Voynich restoration. The 200-sentence reserve remains unscored and no prior target queries were scored.
