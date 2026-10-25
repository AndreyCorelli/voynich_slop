# Iteration 153: source-selected shrinkage improves source validation, with mixed transfer

**Preserve the source-validation improvement:** nested source-only regularization selection improves out-of-fold NLL from1.3745 to.6456 and accuracy from7/13 to8/13 compared with the fixed weakly regularized monotonic model. Full-text transfer remains useful in six authors, but stronger regularization is not a uniform accuracy or robustness improvement. Do not promote it to a validated default on these results alone.

The frozen grid was .0005,.005,.05,.5 in original two-class penalty units. The monotonic two-feature architecture, class-balanced loss and raw0.5 cutoff were unchanged. Within each of the three existing outer type folds, inner leave-one-type-out validation selected the lowest class-balanced NLL, with a deterministic stronger-penalty tie rule. Final strength was selected by the same procedure on all13 source types. No target labels or results entered selection. Cached unsupervised source features include all source IDs as in earlier type-validation experiments; standardization uses only each fit's retained training types.

All three outer folds and the final selection chose.5, the strongest grid endpoint. No larger strengths were added after target evaluation. Inner balanced validation losses were:

| Selection | .0005 | .005 | .05 | .5 |
|---|---|---|---|---|
| Outer0 | 2.1933 | 1.5922 | 1.0684 | .7564 |
| Outer1 | 3.3072 | 1.4433 | .7227 | .6769 |
| Outer2 | 1.2756 | .9297 | .6085 | .4991 |
| Final | 1.9783 | 1.0030 | .7207 | .6761 |

Nested outer OOF metrics on the same13 types:8/13, AUC.6000, NLL.6456, Brier.2271. The preceding fixed-penalty monotonic model scored7/13, AUC.5333, NLL1.3745, Brier.3283. NLL now beats the balanced prior's.6931, but8/13 accuracy is below the10/13 all-ADP majority baseline. With only three conjunction types, this is still weak evidence of general type discrimination, not general POS recovery. Inner balanced losses and outer type-macro NLL are different aggregations and should not be equated.

The selected final strength was frozen before targets and held fixed for all13 omission fits and seven focal-substitution fits, without reselecting per perturbation or author. Full-text results compare with iteration152's weakly regularized monotonic model:

| Text | Previous correct/types | Selected correct/types | Previous NLL | Selected NLL |
|---|---|---|---|---|
| Caesar | 12/15 | 12/15 | .4731 | .6079 |
| Jerome | 12/16 | 12/16 | .6669 | .6604 |
| Gellius | 12/15 | 13/15 | .5068 | .6146 |
| Livy | 10/14 | 10/14 | .6274 | .6658 |
| Apuleius | 6/13 | 7/13 | .7357 | .6986 |
| Curtius | 12/15 | 11/15 | .5704 | .6334 |
| Suetonius | 12/16 | 12/16 | .5824 | .6483 |

Six full texts remain at71.4–86.7%; Apuleius is53.8%. NLL worsens in five authors because shrinkage also weakens confident correct predictions. These are reused development texts and supplied candidate classes, not independent confirmation or exact word identification.

| Text | Omit siue: previous → selected | Middle substitution: previous → selected |
|---|---|---|
| Caesar | 13/15 → 13/15 | 12/15 → 13/15 |
| Jerome | 11/16 → 10/16 | 11/16 → 11/16 |
| Gellius | 10/15 → 10/15 | 10/15 → 10/15 |
| Livy | 8/14 → 6/14 | 10/14 → 8/14 |
| Apuleius | 5/13 → 5/13 | 5/13 → 5/13 |
| Curtius | 7/15 → 6/15 | 8/15 → 7/15 |
| Suetonius | 10/16 → 8/16 | 9/16 → 9/16 |

All20 perturbations per text, every arm and full accuracy/NLL/AUC are retained. No favorable omission or author arm is selected. As an exploratory diagnostic, the largest mean absolute probability movement from the full model over these perturbations shrinks from.277–.340 to.039–.048 across authors. This is expected under strong shrinkage and does not guarantee better decisions: probabilities can cluster around the cutoff and still flip. The accuracy losses in Livy and Curtius show that distinction directly.

Next proposed check: apply the frozen selected model and fixed-penalty comparator to every already frozen iteration144 matched-length window, using cached features only. This tests short-context transfer without changing regularization, thresholds, window positions or candidate eligibility. Report all63 windows and seven full references; no author/window selection. Before calling this an addition to a deciphering algorithm, retain the distinction between source calibration progress and practical grammatical accuracy.

Independent verification checked all source split membership, all four selections, every retained-type standardization and fixed perturbation strength. A separate SLSQP solver and KKT conditions checked180 fitted models;13 nested OOF predictions,2,184 selected target probabilities and441 metric groups were replayed against all matched historical baselines. The focused suite passed18 tests. Artifacts and verification manifest: `experiments/results/grammar-restoration/iteration153/`.
