# Iteration225: anonymous selection enriches POS-compatible pairs in four authors

**Preserve this inferred relational output:** a source-trained anonymous edge ranker selects ten pairs per author with mean gold-reference POS-profile compatibility69.47% Aquinas,71.20% Caesar,78.91% Cicero and88.67% Jerome. Each exceeds its whole-graph baseline; rich19 beats the frequency/support control on three authors and ties Aquinas. Target POS is absent from fitting and selection. These are selected pairwise affinities, not named POS assignments, binary pair accuracy, exact Latin words or a fresh-author confirmation.

## Frozen method

Use fixed193 graph edges and anonymous19 features: symmetric endpoint frequency/outside-query-context summaries and shared-frame support. Control3 uses columns0,9,18: mean log frequency, absolute log-frequency difference and log support. Source target is223's dot product of global word-POS profiles. This measures expected POS agreement of independently sampled global occurrences, not queried-token POS equality or contextual surplus.

Leave each of four authors out; use all other three, equal total source-author mass, source-only weighted standardization, ridge.1 on slopes and free intercept. Minimize half weighted MSE plus.05 squared slope norm. Freeze copied features before label loading and all models/predictions/tied top10/top20 before evaluation. All authors and both models retained, no feature/threshold/author-specific winner selection, new raw annotation or reserve use. Scores are unbounded rankings, not calibrated probabilities. The model learns from source POS-derived targets, so this is supervised grammatical transfer, not language-free discovery.

## Held-out-author development results

| Author | Whole-graph mean | Rich19 top10 | Control3 top10 | Rich19 top20 | Control3 top20 |
|---|---:|---:|---:|---:|---:|
| Aquinas |21.13%|69.47%|69.47%|74.24%|59.06%|
| Caesar |44.24%|71.20%|58.08%|57.60%|60.34%|
| Cicero |36.91%|78.91%|72.84%|73.77%|66.67%|
| Jerome |55.37%|88.67%|87.95%|72.98%|79.09%|

All top10 lists contain exactly ten edges. All rich top20 lists contain20; Jerome control top20 includes21 due a score tie. Rich19 is not universally better at top20: Caesar and Jerome favor the count control. Nor does the Aquinas top20 exceeding its top10 establish monotonic confidence. Keep fixed list sizes and all results rather than choose a model or cutoff using target annotations.

Rich top10 spans14/19/19/20 distinct opaque word types in Aquinas/Caesar/Cicero/Jerome, respectively. These are overlapping pair constraints, not ten independent recovered classes, twenty independently identified words or a common correct Latin-word intersection. Their endpoint coverage is6.93%,31.67%,25.33%,9.57% of graph endpoint types. No named POS is assigned to any endpoint by this regressor.

Gold oracle lists show substantial headroom, with exact ties retained: Aquinas top10/top20 both expand to60 perfect-profile-compatible edges; Jerome both expand to134; Cicero top10 expands12 with mean1 and top20 expands22 with mean.9889; Caesar selects10/.9996 and20/.9327. These are evaluation-only lists, not inferred output or fixed-size oracle success claims.

## Why this matters and what remains open

This is closer to a potential decipherment input than the preceding gold-only relationship tests: the selection itself uses anonymous target features and source-trained models. A later decoder could consume soft pairwise POS-compatibility preferences without requiring named POS or exact words first. The reported compatibility is still evaluated from cached gold; it does not quantify calibrated confidence on each selected edge, prove robust transfer to Voynich, or establish reliable nuclei.

The authors, feature family and development corpus have been repeatedly explored. Baseline enrichment is encouraging, but requires controls against source-label coincidence and concentration in repeated words/contexts. Source supervision, label ambiguities, dependent pairs and limited candidate coverage remain explicit limitations.

## Independent audit and next checks

Independent rational reconstruction verifies1009 target edge labels, source weights/scales, eight augmented least-squares refits, predictions,24 model/oracle lists, means/endpoint coverage and19 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration225/`.

Next freeze two robustness checks for both models/all authors: source-label permutations within each source author, with199 fixed seeds and unchanged fitting/design, and greedy prediction-ranked endpoint-disjoint top10/top20 lists. The first tests whether real source label-feature alignment improves selection beyond a shuffled-label fit; the second tests whether useful mean compatibility survives reduced repeated-word concentration. Greedy selection uses descending frozen prediction then original edge index to resolve ties, never gold; report if fewer than requested pairs are available. Distinct endpoints do not make contextual observations independent. Do not claim named POS restoration or choose winners from these reused targets.
