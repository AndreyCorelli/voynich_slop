# Iteration235: latent POS signal persists, but whole partitions are unstable

Across31 fixed initializations, type-macro oracle purity remains above the conditioned null at fixed.05 in27–31 runs per author. The signal is not confined to one selected seed. However mean pairwise adjusted Rand agreement is only.25–.64, and token-weighted results vary substantially, especially Jerome. Preserve latent relationship information without treating the17-way partitions as reliable grammatical classes.

## Frozen experiment

Use234's corrected embeddings unchanged,17 clusters and the same farthest-first/Lloyd rule. Initial seeds23500–23530, all runs retained; no eigenbasis, cluster count, seed or author-specific winner selection. Freeze155 partitions and anonymous co-membership/stability summaries before reference evaluation.

Each partition is evaluated against the same199 frequency×Case-status profile shuffles used in234, with oracle names re-optimized for every shuffle, both type-macro and covered-token weighting. Report every result and tail. These reused runs share graphs and references; counts of runs meeting a threshold are descriptive robustness evidence, not31 independent tests or a joint confidence estimate. No new raw text, annotation or reserves; Dante remains consumed development.

## Type-macro oracle purity

| Author | Minimum | Mean | Maximum | Runs with conditional tail<=.05 |
|---|---:|---:|---:|---:|
| Aquinas |37.84%|40.59%|43.20%|28/31|
| Caesar |48.44%|55.81%|62.01%|31/31|
| Cicero |46.66%|52.86%|58.54%|27/31|
| Jerome |42.05%|46.64%|52.62%|31/31|
| Dante |42.84%|46.25%|48.88%|31/31|

No best run is adopted. Many-to-one oracle purity is optimistic and permits several groups to receive the same target POS; it is not inferred named-POS accuracy. Conditional controls account for substantial small-group labeling flexibility but are not an independent validation corpus.

## Token-weighted oracle purity

| Author | Minimum | Mean | Maximum | Runs with conditional tail<=.05 |
|---|---:|---:|---:|---:|
| Aquinas |42.17%|49.58%|57.88%|28/31|
| Caesar |56.58%|70.00%|80.01%|28/31|
| Cicero |48.78%|61.96%|68.83%|22/31|
| Jerome |38.68%|46.99%|57.51%|9/31|
| Dante |46.51%|59.69%|66.58%|28/31|

Jerome234's54.83% token purity was a favorable initialization relative to the new46.99% mean. The representation correction still exposed within-component information, but did not produce a robust token-level grouping. Token score variability cannot be hidden by reporting only type-macro signal or the strongest seed. Graph/text coverage is unchanged from231.

## Membership stability

Adjusted Rand index compares partitions after ignoring arbitrary group names and adjusts for chance pair agreement.

| Author | Pairwise ARI minimum | Mean | Maximum |
|---|---:|---:|---:|
| Aquinas |.389|.639|1.000|
| Caesar |.039|.288|1.000|
| Cicero |.263|.502|1.000|
| Jerome |.058|.248|1.000|
| Dante |.206|.452|1.000|

Some initializations yield identical partitions while others disagree substantially. Similar purity does not imply stable membership: different partitions can achieve comparable gold scores. Full co-membership frequencies, largest/singleton/occupied cluster variation and ARI against234's original seed are stored without applying a gold-selected stable-core threshold.

## Audit and next check

Independent155 initialization/Lloyd replays, co-membership/ARI reconstruction and62000 actual/null assignment-metric groups pass. All assignments are replayed, with1240 independent LP-dual optimality certificates covering every actual and predeclared null samples0/99/198;24 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration235/`.

Next extract **unanimous co-membership cores**: words belong to a core only if grouped together in every one of the31 runs. This is an annotation-free equivalence relation defined by identical membership signatures, with singleton cores reported separately. Before reading POS, freeze all non-singleton memberships/pairs. Then evaluate coverage, within-core POS compatibility and purity against the same conditioned-profile controls, all authors retained. Unanimity measures initialization stability only, not correctness or robustness to text perturbation. This tests whether stable local grammatical constraints survive even though the full partitions fail the stability requirement; no named POS, exact words or nuclei are claimed in advance.
