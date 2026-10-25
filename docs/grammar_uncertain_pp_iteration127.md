# Iteration 127: posterior averaging preserves little high-confidence PP coverage

Uncertainty-aware PP integration fails the frozen precision/coverage requirements. On source calibration, no tested mixture retains 80% of hard-class correct selections. At the unchanged test cutoff 0.80, posterior averaging gives **26 correct / zero wrong**, versus **244 correct / 59 wrong** with hard classes and **23 correct / zero wrong** with unknown classes. Preserve the three additional correct selections over unknown, but do not characterize this as a useful broad structural improvement.

## Method and frozen selection

The iteration-124 classifier and its thirteen-type scalar calibration remain fixed. Each opaque target type receives a probability of being a coordinating conjunction versus a preposition. Thirty-two scrambled Sobol draws (seed 12700) assign one class to each type consistently across every occurrence. Each draw runs the complete original PP model with all target lexical names hidden, preserving both contextual tag features and POS overrides. Averaging the resulting PP probabilities approximates marginalization over these class assignments.

This assumes independent type-class probabilities, not a learned joint posterior, and uses a finite numerical approximation. It is not a proof about exact marginalization or all uncertainty-aware models. Surrounding anchors, candidate function-word membership, and segmentation remain supplied.

Five predeclared scores mix this posterior mean with unknown-class scores, at weights 0, 0.25, 0.5, 0.75, and 1. Calibration uses only the existing 829 source-calibration sentences and cached PP labels. The PP cutoff stays 0.80. Require at least 90% precision and retention of 80% of the new hard-class baseline's correct selections; select maximum correct coverage, then fewer errors, then higher mixture weight. If none qualifies, the experimental fallback is the hard-class baseline, not a claim of a newly adopted model.

The source decision is frozen before loading test probabilities. Test evaluation reuses exactly the 770 source-test sentences and fixed cohorts from iteration 120. All test mixture results are descriptive and cannot choose a winning weight. No author scoring, new annotations, reserve features, sealed lexical evaluation, PP-model training, or default change occurs. These are reused development data.

## Calibration failure

The hard-class calibration baseline has **310 correct / 25 wrong (92.54% precision)**, requiring at least **248 correct selections**. The five mixtures produce respectively **29/0, 29/0, 33/0, 35/0, and 35/1**. All fail coverage, so selection is OFF.

## Fixed test results

| Input / integration | Correct PP | Wrong PP | Precision |
|---|---:|---:|---:|
| Unknown classes | 23 | 0 | 100% |
| Hard inferred classes | 244 | 59 | 80.53% |
| Posterior mean | 26 | 0 | 100% |
| 0.25 posterior + 0.75 unknown | 23 | 0 | 100% |
| 0.50 posterior + 0.50 unknown | 24 | 0 | 100% |
| 0.75 posterior + 0.25 unknown | 26 | 0 | 100% |

The posterior mean loses 218 correct selections and removes all 59 false selections relative to hard classes. It introduces no new selections relative to that hard baseline. Of its three additional correct selections over unknown classes, two are in the fixed originally unmapped cohort and one is at another supplied anchor. Unmapped posterior coverage is **13 correct / zero wrong**, versus unknown **11/0** and hard **183/56**. All target-token selections remain empty.

At the pre-existing secondary cutoff 0.55, posterior averaging yields **104 correct / 19 wrong (84.55% precision)**, versus unknown **44/5** and hard **488/181**. This preserves some lower-confidence structural information but still falls below 90% precision; it is not a selected replacement policy. All fixed-cohort metrics and gross changes are saved.

## Interpretation and next proposal

The probabilistic class findings from iterations 124–125 remain potential decipherment inputs. Under this particular downstream model, averaging uncertain complete assignments at the old confidence cutoff removes most high-confidence PP coverage. This does not establish that the class signal is unusable or that another decoder cannot exploit its ranking.

One remaining low-cost diagnostic is to calibrate the PP decision threshold on the posterior-mean source-calibration scores themselves, keeping the same 90% precision and 80% correct-coverage requirements. The old cutoff was not selected for this changed score distribution; source-only threshold calibration would distinguish score-scale mismatch from an insufficient precision/coverage frontier. Freeze any such threshold before test use, do not choose a test threshold, and retain the OFF result if no source setting qualifies. This is a proposal, not an evaluated success.

## Verification

The independent audit verifies 22 frozen input hashes, replays all 68 complete PP score vectors, independently checks 69 metric/transition groups, reconstructs type-consistent Sobol assignments and mixture means, replays source-only selection, and confirms exact reproduction of the earlier hard and unknown baselines. Source partitions and reserve exclusion are checked. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration127/`.
