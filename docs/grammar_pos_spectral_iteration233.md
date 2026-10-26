# Iteration233: graph-only groups retain POS information, with a disconnected-graph limit

Graph-only clusters have more useful POS purity than the failed regression-argmax groups: type-macro oracle purity42.03% Aquinas,61.14% Caesar,50.44% Cicero,38.71% Jerome,48.71% Dante. Each exceeds its frequency×Case-status profile-shuffle control at the fixed descriptive threshold. This preserves latent grammatical grouping as a possible input, not named POS restoration: all mappings and purity labels still use target gold, and several scores remain modest.

## Frozen clustering

Use unweighted conservative193 graphs and the existing198 Dante graph, all endpoint nodes sorted by opaque ID. No POS/Case enters clustering. Form normalized Laplacian `I−D^-1/2 A D^-1/2`; take its lowest17 eigenvectors including zero modes, expanding to include any complete boundary eigenspace within1e-10. Row-normalize, then run one17-cluster farthest-first initialization with first node chosen by Random(23300), followed by Lloyd updates, maximum300 iterations/displacement tolerance1e-10. Empty clusters retain their old centers. No cluster count, initialization or graph choice is selected with labels;17 is the fixed source UPOS inventory capacity.

Freeze clusters before cached231 profiles are read. Evaluate type-macro and covered-token-weighted one-to-one assignment and many-to-one purity. Compare199 whole-profile shuffles within fixed frequency bins×global Case-bearing status, seeds23300–23498. Re-optimize the oracle naming in **every** shuffle, so the comparison accounts for label-fitting flexibility. No raw annotation, new reserve, Seneca label, threshold or source-trained POS fit; Dante remains consumed development data.

## Type-macro diagnostic

| Author | Target majority | Oracle one-to-one | Oracle purity | Null mean purity | Purity tail |
|---|---:|---:|---:|---:|---:|
| Aquinas |25.67%|27.70%|42.03%|35.84%|.005|
| Caesar |20.00%|35.24%|61.14%|48.82%|.005|
| Cicero |31.14%|31.80%|50.44%|45.44%|.025|
| Jerome |25.74%|30.10%|38.71%|32.08%|.005|
| Dante |18.83%|35.72%|48.71%|38.66%|.005|

One-to-one tails are.005,.015,.010,.005,.010. These are multiple correlated, reused-development diagnostics, not multiplicity-adjusted confirmation or per-cluster confidence. Purity can name multiple clusters with the same POS and is optimistic; a17-cluster partition of only60 Caesar nodes has considerable labeling flexibility. The conditioned null has high baseline purity already. Better-than-null does not establish reliable restored classes.

## Covered-token diagnostic

| Author | Oracle one-to-one | Oracle purity | Null mean purity | Purity tail |
|---|---:|---:|---:|---:|
| Aquinas |46.38%|55.09%|45.63%|.005|
| Caesar |45.01%|72.76%|63.23%|.010|
| Cicero |43.13%|62.34%|55.77%|.040|
| Jerome |24.29%|25.94%|30.24%|.905|
| Dante |58.08%|65.93%|55.88%|.005|

Caesar token one-to-one tail is.315, despite its purity tail.010; label flexibility and weighting matter. Jerome is worse than its null mean token purity, so no all-author frequent-token success is claimed. Graph coverage is unchanged from231; these are not whole-text scores. Word-profile oracles range89.85–97.78% type-macro, leaving substantial grouping error rather than only unavoidable annotation ambiguity.

## Disconnected-graph representation limit

All runs occupy17 clusters. Aquinas/Caesar/Cicero/Dante use17 embedding dimensions, with5/11/6/10 zero eigenvalues respectively. Jerome has20 disconnected components, so completing the boundary eigenspace expands its embedding to20 dimensions, **all zero modes**. That embedding represents component membership but contains no within-component spectral directions. Clustering17 ways can merge components yet cannot meaningfully resolve the large mixed component internally. This limits interpretation of the Jerome failure and motivates one explicit geometry correction rather than a label-guided cluster-count search.

The embedding also has numerical distance ties, especially for disconnected components. The fixed run is reproducible on its frozen coordinates; no stability across initializations or graph perturbations is claimed. Oracle naming does not become an annotation-free named POS predictor.

## Audit and next experiment

Independent normalized-Laplacian eigenspace geometry, frozen-coordinate initialization/Lloyd replay, profile/stratum/null reconstruction and2000 assignment-dual certificates validate all actual/null alignment optima. Twenty hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration233/`.

Next freeze a component-aware embedding retaining **all zero modes plus the first17 positive-eigenvalue directions**, including complete boundary ties, for all five authors. Keep17 clusters, initialization seed, update rule and conditional-profile controls unchanged; compare233 exactly, no best-per-author winner. This tests whether the omitted within-component geometry explains the limitation. It remains an oracle grouping diagnostic; any eventual useful grouping still needs stable constraints or source-based naming before it becomes a decipherment input.
