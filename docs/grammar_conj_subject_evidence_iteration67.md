# Iteration 67: learned conjunct-role evidence

The first observable treatment partially preserves coordination but **fails the acceptance checks**. POS-context evidence raises coordinated-subject recovery from 39 to 44/122, but selected-sentence exact-unit F1 falls from 66.87% to 66.06%, and full-source correct units fall from 2,026 to 2,000. Keep iteration 65 as the experimental reference.

## Design

Fit a binary classifier for nominal source dependency base `conj` on outer-fit sentences only. Compare a coarse POS-only model with a contextual model using ±2 POS windows, immediate POS combinations, nearest left/right conjunction-marker distance, nearest nominal POS and whether a conjunction marker intervenes. No word identity, lemma, morphology or dependency field is an inference feature. Fixed sparse logistic loss uses L2 0.001 and minimum feature count three.

At inference add `weight × log P(non-conj)` to every carrier edge of a nominal. This is soft eligibility evidence, not a hard subject mask; carrier order within a frame is preserved. Keep the iteration-65 primary competition penalty, NONE cutoff, full candidate lattice and unit scorer fixed. Choose only the evidence weight, from 0, 0.5, 1, 2, 4, 8, maximizing calibration carrier F1 with fewer-prediction/smaller-weight tie breaks. Zero is included. Primary contextual weights are 1, 0, 4, 0, 4 across folds; coarse weights are 1, 0, 2, 0, 4. There is no test-selected weight or target change.

All source sentences, partitions, 3,365 gold units/519 selected and the 122-unit coordination cohort are unchanged. The gold-conj exclusion result from iteration 66 is an oracle reference, not a competing deployable policy.

| Policy | Full-source correct / false | Full-source F1 | Selected correct / false | Selected F1 | Coordination exact /122 |
|---|---:|---:|---:|---:|---:|
| Competition65 | 2,026 / 1,490 | 58.89% | 337 / 152 | 66.87% | 39 |
| POS-only evidence | 1,988 / 1,418 | 58.72% | 327 / 149 | 65.73% | 38 |
| Context evidence | 2,000 / 1,406 | 59.08% | 328 / 146 | 66.06% | 44 |
| Gold-conj exclusion oracle | 2,045 / 1,380 | 60.24% | 337 / 146 | 67.27% | 48 |

Context improves on the coarse control but does not preserve correct recovery or selected F1. The small full-source F1 improvement is another precision/recall shift. Full-source Palladius F1 remains 50.00%, while Cicero rises 59.29→59.48%; these do not rescue the failed primary guards.

Post hoc attribution shows that context restores six of the nine inspected losses, but creates another coordination loss, yielding net +5. Across all frames it gains 12 exact units and loses 38. The treatment charges every potentially eligible nominal, even outside direct subject competition; uncertainty in the role probe can therefore suppress otherwise useful assignments. This motivates a narrower follow-up, not adoption.

## Verification and next decision

The independent audit refits all ten probes with numerical tolerances for sparse reductions, replays all ten calibration policies, 35,348 test assignments and 17,674 saved probe predictions, preserves prior fields and recomputes evaluation. Inference mutation checks hide lexical and annotation fields; zero evidence reproduces competition65. Probe tests cover gradients, annotation independence, preservation of within-frame ordering and marker-side discrimination.

Artifacts are in `experiments/results/grammar-restoration/iteration67/`, with design, policy and prediction freezes and per-case post hoc attribution. The follow-up will reuse these fitted probes, restrict evidence to contested carriers, and normalize it relative to the most plausible phrase head in each contest, leaving uncontested carriers unchanged. This is adaptive development on reused data and requires separate freezing and evaluation.

No default change, target projection or relabeling occurs. The 200-sentence reserve remains unscored and no prior target queries were scored. Source words/POS remain available upstream; these results do not establish Voynich grammar recovery.
