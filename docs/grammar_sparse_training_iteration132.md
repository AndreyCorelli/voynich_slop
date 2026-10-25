# Iteration 132: matched sparse training improves source and Jerome, not Caesar

**Preserve the partial grammatical success:** training the classifier under the same five-anchor masking used at inference yields **source 95 correct / nine wrong PP selections (91.35% precision)**, **Jerome original 19/1 (95%)**, and **Jerome expanded 17/1 (94.44%)**. The corresponding old sparse-input results were 60/2, 5/0, and 0/0. Caesar remains effectively unrecovered at 1/0 original and 0/0 expanded. This is a conditional structural result with limited transfer, not a shared lexical nucleus or general low-anchor POS restoration.

## One matched training change

Retain only the same supplied surrounding mappings `ut`, `me`, `cum`, `quod`, and `te` during classifier training as well as inference. Every other lexical anchor identity and supplied grammatical tag is removed; opaque occurrence IDs remain. Rebuild the feature vocabulary from these masked inputs, with the same regularization, optimizer settings, class-balanced loss, thirteen noncatalogue training types, sampled occurrences, and three type-held-out folds as iteration 124.

All sixteen target types remain excluded from training labels and globally masked. Recompute thirteen out-of-fold profiles and fit the balanced scalar calibration only on those profiles, yielding offset **0.1977281255**. Freeze the models and calibration before any source-test or author prediction. There is no new target-selected threshold, budget, or model choice.

Evaluate the exact source-test and four cached author contexts from iterations 129–130. All present target types remain included, with support reported separately. Class profiles may use expanded context, but PP inference scores only the original 100 author sentences and pools only those positions. The original PP model and 0.80 cutoff remain fixed. All class predictions and PP views are frozen before PP scores, then all PP scores before metrics.

No new annotations, reserve features, sealed lexical evaluation, lexical search, or default changes occur. These are adaptively reused development texts; supplied five mappings, candidate function-word membership, and segmentation remain privileges.

## Binary class results at identical sparse inputs

| Context | Old correct | Matched-training correct | Majority prior correct | Old NLL | New NLL | Old AUC | New AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Source | 10/16 | **11/16** | 8/16 | 0.6665 | 0.6424 | 0.8125 | 0.8125 |
| Jerome original | 7/13 | **8/13** | 8/13 | 0.6547 | 0.6125 | 0.7875 | 0.7125 |
| Jerome expanded | 7/16 | **10/16** | 8/16 | 0.6957 | 0.7414 | 0.7188 | 0.5781 |
| Caesar original | 6/13 | **7/13** | 7/13 | 0.7331 | 0.7134 | 0.5714 | 0.5000 |
| Caesar expanded | 7/15 | **7/15** | 8/15 | 0.7214 | 0.7009 | 0.7500 | 0.7857 |

Class accuracy improves in four views but does not uniformly improve ranking or probability quality. Expanded Jerome's NLL worsens despite more correct hard decisions. Expanded Caesar still classifies every target type as a conjunction. The raw, uncalibrated Caesar-expanded result is 9/15 correct versus calibrated 7/15; this is recorded, not selected as an author-specific replacement.

## Structural utility

Each cell gives correct / wrong selections. Unknown target classes select nothing at this five-anchor budget in every context.

| Context | Old hard-class PP | New hard-class PP | New precision | New originally unmapped PP |
|---|---:|---:|---:|---:|
| Source | 60/2 | **95/9** | **91.35%** | **60/8 (88.24%)** |
| Jerome original | 5/0 | **19/1** | **95%** | **17/1 (94.44%)** |
| Jerome expanded | 0/0 | **17/1** | **94.44%** | **15/1 (93.75%)** |
| Caesar original | 0/0 | 1/0 | 100% on one selection | 0/0 |
| Caesar expanded | 0/0 | 0/0 | — | 0/0 |

Against old hard classes, source gains 37 correct selections and seven errors while losing two previously correct selections. Jerome original gains fourteen correct and one error without losing its five old successes; expanded gains seventeen correct and one error. The two Jerome views score the same 913 token positions, with seventeen selected positions in common, so these are not independent recovery counts to add together.

Source PP recall is 12.23%; Jerome recall is 28.79% with original class context and 25.76% with expanded context. High selected precision is compatible with substantial unrecovered structure. The fixed originally unmapped source cohort remains below 90% precision, and no target-token PP selections occur. These predictions identify PP membership, not phrase heads, full dependencies, or exact words.

## Implication and next check

The experiment shows that a training/inference mismatch was partly repairable: the same five known mappings now support a larger selective structural subset in source and one cached author. It does not establish reliable recovery across Latin texts, since Caesar fails, nor does it identify any new known word mappings.

Before adding more model variants, challenge this sparse grammatical subset against type-consistent shuffled-class assignments and simple proximity controls, on the same fixed inputs and positions. This would check whether meaningful class assignments contribute beyond accidental class placement or a nearby-preposition heuristic. Keep all contexts, thresholds, and baseline comparisons frozen, and preserve the Caesar failures. A useful grammatical component need not solve lexical restoration, but its information content must survive appropriate controls.

## Verification

Independent review verifies 37 input hashes, retrains all four classifiers with identical sampled positions to iteration 124, replays thirteen out-of-fold profiles and 73 target probabilities, recomputes five PP vectors, and checks twenty fixed-cohort metric/transition groups. Numerical retraining agrees within 1e-8 in objective and 1e-4 in sampled-row probabilities; frozen-model profile and PP replay uses 1e-12 tolerance. Maximum retrained weight difference is approximately 0.000128, reflecting sparse summation/optimizer numerical sensitivity. Strict target exclusion and reserve separation are checked. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration132/`.
