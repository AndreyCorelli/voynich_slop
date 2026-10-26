# Iteration234: within-component directions repair Jerome's representation limit

Adding within-component spectral directions raises Jerome's token-weighted oracle purity25.94→54.83%, and type-macro purity38.71→46.92%. This supports the diagnosed representation limitation. The change is mixed elsewhere: Caesar loses purity and Dante loses type-macro purity. Preserve the controlled correction and both variants; no author-specific embedding selection or reliable named POS recovery follows.

## Frozen correction

Same unweighted conservative graphs, five authors and17 clusters as233. Retain **all zero modes plus the first17 positive Laplacian eigenvectors**, expanding to complete a tied boundary eigenspace within1e-10. Row-normalize; unchanged farthest-first initialization with initial node Random(23300), Lloyd updates/max300/tolerance1e-10. Clusters are frozen before POS evaluation. No cluster-count, seed, graph, weight or label-guided search.

Same cached profiles and199 frequency×Case-status whole-profile shuffles, seeds23300–23498; oracle naming and purity are re-optimized in every null. Report all authors, both type/token metrics and exact233 comparators. No raw annotation, new labels, other reserves or Seneca gold; Dante remains previously consumed development data. All names remain target-gold oracle assignments, not predictions.

## Purity comparison

| Author | Type-macro233→234 | Conditional purity tail234 | Token-weighted233→234 | Conditional purity tail234 |
|---|---|---:|---|---:|
| Aquinas |42.03→42.73%|.005|55.09→50.56%|.005|
| Caesar |61.14→53.36%|.005|72.76→70.57%|.015|
| Cicero |50.44→53.27%|.010|62.34→65.22%|.015|
| Jerome |38.71→46.92%|.005|25.94→54.83%|.015|
| Dante |48.71→46.07%|.005|65.93→66.58%|.005|

All234 purity statistics exceed their conditioned nulls at the fixed descriptive.05 threshold, including Jerome tokens. This does not establish an across-author confirmatory result: multiple correlated metrics, repeated development and oracle label fitting remain. Small clusters, node/type coverage limitations and profile ambiguity persist.

## One-to-one alignment and geometry

| Author | Embedding dimensions | Zero modes | Type-macro one-to-one | Token-weighted one-to-one |
|---|---:|---:|---:|---:|
| Aquinas |22|5|33.84%|46.61%|
| Caesar |35|11|32.02%|46.32%|
| Cicero |23|6|32.73%|47.55%|
| Jerome |37|20|33.28%|49.44%|
| Dante |27|10|32.45%|58.55%|

Every graph occupies17 clusters and now includes positive-eigenvalue directions. Caesar expands beyond11+17=28 to35 dimensions because the boundary eigenvalue is tied; the complete eigenspace is retained by the predeclared rule, not chosen from POS results. Type-macro alignment tails are.005,.010,.010,.005,.005; token alignment Caesar.065 remains outside fixed.05, despite its purity tail.015. Many-to-one purity is optimistic and cannot be reported as named-POS accuracy.

The corrected geometry resolves the zero-only Jerome issue, but clustering capacity and initialization can still matter. The actual type-macro one-to-one scores remain roughly32–34%, far below reliable POS restoration. These results show latent relationship information and a representation effect, not restored Latin words, common nuclei or Voynich plaintext.

## Execution integrity and audit

The initial234 invocation stopped at input-manifest verification before clustering/reference evaluation because a copied input-list edit passed two arguments to a one-argument loader. Preserve its runner/design freeze. A separately frozen retry corrects that coding error without changing the protocol; artifacts reside in `iteration234-retry/`. No failed-result selection or old-artifact edits occurred.

Independent SciPy eigenspace geometry, frozen-coordinate initialization/Lloyd replay, actual/null profile reconstruction and2000 assignment-dual certificates pass, alongside exact233 comparison and24 hashes. The new representation itself is validated; no stability across initializations is claimed.

## Next check

Freeze31 initialization seeds23500–23530 on the same corrected embeddings, retaining all runs without choosing the best. Keep17 clusters and update rules; evaluate all partitions with the same conditioned-profile null and re-optimize the oracle in every shuffle. Report purity/alignment ranges, cluster-size variation and pair co-membership stability. This tests whether the latent groups and Jerome correction survive arbitrary initialization before stable groups are proposed as decoder inputs. Stable anonymous groups would still require separate naming or a decoder that can consume unlabeled constraints.
