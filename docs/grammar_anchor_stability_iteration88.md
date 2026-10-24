# Anchor-sensitivity abstention — iteration 88

**Outcome: the frozen coverage guard rejects stability filtering, but a smaller robust PP-membership subset is worth preserving.** Both source-selected policies remain the original baseline. The strict, predeclared stability rule yields about 95% source precision with 195 anchors under clean and in/et-swapped inputs, at substantial coverage cost. This is a secondary diagnostic, not an adopted policy or independent confirmation.

## Frozen experiment

Keep iteration85 models, inventories and PP thresholds (20 anchors: 0.81; 195: 0.80). Uncertain anchor identities are the fit-frequency top five from iteration87: et, in, ut, ad, cum. For every input, hide each displayed anchor identity individually, preserving underlying opaque equality IDs and recomputing context and pooled type evidence across the split. No reference POS, head, relation or Case is used by the score computation. A baseline-selected token survives only if its minimum score over the five deletions is at least its frozen threshold minus slack.

Predeclared slack grid: 0, 0.05, 0.1, 0.2, 0.4, 1; 1 reproduces the baseline. Evaluate the same six source-chosen perturbations as iteration87, including missing anchors, in/ad swaps and in/et swaps. On source calibration only, maximize worst-pattern precision, breaking ties by total TP then larger slack. Eligibility requires clean TP retention of at least 50%, clean precision at least 90%, at least 20 clean predictions, and at least 10 predictions in every pattern. Both budget policies are frozen before evaluation. These clean-data guards do not guarantee 90% precision under errors.

No retraining, new annotations, reserve or sealed-test scoring. Cached Jerome/Caesar sets and the source test are reused development evaluations. The same stress patterns were already explored in iteration87, so this tests a response to known failures. Anchor mappings are still supplied; the task is partial PP-governed membership, not exact attachment, full grammatical structure, or lexical nucleus recovery.

## Source calibration

| Anchors | Slack | Clean correct / wrong | Clean TP retained | in/et-swap correct / wrong | Worst-pattern precision | Eligible |
|---|---:|---:|---:|---:|---:|---|
| 20 | 0.0 | 50 / 3 | 21.19% | 50 / 3 | 94.23% | no |
| 20 | 0.05 | 75 / 5 | 31.78% | 71 / 5 | 93.42% | no |
| 20 | 0.1 | 79 / 6 | 33.47% | 77 / 6 | 92.59% | no |
| 20 | 0.2 | 80 / 6 | 33.90% | 79 / 7 | 91.86% | no |
| 20 | 0.4 | 80 / 6 | 33.90% | 79 / 7 | 91.86% | no |
| 20 | 1.0 | 236 / 26 | 100.00% | 179 / 75 | 70.47% | yes |
| 195 | 0.0 | 172 / 6 | 37.15% | 169 / 6 | 96.13% | no |
| 195 | 0.05 | 193 / 9 | 41.68% | 191 / 10 | 95.02% | no |
| 195 | 0.1 | 196 / 9 | 42.33% | 197 / 10 | 95.17% | no |
| 195 | 0.2 | 198 / 9 | 42.76% | 199 / 10 | 95.22% | no |
| 195 | 0.4 | 198 / 9 | 42.76% | 199 / 10 | 95.22% | no |
| 195 | 1.0 | 463 / 28 | 100.00% | 321 / 173 | 64.98% | yes |

Every nonbaseline candidate fails the clean 50% retention requirement. Accordingly, the selected slack is 1 for both budgets; their test/transfer results exactly reproduce iteration87. No guard was relaxed to select a better-looking evaluation result.

## Secondary tradeoff report

After seeing the calibration coverage failure, a separate reporting freeze declared a descriptive evaluation of every predeclared slack on every dataset/pattern; it changes no selected policy. The full grid is stored as evaluation-tradeoff-grid.json. The strict endpoint below is one fixed endpoint of that grid, not a target-selected threshold.

| Dataset | Anchors | Clean baseline correct / wrong | Clean strict correct / wrong | Clean strict recall | Swapped baseline correct / wrong | Swapped strict correct / wrong | Swapped strict precision |
|---|---:|---:|---:|---:|---:|---:|---:|
| source | 20 | 191 / 19 | 41 / 7 | 5.28% | 151 / 90 | 43 / 5 | 89.58% |
| source | 195 | 357 / 33 | 133 / 7 | 17.12% | 252 / 186 | 131 / 7 | 94.93% |
| Jerome | 20 | 21 / 0 | 6 / 0 | 9.09% | 11 / 30 | 6 / 0 | 100.00% |
| Jerome | 195 | 40 / 1 | 16 / 1 | 24.24% | 22 / 76 | 15 / 1 | 93.75% |
| Caesar | 20 | 42 / 3 | 4 / 0 | 2.52% | 25 / 3 | 4 / 0 | 100.00% |
| Caesar | 195 | 72 / 4 | 16 / 0 | 10.06% | 37 / 12 | 15 / 0 | 100.00% |

With 195 anchors, strict stability retains 37.25% of clean source correct assignments, 40% Jerome, and 22.22% Caesar. Clean precision is 95.00%, 94.12%, and 100% observed; swapped precision is 94.93%, 93.75%, and 100% observed. These small transfer counts do not establish population precision guarantees. Source clean PP recall is only 17.12%, versus 45.95% baseline.

The result also holds on hidden content positions: 195-anchor strict clean source105correct/7wrong, Jerome13/1, Caesar15/0; swapped source103/7, Jerome13/1, Caesar14/0. Thus the subset is not exclusively visible-anchor tokens. The 20-anchor endpoint is weaker: clean source41/7 (85.42% precision), so stability alone does not ensure high precision.

## Control and limits

The frozen nearest-left source-F1 control is reported for every input in evaluation.json and in the full tradeoff artifact. Its operating point differs from the selective stability policy; this experiment does not establish a matched-coverage advantage over a similarly calibrated proximity filter. A deletion test can preferentially remove genuine PP membership supported by the governing preposition itself. Surviving evidence may come from other supplied anchors or type pooling; stability is not evidence that the mappings are correct. It protects only against the declared influential identities and tested errors.

## Decision and next check

Do not replace the frozen policy under the declared 50% coverage requirement. Preserve the 195-anchor strict subset as an experimental partial grammatical finding, together with its coverage limits and the full grid. Next test type-consistent anchor dropout and mistaken-tag augmentation during fit-only training, retaining clean and corrupted source calibration controls. This targets coverage loss rather than removing the requirement after seeing evaluation results. Keep the frozen model and strict-abstention endpoint as controls; no cipher-side restoration claim yet.

Validation: 48 calibration/evaluation conditions replayed, including 240 deletion inferences; source-calibrated policy selection replayed; original scores reproduce iteration87 despite rekeying; abstention never introduces a new prediction; 1,948 prior input hashes verified; 85 focused tests passed. Secondary full-grid and hidden-position diagnostics are also audited. Artifacts: experiments/results/grammar-restoration/iteration88/.
