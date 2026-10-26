# Iteration223: replacement edges carry soft POS-profile information

Edges have higher global POS-profile compatibility than frequency-stratified profile shuffles in all four authors. The signal includes words without recognized Case, so such words should not be discarded as grammatically useless. However this first control does not preserve Case applicability: it does not yet establish POS information beyond the already detected Case-bearing separation. No POS labels are inferred.

## Frozen measurement

Use all546 endpoints of the fixed193 conservative graph and cached201 POS references. For each word, form its global occurrence-weighted POS distribution, retaining every cached tag. Edge compatibility is the dot product of the two distributions; primary statistic is its unweighted edge mean. This is expected POS agreement of independently sampled global word occurrences, **not observed POS agreement in the queried shared frames**, hard word-POS identity or context-specific surplus.

Shuffle whole profiles among nodes within fixed global-frequency bins5–9,10–19,20–49,50–99,100+, sorted opaque IDs,199 seeds22300–22498. Preserve each profile intact and stratum profile counts. Freeze graph/protocol before reference projection; retain all authors/tags and fixed both-Case/mixed/neither-Case groups. Group memberships stay attached to actual nodes across shuffles, so the group controls do not preserve the labels defining those groups. No fits, new raw text, annotations, reserves, word identities or target-selected winner.

## Results

| Author | Edges | POS-profile agreement | Frequency-null mean | Null maximum | Upper tail |
|---|---:|---:|---:|---:|---:|
| Aquinas |565|21.13%|10.69%|14.53%|.005|
| Caesar |51|44.24%|14.36%|26.04%|.005|
| Cicero |93|36.91%|16.59%|24.13%|.005|
| Jerome |300|55.37%|16.17%|21.83%|.005|

All four real means exceed all199 fixed shuffles. These are separate reused-development diagnostics, not multiplicity-adjusted inference, independent edge samples, or accuracy of a named-POS restorer. The large residual incompatible mass also rules out treating every replacement edge as a hard same-POS constraint.

| Author | Both Case-bearing agreement | Mixed Case agreement | Neither Case-bearing agreement | Neither-Case null mean |
|---|---:|---:|---:|---:|
| Aquinas |29.57%|4.37%|31.45%|9.75%|
| Caesar |53.40%|0%|72.11%|14.87%|
| Cicero |52.81%|5.51%|40.42%|16.32%|
| Jerome |64.25%|16.71%|69.76%|16.37%|

Both-Case and neither-Case means exceed all frequency-only shuffles for every author; mixed-Case groups do not (upper tails.995,1.000,.950,.405). Because Case membership and POS are correlated, these subgroup contrasts require the stronger control below. They are not additional independent discoveries.

All-tag contributions are retained in artifacts. Largest whole-graph contributions vary by author: NOUN in Aquinas(.08318), ADP in Caesar(.15414), PRON in Cicero(.15475), VERB in Jerome(.21333). Non-Case structures therefore include potentially useful classes such as adpositions and conjunctions, while the useful relation is not confined to a universal POS category. These are gold-reference descriptions, not recovered identities.

## Verification and next control

Independent rational reconstruction verifies546 profiles,200791 null-edge comparisons, all16 groups, per-tag contribution sums and20 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration223/`.

Next shuffle whole POS profiles within **frequency bin × global Case-bearing status**, using the same graph, statistic, group definitions and199 predeclared seeds. This preserves the already observed Case split and tests the narrower claim of POS compatibility beyond it. Keep all authors/groups, no selected POS family or new annotations. If the signal survives, it would justify investigating soft pairwise POS constraints as an output in its own right; if it does not, retain only the established coarse Case relation. Neither outcome by itself identifies named POS labels from ciphertext.
