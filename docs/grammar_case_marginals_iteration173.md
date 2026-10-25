# Iteration 173 — POS-specific case frequencies do not explain the association

**Preserve this positive diagnostic:** on the unchanged shared-context graphs, both-PRON/DET case agreement exceeds all 199 within-exact-POS case-label permutations in each Cicero passage. This rules out the tested explanation based solely on whole-passage POS-specific case frequencies. It does not isolate contextual disambiguation from word-specific morphology or provide a new predictor.

## Frozen test

Keep the exact two original floor-five/two-frame graphs and POS/case references from iteration172. For each pool, generate 199 fixed seeds17300–17498; initialize NumPy default_rng per seed, visit POS tags in sorted order, and permute all token case labels within each exact POS. Missing and unrecognized labels are included, preserving the entire POS-specific case inventory. Word identities, POS, positions and frames remain fixed. Save assignments before evaluation and compressed detailed scores before aggregates.

Primary stratum: both occurrences PRON/DET. Fixed descriptive strata: all, PRON/DET involving, exactly one PRON/DET, neither. Use unchanged recognized-case, frame-within-edge/edge-macro weighting, retaining all empty groups and coverage changes. Report the corrected conditional rank tail `(1 + number of null scores >= actual)/200` only when actual and all199 controls are nonempty. These are descriptive randomization results on reused development data and a previously investigated graph rule, not fresh validation or calibrated confidence in a decipherment.

## Results

| Passage | Group | Actual macro agreement | Null mean | Null maximum | Nulls at least actual / nonempty | Corrected tail |
|---|---|---:|---:|---:|---:|---:|
| Earlier | All | 72.22% | 27.91% | 45.31% | 0/199 | .005 |
| Earlier | PRON/DET involving | 72.22% | 27.85% | 45.31% | 0/199 | .005 |
| Earlier | Both PRON/DET (primary) | 71.88% | 28.61% | 50.47% | 0/199 | .005 |
| Earlier | Exactly one PRON/DET | 75.00% | 21.57% | 100.00% | 11/199 | .060 |
| Earlier | Neither | — | 34.52% | 100.00% | — /42 | — |
| Replication | All | 70.41% | 26.29% | 36.00% | 0/199 | .005 |
| Replication | PRON/DET involving | 69.56% | 26.33% | 36.55% | 0/199 | .005 |
| Replication | Both PRON/DET (primary) | 67.01% | 27.89% | 43.08% | 0/199 | .005 |
| Replication | Exactly one PRON/DET | 75.13% | 23.07% | 49.07% | 0/199 | .005 |
| Replication | Neither | 100.00% | 24.75% | 100.00% | 15/199 | .080 |

Both-family primary coverage remains exactly16 earlier and24 replication case edges in every null and actual. Broader groups change coverage as missing labels move: all-group null case edges18–20 earlier and36–39 replication; mixed-family2–3 and11–13; neither0–2 and1–2. Actual comparison counts remain those of172:69/85 primary pairs,4/31 mixed-family pairs,0/2 neither. Empty actual earlier-neither is not scored as perfect and has no tail. Missing nulls are retained in the artifacts rather than replaced.

## What this adds

The high observed scores are not reproduced merely by drawing cases from the relevant POS inventories: the primary observed-minus-null-mean gaps are43.26 and39.12 percentage points. The mixed-family result remains a limited lead: it clears this control in replication but has only four earlier comparisons and a .060 descriptive tail there. The two-comparison replication-neither group provides no convincing wider-family evidence.

This test deliberately breaks word-specific morphology as well as contextual case assignment. A frequent word's normal case profile might therefore explain much of the observed score while still constituting useful case-compatible grouping; rejecting this null is not proof that context disambiguates case within a word. Gold POS/case availability remains an evaluation privilege, both passages come from Cicero development data, and no labels, lexical nuclei, syntactic links or new decipherment algorithm have been restored.

Next proposed diagnostic: permute case labels within each **opaque word ID and exact POS** on the fixed graphs. Preserve missing labels and each word/POS case profile, freeze seeds and assignments, retain all sparse groups, and report how many graph-relevant positions can actually change. This asks whether the specific occurrence contexts add information beyond word-level morphology; a largely invariant result would narrow the interpretation rather than invalidate the existing type-grouping association.

## Verification

Independent brute-force replay checked all398 permutations and POS inventories, reference-to-word-stream alignment,400 graph/assignment views,35,600 edge records,129,200 Cartesian pairs,2,000 stratum metric groups, pair partitions, every contrast and exact172 original baselines. Ten input/assignment/score hashes passed. The broader test suite was not rerun for this reference-only diagnostic. No new annotations, reserves or sealed data were accessed.

Runner: `benchmarks/grammar_case_marginals_iteration173.py`; reviewer: `benchmarks/grammar_case_marginals_iteration173_review.py`. Frozen designs, complete assignments, detailed scores, summaries, contrasts, audit and verification manifest are in `experiments/results/grammar-restoration/iteration173/`.
