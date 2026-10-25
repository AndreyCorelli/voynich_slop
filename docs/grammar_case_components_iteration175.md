# Iteration 175 — word-level connectivity does not yield coherent case classes

**Negative result, preserving the earlier success:** closing the opaque word graph into connected components does not produce useful anonymous case classes. Transitive-only PRON/DET comparisons score about27% in both passages and do not exceed the word/POS-profile-preserving controls. Keep iteration174's frame-conditioned pairwise association; do not adopt connected-component equality constraints.

## Frozen design

Use the same floor-five/two-distinct-frame graphs in both Cicero pools, original plus all16 existing word shuffles. Before case/POS evaluation, freeze connected components, sorted members, all distinct unordered member pairs, each pair's direct-edge flag, and each member's union of incident-frame occurrence positions. Component membership and these positions use no labels.

For each member pair, compare all Cartesian pairs of its selected positions, retaining recognized cases within the five fixed172 POS strata. Average case fractions equally over eligible type pairs within each component, then equally over covered components (primary); type-pair-macro and pooled scores are secondary. Report all, direct, and transitive-only member pairs separately. Case-free components and empty strata remain in outputs. On the original components also evaluate all199 frozen174 case permutations preserving each word/exact-POS case profile. Word-null token labels travel through the original fixed token permutations.

**This changes the estimand:** occurrence positions are pooled across each word's incident frames. Comparisons need no longer share a particular frame, even for direct member pairs. The scores therefore cannot be interpreted as a rerun or refutation of the old frame-macro score. This experiment asks whether a word-level case class remains coherent after collapsing those distinctions.

## Graph composition

| Passage | Component sizes (descending) | Original direct edges | All distinct within-component type pairs |
|---|---|---:|---:|
| Earlier | 37,4,2,2,2,2,2,2 | 52 | 678 |
| Replication | 81,4,3,2,2 | 126 | 3,251 |

Both graphs collapse mostly into a large component. Their anonymous IDs do not imply named cases or restored POS labels.

## Primary stratum: both occurrences PRON/DET

| Passage | Pair mode | Case components | Eligible type pairs | Component-macro agreement | Type-pair-macro agreement | Word-null maximum (at least actual/nonempty) | Profile-null maximum (at least actual/nonempty) |
|---|---|---:|---:|---:|---:|---:|---:|
| Earlier | All | 2 | 137 | 65.16% | 30.82% | 45.72% (0/16) | 66.40% (1/199) |
| Earlier | Direct | 2 | 16 | 77.96% | 58.67% | 75.00% (0/15) | 80.37% (5/199) |
| Earlier | Transitive only | 1 | 121 | 27.14% | 27.14% | 45.72% (9/16) | 31.27% (26/199) |
| Replication | All | 1 | 406 | 28.52% | 28.52% | 35.48% (3/16) | 32.06% (153/199) |
| Replication | Direct | 1 | 24 | 44.37% | 44.37% | 54.49% (3/16) | 48.51% (108/199) |
| Replication | Transitive only | 1 | 382 | 27.52% | 27.52% | 28.70% (3/16) | 31.22% (159/199) |

All original primary case comparisons in the replication graph fall in the giant component. Earlier, its giant component scores30.31% over136 eligible type pairs, while a two-word component scores100% on one pair. Equal-component weighting raises the headline mean to65.16%; the30.82% type-pair mean makes this small-component effect explicit. These are evaluation diagnostics, not a rule for selecting components.

For transitive-only primary pairs, profile-null means are25.75% earlier and28.26% replication, versus actual27.14%/27.52%. There is no replicated improvement beyond those profiles. The full all-POS transitive score in replication narrowly exceeds all16 word-null scores (27.92% versus27.69% maximum) but not the profile-preserving null (50/199 at least actual), and the earlier passage fails the word-null comparison. This isolated control result is not promoted.

All five strata, every component's covered-pair count and agreement, all/direct/transitive metrics, pooled counts, all432 views, and both null families are retained in the artifacts. Empty groups are not scored as perfect; null comparisons report their actual nonempty counts.

## Interpretation and next step

Word-level transitivity is not supported. Frame-conditioned substitution compatibility can be useful while a word participates in several case environments; joining those environments through the same word ID conflates them. The direct-pair decline after position pooling, particularly in replication, is consistent with the need to retain frame identity. This is a diagnostic explanation, not a proof that one particular context model will work.

Iteration174 remains the positive result: original within-frame macro agreement exceeds all199 word/POS-profile controls in both passages. No new case classes, POS labels, lexical nuclei, syntactic links or decoder have been recovered here. Gold reference conditioning and same-author development reuse remain explicit.

Next proposed diagnostic: keep nodes as **(opaque word ID, ordered frame)** instead of one node per word, linking only primary-supported type pairs within the same frame. Freeze components using those nodes before labels, report their sizes and how many contain at least three word types, and evaluate transitive pairs using that frame's actual occurrence positions. Preserve all empty/sparse outcomes and the same null controls. This directly tests context-preserving composition; a mostly two-node result would show that useful group coverage is still missing rather than establish restored classes.

## Verification

Independent union-find reconstruction checked all34 original/word-null graph views, memberships, occurrence-position unions and direct/transitive flags. A separate matrix count implementation verified all844,781 detailed pair records across432 graph/assignment views; independent component summaries, coverage, pair-count partitions and all contrasts passed. Frozen-input/component/score hashes passed. The broader test suite was not rerun for this reference-only benchmark. No new annotations, reserved or sealed data were used.

Runner: `benchmarks/grammar_case_components_iteration175.py`; independent reviewer: `benchmarks/grammar_case_components_iteration175_review.py`. Frozen proposal/design, components, gzip JSON-lines full scores, summaries, contrasts, audit and verification manifest reside in `experiments/results/grammar-restoration/iteration175/`.
