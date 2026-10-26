# Iteration224: POS compatibility survives Case-conditioned controls

**Preserve POS compatibility beyond the coarse Case split:** all four whole-graph POS-profile agreement means exceed every frequency×Case-status profile shuffle. The neither-Case edge group also survives in all four authors. This establishes a reference-level relationship signal that might support grammatical constraints independently of exact words; it does not yet infer POS or rank reliable edges without annotations.

## Frozen control

Reuse223 profiles, graph, edge groups and actual values exactly. Shuffle whole global POS profiles among nodes within the fixed frequency bins5–9,10–19,20–49,50–99,100+, now also preserving global recognized-Case-bearing status. Sorted opaque IDs,199 seeds22400–22598. Primary statistic remains unweighted edge mean profile dot product; all POS tags, authors and predeclared subgroups retained. No refits, raw text, new annotations, reserves, threshold tuning or chosen POS family.

This preserves coarse Case separation and frequency strata, not exact frequency, degree, syntactic position or author-internal work. The statistic measures global-profile compatibility, not observed shared-slot POS equality, contextual surplus or a named POS prediction. Finite conditional shuffle tails are separate reused-development diagnostics, without across-family multiplicity claims or independent edge assumptions.

## Whole-graph result

| Author | Edges | Actual compatibility | Frequency×Case null mean | Null maximum | Upper tail |
|---|---:|---:|---:|---:|---:|
| Aquinas |565|21.13%|13.66%|18.15%|.005|
| Caesar |51|44.24%|19.57%|32.60%|.005|
| Cicero |93|36.91%|22.74%|31.94%|.005|
| Jerome |300|55.37%|22.75%|30.36%|.005|

Conditioning raises the null means relative to223, as expected if the earlier Case split explains part of the POS association. It does not explain the entire whole-graph signal. There are38 nonempty strata:10 Aquinas,9 Caesar,9 Cicero,10 Jerome. Cicero has one singleton stratum; Aquinas and Cicero each have one profile-invariant stratum. Their restricted permutation opportunities are explicitly retained, not dropped to improve a result.

## Subgroups and narrowed claims

| Author | Both-Case tail | Mixed-Case tail | Neither-Case actual | Neither-Case null mean | Neither-Case tail |
|---|---:|---:|---:|---:|---:|
| Aquinas |.105|.060|31.45%|12.78%|.005|
| Caesar |.005|1.000|72.11%|29.35%|.005|
| Cicero |.080|.200|40.42%|16.87%|.005|
| Jerome |.005|.005|69.76%|24.77%|.005|

The stronger control removes a fixed.05 separation for Aquinas/Cicero **both-Case** groups. Preserve that limitation rather than carrying forward223's weaker-control result unchanged. Neither-Case groups, however, retain excess compatibility in every author, and Jerome's mixed group also exceeds all shuffles. These correlated subgroup results are descriptive, not independent discoveries or a selected deployment rule.

Actual whole-graph compatibility spans21–55%, leaving too much incompatible mass for a hard same-POS constraint on every edge. Global POS profiles may be ambiguous, and the graph does not label which edges provide the reliable information. These are soft anonymous relationships whose labels are currently measured with gold; no named cases/POS, Latin nuclei or Voynich plaintext have been restored.

## Audit and next experiment

Independent rational profile reconstruction and constrained permutation replay verify200791 null-edge comparisons,38 strata,16 groups, exact223 observed values and18 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration224/`.

Next test annotation-free selection of these potentially useful relations: source-trained regression of POS-profile compatibility from the existing193 anonymous19 edge features, against the fixed3-feature frequency/support control. Equal-author weights over the other three authors, source-only standardization, ridge.1, fixed tied top10/top20, no author-specific feature/model winner or threshold search. Evaluate selected mean compatibility and coverage against the whole graph, both controls and an explicitly gold oracle headroom list. Scores are unbounded ranking scores, not probabilities; target POS appears only after predictions/lists freeze. This tests whether the reference signal can become an inferred grammatical input without requiring exact word restoration.
