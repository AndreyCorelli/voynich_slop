# Iteration237: unanimous initialization relations are only partly text-robust

After deleting10% of admitted sentence groups, original core pairs retain co-membership49–72% on average when missing endpoints count as failures. Conditional retention is higher68–95%, showing that graph eligibility loss explains much of the fragility, but not all. Preserve the distinction: initialization unanimity is not reliable coverage under text perturbation, nor a grammatical correctness guarantee.

## Frozen perturbation

For each author, sort cached lexical `(path,sent_id)` keys and remove `floor(.1*sentence_count)` groups using each seed23700–23730. This removes10% of sentence groups, not necessarily10% of tokens. Mask all their lexical positions; rebuild frequencies, lexical-neighbor frames and pairs with unchanged floor5/two-distinct-frame eligibility. No bridging across removed sentences, raw text or annotation rereading.

Run the corrected234 embedding and235 Lloyd rule with fixed initialization seed23500, one of the original31 consensus runs. No graph relaxation, new seed/model winner or target POS input. Zero-deletion graphs exactly reproduce the originals, and their labels exactly reproduce235's first run. Graphs with fewer than17 nodes would be explicitly unclusterable; none occur. Freeze every deletion/graph/partition before retention analysis. All five authors and155 replicates retained; Seneca and other reserves untouched.

The changed graph/node universe can change farthest-first initialization and numerical tie behavior even with the same seed. This is whole-pipeline sensitivity, not a pure geometry-only or independently isolated data effect. No new POS quality metric is inferred from retention.

## Original unanimous-pair survival

| Author | Original core pairs | Mean both-endpoint survival | Mean conditional co-membership retention | Mean unconditional retention |
|---|---:|---:|---:|---:|
| Aquinas |481|75.40%|83.13%|62.74%|
| Caesar |10|76.77%|94.71%|72.26%|
| Cicero |61|64.36%|87.91%|56.74%|
| Jerome |526|68.56%|85.55%|58.40%|
| Dante |60|72.53%|67.69%|48.98%|

Conditional retention divides by pairs whose two words still belong to the rebuilt replacement graph. Unconditional retention divides by all original core pairs, treating endpoint drops as failure. These are means of per-replicate ratios, so products of the reported means need not equal the third mean exactly. Missing graph endpoints need not mean that the word disappeared entirely: it may fall below frequency or shared-context eligibility.

## Range and core-level impact

| Author | Unconditional retention range | Conditional retention range | Mean intact original cores / original non-singleton cores |
|---|---|---|---|
| Aquinas |49.48–77.96%|65.03–97.14%|24.65/42|
| Caesar |50.00–90.00%|75.00–100%|7.23/10|
| Cicero |34.43–80.33%|72.41–100%|11.13/20|
| Jerome |38.59–69.77%|57.83–99.43%|26.84/49|
| Dante |31.67–73.33%|46.34–91.18%|12.26/24|

An intact core requires every original member to survive and share one rebuilt cluster. No unclusterable replicate or inadequate matching capacity explains the losses. Dante has additional membership instability beyond missing nodes; Caesar's conditional figure is high but concerns only10 pairs and previously3.75% token coverage. Neither supports a universal high-confidence grammatical reconstruction claim.

## Audit and next check

Independent masked-frame/graph reconstruction and155 partition replays pass, with15 independently computed SciPy eigenspace-geometry checks,155 retention groups, exact zero-deletion/initial-run baselines and22 hashes. Artifacts: `experiments/results/grammar-restoration/iteration237/`.

Next construct strict **joint-stability cores**: start from236 unanimous cores, require each retained word to appear in every deletion graph, then intersect co-membership across all31 deletion partitions. Freeze this rule and memberships before POS evaluation. Count every excluded word/pair and report empty output without relaxing the criterion. Evaluate resulting compatibility/purity/coverage with the same frequency×Case profile controls in all authors. This tests whether a smaller stable local input survives both initialization and text variation; it does not assume that additional stability implies grammatical accuracy or restore exact words.
