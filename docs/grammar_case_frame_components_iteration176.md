# Iteration 176 — frame-preserving groups retain the conditional case signal

**Positive with limited new coverage:** keeping each word/frame combination separate avoids the failure of word-level components. Both-PRON/DET frame-group case consistency exceeds all199 word/POS-profile controls in both Cicero passages. There are larger groups, but replicated evidence for new indirect case relations is still absent; most components contain just two word types.

## Frozen design

Retain exact floor-five/two-shared-frame primary type edges. For each ordered frame, link only its primary-supported type pairs, and build connected components within that frame. Nodes are (opaque word ID, ordered frame); no edges join different frames. Freeze members, that frame's occurrence positions, direct/transitive member pairs and all size/coverage histograms before labels. Repeat for the original and16 existing word-null graphs.

Use the same175 recognized-case counts and five occurrence-POS strata. Primary: both-PRON/DET component-macro agreement, averaging eligible type-pair fractions within a group, then covered groups equally. Secondary: type-pair-macro and pooled counts. Keep all/direct/transitive modes, empty and case-free groups; on original components retain all199 frozen174 word/POS-profile permutations. Labels never choose nodes, edges or groups.

This is frame-group weighting, which differs from174's edge/frame weighting. Reconstruct the old edge/frame macro from direct detailed records as an independent baseline check; do not describe a difference in percentages as an improvement over174. The `types` metric counts word-frame nodes across components, while `case_types` counts distinct opaque word IDs.

## Label-free group coverage

| Passage | Groups | Size histogram | Groups with >=3 types | Word-frame nodes | Distinct word IDs | Member-pair instances | New transitive pair instances |
|---|---:|---|---:|---:|---:|---:|---:|
| Earlier | 106 | 95×2,9×3,2×4 | 11 | 225 | 53 | 134 | 10 |
| Replication | 220 | 173×2,30×3,13×4,1×5,3×6 | 47 | 511 | 92 | 396 | 86 |

The groups with at least three types account for7 earlier and13 replication groups with any both-PRON/DET case comparison (11 and35 eligible member-pair instances). Across all POS,8 and15 larger groups have comparable cases (12 and54 pair instances). These are coverage counts, not a gold-label selection rule. Repeated word pairs in different frames remain distinct pair instances.

## Conditional case consistency

| Passage | Stratum/mode | Case groups | Eligible member-pair instances | Component-macro agreement | Word-null maximum (at least actual/nonempty) | Profile-null maximum (at least actual/nonempty) |
|---|---|---:|---:|---:|---:|---:|
| Earlier | Both PRON/DET, all | 40 | 44 | 72.50% | 42.86% (0/16) | 66.46% (0/199) |
| Earlier | Both PRON/DET, direct | 40 | 44 | 72.50% | 60.00% (0/15) | 66.46% (0/199) |
| Earlier | Both PRON/DET, transitive only | 0 | 0 | — | 100.00% (—/14) | — (—/0) |
| Replication | Both PRON/DET, all | 51 | 73 | 72.22% | 51.67% (0/16) | 60.65% (0/199) |
| Replication | Both PRON/DET, direct | 49 | 59 | 71.09% | 58.33% (0/16) | 60.88% (0/199) |
| Replication | Both PRON/DET, transitive only | 7 | 14 | 76.19% | 75.00% (0/16) | 76.19% (1/199) |
| Earlier | All POS, all | 45 | 49 | 71.11% | 46.67% (0/16) | 67.96% (0/199) |
| Replication | All POS, all | 70 | 109 | 72.66% | 45.32% (0/16) | 62.67% (0/199) |

For all-mode both-PRON/DET groups, profile-null means are50.26% and49.22%, versus actual72.50% and72.22%. The zero-of199 results are descriptive comparisons on reused development data, not calibrated confidence in a new decipherment model.

The larger passage's14 transitive primary comparisons involve14 distinct word IDs and match case in11/14 occurrences (pooled78.57%; component-macro76.19%). One profile-preserving null ties its primary score; this is a limited lead rather than universal separation. The earlier passage has no case-comparable transitive primary pair at all. Its sole transitive case comparison across all POS is mixed-family and disagrees (0%), and all profile controls also give0%.

Mixed-family all-mode consistency is60% earlier (5 pair instances) versus75% for its direct-only subset (4), and70.83% replication (33) versus73.41% direct-only (22). The earlier mixed-family group does not clear controls; retain the previously stated cross-family limitation. Every group, component, stratum and null result remains in the artifacts.

## Interpretation and next step

Frame identity matters for composing this relation. Anonymous word/frame groups preserve conditional case compatibility, whereas merging all occurrences of each word into one global component failed in175. This supports retaining a context-specific soft morphological relation as a possible decipherment input. It does not establish globally shared case classes, named cases, inferred PRON/DET membership, syntactic links or lexical nuclei.

Coverage remains the bottleneck: only40/106 and51/220 groups have comparable both-PRON/DET cases, and identifying those groups currently uses reference labels for evaluation. These counts do not establish a deployable selection rule. Most groups are two-node restatements of direct relations, and the new transitive evidence has no comparable earlier-passage replication. Both passages are Cicero development data; gold reference availability remains a privilege.

Next proposed diagnostic: test a predeclared label-free shortlist based on endpoint frequency and repeated-frame support, with frequency-only controls and explicit unconditional case applicability as well as conditional consistency. Freeze the ranking and cutoffs before evaluating labels; retain all proposed lists and ties. This addresses which potentially useful groups can actually be selected without POS/case truth, rather than assuming the scored family is detectable.

## Verification

Independent per-frame union-find reconstruction checked34 graph views, memberships, positions, direct flags and size/coverage histograms. Independent matrix counts and component summaries verified118,207 detailed member-pair records across432 graph/assignment views, all null contrasts and direct/transitive count partitions. Direct records reproduce170 old edge/frame baseline metric groups across34 original/word-null views, with case counts exact and macro agreement within1e-12. Frozen hashes passed. The broader test suite was not rerun for this reference-only diagnostic; no new annotations or reserved/sealed data were used.

Runner: `benchmarks/grammar_case_frame_components_iteration176.py`; reviewer: `benchmarks/grammar_case_frame_components_iteration176_review.py`. Frozen design, components, coverage, complete compressed scores, summaries, contrasts, audit and verification manifest: `experiments/results/grammar-restoration/iteration176/`.
