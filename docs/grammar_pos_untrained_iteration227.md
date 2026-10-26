# Iteration227: untrained structural rankings recover some pairwise compatibility

A fixed shared-frame-support ranking, without source labels, selects ten endpoint-disjoint pairs with mean reference POS compatibility59.14% Aquinas,54.56% Caesar,88.10% Cicero and66.94% Jerome. Each exceeds its whole-graph mean. This preserves a potential manuscript-internal grammatical input; it does not establish named POS restoration or a universally best selector. Greedy tie-breaking remains a material robustness question.

## Frozen selectors

Use the same193 conservative graph, opaque token counts and valid lexical-neighbor frames respecting sentence/nonlexical boundaries. Four scores are predeclared separately: shared-frame support high; mean endpoint log frequency high; its negative(low frequency); frame Jaccard intersection/union high. The complete frame sets include every valid lexical-neighbor occurrence, not only queried frames. No POS/Case enters scores or selection.

Freeze features/scores and tied top10/top20 plus greedy endpoint-disjoint10/20 before loading compatibility labels. Retain all authors, methods and directions; no gold-selected author routing, new raw annotation, reserve use or fits. Greedy selection orders by score then original edge index. That arbitrary tie-break is explicit, not an inferred confidence or a guarantee of invariance to word-ID ordering.

## Endpoint-disjoint10 comparison

All lists below contain ten pairs spanning20 distinct word types.

| Author | Whole graph | Support | Frequency high | Frequency low | Jaccard | Learned rich19 |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |21.13%|59.14%|48.90%|52.86%|52.86%|79.18%|
| Caesar |44.24%|54.56%|42.16%|51.48%|46.75%|67.97%|
| Cicero |36.91%|88.10%|24.85%|39.17%|70.30%|78.91%|
| Jerome |55.37%|66.94%|46.08%|80.00%|90.00%|88.67%|

Shared support gives a consistent descriptive enrichment over the whole graph here, while learned rich19 remains stronger in Aquinas/Caesar/Jerome and raw support is stronger in Cicero. Jerome's Jaccard90% is a retained comparator, not a selected deployment rule. High frequency alone is weak or below baseline in several authors, and low frequency is not a universal explanation for the learned results.

## Ties and wider lists

| Author | Support tied top10 count / mean | Support tied top20 count / mean | Support disjoint20 mean |
|---|---|---|---:|
| Aquinas |12 /57.89%|25 /46.87%|60.67%|
| Caesar |11 /65.89%|51 /44.24%|41.27%|
| Cicero |12 /86.06%|24 /75.04%|64.47%|
| Jerome |11 /62.14%|20 /64.13%|78.47%|

Shared-frame count is discrete, and ties can expand nominal lists dramatically: Caesar's tied top20 includes its entire51-edge graph. All four untrained methods' disjoint10/20 requests are available, but expanding to20 does not guarantee improved compatibility. Frequency-low Jerome tied top10 expands14(mean85.71%); Jaccard top20 expands27(mean85.19%). Keep actual counts and all variants rather than comparing nominal sizes as equal.

The measured quantity is global word-POS-profile dot product, not binary same-POS correctness or token POS accuracy. Endpoint-disjoint does not remove shared-context/annotation dependence. No common Latin-word nuclei, named POS labels or calibrated individual edge confidence are produced. The selected anonymous pair preferences could still be useful to another decipherment method under compatible word-substitution assumptions.

## Audit and next check

Independent count/frame reconstruction verifies1009 edge-feature rows,64 lists, all compatibility/coverage/shortfall summaries, exact225/226 comparators and22 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration227/`.

Next test sensitivity to arbitrary edge ordering. For all four fixed untrained scores, randomize order only within exact score ties using199 fixed seeds, then repeat greedy disjoint10/20. Compare with a uniformly randomized edge-order greedy matching using the same random priorities. Freeze every list before evaluation; report full compatibility ranges, means, shortfalls and paired differences without choosing an author-specific method. This tests whether structural rankings enrich compatibility beyond generic disjoint selection and whether the result survives changes irrelevant to grammatical content. It is a robustness diagnostic, not a label-permutation significance test or fresh validation.
