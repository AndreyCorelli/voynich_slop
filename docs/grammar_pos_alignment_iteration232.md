# Iteration232: oracle naming cannot rescue the current predicted groups

The four development authors remain weak even after optimal target-gold class renaming: node-model type-macro scores26.14% Aquinas,21.75% Caesar,29.34% Cicero,33.49% Jerome. Dante improves12.85→34.78%, indicating a naming mismatch there, but not reliable grouping. The current feature/regression/argmax pipeline mixes grammatical classes and collapses to four or five occupied groups; naming alone is not the main universal bottleneck.

## Frozen diagnostic

Keep all231 predictions and argmax groups unchanged: source prior, node model, support-pair averaging and rich-pair averaging in five authors. Freeze group memberships before truth projection. Build predicted-group×true-POS-profile-mass contingency tables with equal type weights and separately with covered-token frequencies.

Evaluate identity naming, oracle target-majority constant prediction, best one-to-one17-label assignment, and many-to-one group purity. Each weighting gets its own oracle mapping; neither mapping is transferable or deployed. Also retain the per-word best-profile-tag ceiling, accounting for words genuinely occurring with multiple tags. Empty predicted groups have arbitrary optimal labels, so report mappings only for occupied groups. No fits, feature changes, thresholds, new annotation, raw text or reserves; Dante remains consumed development data.

## Node-model type-macro ceilings

| Author | Occupied groups /17 | Identity names | Target majority | Oracle one-to-one | Oracle many-to-one purity |
|---|---:|---:|---:|---:|---:|
| Aquinas |5|25.09%|25.67%|26.14%|27.92%|
| Caesar |4|20.31%|20.00%|21.75%|23.42%|
| Cicero |4|28.45%|31.14%|29.34%|32.72%|
| Jerome |5|33.08%|25.74%|33.49%|33.49%|
| Dante |5|12.85%|18.83%|34.78%|34.78%|

One-to-one alignment can fall below the target-majority baseline: distinct predicted groups must receive distinct labels, while a constant predictor uses the same label everywhere. Many-to-one purity removes that restriction and still remains low. Thus low identity accuracy is not hiding a generally clean partition with permuted names. Dante has a larger naming problem, but even its target-gold best mapping is only34.78%.

## Token-weighted node-model ceilings

| Author | Identity names | Target majority | Oracle one-to-one | Oracle purity |
|---|---:|---:|---:|---:|
| Aquinas |15.03%|16.25%|22.13%|24.37%|
| Caesar |16.15%|30.70%|31.20%|32.75%|
| Cicero |27.65%|25.12%|29.38%|32.97%|
| Jerome |33.21%|22.14%|39.11%|39.11%|
| Dante |7.56%|22.64%|31.57%|31.57%|

These cover graph-word occurrences only, not the whole text. A larger token-weighted alignment gain, notably Caesar/Dante, does not establish strong classes: it often approaches a high target-majority baseline. The target-majority itself uses gold and is a diagnostic comparator.

Pair refinements do not create a reliable partition: their type-macro oracle one-to-one scores span23.42–34.78% across authors/methods, with Aquinas26.64%, Cicero28.85–29.34%, Jerome32.53–33.11%. All prior-only predictions form one group, whose best oracle relabeling equals target majority exactly. This guards against mistaking a renamed majority class for recovered structure.

## Interpretation

Stop treating label-name calibration as a sufficient repair for the current node predictor. Its anonymous counts/entropies, linear profile fit and argmax grouping have not produced useful named-POS recovery or a strong hidden POS partition. This does not refute the independent pairwise graph compatibility evidence: a graph can encode useful local relationships without this node representation yielding coherent classes. Exact Latin nuclei and Voynich plaintext remain unresolved.

## Audit and next experiment

Independent scalar contingencies verify40 author/method/weighting groups. Assignment-dual linear programs certify optimality of all40 one-to-one scores, alongside purity bounds, exact231 identity metrics and23 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration232/`.

Next test a genuinely different representation: graph-only grouping rather than regression argmax. Freeze a normalized-Laplacian spectral embedding and17-way clustering, using the source POS inventory size as a fixed capacity, one deterministic seed and no target-label choice. Score only with explicit oracle alignment/purity and profile-shuffle controls preserving frequency×Case status. Cluster formation must see anonymous graph structure alone; source/target POS supplies evaluation only. This tests whether the earlier relationship signal supports latent grammatical groups, with no promise of names or calibrated classes. If it also fails beyond controls, retain pairwise relations as soft decoder inputs rather than forcing them into POS classes.
