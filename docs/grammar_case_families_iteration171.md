# Iteration 171 — the case signal is concentrated in pronoun/determiner pairs

**Preserve, with a narrower interpretation:** the two Cicero graphs show reproducible conditional case agreement almost exclusively on occurrence pairs involving at least one pronoun or determiner. They do not currently support a broad claim about nominal morphology.

## Frozen evaluation

Keep the floor-five, two-distinct-shared-frame graphs from iterations 166/168 unchanged. Partition Cartesian occurrence pairs into three disjoint groups: at least one POS in PRON/DET; neither PRON/DET and both in NOUN/PROPN/ADJ/NUM; all other pairs. Report the full graph and the union of the last two groups as fixed controls. POS and case references travel with each token through the same sixteen original shuffles; all groups, including empty ones, are retained.

Labels are used only to describe where the signal occurs, never to build or filter a deployable graph. Within each group, compare only recognized case labels, average eligible occurrence pairs within a frame, then frames within an edge, then covered edges. Edges can belong to multiple strata through occurrence ambiguity, so macro means and edge counts need not add; pair counts must partition exactly. Applicability denominators retain all original graph edges/frames, while pair denominators are the selected family's pairs. No new annotations or reserved/sealed data were used.

## Results

| Passage | Pair group | Case edges | Eligible case comparisons | Matching cases | Edge/frame macro agreement | Nonempty nulls | Highest null |
|---|---|---:|---:|---:|---:|---:|---:|
| Earlier | All | 18 | 73 | 60 | 72.22% | 16 | 50.00% |
| Earlier | PRON/DET involving | 18 | 73 | 60 | 72.22% | 16 | 50.00% |
| Earlier | Neither PRON/DET | 0 | 0 | 0 | — | 0 | — |
| Earlier | Both nominal, neither PRON/DET | 0 | 0 | 0 | — | 0 | — |
| Earlier | Other neither | 0 | 0 | 0 | — | 0 | — |
| Replication | All | 36 | 118 | 89 | 70.41% | 16 | 55.56% |
| Replication | PRON/DET involving | 35 | 116 | 87 | 69.56% | 16 | 55.56% |
| Replication | Neither PRON/DET | 1 | 2 | 2 | 100.00% | 2 | 100.00% |
| Replication | Both nominal, neither PRON/DET | 1 | 2 | 2 | 100.00% | 2 | 100.00% |
| Replication | Other neither | 0 | 0 | 0 | — | 0 | — |

The PRON/DET-involving group accounts for **73/73** earlier case comparisons and **116/118 (98.31%)** in replication; its agreement exceeds all sixteen controls in each passage. The replication group involves 32 supported types, versus 33 in the full case-comparable graph. The only other case edge has two matching occurrence comparisons, and one of its two nonempty nulls also scores 100%; it provides no useful evidence of generalization beyond the PRON/DET family.

## Implication for decipherment

This is a narrower candidate grammatical relation worth preserving: repeated contexts connect forms with compatible case, predominantly in a pronoun/determiner family. Existing inference has not identified that family, detected case-bearing positions, named cases, recovered antecedent links, or restored lexical identities. Gold family/case availability remains an evaluation privilege, and the two passages are same-author reused development material. Neither percentages nor family labels should be used as a hard decoder constraint without further validation.

Next diagnostic: split PRON/DET-involving comparisons into both endpoints PRON/DET versus exactly one, and show exact POS-pair composition under the same frozen graphs/nulls. This will distinguish substitution among pronominal forms from compatibility across grammatical families and guide any later candidate-morphology experiment. Freeze definitions before scoring; do not infer a pronoun detector from this label-conditioned analysis.

## Verification

Independent brute-force replay verified 34 graph views, 3,899 edge records, 10,000 Cartesian occurrence pairs and 170 stratum metric groups. All three leaf-group count partitions, references aligned to the exact word streams, detailed scores, summaries, null contrasts, and historical all-group baselines passed. Thirteen input/reference/score hashes passed. The broader test suite was not rerun for this reference-only diagnostic.

Runner: `benchmarks/grammar_case_families_iteration171.py`; independent review: `benchmarks/grammar_case_families_iteration171_review.py`. Frozen design, references, scores, summaries, contrasts and audit are in `experiments/results/grammar-restoration/iteration171/`; the verification manifest covers the report, code, and artifacts.
