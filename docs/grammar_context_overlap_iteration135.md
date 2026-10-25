# Iteration 135: anchor-free directional class signal on expanded Caesar

**Preserve the conditional finding:** a single count-corrected left/right context-overlap statistic, with no supplied word mappings at inference, classifies **13/15 expanded Caesar types correctly (86.67%)**, with **AUC 1.0** and mean NLL **0.416** versus balanced prior 0.693. All eight prepositions are correct; the two errors are conjunctions `atque` and `que`. This is a promising anchor-free binary-class result on a supplied function-word catalogue, not blind function-word discovery, general POS tagging, or lexical nucleus recovery.

Transfer is uneven: the same frozen primary predictor gets source 9/16, original Jerome 3/13, expanded Jerome 10/16, and original Caesar 6/13. No model or cutoff is selected per text. Expanded Caesar is repeatedly used development data, not independent confirmation.

## One explicit directional statistic

For each opaque target type, collect counts of immediately preceding and following opaque IDs, without crossing sentence boundaries. Let the normalized left and right counts be L and R. Raw overlap is the sum, over neighbor IDs, of min(L, R). Larger values indicate more similar left/right neighbor distributions.

To control for overlap expected from neighbor frequencies and sample sizes, pool the left and right observations and consider random repartitions preserving the two sample sizes and the combined count of every neighbor. A hypergeometric marginal gives the exact expected overlap contribution for each neighbor. The primary statistic is observed overlap minus this count-conditioned null mean. It is a descriptive correction, not a grammatical significance test; overlapping observations are not independent samples.

The two frozen controls use raw overlap and log(1 + occurrence count). Each arm is a two-parameter logistic classifier: bias plus one standardized scalar, with class-balanced loss and the existing regularization. Direction and weights are learned on the same thirteen noncatalogue types; all sixteen target types remain excluded from training labels. Standardization is fit separately within each training fold, and a scalar calibration offset uses only thirteen held-type out-of-fold probabilities. Models and calibrations are frozen before target statistics and predictions.

No anchor identities, supplied POS tags, or five-word mappings enter these predictors. Consistent opaque-ID renaming and poisoning anchor/tag fields leave the statistics unchanged. Candidate function-word membership, occurrence grouping, and segmentation remain supplied. Thus “anchor-free” describes inference features, not the absence of supervised training labels or candidate-set privileges.

## All frozen results

Each cell gives correct / present types, AUC, and mean NLL. All present types are retained, with support flags saved rather than used to filter outcomes.

| Context | Corrected overlap, primary | Raw overlap, control | Frequency, control |
|---|---|---|---|
| Source 770 sentences | 9/16 · 0.6719 · 0.730 | 11/16 · 0.7344 · 0.613 | 9/16 · 0.5625 · 1.636 |
| Jerome 100 | 3/13 · 0.3500 · 1.039 | 9/13 · 0.6000 · 0.622 | 5/13 · 0.5250 · 2.797 |
| Jerome 829 | 10/16 · 0.6719 · 0.718 | 9/16 · 0.5938 · 0.621 | 12/16 · 0.7500 · 1.046 |
| Caesar 100 | 6/13 · 0.6190 · 0.790 | 5/13 · 0.4524 · 0.790 | 7/13 · 0.4762 · 1.443 |
| **Caesar 2,494** | **13/15 · 1.0000 · 0.416** | 7/15 · 0.6161 · 0.728 | 9/15 · 0.6786 · 2.920 |

The expanded Caesar result is not reproduced by either raw overlap or frequency alone. Its weighted type-class accuracy is **89.29%**, against constant modal type references, not token-level POS annotations. Corrected scores rank every conjunction above every preposition, although the source-trained cutoff misclassifies the two lower-scoring conjunctions. This small-sample perfect ordering is not a universal accuracy guarantee and does not justify selecting a target threshold.

Across the other contexts, the primary often has worse NLL than the balanced prior. Raw overlap has useful source and short-Jerome results, but is retained as a control rather than substituted after inspecting outcomes. Frequency also sometimes has higher accuracy with poor probability quality. No single arm is consistently best.

## Meaning for decipherment

This provides a concrete new direction: class information can be present in opaque word-order statistics without already knowing surrounding translations. It could eventually supply constraints to another decipherment algorithm, independently of whether the current lexical decoder benefits. The one-author long-context success must be preserved alongside failures, especially poor original Jerome and Caesar performance.

There is no PP integration in this iteration and no recovered exact Latin word identity. The experiment consumes only existing word forms and old modal class references, adds no grammar annotations or reserve features, and makes no sealed lexical query or default change. Texts and candidate types have been repeatedly used in development.

Next: a frozen context-volume curve on the cached author expansions, with common-type comparisons and missing/support reported, would test whether the Caesar result appears consistently as evidence grows or depends on a particular passage mixture. Keep this primary statistic, its model, and cutoff unchanged; do not choose an arm or threshold from the target curves. Such a check is needed before describing the result as a reliable grammatical input.

## Verification

Fifteen focused tests pass, including an exhaustive small-fixture comparison of the null expectation with every count-preserving partition, ID-renaming/private-field checks, direction reversal, sentence edges, and empty input. Independent review verifies 21 frozen hashes, recomputes statistics for 86 type/context combinations using integer-combination probabilities instead of SciPy's hypergeometric implementation, retrains all twelve scalar models, and checks 219 target probabilities and sixty metric groups. Anchor-field poison and ID-renaming invariance hold on all five contexts; strict type exclusion and reserve separation are checked. Artifacts are in `experiments/results/grammar-restoration/iteration135/`.
