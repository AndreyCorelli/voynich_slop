# Iteration236: unanimous cores are stable relations, not confident POS classes

Unanimous31-run cores retain above-control POS compatibility in every author, but initialization stability is not grammatical confidence. Core-average pair compatibility ranges32–62%, and larger cores are often mixed. Preserve stable anonymous relationships as a possible decoder input; do not impose same-POS equality or report oracle purity as restored labels.

## Frozen cores

Two words share a core exactly when their31 partition-label signatures match. This is an equivalence relation independent of arbitrary cluster names; no cross-run label alignment is needed. Freeze all memberships, singleton cores and within-core unordered pairs before POS evaluation. Report every author/core, without selecting a POS-favorable core or threshold.

Evaluate global-profile dot products of distinct word pairs: primary statistic averages pair compatibility within each core, then averages non-singleton cores equally. Pair-weighted compatibility is separate, so one large core cannot silently dominate the primary result. Oracle purity gives each core its target-gold majority POS; both core-macro and word-weighted purity are reported. Shuffles preserve frequency×Case status and whole profiles,199 fixed assignments shared with previous experiments, re-optimizing purity each time. No new raw annotation, reserves, naming model or target-guided selection; Dante remains consumed development.

## Compatibility and coverage

| Author | Non-singleton cores | Covered graph nodes | Within-core pairs | Core-macro compatibility | Pair-weighted compatibility | Admitted token coverage |
|---|---:|---|---:|---:|---:|---:|
| Aquinas |42|157/202|481|32.22%|29.80%|40.56%|
| Caesar |10|20/60|10|56.75%|56.75%|3.75%|
| Cicero |20|55/75|61|38.39%|35.05%|21.23%|
| Jerome |49|183/209|526|62.14%|44.71%|40.28%|
| Dante |24|62/76|60|34.74%|27.69%|25.48%|

Core-macro compatibility tails are.020,.010,.005,.005,.005 against conditioned-profile shuffles; pair-weighted tails.005,.010,.005,.005,.005. These separate correlated development tests are not multiplicity-adjusted confidence, independent edge observations or proof each core is correct. All pairs are included, even if not original graph edges; co-clustering can link words without a direct replacement edge.

Singleton counts are45/40/20/26/14. Non-singleton core size ranges2–17 Aquinas,exactly2 Caesar,2–6 Cicero,2–21 Jerome,2–6 Dante. The larger Aquinas/Jerome cores account for many pairs, and their lower pair-weighted compatibility shows that stability can preserve mixed groups. Caesar's10 stable pairs cover only1027/27386 tokens, sharply limiting their usefulness despite above-null association. Text word-type coverage is3.38%,.30%,.68%,3.05%,.92%; no whole-text reconstruction follows.

## Oracle purity is a different quantity

| Author | Core-macro oracle purity | Word-weighted oracle purity | Conditional core-purity tail |
|---|---:|---:|---:|
| Aquinas |61.29%|55.32%|.005|
| Caesar |76.29%|76.29%|.010|
| Cicero |64.21%|62.00%|.010|
| Jerome |78.12%|71.29%|.005|
| Dante |63.97%|61.04%|.005|

Small cores inflate purity: even a two-word mixed-POS core can receive a50% oracle majority score. Thus61–78% purity must not be described as that fraction of correctly inferred POS classes. Pair compatibility is often much lower and requires no oracle class naming. The groups themselves are inferred anonymously, while their named-class quality is assessed only with gold.

## Audit and next robustness test

Independent equivalence verification checks49432 word pairs, full profile/null replay995 groups, coverage and21 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration236/`.

Next test sensitivity to the text, rather than another initialization threshold:31 fixed10% sentence-deletion replicates on the existing admitted streams, same floor5/two-frame graph rules and corrected spectral pipeline, fixed initial seed23500. Use cached sentence-position keys only, never raw annotations. Compare each original unanimous pair with the rebuilt partition: unconditional retention counts dropped endpoints as failures; conditional retention uses surviving endpoints, with coverage and unclusterable graphs explicit. Keep all authors/replicates and no best deletion/seed selection. Changing node universes also changes the pipeline's numerical initialization, so this tests whole-pipeline robustness rather than a pure isolated geometry effect. Unanimity across initializations does not establish data robustness, and neither form of stability alone establishes grammatical correctness.
