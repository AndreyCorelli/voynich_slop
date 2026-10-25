# Iteration 129: useful conditional structure with few supplied anchors

**Preserve the low-anchor finding:** with five source-fit-ranked surrounding mappings supplied, opaque inferred hard classes yield **60 correct PP selections / two errors (96.77% precision)** at the pre-existing 0.80 cutoff; the matching unknown-class baseline selects nothing. The fixed originally unmapped cohort contributes **30 correct / two wrong (93.75%)**. With no surrounding mappings, class accuracy falls to chance and useful PP coverage nearly disappears. This is a conditional grammatical result, not blind decipherment or a lexical nucleus.

## Frozen challenge

Rank the 179 non-target anchor types by source-fit word frequency, breaking ties lexically. The six budgets are fixed in advance: 0, 5, 20, 50, 100, and 179. Their ranking uses only existing source-fit word forms, never test outcomes. Each removed anchor loses both its lexical name and supplied grammatical tag, while retaining its opaque occurrence ID.

All sixteen target names/classes remain hidden at every budget. Recompute their probabilities using exactly the iteration-124 model and scalar calibration; no training or recalibration occurs. The original PP model is likewise frozen. Posterior averaging uses the same 32 type-consistent Sobol draws as iteration 127, with the same seed. Compare unknown, hard-inferred, and posterior-mean classes at each budget.

The primary PP cutoff is exactly iteration 128's source-selected 0.4849530056062174, unchanged across budgets and arms. The old 0.80 cutoff is a predeclared secondary setting. Every budget and both cutoffs are reported; no winning test budget or threshold is adopted. Fixed evaluation cohorts remain those of iteration 120, including originally supplied-anchor positions even when their mappings are now removed.

All 770 source-test sentences and 9,956 tokens are reused development data. All budget inputs and class predictions are frozen before PP scoring, and all PP scores before metrics. No new annotations, reserve features, author scoring, sealed lexical evaluation, lexical search, or default change occurs. The full-budget outputs reproduce the previous experiment.

## Class information and supplied-key size

| Supplied non-target types | Visible anchor tokens | Binary classes correct | AUC | Type-mean NLL |
|---|---:|---:|---:|---:|
| 0 | 0 | 8/16 | 0.4844 | 0.741 |
| 5 | 570 (5.73%) | 10/16 | 0.8125 | 0.666 |
| 20 | 1,230 (12.35%) | 10/16 | 0.9688 | 0.632 |
| 50 | 1,633 (16.40%) | 15/16 | 0.9375 | 0.601 |
| 100 | 1,947 (19.56%) | 14/16 | 0.8750 | 0.598 |
| 179 | 2,184 (21.94%) | 14/16 | 0.9219 | 0.574 |

All sixteen targets remain present and supported at every budget. At zero budget, all are classified as conjunctions, so the eight correct classifications do not show discrimination. The five supplied mappings are `ut`, `me`, `cum`, `quod`, and `te`, selected by fit frequency rather than handpicked to repair observed test errors. These are assumed known mappings and are not discovered nuclei.

At five and twenty anchors the six mistakes are `ab`, `de`, `ex`, `in`, `per`, and `sine`. At fifty, only `per` is wrong. Stronger type accuracy at an intermediate budget is descriptive; it does not establish fifty as a generally optimal budget. Context masking can remove misleading signals as well as useful ones, but this experiment does not identify the mechanism of that improvement.

## PP structure at the frozen source-selected cutoff

Each cell gives correct / wrong selections at cutoff 0.484953. Baselines use the same budget and cutoff.

| Supplied types | Unknown classes | Hard inferred classes | Posterior mean |
|---|---:|---:|---:|
| 0 | 0/0 | 0/0 | 3/0 |
| 5 | 0/0 | 144/29 | 30/19 |
| 20 | 0/0 | 144/29 | 85/25 |
| 50 | 11/1 | 440/115 | 140/34 |
| 100 | 42/5 | 476/101 | 205/37 |
| 179 | 45/5 | 500/191 | 271/52 |

At this fixed primary cutoff, posterior precision is 61.22% with five anchors and 77.27% with twenty; the full-budget posterior result remains 83.90%. The three zero-anchor correct selections are too few to establish reliable blind structure, and target catalogue membership, segmentation, opaque grouping, and trained models remain supplied. Posterior averaging is not the strongest integration in every budget.

## Predeclared old-cutoff result worth preserving

At the pre-existing 0.80 cutoff, hard-class results across budgets are:

| Supplied types | Correct / wrong PP | Precision |
|---|---:|---:|
| 0 | 0/0 | — |
| 5 | **60/2** | **96.77%** |
| 20 | 66/3 | 95.65% |
| 50 | 200/20 | 90.91% |
| 100 | 230/14 | 94.26% |
| 179 | 244/59 | 80.53% |

The five-anchor result has 7.72% recall among all 777 positive PP positions; its fixed originally unmapped result is 30/2, versus 0/0 for matching unknown classes. At twenty anchors, the unmapped result is 34/3; at fifty, 147/12; at one hundred, 170/12. The original-other-anchor cohort is fixed and includes positions whose mappings were removed; it must not be described as the currently visible cohort.

These are multiple related development comparisons, not fresh precision guarantees. The reduced budgets do not meet the earlier full-budget 80% coverage requirement, and this challenge does not relax that requirement or adopt a new policy. The small five-anchor subset is nevertheless a real conditional structural signal worth testing as a separate low-coverage decipherment component, consistent with the high-level goal.

## What to check next

Freeze a five-anchor branch motivated by this source finding and check it on the already cached Jerome and Caesar contexts, reporting all original scored positions and the same originally-unmapped cohorts. Keep the fit-ranked five mappings, model, and old 0.80 cutoff unchanged; do not choose budgets per author. This would test whether a modest known-key requirement can support reproducible grammatical information. It would remain development replication, and the supplied function-word catalogue and known mappings would still need a practical discovery mechanism before Voynich application.

## Verification

The audit independently reconstructs fit-frequency ranking, all masking operations and class probabilities, all complete-assignment PP vectors, posterior means, and fixed-cohort confusion/transition counts, and checks full-budget reproduction and reserve exclusion. Nine focused tests pass. Detailed audit counts and frozen artifacts are in `experiments/results/grammar-restoration/iteration129/`.
