# Iteration 177 — label-free group shortlists do not solve applicability or diversity

**Primary result:** the fixed combined top20 ranking selects groups without POS/case labels, but only6/22 earlier and5/20 replication groups contain comparable cases. Their100% conditional agreement comes from just one distinct case-comparable word pair in each passage. This is not a100% grammatical restoration result or a reliable detector of useful case groups.

## Frozen rankings

Use exact176 frame components. Compute three scores without labels: mean log member-word frequency; mean log distinct-shared-frame support across direct member edges; their sum (the log of the product of those geometric means). Fix top10/20/40 and all-group controls, including **all exact floating-score boundary ties**, so actual list sizes may exceed the requested cutoff. Primary: combined20, all-POS/all-pair mode, avoiding any truth-supplied family filter. Rankings/cutoffs are not selected from outcomes.

Freeze features, selections and tie inventories before reading176 scored records. Apply the same rules independently to each of16 word-null graphs; each of199 profile nulls retains the original graph's fixed selections. Reaggregate all five POS strata and all/direct/transitive modes. No labels select groups, rank words, discard empty groups or tune cutoffs.

Report conditional component-macro case agreement alongside: case-comparable groups/all selected groups; recognized-case occurrence pairs/all occurrence pairs; and a component joint yield that sums covered-group agreements over **all selected groups**, giving inapplicable groups zero contribution solely for this diagnostic. Joint yield is not a correctness/accuracy claim: no case label has been predicted. Retain pooled matching/all-pair rates, all ties, coverage and null contrasts.

## Original-list results

| Passage | Ranking/cutoff | Selected groups | Case groups | Case applicability | Conditional agreement | Component joint yield | Case occurrence comparisons |
|---|---|---:|---:|---:|---:|---:|---:|
| Earlier | All | 106 | 45 | 42.45% | 71.11% | 30.19% | 74 |
| Earlier | Frequency10 | 10 | 0 | 0.00% | — | 0.00% | 0 |
| Earlier | Frequency20 | 20 | 6 | 30.00% | 100.00% | 30.00% | 8 |
| Earlier | Frequency40 | 40 | 10 | 25.00% | 70.00% | 17.50% | 13 |
| Earlier | Support10 | 11 | 6 | 54.55% | 100.00% | 54.55% | 8 |
| Earlier | Support20 | 21 | 16 | 76.19% | 87.50% | 66.67% | 39 |
| Earlier | Support40 | 106 | 45 | 42.45% | 71.11% | 30.19% | 74 |
| Earlier | Combined10 | 10 | 6 | 60.00% | 100.00% | 60.00% | 8 |
| Earlier | **Combined20 (primary)** | **22** | **6** | **27.27%** | **100.00%** | **27.27%** | **8** |
| Earlier | Combined40 | 40 | 14 | 35.00% | 71.43% | 25.00% | 38 |
| Replication | All | 220 | 70 | 31.82% | 72.66% | 23.12% | 148 |
| Replication | Frequency10 | 10 | 0 | 0.00% | — | 0.00% | 0 |
| Replication | Frequency20 | 22 | 1 | 4.55% | 100.00% | 4.55% | 1 |
| Replication | Frequency40 | 40 | 6 | 15.00% | 100.00% | 15.00% | 8 |
| Replication | Support10 | 12 | 5 | 41.67% | 100.00% | 41.67% | 7 |
| Replication | Support20 | 20 | 5 | 25.00% | 100.00% | 25.00% | 7 |
| Replication | Support40 | 40 | 13 | 32.50% | 94.44% | 30.69% | 34 |
| Replication | Combined10 | 16 | 5 | 31.25% | 100.00% | 31.25% | 7 |
| Replication | **Combined20 (primary)** | **20** | **5** | **25.00%** | **100.00%** | **25.00%** | **7** |
| Replication | Combined40 | 40 | 6 | 15.00% | 100.00% | 15.00% | 8 |

Every list was retained. Support40 selects all106 earlier groups because of its boundary tie; it is not an independent improvement. Ties and ranking features are frozen in the artifacts. Exact floating-score ties are the predeclared policy, not an approximate mathematical-equality test.

## Primary result and controls

The primary joint yield27.27%/25% does not consistently improve on the all-group baseline30.19%/23.12%. Earlier frequency20 already covers the same six case-comparable groups with a smaller list, yielding30%; replication frequency20 covers only one case group, so combined improves that narrow comparison but not enough to establish reliable group detection.

Each primary list's recognized-case comparisons come from **one unique opaque word pair (two word types)** repeated across6 earlier or5 replication frame groups. Perfect conditional agreement therefore has very little lexical diversity; these are not six/five independently restored nuclei. Support10 has exactly the same recognized-case pair diversity in each passage. Support20 expands the earlier case-comparable set to five unique word pairs/six types, but replication remains one pair/two types. This diversity audit is descriptive; no list was replaced or tuned from it.

For primary conditional agreement,6/199 earlier and23/199 replication profile nulls also reach100%. Word-null conditional scores are undefined in14/16 earlier and16/16 replication controls because the selected groups have no comparable cases; the two nonempty earlier controls score0% and100%. Do not treat an empty null conditional score as0% or as evidence of perfect separation.

Joint yield remains defined for nonempty selected lists even when no cases apply: primary actual27.27%/25% exceeds all16 word-null joint yields (max5%/0%), but those null graphs have very little case applicability. Profile-null joint yields reach the actual maximum6 and23 times, respectively. This distinguishes structure/applicability from conditional agreement and prevents a misleading100% accuracy claim.

Support-only lists are a lead, not a frozen winner: support20 earlier has76.19% applicability and87.50% consistency, while replication has25% applicability on just seven comparisons. Support10 raises applicability above the all-group baseline in both passages, but still depends on one recognized-case word pair. The broad176 frame-conditioned finding remains intact; the fixed primary shortlist fails to provide a reliable diverse interface to a decoder.

## Implications and next step

No POS/case-bearing detector, named case assignment, syntactic relation or lexical nucleus was restored. Rankings are deployable from opaque counts, but their evaluated grammatical applicability is modest and case evidence is concentrated. Both passages are same-author reused development material, not fresh validation.

Next proposed diagnostic: rank **unique word-pair bundles** rather than separate frame groups, retaining each bundle's individual frame-specific occurrence comparisons. This prevents multiple frames of one pair from occupying many shortlist slots without collapsing case contexts as175 did. Freeze the frequency/support ranking, cutoffs, tie policy and all outcomes before scoring, and report unique types/pairs, unconditional applicability and conditional consistency. Preserve frequency-only controls and existing nulls; do not select grammatical families using reference labels.

## Verification

Independent replay verified34 graph rankings, all frequency/support features, every tie-inclusive selection,432 graph/assignment views and64,800 selected metric groups. All176 all-list baselines match exactly, including component details, and every null contrast passed. Frozen design/selection hashes passed. The broader test suite was not rerun for this reference-only aggregation. Existing176 detailed scores were reused; no new annotations, reserves or sealed data were accessed.

Runner: `benchmarks/grammar_case_group_selection_iteration177.py`; reviewer: `benchmarks/grammar_case_group_selection_iteration177_review.py`. Frozen proposals/design, features, selections, boundaries, complete selected summaries, contrasts, audit and verification manifest: `experiments/results/grammar-restoration/iteration177/`.
