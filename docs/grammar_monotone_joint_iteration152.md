# Iteration 152: nonnegative slopes provide a partial robustness repair

**Promising modification:** nonnegative feature slopes prevent the destructive role-coefficient reversal while preserving all full-model hard predictions. Under the middle-siue perturbation, six authors improve relative to matched unconstrained fits; Apuleius worsens. This repairs a particular training instability, not general restoration or the shortage of reliable lexical nuclei.

The frozen design constrained both standardized logit slopes to be nonnegative, with an unrestricted intercept. This encodes the hypothesis that more corrected context overlap and role similarity support CCONJ. The model retains the identical class-balanced loss, regularization, source features/types and raw0.5 threshold. An antisymmetric two-class parameterization preserves the original regularization exactly: .0005||W||² becomes .00025||beta||². No target tuning, offsets or author-specific choices were made.

Twenty-four models were fitted before target predictions: three original source-validation folds, one full fit, all13 training-type omissions, and all seven previously frozen focal substitutions. All predictions were frozen before reference evaluation. Features and unconstrained baselines are cached from the prior experiments; no new annotations, reserved material or sealed works were used.

| Text | Full (both arms) | Omit siue: unconstrained → constrained | Middle substitution: unconstrained → constrained |
|---|---|---|---|
| Caesar | 12/15 | 9/15 → 13/15 | 10/15 → 12/15 |
| Jerome | 12/16 | 7/16 → 11/16 | 8/16 → 11/16 |
| Gellius | 12/15 | 4/15 → 10/15 | 4/15 → 10/15 |
| Livy | 10/14 | 5/14 → 8/14 | 5/14 → 10/14 |
| Apuleius | 6/13 | 6/13 → 5/13 | 6/13 → 5/13 |
| Curtius | 12/15 | 5/15 → 7/15 | 5/15 → 8/15 |
| Suetonius | 12/16 | 6/16 → 10/16 | 6/16 → 9/16 |

The full unconstrained fit already has positive slopes, so its predictions remain the same apart from tiny optimizer differences. No new full-text accuracy gain is claimed. Under middle substitution, NLL improves in every text, including Apuleius (.8861→.8417 despite losing one correct decision). Gellius NLL improves1.7090→.5910, Livy .9559→.6756 and Curtius1.7011→.6487. Probability quality and hard accuracy are reported separately.

All perturbations were retained. Correct-count ranges are:

| Text | All13 omissions: unconstrained → constrained | All7 substitutions: unconstrained → constrained |
|---|---|---|
| Caesar (/15) | 9–12 → 10–13 | 10–12 → 12–12 |
| Jerome (/16) | 7–12 → 11–12 | 7–12 → 11–12 |
| Gellius (/15) | 4–13 → 10–13 | 4–12 → 10–12 |
| Livy (/14) | 5–11 → 8–11 | 5–10 → 10–10 |
| Apuleius (/13) | 6–9 → 5–9 | 6–7 → 5–7 |
| Curtius (/15) | 5–12 → 7–12 | 5–12 → 8–12 |
| Suetonius (/16) | 6–12 → 10–12 | 6–12 → 9–12 |

For each of the six improving authors, only the siue omission changes omission-panel accuracy; the other12 omissions tie their unconstrained counterparts. Five of seven motif substitutions improve, and two tie. Apuleius shows the opposite direction on those same affected cases. These are correlated perturbations, not independent replications, and the ranges are diagnostic rather than selected models.

Source out-of-fold performance on the same13 types remains7/13 correct, while AUC improves.2667→.5333, NLL2.0611→1.3745 and Brier.4121→.3283. This is still weak discrimination and NLL worse than the balanced prior's.6931. Constraints alone do not resolve training uncertainty or overconfidence. In particular, positive but extreme slopes from omitting ue are not prevented merely by enforcing sign.

Keep this as a candidate robustness modification, not a validated deployment default. It preserves the useful full-text grammatical signal while limiting one known failure, but residual sensitivity remains substantial, especially Curtius and Apuleius. Catalogue membership is still supplied; no arbitrary token POS tagging or exact word identities were recovered.

Next proposal: test stronger regularization selected only through nested source held-out-type validation, with a small frozen strength grid and the monotonic architecture fixed. Use outer existing folds for honest source reporting and source-only inner folds for selection; freeze the final selection before target evaluation. Compare all existing perturbations rather than choosing a favorable author. This targets remaining overconfidence and large positive slopes without adding features or new labels.

Independent verification optimized all24 models with a separate binary objective/SLSQP solver, checked nonnegative bounds and KKT conditions, replayed13 source OOF probabilities and2,184 constrained target probabilities, and checked294 paired metric groups and every unconstrained reference. The focused suite passed18 tests. Artifacts and verification manifest: `experiments/results/grammar-restoration/iteration152/`.
