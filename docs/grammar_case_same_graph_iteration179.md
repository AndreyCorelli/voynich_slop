# Iteration 179 — support10 does not demonstrate same-graph enrichment

**The selection lead does not clear this diagnostic.** Random size-ten subsets of the same original graph match or exceed support10's joint yield in398/999 earlier and278/999 replication samples. Case applicability and case-type diversity are also ordinary under these controls. Do not adopt support ranking as a validated useful-pair selector; the underlying frame-conditioned case association remains a separate positive result.

## Frozen diagnostic

Freeze178 support10 as candidate, frequency10 as comparator, and all-pair reference. Sample999 size-ten unique-edge subsets uniformly without replacement from each same original primary graph (52 earlier edges,126 replication), NumPy default_rng independently initialized per seed179000–179998 and pool, sorted selected indices. Candidate support10/frequency10 lists must already contain exactly ten pairs; no truncation or retuning. Freeze all indices before reading cached172 case comparisons.

Preserve each bundle's frame-specific172 scoring and all five POS strata. Primary: support10 all-POS edge joint yield versus random subsets. Secondary: case applicability, conditional agreement, recognized-pair applicability, matching/all-pair rate, case-edge counts and selected/case-involved type diversity. Retain subsets with no cases; their joint yield is0, but conditional agreement is undefined. Report corrected descriptive tails `(1 + count >= actual)/1000` only when all999 controls and actual are defined. Support10 was a control-derived hypothesis from the same development outcomes; this is not fresh validation or a calibrated decipherment confidence test.

## Primary and applicability results

| Passage | Metric | Support10 | Random mean | Random at least support10 | Corrected descriptive tail |
|---|---|---:|---:|---:|---:|
| Earlier | Joint yield (primary) | 30.00% | 24.37% | 398/999 | .399 |
| Replication | Joint yield (primary) | 28.33% | 20.32% | 278/999 | .279 |
| Earlier | Case-edge applicability | 40.00% | 34.18% | 479/999 | .480 |
| Replication | Case-edge applicability | 30.00% | 28.46% | 572/999 | .573 |
| Earlier | Case-involved word types | 6 | 5.91 | 608/999 | .609 |
| Replication | Case-involved word types | 6 | 5.09 | 443/999 | .444 |
| Earlier | All selected word types | 15 | 16.72 | 925/999 | .926 |
| Replication | All selected word types | 18 | 17.50 | 534/999 | .535 |

Support10's observed advantage over the full-graph yield (30% versus25%;28.33% versus20.12%) does not translate into unusual same-size-subset performance. Random joint yields span0–60% earlier and0–65% replication. The sampling means are close to the exact full-graph yield expected for uniform fixed-size subsets; finite Monte Carlo differences are retained rather than adjusted.

## Conditional consistency and missing applicability

Earlier support10 conditional agreement75% is matched/exceeded by524 of992 nonempty random subsets; replication94.44% by246 of969. Nonempty random conditional means are71.55%/70.91%, and each passage has random subsets reaching100%. Seven earlier and30 replication subsets contain no case-comparable pair and remain undefined for conditional agreement; no full-control corrected conditional tail is reported. Every random subset has exactly ten distinct edges even when no cases apply.

Frequency10 is weaker: earlier joint yield10% is matched/exceeded by942/999 random subsets; replication has zero applicable cases and joint yield0%, matched by all999. Earlier frequency10's100% conditional consistency is based on one pair and is matched by149/992 nonempty random subsets. This reinforces why conditional agreement alone is not a useful selection metric.

All case-edge-count histograms, all999 sampled sets per pool, all candidate/reference summaries and five-stratum comparisons are retained, including zero-case samples. Random subsets overlap and share the same reference graph; they are conditional controls, not independent new texts.

## Interpretation and next direction

Iteration178's support-only lead is not promoted. Its separation from case-label permutations establishes a relation within those selected examples, but does not show selection superiority over ordinary edges from the same graph. The stronger earlier result remains context-specific compatibility beyond empirical word/POS case profiles (174), with frame-preserving composition (176); no useful-pair confidence rule or case-bearing detector has been established.

Next proposed direction: target **case applicability** directly using richer anonymous context features, rather than frequency/support reranking. Freeze a small source-only diagnostic model and frequency/support controls before evaluation; use existing case references only as training/evaluation labels, exclude queried shared-frame occurrences from contextual feature extraction where feasible, and transfer the unchanged rule to the other passage. Report unconditional coverage/calibration and conditional consistency separately, retain all negative results, and disclose same-author development reuse rather than calling it fresh validation. This would be an explicit supervised source-language component usable later on opaque words, not supplied target POS/case selection or recovered Latin identities; the exact feature/model protocol remains to freeze before running.

## Verification

Independent replay verified all1,998 random subsets, unique sampling without replacement, frozen candidate lists,10,020 stratum metric groups, all178 candidate/all-pair baselines, case-edge histograms and every null contrast. Input/selection hashes passed. The broader test suite was not rerun for this reference-only subset/aggregation benchmark. Existing cached scores were reused; no new annotations, reserves or sealed data were accessed.

Runner: `benchmarks/grammar_case_same_graph_iteration179.py`; reviewer: `benchmarks/grammar_case_same_graph_iteration179_review.py`. Frozen design, sampled indices, complete summaries, contrasts, histograms, audit and verification manifest: `experiments/results/grammar-restoration/iteration179/`.
