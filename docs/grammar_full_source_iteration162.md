# Iteration 162: full source inventory is not a consistent improvement

Expanding training from13 to29 source function types does not consistently improve the anonymous binary classifier. The primary fixed weak-penalty model improves Gellius and Apuleius but worsens the other five texts. Source out-of-fold accuracy is15/29 at both penalty strengths, below the18/29 majority baseline. Keep the earlier conditional successes, but do not adopt this expansion as a validated repair.

This explicitly changes the validation question. All source-fit types with>=5 occurrences and modal ADP/CCONJ are included, without a purity cutoff:18 ADP and11 CCONJ, comprising the old13 plus all16 previously excluded catalogue types. Their labels come exclusively from cached source-fit annotations, never target-text annotations. The final source model has therefore seen these Latin word types, while target IDs are independently salted and inference uses only two anonymous scalar features. This is author transfer with source lexical exposure, not the previous strict16-type exclusion benchmark.

The original13 source folds are preserved. Added types are deterministically SHA-sorted within class and assigned round-robin to three folds. Each held-out type is excluded from its source OOF fit, including added types. The same class-balanced monotonic model is fitted at two predeclared fixed penalties: primary.0005, secondary.5. No penalty or author arm was selected from target results. Eligibility/folds, then models, then predictions were frozen before their downstream stages.

| Text | Strict13 weak → expanded29 weak (primary) | Strict13 strong → expanded29 strong (secondary) |
|---|---|---|
| Caesar | 12/15 → 11/15 | 12/15 → 12/15 |
| Jerome | 12/16 → 11/16 | 12/16 → 11/16 |
| Gellius | 12/15 → 13/15 | 13/15 → 13/15 |
| Livy | 10/14 → 9/14 | 10/14 → 11/14 |
| Apuleius | 6/13 → 8/13 | 7/13 → 9/13 |
| Curtius | 12/15 → 11/15 | 11/15 → 12/15 |
| Suetonius | 12/16 → 10/16 | 12/16 → 11/16 |

The secondary strength has gains in three texts, ties in two and losses in two. Reporting its favorable cases does not rescue the primary experiment, and no author-specific combination is adopted. Supplied16-candidate membership, source-modal references and segmentation caveats remain. Apuleius's stronger-model9/13 is not robustly restored POS, particularly given its chance-level AUC.525.

Source OOF on all29 types gives weak AUC.5051/NLL.8086 and strong AUC.5606/NLL.6817, with15/29 correct for both. On the original13 subset, both are7/13, weak AUC.4333/NLL.8009 and strong AUC.5333/NLL.6709. The old13 held-type memberships are preserved, but fits now also include two-thirds of the added types. Do not compare all29 and old13 accuracies as equal-denominator estimates. The weak model's source ranking remains near chance despite the increased conjunction inventory.

Every29 leave-one-training-type-out model and all seven existing focal-siue perturbations were tested at both strengths. Strict13 controls use their matched omission/perturbation models; omission of a newly added type leaves the strict model unchanged because that type was already excluded. Source features for all29 types were recomputed under every focal perturbation.

| Text | Expanded29 weak: full / omit siue / middle substitution | Expanded29 strong: full / omit siue / middle substitution |
|---|---|---|
| Caesar (/15) | 11 / 12 / 12 | 12 / 12 / 12 |
| Jerome (/16) | 11 / 11 / 10 | 11 / 10 / 10 |
| Gellius (/15) | 13 / 13 / 12 | 13 / 13 / 12 |
| Livy (/14) | 9 / 10 / 10 | 11 / 11 / 10 |
| Apuleius (/13) | 8 / 8 / 5 | 9 / 9 / 5 |
| Curtius (/15) | 11 / 12 / 12 | 12 / 12 / 11 |
| Suetonius (/16) | 10 / 10 / 12 | 11 / 11 / 12 |

Siue type omission is less damaging than in the earlier small inventory. However, the single-occurrence middle substitution still drops Apuleius8→5 or9→5, and other omissions expose residual variation. Full per-omission/perturbation metrics are retained; overlapping variants are not independent replications. Expanding supervision changes the boundary rather than uniformly improving it.

This indicates that the original tiny inventory was not the only bottleneck. Within the tested monotonic linear family, the two symmetry scalars do not provide reliable class separation across source types. It does not prove the features contain no information, nor invalidate the coarse frequency-led grammatical shortlist. No exact word identities or nuclei are recovered.

Next proposed diagnostic: add occurrence frequency explicitly to this full-source binary task, with controls for frequency alone and the existing two-feature model. Normalize inference counts to the source token budget before log1p transformation, freeze the three arms and source-only nested regularization rule, and inspect source held-type performance before claiming author benefit. The frequency coefficient should be unconstrained while the two symmetry slopes retain their hypothesis; do not assume more frequent means conjunction. This tests missing transferable count information without immediately adding a flexible model to a small dataset. It remains supplied-candidate binary classification, separate from the broader shortlist result.

Independent verification reconstructed all29 source labels/counts and folds, recomputed232 source feature vectors via combinatorial overlap/dictionary roles, verified arbitrary source-ID renaming, and independently optimized/KKT-checked80 fits. It replayed58 source OOF probabilities,15,392 target probabilities and1,036 metric groups, including all strict13 controls. Source-fit/reserve overlap is zero and no target annotations enter training. The focused suite passed18 tests. Artifacts and manifest: `experiments/results/grammar-restoration/iteration162/`.
