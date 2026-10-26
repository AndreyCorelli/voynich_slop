# Iteration220: replacement edges carry frequency-controlled applicability signal

**Preserve a relationship-level signal:** connected endpoints share binary Case applicability64.42–78.49% of the time, exceeding all199 fixed frequency-stratified label shuffles in each author (upper tail.005). This supports testing soft graph propagation with anonymous edges. It is not inferred grammar, evidence that every edge is correct, or permission to equate whole components.

## Frozen diagnostic

Use the unchanged193 conservative two-shared-frame graph, all546 endpoint nodes including degree1. Build frequencies, degrees and components before loading cached201 reference labels. Binary label means any recognized Case anywhere in the word's occurrences. Primary statistic is unweighted edge agreement. Shuffle labels within fixed global-frequency strata5–9,10–19,20–49,50–99,100+, using sorted opaque IDs and seeds22000–22198; preserve stratum label counts, compute `(1+exceedances)/200`. All four authors retained, no statistic/stratum/graph winner selection or new raw text, annotations or reserves.

This null conditions on coarse frequency strata, not exact frequency, degree, POS or profiles. It does not isolate a uniquely grammatical cause, prove degree-independent signal, or validate propagation performance. Edge observations are dependent; the permutation statistic uses the whole graph jointly. Four separate tests are reported, without an across-author correction claim.

## Graph results

| Author | Nodes | Edges | Case-bearing nodes | Edge agreement | Null mean | Null maximum | Upper tail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Aquinas |202|565|130|64.42%|48.99%|54.69%|.005|
| Caesar |60|51|38|72.55%|56.04%|68.63%|.005|
| Cicero |75|93|40|78.49%|48.33%|62.37%|.005|
| Jerome |209|300|133|77.33%|51.95%|60.00%|.005|

| Author | Both Case-bearing edges | Neither Case-bearing | Mixed edges | Mixed components / all | Nodes in mixed components |
|---|---:|---:|---:|---:|---:|
| Aquinas |207|157|201|1/5|194/202|
| Caesar |22|15|14|2/11|40/60|
| Cicero |30|43|20|3/6|69/75|
| Jerome |129|103|68|3/20|168/209|

Mixed edges comprise35.58%,27.45%,21.51%,22.67%; most nodes belong to mixed components. Thus a hard edge-equality constraint or connected-component Case label would be wrong for many nodes. Shared replacement context supplies a soft affinity, not transitive identity. Degree1 nodes number66/37/41/97, compared with136/23/34/112 degree>=2 centers evaluated previously; any propagation pilot must explicitly handle these additional graph nodes.

## Existing classifier errors are clustered too

Using the unchanged211 baseline and216 balanced applicability predictions on the305 eligible centers, report each center's true-label neighbor fraction. Aquinas baseline false positives have mean76.79% same-label neighbors; balanced false positives73.31%. Jerome false positives have78.12% and77.07% respectively. These gold-reference neighborhoods often agree on the **true negative** class while the classifier predicts positive; score smoothing will not fix a whole wrongly oriented cluster automatically. Cicero balanced false negatives average48.61% same-label neighbors, so even gold local majority can be unreliable for some errors.

These values motivate a bounded propagation test with the original scores retained, rather than unrestricted smoothing or a claim that all classifier errors can be repaired. The relationship signal may eventually help grammatical recovery; no new POS, named cases, or exact Latin nuclei have yet been restored by this diagnostic.

## Audit and next experiment

Independent graph/label/component reconstruction verifies546 nodes,200791 null-edge comparisons,610 fixed classifier error records, all mixing/degree/tail summaries and24 hashes. Artifacts: `experiments/results/grammar-restoration/iteration220/`.

Next freeze one propagation step: `p_new(word)=.5*p_original(word)+.5*mean(p_original(neighbor))`. Project the same anonymous12 features for all endpoint nodes, including degree1, before labels; predict with unchanged source-trained211 baseline and216 balanced applicability models. No retraining, target labels in propagation, iteration/strength search or convergence to component consensus. Compare original/refined applicability on all nodes and the existing305 centers; retain207 support ranking with fixed.5 gates and score products, all authors/tied top3/top5. Measure supported-center retention and actual precision, not homophily alone. Generalization to degree1 nodes outside earlier eligibility is an explicit limitation.
