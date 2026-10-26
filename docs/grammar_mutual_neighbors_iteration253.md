# Iteration 253: local stable neighbors add a recurring Jerome relation

**HIGHLIGHT: a seed-free local relation finds the same pure-reference ADV pair in two Jerome sentence splits, where strict whole-graph clustering found no shared group.** It covers747/30,000 tokens (2.49%) by global word frequency. Aquinas retains its known AUX pair with the same low aggregate recurrence, rather than gaining reliable recovery.

This preserves a second author's small cross-half grammatical signal under the new relation rule. Neither class names nor word identities are inferred, and this new rule still requires matched order controls before decoder use.

## Frozen change

Replace global k-means partition/co-assignment with **mutual nearest-neighbor pairs** in fixed time-one diffusion geometry. Exclude self and retain all neighbors within1e-10 of the row minimum. A pair must be mutual in the initial graph and every one of31 sentence-deletion graphs; missing or ineligible graphs fail. Cross-half output is the direct pair intersection. Do not merge pairs transitively into classes.

Graph frequency>=5, two shared frames, initial/deletion graphs and eligibility>=17 nodes remain unchanged. This tests local relations without changing graph coverage. All five full texts,190 original random halves and38 previously used Aquinas252 halves are included; the latter are explicitly reused diagnostics, not fresh validation. All233 case outputs and114 cross-half pair sets are frozen before cached POS evaluation. No neighbor count, diffusion time, tolerance or confidence threshold is searched.

## Cross-half outcomes

| Dataset and split family | Prior diffusion clustering: nonempty splits /19 | Local stable neighbors: nonempty splits /19 | New returned pair occurrences | Fully pure pair occurrences |
|---|---:|---:|---:|---:|
| Aquinas discovery246 |3|2|2|2|
| Aquinas reused252 |3|1|1|1|
| Caesar246 |0|0|0|0|
| Cicero246 |0|0|0|0|
| Jerome246 |0|2|2|2|
| Dante246 |0|0|0|0|

Aquinas returns exactly the same two-word reference-AUX pair as before: at24603/24616 and25215. Aggregate recurrence remains2/19 and1/19, though the individual splits differ from clustering. Its global token coverage is1,252/30,000 (4.17%). None of the three fixed ADP-triple pair constraints survives the local rule in either split family; the triple is not recovered. This is a precision/coverage change, not an across-the-board improvement.

Jerome returns one identical two-word pair at24606/24609. Both global profiles are100% ADV in the reference, covering747 tokens (2.49%). This is a different relation from the earlier six-word VERB core. It is absent from the full-text stable-neighbor output, which is empty, so output remains non-monotonic with sample size and recurrence is rare. Its two appearances are not independent text replications.

All five shared pair occurrences across these families are reference-pure, but they represent just two distinct pairs in two corpora. This selected reused-development observation is not general grammatical precision or a calibrated confidence estimate.

## Full-text behavior remains inconsistent

| Author | Stable local pairs | Mean global POS compatibility | Fully pure pairs | Covered full-text tokens |
|---|---:|---:|---:|---:|
| Aquinas |2|100%|2|223|
| Caesar |2|26.38%|0|229|
| Cicero |3|80.94%|2|1,016|
| Jerome |0|Undefined|0|0|
| Dante |1|100%|1|794|

Aquinas's incompatible full-text pair is removed, and Dante now has one pure full-text relation instead of the previous zero-compatibility pair. Caesar remains poor, Cicero retains a mixed pair, and Jerome's full output disappears. Therefore stable local neighbors alone cannot be trusted as a universal grammatical oracle. Reference purity evaluates pairs after anonymous selection; it does not recover named tags.

## Next proposed control

Run matched order-control pilots for **both Aquinas and Jerome**, retaining all19 fixed shuffle seeds24000–24018 and all19 original split seeds per control. Apply the identical local-neighbor/deletion/cross-half rule and score the largest fully reference-POS-pure shared pair over every split and class (real score2 for each author, zero if absent). Reuse Aquinas's frozen251 control graphs and the real253 outputs; construct the corresponding Jerome control graphs with exactly the same masking and deletion rules. Freeze every anonymous result before reference scoring and keep all empty outputs.

Report the finite19-control tail separately for each author, with no selected class, split or author winner and no parameter adjustment. This is a targeted two-author reused-corpus pilot, not fresh confirmation. It checks whether the new anonymous pair rule has order specificity rather than inheriting the old clustering controls. If favorable, unused Jerome split validation remains necessary.

## Goal and audit

Preserve the new Jerome relation as a potential small grammatical input while keeping the limited recurrence and false full-text relations explicit. No exact nuclei, four-text word intersection, named-POS model or Voynich decipherment is established. No raw annotations, reserves or sealed Seneca gold were consumed.

Independent matrix exponentiation reconstructs all4,811 eligible graph geometries and nearest sets; all6,061 graph-relation cases, 233 stable case intersections, 114 cross-half intersections, all author/pair metrics, four fixed-group summaries and503 hashes pass. Frozen250/252 inputs are unchanged. The final manifest freezes the aggregate summary, both runners, this report and all outputs.

Artifacts: `experiments/results/grammar-restoration/iteration253/`; runner: `benchmarks/grammar_mutual_neighbors_iteration253.py`; reviewer: `benchmarks/grammar_mutual_neighbors_iteration253_review.py`.
