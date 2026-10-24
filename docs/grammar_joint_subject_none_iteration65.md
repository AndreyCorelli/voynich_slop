# Iteration 65: joint subject selection with NONE

**Encouraging as a precision/F1 policy, not as increased grammatical coverage.** Soft competition between subjects assigned to the same finite carrier raises full-source exact-unit F1 from **56.86% to 58.89%** and selected-sentence F1 from **64.85% to 66.87%**. The primary policy improves every outer fold and beats a finely calibrated global NONE threshold. It removes 427 false units but also loses 72 correct units net. Coordination is a particular weakness, so keep this experimental rather than changing the default.

This satisfies the requested run/analyze/continue decision with an encouraging result. The subsequent work challenged this result with matched threshold and no-rerouting controls, rather than moving to the unrelated predicate-complement audit. That audit remains proposed.

## Frozen experiment

The source, five fit/calibration/test sentence partitions, original morphology models, broad subject–carrier lattice, iteration-56 carrier-score models and iteration-57 head/type models remain fixed. The task has 3,365 gold units, including 519 in the 304 selected sentences, across the same 4,070 source sentences. No training, new lexical features, gold morphology, dependency labels, or gold subject/carrier anchors are added at inference. The single ambiguous-carrier frame is excluded from competition and expanded-task evaluation.

Unlike iteration 64, subject assignments are optional. For each sentence maximize:

`sum(selected edge score − frozen NONE cutoff) − λ × sum_carriers(max(0, attached subjects − 1))`.

Each subject can select one compatible carrier or NONE. Several subjects can share a carrier when their utilities justify the penalty; there is no hard one-subject cap. Positive-utility alternative carriers can replace the original best carrier. Original tied-best frames remain abstained, preserving the baseline convention. Nonpositive edges cannot improve on NONE and are omitted.

The signed-incidence network LP has integral vertices with these bounds; every solve checks integrality. An emitted edge must occur in every optimum: if excluding it preserves the optimal objective within 1e-8, the subject abstains. No global-ambiguity abstentions occurred in the saved test solves. Zero penalty reproduces the original endpoint and complete-unit baseline for all 17,674 unambiguous frames.

The old calibrated NONE cutoffs remain −1 or −0.5 by fold. Only λ is calibrated, on the fixed grid 0, 0.25, 0.5, 1, 2, 4, 8. The predeclared primary policy maximizes carrier F1; the secondary maximizes exact-unit F1. Ties prefer fewer predictions, then smaller λ. Primary penalties are 2, 4, 1, 1, 2 across folds; secondary penalties are 2, 4, 8, 4, 2. The secondary hits the grid boundary in one fold; the grid was not extended after evaluation. Head/type predictions use the original frozen model at whichever carrier is selected.

## Main results

| Policy | Full-source correct / false units | Full-source exact-unit F1 | Selected correct / false units | Selected F1 |
|---|---:|---:|---:|---:|
| Original independent baseline | 2,098 / 1,917 | 56.86% | 346 / 202 | 64.85% |
| Joint, carrier calibration — primary | 2,026 / 1,490 | 58.89% | 337 / 152 | 66.87% |
| Joint, unit calibration — secondary | 2,005 / 1,432 | 58.95% | 335 / 142 | 67.27% |

Primary full-source precision rises from 52.25% to 57.62%; recall falls from 62.35% to 60.21%. Carrier-edge F1 rises from 67.13% to 69.52%, with selected carrier F1 70.85%→72.82%. The unit scorer itself is unchanged; this experiment does not establish better head localization conditional on a correct endpoint.

All five full-source fold F1 values improve under the primary policy: 58.05→59.69, 55.98→57.72, 58.71→60.84, 56.44→58.07, 55.06→58.04%. Full-source Cicero improves 57.18→59.29%; Palladius only 49.69→50.00%. Selected Cicero improves 65.98→68.11%, Palladius 59.57→61.02%. The secondary regresses on full-source Palladius (49.15%), another reason to keep the predeclared primary policy as the main conclusion.

| Full-source gold type | Original correct / F1 | Primary correct / F1 |
|---|---:|---:|
| Direct | 1,690 / 63.51% | 1,655 / 65.67% |
| Copular | 259 / 37.48% | 233 / 38.04% |
| Auxiliary | 149 / 44.08% | 138 / 44.81% |

Per-type F1 improves, but correct recovery decreases in every type. Selected copular recovery remains 7/32 and auxiliary recovery 14/17 under the primary policy. This is a better precision/recall operating policy, not restoration of more correct structures.

## Is this merely a global threshold adjustment?

After viewing the main results, a separately frozen control recalibrated a global NONE threshold over every distinct calibration best-edge margin, plus extremes and the original cutoff. Both carrier-F1 and unit-F1 calibration were allowed, with the original tie-abstention rule and frozen head model. A prefix-sum sweep was checked against actual predicted edge/unit sets at the chosen thresholds. No test scores selected thresholds.

| Policy | Full-source F1 | Selected F1 |
|---|---:|---:|
| Exact global threshold, carrier calibration | 56.77% | 64.28% |
| Exact global threshold, unit calibration | 57.46% | 64.60% |
| Joint primary | 58.89% | 66.87% |

The gain survives a substantially finer threshold search. Because this control was designed after the primary result, it is a diagnostic challenge, not independent confirmation.

A second separately frozen ablation retained each subject's original best carrier and allowed competition to drop assignments but not reroute them. It used the same penalty grid and calibration protocol. Carrier-calibrated drop-only achieves 58.73% full-source and 66.94% selected F1, recovering 1,974 units overall and 329 selected. Thus most of the F1 benefit survives without alternative-carrier search. The full decoder retains 52 more correct units overall than this separately calibrated control, with nearly the same F1; do not attribute the entire improvement to rerouting.

## What changed, and what still fails?

The primary decoder drops 499 assignments, of which 87 were exact. It reroutes 118, gaining 39 exact units but losing 24 previously exact ones. Across both mechanisms it loses 111 exact predictions and gains 39, for net −72. It emits 499 fewer predictions in total.

The coordination cohort is concerning: among 122 gold units whose subjects belong to gold conjunction components, exact recovery falls from 48 to 39 (secondary: 34). The eight units in the four multiple-gold-subject carrier groups go from one exact to two. A soft penalty permits exceptions mathematically, but it does not reliably recognize coordination. Source annotations define these diagnostic cohorts; they are not inference features.

A post hoc author-stratified sentence bootstrap, with 2,000 resamples and fixed policies, puts the primary-minus-original full-source F1 difference at approximately +1.34 to +2.75 percentage points (95% percentile interval); against the unit-calibrated global threshold it is +0.63 to +2.20 points. These intervals omit training/calibration uncertainty and reuse development data. They are not fresh validation or a guarantee of transfer.

## Reproduction and status

Code: `src/voynich_smt/joint_subject_none.py`. The main runner/audit are `benchmarks.grammar_joint_subject_none_iteration65` and `_audit`; threshold-control and drop-only runners each have their own audit. `benchmarks.grammar_joint_subject_none_iteration65_analysis` produces post hoc error attribution, author/fold checks, coordination cohorts and bootstrap summaries.

Artifacts are in `experiments/results/grammar-restoration/iteration65/`, with `threshold-control/` and `drop-only-control/` subdirectories. Separate design, lattice/policy and prediction freezes preserve ordering and disclose the post-result controls. The main replay reconstructs 35,348 calibration/test scored frames and replays 53,022 test assignments; each control audit replays 35,348 test assignments and all its calibration policies. Prior fields and baseline predictions are preserved. **111 relevant tests pass**, including exhaustive small-instance checks of the network optimization and global-threshold sweep. All older frozen input hashes remain unchanged.

Keep carrier-calibrated competition as an experimental precision/F1 option; retain the independent baseline for coverage and comparisons. The next targeted proposal is to preserve coordination using observable evidence, with the same global-threshold/drop-only controls and explicit coverage accounting. Gold conjunctions must not become an inference shortcut. Fresh confirmation remains necessary before any default change; neither small author-specific gains nor bootstrap intervals substitute for it.

The 200-sentence reserve remains unscored, no prior target queries were scored, and source POS/readable words remain available upstream. This is not evidence of plaintext or Voynich grammar recovery.
