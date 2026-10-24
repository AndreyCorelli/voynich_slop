# Iteration 68: conjunct evidence confined to carrier competition

**A useful partial improvement over iteration 65.** The predeclared contextual treatment raises exact-unit F1 from **58.89% to 59.41%** overall and **66.87% to 67.53%** on selected sentences. It recovers **10 more correct units with 37 fewer false units**. Coordination recovery rises from **39 to 43/122**, meeting the development checks while still falling short of the original independent baseline's 48/122.

The route matters: iteration 66 found an effective gold-conj oracle; iteration 67's global learned penalty partially recovered coordination but lost coverage and selected F1. This iteration restricts that same learned evidence to actual contests. All stages and the failed global treatment remain preserved. This is adaptive development on reused data, not independent confirmation.

## Frozen treatment

Reuse both iteration-67 classifiers exactly: POS-only and POS-context nominal-conjunct probabilities, fitted on the outer fit partitions. No probe, carrier model or head/type model is refitted. The same 4,070 source sentences, 3,365 gold units/519 selected, candidate lattices, source POS, iteration-65 primary penalties/NONE cutoffs and all target labels remain fixed.

For each sentence, find original independently accepted unique-best subject/carrier assignments at the fixed NONE cutoff. A carrier is contested if at least two subjects prefer it. Within each contest, take the greatest `log P(non-conj)` among those subjects as the reference. Add to an edge targeting that carrier:

`weight × min(0, subject log P(non-conj) − contest reference)`.

Thus the most plausible phrase head under the probe is not penalized, other contenders receive only relative penalties, and no score is increased. Uncontested carrier edges receive no new penalty. Joint rerouting can still indirectly affect their final assignments; this is a score-locality guarantee, not an output-invariance guarantee. Original tied-best/below-cutoff subject eligibility remains frozen so candidate-specific adjustments cannot activate previously excluded tied frames.

There is no gold coordination, dependency, morphology or word identity in this added inference stage. Source words remain available upstream in the old morphology system. No conjunct targets are projected and no target is relabeled.

For each frozen classifier, choose only the evidence weight on calibration carrier F1, from 0, 0.5, 1, 2, 4, 8; ties prefer fewer predictions and smaller weight. Zero reproduces competition65. Context is the predeclared primary; its weights are 2, 0, 4, 8, 2 by fold. POS-only weights are 1, 0.5, 8, 8, 2. Grid boundaries were not extended after evaluation.

## Results and controls

| Policy | Source correct / false units | Source F1 | Selected correct / false units | Selected F1 | Coordination exact /122 |
|---|---:|---:|---:|---:|---:|
| Original independent baseline | 2,098 / 1,917 | 56.86% | 346 / 202 | 64.85% | 48 |
| Competition65 | 2,026 / 1,490 | 58.89% | 337 / 152 | 66.87% | 39 |
| Global context evidence67 | 2,000 / 1,406 | 59.08% | 328 / 146 | 66.06% | 44 |
| Relative contested POS-only | 2,035 / 1,461 | 59.32% | 343 / 146 | 68.06% | 39 |
| Relative contested context — primary | 2,036 / 1,453 | 59.41% | 339 / 146 | 67.53% | 43 |
| Gold-conj exclusion66 — oracle only | 2,045 / 1,380 | 60.24% | 337 / 146 | 67.27% | 48 |

The primary meets the specified guards relative to competition65: more coordinated-subject recovery, nondecreasing total correct units and overall F1, and no selected-F1 regression. Unlike the global addition, it does not purchase its gain by losing more correct units overall. It still recovers 62 fewer correct units than the original independent baseline; the broader precision/coverage tradeoff remains.

The POS-only control is strong: it gives almost the same full-source F1 and better selected F1. Context is the part associated with coordination recovery, not an established universal F1 advantage over POS alone. Do not choose the POS control or contextual model as a default from these development comparisons.

The old iteration-65 exact global-threshold controls achieve 56.77%/57.46% source F1 and 64.28%/64.60% selected F1; its carrier-calibrated drop-only control gives 58.73%/66.94%. Both relative variants exceed those recorded operating points. These older controls are references, not newly recalibrated models with the added role features. POS-only relative evidence is the direct feature-ablation control here.

| Gold type | Competition65 correct / F1 | Relative context correct / F1 |
|---|---:|---:|
| Direct | 1,655 / 65.67% | 1,663 / 66.14% |
| Copular | 233 / 38.04% | 232 / 38.16% |
| Auxiliary | 138 / 44.81% | 141 / 46.31% |

The net gain is primarily direct/auxiliary recovery; copular correct recovery declines by one despite its tiny F1 increase. Full-source Cicero F1 rises 59.29→59.81%, Palladius 50.00→50.51%; Palladius has only 153 gold units, so this is a small change. The POS control does better on Palladius (52.53%).

## Coordination and remaining uncertainty

Relative context restores five of the nine specifically inspected competition65 losses, but creates one new coordination loss (sentence86384, subject11), for net +4. Among all frames, 95 unit predictions change: 19 exact units are gained and nine lost. The original cases, new loss, source probabilities and rival probabilities are recorded in `posthoc-analysis.json`; none was handled with a word-specific exception.

A post hoc author-stratified sentence bootstrap with 2,000 resamples gives a conditional 95% percentile interval of approximately +0.18 to +0.87 percentage points for source F1 versus competition65 and +0.13 to +1.51 for selected F1. Versus the POS control the intervals include zero (source −0.40 to +0.55 points). These intervals condition on frozen policies and omit adaptive model-selection/training uncertainty; they do not establish fresh generalization.

The findings support localizing role evidence to competing assignments and protecting one plausible phrase head, rather than globally lowering nominal eligibility. They do not show complete preservation of coordination or resolve copular localization. The next targeted audit is the four unrecovered original cases and the new loss, including whether zero calibration weights or incorrect root/rival role ranking explain them. Any fresh evaluation should compare a short frozen list including65 and both68 variants, not a test-selected winner.

## Verification and status

Artifacts are in `experiments/results/grammar-restoration/iteration68/`, with design, policy and prediction freezes. The audit verifies exact reuse of all ten probe models, replays ten calibration policies, 35,348 test assignments and 17,674 probe records, preserves all older fields and recomputes evaluation. The earlier oracle66 and global67 runs have their own independent audits. **120 relevant tests pass**, including soft-evidence gradients, annotation independence, network optimization, protected contest references, score locality, no boosts, and preservation of original tie abstention.

Keep iteration65 preserved as the positive reference and68 as a promising experimental follow-up; no default changes. The 200-sentence reserve remains unscored, no prior target queries were scored, and all earlier frozen manifests remain unchanged. These are source-development grammar diagnostics, not plaintext or Voynich restoration results.
