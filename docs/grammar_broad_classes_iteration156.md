# Iteration 156: a frequency-led coarse grammatical shortlist

**Preserve this limited positive finding:** in nested held-out-word-type source evaluation, the combined model's top10 contains8 members of the defined grammatical group. Frequency alone also achieves8/10, and15/20. This is a potentially useful coarse grammatical shortlist, primarily supported by frequency; it is not exact POS tagging, identification of word meanings, or a demonstrated cross-text restoration algorithm.

The positive group was frozen as ADP/AUX/CCONJ/DET/PART/PRON/SCONJ; every other modal POS is negative, including ADV. It is a precisely defined seven-tag union, not a universal definition of function words. Eligibility remains>=5 source-fit occurrences and>=80% modal POS agreement. All16 original catalogue targets are excluded from every fitting/selection fold. There are771 eligible non-target types,150 positive and621 negative (19.46% positive prevalence).

Three arms were fixed before running: the two anonymous structural scalars, log1p frequency alone, and the combined three features. All use unconstrained class-balanced logistic fitting, the same frozen ridge grid and source-only nested three-fold type validation. Standardization uses retained fit types; the unlabeled source graph includes held-out types transductively. Eligibility/folds were frozen before features, models before predictions, and predictions before metrics. No new annotations, reserved material or sealed works were used.

| Nested OOF metric | Structural | Frequency | Combined |
|---|---|---|---|
| True positives | 60 | 87 | 90 |
| False positives | 206 | 149 | 150 |
| Precision at raw>.5 | 22.56% | 36.86% | 37.50% |
| Recall | 40.00% | 58.00% | 60.00% |
| Average precision | .2098 | .4311 | .4433 |
| ROC AUC | .5481 | .7243 | .7284 |
| NLL | .6928 | .6103 | .6040 |
| Correct top5 | 0/5 | 4/5 | 4/5 |
| Correct top10 | 1/10 | 8/10 | 8/10 |
| Correct top20 | 1/20 | 15/20 | 14/20 |
| Correct top50 | 7/50 | 27/50 | 30/50 |

All four shortlist budgets were predeclared; top10 is highlighted without treating it as a newly validated optimal cutoff. The combined top10 is est, me, non, te, si, esse, mihi, quae, qui, etiam. Under inherited source-modal references, non and etiam are ADV and outside the specified union. No manual relabeling was applied. These names are revealed for evaluation; the detector sees opaque equality/order and occurrence counts, not their plaintext identities.

Structural features alone are near chance in broad-class ranking and poor at the top of the list. The combined arm improves frequency AP by.0122 and AUC by.0041, with three more positives and one more false positive at the fixed threshold. That small source-only increment is not established as reliable structural benefit; frequency accounts for most of the useful ranking. Frequency remains a legitimate possible grammatical cue, but must not be presented as exact lexical recovery.

Overall combined type accuracy is72.76%, below the80.54% all-negative majority baseline. Its raw threshold precision is only37.5%, so the result does not mean that72–80% of arbitrary POS are correctly restored. The useful observed result is enrichment in small top-ranked sets for a coarse class union. With771 correlated source-type observations and only one source partition, these shortlist percentages do not establish author-independent reliability.

A further applicability limitation matters: eligibility uses known modal purity of held-out types. That is permissible for this defined source benchmark, but purity is unavailable in an undeciphered text. Training may use source purity; deployment candidate filtering cannot. Before transfer claims, evaluate all types with occurrence support alone, retaining purity only as an evaluation subgroup, rather than filtering unknown types with their labels. The16 excluded catalogue targets remain positive-only secondary recall checks, not a way to estimate precision.

Next proposed check: remove the purity restriction from inference/evaluation while preserving source label-quality filtering for training. Freeze folds for all source types with>=5 occurrences, train only eligible pure types in each training fold, and evaluate every supported held-out type using its existing modal reference. Keep structural/frequency/combined arms, source-only nested selection and all16 targets excluded from fitting. Report pure/mixed subgroups and all shortlist budgets without selecting favorable outcomes. If the coarse signal survives that applicability check, replicate on already annotated author streams before using it as input to another deciphering method.

Independent verification reconstructed787 eligible source types and their labels, recomputed787 anonymous feature vectors, checked every source split/selection and independently optimized156 models with gradient checks. All three detector metric sets and target exclusion were replayed;18 focused tests passed. Frozen artifacts and manifest: `experiments/results/grammar-restoration/iteration156/`.
