# Anchor-error rehearsal — iteration 89

**Finding: rehearsing known anchor errors sharply reduces their false positives, but the source-selected 90% precision policy fails on the source test.** Preserve this as a conditional robustness gain; do not adopt it as a validated high-precision restoration policy.

## Frozen change

Focus on the 195-anchor setting because iteration88 found its smaller robust subset promising. Keep the source85 POS models, supplied inventory, public features, hidden equality IDs, and training labels unchanged. Retrain only the three eight-class PP/head-category models on three equally weighted source-fit views: clean inputs, et/in/ut/ad/cum hidden, and in/et swapped. Every change applies consistently to every occurrence of a type. This is rehearsal of known errors, not randomly sampled corruption or a test of unseen-error robustness.

For each view separately, obtain POS probabilities using the frozen model that excluded the sentence fold, apply the displayed-anchor tag override, and pool only within that held-out POS fold. Never pool across clean and corrupted views. Each PP model excludes every view of its held-out sentence fold. The fit objective, regularization and optimizer remain unchanged. No target words, annotations, morphology or reference dependencies enter inference features.

Calibrate original and augmented models identically on all six iteration87 perturbations. The primary robust policy scans thresholds 0..1 in steps of0.01 and requires empirical precision at least90%, ten predictions and ten types in EVERY pattern, plus at least232 clean TP (half the original source-calibration baseline463, rounded up). Select maximal summed TP, tie higher threshold. No qualifying threshold means no robust policy. Also preserve a clean-only empirical90 policy and the unchanged0.80 score cutoff as secondary diagnostics. All policies were frozen before source-test or author evaluation.

The reserve and sealed lexical test remain unscored. No new annotations or raw target queries. The source and cached Jerome/Caesar sets are reused development data; this is PP-governed membership, not exact attachment, Case values, discovered anchor mappings or lexical nuclei.

## Calibration

The original model has no qualifying robust threshold. The augmented model qualifies at0.71: clean369correct/39wrong (90.44% precision); swapped363/39 (90.30%). All six pattern precisions lie between90.18% and90.75%. Clean TP retention is79.70% of the original463 calibration baseline. Both models select0.70 under clean-only calibration. The robust criterion is empirical and has no multiple-threshold or dependence correction; it is not a precision guarantee.

## Source-selected policy outcome

| Dataset | Pattern | Augmented correct / wrong at0.71 | Precision | Recall |
|---|---|---:|---:|---:|
| source | correct | 307 / 42 | 87.97% | 39.51% |
| source | missing_top1 | 310 / 42 | 88.07% | 39.90% |
| source | missing_top5 | 221 / 31 | 87.70% | 28.44% |
| source | missing_top_adp | 305 / 41 | 88.15% | 39.25% |
| source | swap_adps | 364 / 54 | 87.08% | 46.85% |
| source | swap_adp_conjunction | 307 / 42 | 87.97% | 39.51% |
| Jerome | correct | 29 / 2 | 93.55% | 43.94% |
| Jerome | missing_top1 | 28 / 2 | 93.33% | 42.42% |
| Jerome | missing_top5 | 23 / 2 | 92.00% | 34.85% |
| Jerome | missing_top_adp | 28 / 2 | 93.33% | 42.42% |
| Jerome | swap_adps | 41 / 4 | 91.11% | 62.12% |
| Jerome | swap_adp_conjunction | 29 / 2 | 93.55% | 43.94% |
| Caesar | correct | 62 / 4 | 93.94% | 38.99% |
| Caesar | missing_top1 | 63 / 4 | 94.03% | 39.62% |
| Caesar | missing_top5 | 43 / 2 | 95.56% | 27.04% |
| Caesar | missing_top_adp | 61 / 4 | 93.85% | 38.36% |
| Caesar | swap_adps | 80 / 7 | 91.95% | 50.31% |
| Caesar | swap_adp_conjunction | 62 / 4 | 93.94% | 38.99% |

Primary source-test clean307/42 and swapped307/42 both have87.97% precision, below90%; other source patterns range87.08%–88.15%. The intended source precision condition therefore fails. Transfer is encouraging but small: clean and swapped Jerome29/2 (93.55% precision/43.94% recall), Caesar62/4 (93.94%/38.99%). These do not override the source failure or establish general robustness.

## Unchanged0.80 cutoff and strict-filter control

The unchanged cutoff is a predeclared secondary diagnostic, not the selected robust policy or a recalibrated conservative guarantee for the new model. It preserves high observed precision while reducing coverage.

| Dataset | Pattern | Original at0.80 correct / wrong | Augmented at0.80 correct / wrong | Augmented precision | Augmented recall | Strict88 correct / wrong |
|---|---|---:|---:|---:|---:|---:|
| source | correct | 357 / 33 | 173 / 17 | 91.05% | 22.27% | 133 / 7 |
| source | missing_top1 | 349 / 30 | 166 / 14 | 92.22% | 21.36% | 132 / 7 |
| source | missing_top5 | 130 / 7 | 95 / 7 | 93.14% | 12.23% | 130 / 7 |
| source | missing_top_adp | 237 / 20 | 169 / 17 | 90.86% | 21.75% | 129 / 7 |
| source | swap_adps | 363 / 35 | 209 / 21 | 90.87% | 26.90% | 132 / 7 |
| source | swap_adp_conjunction | 252 / 186 | 159 / 16 | 90.86% | 20.46% | 131 / 7 |
| Jerome | correct | 40 / 1 | 15 / 0 | 100.00% | 22.73% | 16 / 1 |
| Jerome | missing_top1 | 38 / 1 | 16 / 0 | 100.00% | 24.24% | 15 / 1 |
| Jerome | missing_top5 | 15 / 1 | 12 / 0 | 100.00% | 18.18% | 15 / 1 |
| Jerome | missing_top_adp | 22 / 1 | 15 / 0 | 100.00% | 22.73% | 16 / 1 |
| Jerome | swap_adps | 40 / 1 | 24 / 0 | 100.00% | 36.36% | 16 / 1 |
| Jerome | swap_adp_conjunction | 22 / 76 | 16 / 0 | 100.00% | 24.24% | 15 / 1 |
| Caesar | correct | 72 / 4 | 27 / 1 | 96.43% | 16.98% | 16 / 0 |
| Caesar | missing_top1 | 73 / 4 | 26 / 1 | 96.30% | 16.35% | 16 / 0 |
| Caesar | missing_top5 | 16 / 0 | 15 / 0 | 100.00% | 9.43% | 16 / 0 |
| Caesar | missing_top_adp | 32 / 1 | 27 / 1 | 96.43% | 16.98% | 15 / 0 |
| Caesar | swap_adps | 70 / 4 | 41 / 2 | 95.35% | 25.79% | 16 / 0 |
| Caesar | swap_adp_conjunction | 37 / 12 | 26 / 1 | 96.30% | 16.35% | 15 / 0 |

Under in/et swapping, source false positives fall186→16, Jerome76→0, Caesar12→1. Relative to the strict stability endpoint, source swapped correct assignments rise131→159 while wrong assignments rise7→16; this is a precision/coverage tradeoff. Clean source TP is173versus357original (48.46% retained), Jerome15versus40 (37.50%), Caesar27versus72 (37.50%). It does not solve the original coverage requirement at this cutoff. The augmentation response could partly suppress reliance on the specially rehearsed identities.

The frozen nearest-left F1 control is included for every pattern in evaluation.json; it is unchanged by the new model. This experiment has not established an advantage over a similarly calibrated or retrained proximity-only model at matched precision/coverage. Full source-calibration threshold curves, clean-only policies and every evaluation pattern are preserved.

## Decision and next bottleneck

Preserve the reduction in false confidence on rehearsed errors, together with the calibration failure and clean-coverage cost. Keep the original policy and strict stability endpoint as controls; no default replacement. Before treating augmentation as a general algorithm addition, challenge the frozen model with source-frequency-chosen anchor swaps absent from training, without refitting or changing thresholds. This separates broader robustness from a response specific to in/et. Only after that should training-error distributions or conservative calibration be expanded.

Validation: all training objectives reconstructed from the view-separated fold-local features and pooled probabilities; frozen POS weights verified; all calibration/transfer predictions and policies replayed; 2,097 prior input hashes verified; 86 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration89/.
