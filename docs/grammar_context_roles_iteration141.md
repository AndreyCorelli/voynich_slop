# Iteration 141: second-order role similarity adds ranking information, but calibration collapses

**Preserve the new ranking evidence:** an anchor-free second-order context statistic raises Gellius AUC from **0.8393 to 0.9107** and Livy from **0.6458 to 0.7083**; neither is matched by any of sixteen frequency-preserving shuffles. However, it loses the old Caesar separation and performs near chance on Jerome. The calibrated classifier predicts every candidate as a conjunction, so this is not a successful general class-restoration model.

## One second-order statistic

From a single opaque word stream, build directed adjacency counts B. Row-normalize B to obtain each word's right-neighbor distribution R, and row-normalize its transpose for the left-neighbor distribution L. A word's context-role vector is the concatenation [L, R].

For each candidate type, average these role vectors over its left neighbors and separately over its right neighbors, weighted by their observed conditional frequencies. The sole supervised feature is cosine similarity between those two averages. Thus different neighbor words can contribute similar contextual roles without having identical IDs. No plaintext names, anchor tags, known mappings, or sentence boundaries enter this representation.

A source-trained two-parameter logistic classifier (bias plus one standardized scalar) uses exactly thirteen noncatalogue types, the existing three held-type folds, class-balanced loss, and regularization. All sixteen target labels remain excluded. Graphs include unlabeled occurrences of held types; no held class labels enter them. Training words are concatenated into one stream, matching sentence-free inference. The thirteen out-of-fold probabilities fit one scalar calibration offset, frozen before target statistics.

All four full streams remain unchanged from iteration 139. Sixteen fixed global word-order shuffles per text preserve token counts (seeds 14100–14115). All 68 transformations are frozen before target statistics, then predictions before references and metrics. There is no author-specific feature, model, cutoff, or null selection. No new annotations, reserve features, sealed works, PP inference, defaults, or lexical nuclei are introduced.

## Frozen results

The primary is the calibrated model. The uncalibrated model is a predeclared control, not a replacement chosen per author.

| Text | Calibrated correct / present | Uncalibrated correct | New AUC | Previous corrected-overlap AUC | Null maximum AUC |
|---|---:|---:|---:|---:|---:|
| Caesar | 7/15 | 11/15 | **0.5179** | **1.0** | 0.6071 |
| Jerome | 8/16 | 11/16 | **0.4844** | 0.6719 | 0.6094 |
| Gellius | 7/15 | **12/15** | **0.9107** | 0.8393 | **0.6786** |
| Livy | 6/14 | **9/14** | **0.7083** | 0.6458 | **0.5625** |

Calibration is monotone, so it does not change AUC. Calibrated NLL is 0.7285 Caesar, 0.6679 Jerome, 0.6122 Gellius, and 0.6928 Livy. Improvements in loss or ranking do not make the calibrated hard predictions useful when all prepositions are missed.

Gellius and Livy show order-sensitive information beyond these frequency-preserving nulls, while Caesar and Jerome overlap their null distributions. The sixteen nulls are descriptive correlated controls, not independent reliability guarantees. Gellius still includes the known raw-`c` reference ambiguity; candidate membership, word boundaries, and source-modal reference classes remain supplied.

## Concrete calibration failure

The feature is bounded in [0, 1]. The frozen final model plus source-fitted offset has calibrated class logit

`logit P(CCONJ) = 0.14681719 + 4.30685070 × role_similarity`.

Its probability is therefore at least **0.53664** throughout the entire feasible feature domain. The implied 0.5 class boundary is at feature value **−0.03409**, outside the domain. Every possible valid input is consequently classified as CCONJ, not merely the observed four streams.

This is independently verified from source-model parameters without fitting target labels. The thirteen-type out-of-fold offset does not transfer benignly to the final one-scalar model here. A source-only domain check could detect this failure before target evaluation. It does not explain the lost Caesar/Jerome ranking, which is already poor before calibration, so another intercept alone cannot make the statistic universally good.

## Implication and next proposal

Reject this as a replacement classifier. Preserve the Gellius/Livy role-ranking evidence separately from the earlier corrected-overlap Caesar signal: the two scalars appear complementary in these development results, although combining them has not yet been tested.

A bounded next experiment is a small source-only model using both scalars jointly, with matched single-feature controls, raw probabilities retained, and a source-only feasible-domain check for any calibration. Keep all thirteen training types and sixteen-type exclusion, freeze every choice before four-text evaluation, and do not pick a model per author. This tests whether complementary information can provide a more transferable grammatical input without another large feature bundle. No benefit or reliable lexical seed is assumed.

## Verification

Eighteen focused tests pass, including an independent dense-matrix fixture comparison, arbitrary ID renaming, direction reversal, missing candidates, and empty/singleton streams. Independent review verifies 23 frozen hashes, retrains all four scalar models, reconstructs graph statistics for 1,033 type/context cases with a separate dictionary-based implementation, replays 1,020 target probabilities and 204 metric groups, verifies all 68 transformations and preserved counts, and proves the calibrated feasible-domain collapse. Strict type exclusion and reserve separation are checked. Artifacts are in `experiments/results/grammar-restoration/iteration141/`.
