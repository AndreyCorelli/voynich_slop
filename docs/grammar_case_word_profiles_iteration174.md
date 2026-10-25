# Iteration 174 — case association exceeds word/POS-profile-preserving controls

**Highlight this positive result:** both-PRON/DET case agreement in the unchanged shared-context graphs exceeds all199 permutations that preserve every word's exact-POS case profile, in both Cicero passages. The control meaningfully changes graph-relevant labels. Unlike iteration173, it preserves word-specific empirical morphology, supporting occurrence-context association beyond those profiles under the tested null.

## Frozen test

Use the exact two original floor-five/two-distinct-frame graphs and172 POS/case references. Group all passage tokens by opaque word ID plus exact POS, sort group keys, and permute case labels within every group for each of199 fixed seeds17400–17598. Initialize NumPy default_rng for each seed/pool, visiting all groups including singletons. Missing/unrecognized cases participate and every word/POS case inventory is preserved. Freeze complete assignments, inventories, group indices, graph positions and movement counts before evaluating case scores; freeze detailed scores before aggregation.

Primary: both PRON/DET occurrences. All, PRON/DET involving, exactly one PRON/DET and neither are fixed descriptive strata. Weight eligible occurrence comparisons within each frame, average eligible frames within each edge, then average covered edges exactly as166/172. Empty actuals remain undefined; calculate corrected conditional rank tails only when actual and all199 controls have case comparisons. Labels stratify evaluation and construct diagnostic nulls, never select inference edges.

## Conditional case agreement

| Passage | Group | Actual | Null mean | Null range | Nulls at least actual / nonempty | Corrected tail |
|---|---|---:|---:|---:|---:|---:|
| Earlier | All | 72.22% | 53.90% | 38.89–70.83% | 0/199 | .005 |
| Earlier | PRON/DET involving | 72.22% | 53.90% | 38.89–70.83% | 0/199 | .005 |
| Earlier | Both PRON/DET (primary) | 71.88% | 49.77% | 32.37–67.19% | 0/199 | .005 |
| Earlier | Exactly one PRON/DET | 75.00% | 86.93% | 50.00–100.00% | 187/199 | .940 |
| Earlier | Neither | — | — | — | — /0 | — |
| Replication | All | 70.41% | 51.90% | 39.87–63.27% | 0/199 | .005 |
| Replication | PRON/DET involving | 69.56% | 50.53% | 38.15–62.22% | 0/199 | .005 |
| Replication | Both PRON/DET (primary) | 67.01% | 45.63% | 31.34–58.68% | 0/199 | .005 |
| Replication | Exactly one PRON/DET | 75.13% | 61.22% | 48.99–77.78% | 3/199 | .020 |
| Replication | Neither | 100.00% | 100.00% | 100.00–100.00% | 199/199 | 1.000 |

The primary actual-minus-null-mean differences are22.11 and21.38 percentage points. All/primary/mixed/neither case-edge counts stay exactly18/16/2/0 earlier and36/24/11/1 replication in all199 permutations; the PRON/DET-involving counts are18/35. Original scores exactly reproduce172. The descriptive corrected tail is `(1 + count >= actual)/200`, not a fresh validation probability or estimated probability of successful decipherment.

## Is the permutation inert?

A potentially movable position has more than one distinct case label in its passage-wide word/POS group, including missing labels. Positions below are unique token indices used by any Cartesian pair in that POS stratum, counted before filtering for case availability; strata may overlap through occurrence ambiguity. Every potentially movable position here originally has a recognized case.

| Passage | Stratum | Graph-relevant positions | Potentially movable | Actually changed per permutation, min–max (mean) |
|---|---|---:|---:|---:|
| Earlier | All | 267 | 90 | 19–42 (29.79) |
| Earlier | PRON/DET involving | 148 | 90 | 19–42 (29.79) |
| Earlier | Both PRON/DET | 99 | 75 | 14–37 (24.96) |
| Earlier | Exactly one PRON/DET | 56 | 18 | 1–11 (5.67) |
| Earlier | Neither | 121 | 0 | 0–0 (0.00) |
| Replication | All | 602 | 193 | 54–82 (67.53) |
| Replication | PRON/DET involving | 318 | 187 | 52–81 (65.87) |
| Replication | Both PRON/DET | 129 | 110 | 29–53 (41.30) |
| Replication | Exactly one PRON/DET | 200 | 87 | 18–37 (28.30) |
| Replication | Neither | 319 | 6 | 0–5 (1.65) |

The six movable replication-neither positions do not change its single case-comparable edge's score; actual case evidence there remains just two comparisons. This is not new evidence for broader nominal agreement. Full position lists and every seed's changes are preserved in `movement.json`.

## Interpretation and limits

The within-family association cannot be reproduced simply by keeping each word's empirical case profile and randomly placing those cases among its same-POS occurrences. This strengthens the case for context-sensitive morphological compatibility as a potential input to another decipherment method. It remains a conditional diagnostic: gold POS/case availability is supplied, each occurrence is evaluated on a reused development graph, both passages are Cicero, and the test does not control all possible local distribution shifts. No automatic case-bearing detector, named case assignments, POS labels, syntactic links or lexical nuclei have been produced.

The cross-family lead remains qualified: replication is above most but not all controls, and earlier scores below its null mean. Never promote it as a replicated cross-family constraint. Shared-frame endpoint words occur in separate positions; the relation is substitution compatibility, not agreement between co-occurring words or antecedent attachment.

Next proposed check: determine whether the original label-free graph combines these pairwise relations into coherent anonymous grammatical groups. Freeze connected components using only opaque IDs and edges, evaluate occurrence-case consistency and coverage with existing references, and retain all components and matched controls. Do not select case-pure components using labels or infer named cases from them. This tests whether composition of the relation is useful, rather than assuming pairwise compatibility is transitive; failure would favor retaining a soft pairwise constraint.

## Verification

Independent brute-force replay verified398 permutations and all word/POS inventories, reference-stream alignment, graph-position universes and every mobility count,400 graph/assignment views,35,600 edge records,129,200 Cartesian pairs,2,000 stratum metric groups, disjoint pair-count identities, all summaries/contrasts and exact172 baselines. Input/assignment/score hashes passed. The broader test suite was not rerun for this reference-only diagnostic. No new annotations or reserved/sealed data were used.

Runner: `benchmarks/grammar_case_word_profiles_iteration174.py`; reviewer: `benchmarks/grammar_case_word_profiles_iteration174_review.py`. Artifacts under `experiments/results/grammar-restoration/iteration174/` include frozen proposals/design, full compressed assignments and detailed scores, group inventories, movement counts, summaries, contrasts, audit and verification manifest.
