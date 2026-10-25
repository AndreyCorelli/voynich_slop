# Iteration 178 — unique-pair selection: primary fails, support-only control is a lead

**Preserve a qualified lead:** the predeclared support-only top10 control selects four earlier and three replication case-comparable word pairs, spanning six word types in each passage. Their75%/94.44% conditional case agreement clears all199 word/POS-profile controls; joint diagnostic yield30%/28.33% exceeds the all-pair25%/20.12% baselines. The primary combined20 ranking fails applicability, and superiority of support ranking to random same-size lists is not established.

## Frozen design

Use every existing primary floor-five/two-shared-frame word-pair edge as one bundle. Rank each pair once, retaining all of its separate frame comparisons; no occurrence positions are pooled across frames. Scores: mean log frequency of its two endpoints, log distinct shared-frame support, and their sum. Fix top10/20/40 plus all-pair controls, including all exact floating-score boundary ties. Primary remains combined20, all-POS, with no supplied family filter. Freeze features, selections and boundary records before reading cached comparisons.

Use exact172 edge/frame scoring: compare recognized-case occurrences within a frame, average covered frames within a pair, then covered pairs equally. Retain all five172 POS strata and every empty result. Independently rank each16 word-null graph; keep original rankings fixed under all199 existing174 word/POS-profile permutations. Reuse the audited cached scores rather than generating new annotations.

Report selected and case-comparable unique pairs, involved word types, case applicability, conditional agreement, recognized-case pair applicability, and joint yield (sum of covered-pair agreements divided by **all selected pairs**, an evaluation diagnostic rather than accuracy). Individual frames remain evidence within a bundle, never additional ranking slots. Selection unit and weighting differ from177, so changes are not an isolated causal estimate of deduplication.

## All original-list results

| Passage | List | Selected pairs | Case pairs | Case types | Conditional agreement | Joint yield | Case occurrence comparisons |
|---|---|---:|---:|---:|---:|---:|---:|
| Earlier | All | 52 | 18 | 21 | 72.22% | 25.00% | 73 |
| Earlier | Frequency10 | 10 | 1 | 2 | 100.00% | 10.00% | 17 |
| Earlier | Frequency20 | 20 | 3 | 5 | 50.00% | 7.50% | 21 |
| Earlier | Frequency40 | 40 | 14 | 15 | 64.29% | 22.50% | 65 |
| Earlier | **Support10 (fixed control)** | **10** | **4** | **6** | **75.00%** | **30.00%** | **39** |
| Earlier | Support20 | 52 | 18 | 21 | 72.22% | 25.00% | 73 |
| Earlier | Support40 | 52 | 18 | 21 | 72.22% | 25.00% | 73 |
| Earlier | Combined10 | 10 | 3 | 4 | 66.67% | 20.00% | 35 |
| Earlier | **Combined20 (primary)** | **20** | **3** | **4** | **66.67%** | **10.00%** | **35** |
| Earlier | Combined40 | 40 | 14 | 15 | 64.29% | 22.50% | 65 |
| Replication | All | 126 | 36 | 33 | 70.41% | 20.12% | 118 |
| Replication | Frequency10 | 10 | 0 | 0 | — | 0.00% | 0 |
| Replication | Frequency20 | 20 | 1 | 2 | 95.83% | 4.79% | 18 |
| Replication | Frequency40 | 40 | 2 | 3 | 47.92% | 2.40% | 22 |
| Replication | **Support10 (fixed control)** | **10** | **3** | **6** | **94.44%** | **28.33%** | **30** |
| Replication | Support20 | 33 | 7 | 11 | 81.75% | 17.34% | 45 |
| Replication | Support40 | 126 | 36 | 33 | 70.41% | 20.12% | 118 |
| Replication | Combined10 | 10 | 1 | 2 | 95.83% | 9.58% | 18 |
| Replication | **Combined20 (primary)** | **20** | **1** | **2** | **95.83%** | **4.79%** | **18** |
| Replication | Combined40 | 40 | 2 | 3 | 47.92% | 2.40% | 22 |

All lists remain reported. Support20/40 in the earlier passage and support40 in replication expand to the complete graphs through boundary ties. These are baseline restatements, not additional successes.

## Primary failure

Combined20 has only3/20 earlier and1/20 replication case-comparable pairs (15%/5% applicability). Its joint yields10%/4.79% are worse than the full graphs25%/20.12%. The replication primary is still concentrated on one pair. Word-null conditional comparisons are sparse: only4/16 earlier and1/16 replication null graphs have any case-comparable selected pair, and one null in each passage meets/exceeds actual agreement. Empty nulls are not treated as0% conditional agreement. All199 profile controls are nonempty;0 earlier and2 replication profile scores meet/exceed primary agreement.

## Support-only lead, kept separate from the primary

Support10 selects exactly ten distinct pairs in each passage, with40%/30% case applicability (full-graph baselines34.62%/28.57%). Its recognized-case comparisons all involve two PRON/DET occurrences, but that membership was not supplied to selection. It uses39/30 case occurrence comparisons across four/three distinct pairs, rather than repeated frame slots of one pair.

| Passage | Actual conditional agreement | Word-null max (at least actual/nonempty) | Profile-null mean / max (at least actual/nonempty) | Joint yield actual / full-graph baseline |
|---|---:|---:|---:|---:|
| Earlier | 75.00% | 50.00% (0/10) | 47.63% /68.75% (0/199) | 30.00% /25.00% |
| Replication | 94.44% | 100.00% (1/3) | 70.16% /89.81% (0/199) | 28.33% /20.12% |

Support10 joint yield exceeds all16 word-null values and all199 profile-null values in each passage (profile maxima27.50%/26.94%). Conditional word-null separation is not universal in replication, where the three nonempty controls include100%. Whole-text word shuffles also change graph structure and applicability, so they do not establish that support selection enriches useful pairs relative to sampling from the actual graph.

This is one promising fixed control among multiple tested lists, identified after observing outcomes. It is **a hypothesis for the next diagnostic**, not an adopted winner, fresh confirmation, or a calibrated high-confidence shortlist. The gain over all-pair mean yield is modest and remains concentrated in only four/three case-comparable relations. No named cases, POS detector, lexical nuclei or syntactic links are restored; both passages remain Cicero development material.

## Next diagnostic

Freeze support10 as the candidate and sample many uniformly random size-ten **unique-pair subsets of each same original graph**, without reading labels for sampling. Compare its applicability, conditional agreement, joint yield and pair/type diversity against these same-graph controls; retain empty subsets and predeclare how undefined conditional scores are handled. This directly tests enrichment from support ranking beyond the existing graph's average usefulness. Keep frequency10 as a fixed control and do not retune support cutoffs after results.

## Verification

Independent replay checked34 graph rankings and exact tie-inclusive unique-pair selections,432 assignment views,21,600 selected stratum metric groups, all172/174 all-bundle baselines and every null contrast. Frozen input/selection hashes passed. The broader test suite was not rerun for this reference-only ranking/aggregation; previously audited detailed comparisons were reused. No new annotations, reserves or sealed data were accessed.

Runner: `benchmarks/grammar_case_pair_selection_iteration178.py`; reviewer: `benchmarks/grammar_case_pair_selection_iteration178_review.py`. Frozen proposal/design, features, selections, boundaries, all summaries, contrasts, audit and verification manifest: `experiments/results/grammar-restoration/iteration178/`.
