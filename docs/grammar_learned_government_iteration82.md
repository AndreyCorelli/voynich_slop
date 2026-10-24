# Learned structural membership with cross-fitting — iteration 82

**Inferred PP membership is a useful partial grammatical result under the stated supplied-POS/readable-context setting; downstream Case improvement is negligible.** This experiment learns structural labels rather than supplying them at inference. It must be distinguished from81's structural oracle and from blind cipher-side restoration.

The learned PP-membership classifier has81.01%F1at the default0.5threshold (81.82%precision,80.21%recall). A secondary source-only confidence calibration selects337correct memberships and33wrong on the held-out source split: **91.08%precision,60.07%recall**, covering286selected word types. However, a strong nearest-left-preposition control reaches92.17%precision/56.68%recall. The learned model offers modest extra coverage, not a large advance over that rule.

## Fixed source experiment and OOF training

Retain81's source49fold0fit/calibration/test split and nominal atomic-Case cohort:8,840/2,880/2,783positions. Center coarse POS and nominal membership remain supplied; readable surrounding words, predicted POS/finite proxies and sentence boundaries remain available. No Caesar or reserve scoring occurs. This is reused source development material, dominated by Cicero, not fresh independent confirmation.

Learn an8-class joint distribution over PP membership (yes/no) and the actual head's coarse candidate-POS category (VERBAL/NOMINAL/OTHER/ROOT). Structural supervision uses the actual source links, but inference features are the nearest-cue baseline only; no reference head, membership, Case or subject/object role enters the predicted arm's inputs.

Three sentence-blocked inner folds are fixed by SHA256sentence-IDmod3. Each fit position's structural probabilities come only from a probe trained on the other two folds. Fit the downstream binary nominative model on baseline features plus these8continuous out-of-fold probabilities. Cal/test probabilities average the three frozen probes. This keeps the new structural supervision out of its own fit-position predictions. Upstream49/71feature models stay frozen with the same access as81; only the new probes are cross-fitted. The out-of-fold single-probe versus inference-ensemble averaging can change variance and is a remaining distribution difference.

A matched coarse-oracle Case model uses one-hot joint structural labels, allowing us to distinguish loss from coarsening from loss due to inference. Frozen81baseline/full-oracle models remain controls. Within-sentence shams move structural probability vectors or one-hot labels while keeping baseline features fixed. All model choices are fixed; source calibration alone selects F1andprecision90policies before held-out policy outcomes.

## Primary downstream Case result

| Structural input | Nominative F1 | Brier | NLL | Selective correct / wrong | Selective precision |
|---|---:|---:|---:|---:|---:|
| Frozen nearest-cue baseline | 53.51% | .15740 | .47348 | 61 / 13 | 82.43% |
| Predicted structure, OOF-trained Case | **53.64%** | .15693 | .47203 | 69 / 10 | 87.34% |
| Shammed predicted structure | 52.49% | .15851 | .47739 | 61 / 11 | 84.72% |
| Matched coarse oracle | 55.85% | .14914 | .45066 | 75 / 13 | 85.23% |
| Shammed coarse oracle | 51.81% | .16119 | .48833 | 33 / 5 | 86.84% |
| Frozen full81oracle | 56.56% | .14521 | .43646 | 79 / 8 | 90.80% |

The predicted Case gain is only0.13percentage points, with true positives499→516butfalse positives632→674. Its source-selected precision90policy transfers below90%on test. Do not adopt it as a useful downstream Case addition. The coarse oracle preserves much of the full oracle's F1gain, but not its selective precision; imperfect predicted structure accounts for a further gap.

## Structural predictions themselves

PP membership means the nominal belongs to a case-linked ADP phrase, including inherited membership through81's declared amod/conj/flat/fixed paths. It is **not** an exact preposition-to-head attachment or a complete phrase parse.

| Prediction | Accuracy | Source-majority accuracy |
|---|---:|---:|
| Joint PP/head category | 40.64% | 21.34% |
| PP membership | 92.42% | 79.84% |
| Head category | 44.09% | 27.52% |

PP accuracy alone is insufficient because of class imbalance. At the fixed0.5threshold, PP counts are450true positives,100false positives,111false negatives and2,122true negatives:81.01%F1. Head-category prediction remains comparatively weak; no high-confidence head-category restoration is established.

## Secondary selective PP analysis and proximity controls

After the primary results and default PP metrics were seen, a separately frozen **secondary** analysis calibrated PP policies using source calibration only. It did not choose thresholds on held-out labels, but is development follow-up rather than predeclared independent confirmation. The precision90threshold0.83has source-calibration368correct/39wrong (90.42%precision) across319types, then held-out337correct/33wrong (91.08%) across286types.

Additional secondary controls, declared before their held-out policy metrics, use only the nearest predicted ADP distance: left-only or either-side, with fixed1/distance scores and the same source calibration rule.

| PP policy | Correct / wrong | Precision | Recall |
|---|---:|---:|---:|
| Learned, source-F1threshold0.52 | 444 / 95 | 82.37% | 79.14% |
| Nearest-left, source-F1policy | 450 / 113 | 79.93% | 80.21% |
| Either-side nearest, source-F1policy | 465 / 302 | 60.63% | 82.89% |
| Learned, source precision90policy | **337 / 33** | **91.08%** | **60.07%** |
| Nearest-left, source precision90policy | **318 / 27** | **92.17%** | **56.68%** |

The nearest-left control is strong. Learned selective coverage adds19correct memberships and6errors in aggregate, not a major precision advance. The high precision is conditional on supplied nominal POS and readable contextual inputs; it is not a guarantee after removing those privileges.

Cicero accounts for2,632/2,783test positions: selective330correct/33wrong (90.91%precision,60.66%recall). Palladius contributes151positions and only17PPpositives: selective7correct/0wrong (41.18%recall), too small to establish100%precision transfer.

## Decision and next work

Preserve PP membership as an **inferred, conditional partial-grammar finding**, alongside the strong simple proximity control. This is separate from the failed downstream Case objective and from oracle structure. It establishes neither full attachments nor exact Case restoration.

The next test should remove the supplied center-POS feature, first on the same nominal cohort to isolate that feature's effect. Then evaluate membership eligibility over all token positions so nominal-cohort selection cannot hide errors, with a clearly defined positive membership scope. Keep source-only calibration, nearest-left control, author breakdown and uncertainty/coverage reporting before any target transfer. A source-only result with fewer supplied inputs would be a more defensible grammatical-restoration module.

## Verification

All8,840OOFpositions have sentence-exclusion provenance checked; probe and Case fit gradients/objectives pass. Calibration/test predictions, policies, sham/proximity controls and secondary policies replay. Changing oracle bundles and Case labels leaves predicted structural probabilities and non-oracle scores unchanged. Audit verifies1,626prior input hashes.

Five new tests cover stable folds, multinomial analytic gradients, joint label preservation, continuous probability features and within-sentence shams; all61focused tests pass. Grammar reserve and sealed lexical final test remain unscored. No new target annotations, target scoring or dictionary search.

Artifacts: `experiments/results/grammar-restoration/iteration82/`; implementation: `src/voynich_smt/coarse_government.py`; runner/audit and secondary analyses: `benchmarks/grammar_learned_government_iteration82*.py`.
