# Anchor-error robustness — iteration 87

**Finding: missing anchors mostly cost recall; incorrect anchor classes can create confident false grammatical assignments.** Preserve the positive anchor-conditional PP membership finding from iterations 85–86, but do not treat its precision as robust to incorrect mappings.

Models, supplied anchor inventories and source-calibrated thresholds remain frozen: 20 anchors at 0.81, 195 at 0.80. Six patterns were frozen before scoring, selected using only fit-frequency among the common 20 anchors: correct; remove et; remove et/in/ut/ad/cum; remove in; swap in/ad (same ADP tag); swap in/et (ADP/CCONJ). Errors apply consistently to every occurrence of a type. Opaque equality IDs are preserved, including under swaps. No retraining, recalibration, target-driven pattern selection, new annotations, reserve evaluation or lexical search.

All source-test tokens and the same cached 100 Jerome / 100 Caesar sentences from iteration 86 are evaluated. These are reused development data, not fresh confirmation. PP membership uses the existing case-dependent/inherited-node reference definition; it is not exact attachment, a complete phrase span, or Case restoration.

| Set | Anchors | Perturbation | Correct / wrong | Precision | Recall | New false positives | Lost correct |
|---|---:|---|---:|---:|---:|---:|---:|
| source | 20 | correct | 191 / 19 | 90.95% | 24.58% | 0 | 0 |
| source | 20 | missing_top1 | 179 / 16 | 91.79% | 23.04% | 0 | 15 |
| source | 20 | missing_top5 | 42 / 5 | 89.36% | 5.41% | 0 | 151 |
| source | 20 | missing_top_adp | 131 / 18 | 87.92% | 16.86% | 0 | 60 |
| source | 20 | swap_adps | 216 / 34 | 86.40% | 27.80% | 23 | 47 |
| source | 20 | swap_adp_conjunction | 151 / 90 | 62.66% | 19.43% | 75 | 60 |
| source | 195 | correct | 357 / 33 | 91.54% | 45.95% | 0 | 0 |
| source | 195 | missing_top1 | 349 / 30 | 92.08% | 44.92% | 0 | 10 |
| source | 195 | missing_top5 | 130 / 7 | 94.89% | 16.73% | 0 | 229 |
| source | 195 | missing_top_adp | 237 / 20 | 92.22% | 30.50% | 0 | 120 |
| source | 195 | swap_adps | 363 / 35 | 91.21% | 46.72% | 2 | 6 |
| source | 195 | swap_adp_conjunction | 252 / 186 | 57.53% | 32.43% | 167 | 121 |
| Jerome | 20 | correct | 21 / 0 | 100.00% | 31.82% | 0 | 0 |
| Jerome | 20 | missing_top1 | 17 / 0 | 100.00% | 25.76% | 0 | 4 |
| Jerome | 20 | missing_top5 | 7 / 0 | 100.00% | 10.61% | 0 | 14 |
| Jerome | 20 | missing_top_adp | 11 / 0 | 100.00% | 16.67% | 0 | 10 |
| Jerome | 20 | swap_adps | 24 / 0 | 100.00% | 36.36% | 0 | 2 |
| Jerome | 20 | swap_adp_conjunction | 11 / 30 | 26.83% | 16.67% | 30 | 11 |
| Jerome | 195 | correct | 40 / 1 | 97.56% | 60.61% | 0 | 0 |
| Jerome | 195 | missing_top1 | 38 / 1 | 97.44% | 57.58% | 0 | 2 |
| Jerome | 195 | missing_top5 | 15 / 1 | 93.75% | 22.73% | 0 | 25 |
| Jerome | 195 | missing_top_adp | 22 / 1 | 95.65% | 33.33% | 0 | 18 |
| Jerome | 195 | swap_adps | 40 / 1 | 97.56% | 60.61% | 0 | 0 |
| Jerome | 195 | swap_adp_conjunction | 22 / 76 | 22.45% | 33.33% | 75 | 18 |
| Caesar | 20 | correct | 42 / 3 | 93.33% | 26.42% | 0 | 0 |
| Caesar | 20 | missing_top1 | 42 / 3 | 93.33% | 26.42% | 0 | 1 |
| Caesar | 20 | missing_top5 | 4 / 0 | 100.00% | 2.52% | 0 | 38 |
| Caesar | 20 | missing_top_adp | 21 / 2 | 91.30% | 13.21% | 0 | 21 |
| Caesar | 20 | swap_adps | 42 / 5 | 89.36% | 26.42% | 4 | 12 |
| Caesar | 20 | swap_adp_conjunction | 25 / 3 | 89.29% | 15.72% | 1 | 20 |
| Caesar | 195 | correct | 72 / 4 | 94.74% | 45.28% | 0 | 0 |
| Caesar | 195 | missing_top1 | 73 / 4 | 94.81% | 45.91% | 0 | 0 |
| Caesar | 195 | missing_top5 | 16 / 0 | 100.00% | 10.06% | 0 | 57 |
| Caesar | 195 | missing_top_adp | 32 / 1 | 96.97% | 20.13% | 0 | 40 |
| Caesar | 195 | swap_adps | 70 / 4 | 94.59% | 44.03% | 0 | 3 |
| Caesar | 195 | swap_adp_conjunction | 37 / 12 | 75.51% | 23.27% | 11 | 37 |

Every missing-anchor condition introduces zero new false positives relative to its correct-anchor baseline. Precision can nevertheless fall when correct assignments disappear disproportionately: removing in gives 87.92% source precision with 20 anchors. Removing five common anchors reduces 195-anchor recall from 45.95% to 16.73% source, 60.61% to 22.73% Jerome, and 45.28% to 10.06% Caesar. These results concern the tested removals only; missing anchors are not generally proven harmless.

Cross-class in/et errors are much more damaging: with 195 anchors, source gains 167 new false positives and loses 121 correct assignments; Jerome gains 75 false positives and loses 18 correct; Caesar gains 11 false positives and loses 37 correct. Precision falls to 57.53%, 22.45%, and 75.51%, respectively. One swapped pair affects different token counts by corpus (460 source, 111 Jerome, 63 Caesar), so these are frequency-dependent stress cases, not a universal error-rate estimate.

Same-class in/ad swaps are comparatively mild with 195 anchors (source 91.21%, Jerome 97.56%, Caesar 94.59% precision), but degrade source precision to 86.40% at 20 anchors. Readable identity matters beyond the supplied POS class, and a larger inventory sometimes cushions errors.

## Frozen proximity control

Nearest-left uses its original source-F1 threshold, so its operating point differs from the selective learned policy. It remains a required control, not a matched-precision comparison. Full metrics are preserved in each evaluation artifact.

| Set | Anchors | Correct-anchor nearest F1 | in/et-swap nearest F1 | Correct-anchor model F1 | in/et-swap model F1 |
|---|---:|---:|---:|---:|---:|
| source | 20 | 65.21% | 43.01% | 65.41% | 43.87% |
| source | 195 | 69.03% | 47.44% | 73.68% | 50.81% |
| Jerome | 20 | 81.03% | 31.02% | 81.03% | 31.52% |
| Jerome | 195 | 79.66% | 30.69% | 81.36% | 32.98% |
| Caesar | 20 | 67.42% | 45.19% | 67.42% | 45.57% |
| Caesar | 195 | 73.12% | 52.76% | 76.98% | 54.98% |

## Decision and next experiment

Keep the frozen policies as conditional PP-membership candidates. Anchor verification or uncertainty handling is now a prerequisite for cipher-side use. Next test a source-calibrated stability/abstention rule: hide each influential anchor type in turn and retain assignments only when their support survives the specified uncertainty. First measure the clean-data coverage cost and whether this rejects false positives under the already declared errors. Freeze the rule on source calibration before transfer; compare simple proximity, and do not assume stability proves an anchor correct. This is proposed, not yet tested.

Validation: all 36 conditions replayed, correct-anchor scores reproduce iterations 85–86 despite rekeying, public type IDs remain unchanged under perturbation, frozen thresholds checked, 1,794 prior input hashes verified, and 83 focused tests passed. The reserve and sealed lexical final test remain unscored.

Artifacts: `experiments/results/grammar-restoration/iteration87/`; design and prediction freezes precede evaluation. The proposal snapshot preserves the pre-experiment tracker.
