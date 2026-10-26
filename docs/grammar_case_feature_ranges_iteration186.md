# Iteration 186 — unstable false positives occupy an uncovered entropy regime

**Mechanism supported, no rejection rule adopted:** all four non-case pairs displaced along185's weight path fall outside the remaining source's left-entropy ranges when sourcepair21 is removed. All four case-comparable replacements remain inside those two ranges. However, two other case-comparable target pairs also lie outside, so a range flag cannot be equated with a wrong candidate or safely discarded evidence.

## Frozen geometry audit

Evaluate every one of the19 raw180 feature coordinates for every126 target row. Construct closed coordinate-wise min/max ranges from all52 source rows and from51 rows excluding21. Define outside by `value < min - 1e-12` or `value > max + 1e-12`; retain raw excursions and distances in original full-source rich scales. Keep all extrema source-row IDs and zero-distance/empty outcomes.

Freeze ranges, geometry and masks before case scoring. Predeclare any-coordinate outside and the union of two185-identified coordinates: mean left-context entropy and absolute endpoint difference in left-context entropy. Report all targets, frozen original/omitted top10, departed and entered cohorts, with per-coordinate case applicability and original/omitted probabilities. No clipping, rejection, refit, threshold tuning or selective confidence estimate is applied. Words or identities do not become features.

## The influential example expands source coverage

| Raw feature | Full52 source range | Without pair21 |
|---|---:|---:|
| Mean left-context entropy | .4193–1.0000 | .6776–1.0000 |
| Endpoint left-entropy difference | approximately0–.7407 | approximately0–.4241 |

Pair21 alone supplies the full-source minimum mean entropy and maximum entropy difference. Removing it exposes target rows from this regime to a classifier with no retained source example at those extremes. These are coordinate bounds, not a multivariate support estimate or a guarantee of interpolation inside them.

## All-target coverage, not just selected errors

| Source ranges / mask | Outside target pairs | Case-comparable outside | Inside target pairs | Case-comparable inside |
|---|---:|---:|---:|---:|
| Full source, any of19 coordinates | 38 | 10 | 88 | 26 |
| Full source, either left-entropy coordinate | 4 | 0 | 122 | 36 |
| Without21, any of19 coordinates | 44 | 13 | 82 | 23 |
| Without21, either left-entropy coordinate | 9 | 2 | 117 | 34 |

The any-coordinate flag does not cleanly distinguish applicability: many useful pairs are outside for other features. Even the more focused predeclared entropy flag would remove2/36 applicable pairs under the without21 ranges. Its full-source4/4 non-case pattern is a small descriptive subset on already-investigated target data, not a validated high-confidence rule.

## Cohort coverage under the two entropy coordinates

| Frozen cohort | Without21 outside | Case-comparable outside | Without21 inside | Case-comparable inside |
|---|---:|---:|---:|---:|
| All targets | 9 | 2 | 117 | 34 |
| Omitted-model original top10 | 5 | 1 | 5 | 4 |
| Original full-model top10 | 1 | 1 | 9 | 8 |
| Departed along0→1 weight path | 4 | 0 | 0 | 0 |
| Entered along0→1 weight path | 0 | 0 | 4 | 4 |

Thus rejecting outside pairs from the omitted top10 would discard four non-case candidates **and one useful pair**, leaving five original-list members rather than a repaired ten-pair list. Rejecting from the original full-model top10 using the same without21 ranges would discard one useful pair. Neither operation was applied or reranked in this diagnostic.

The four departing target indices69,21,92,82 are all outside the without21 entropy envelope. Three are already outside the full-source entropy envelope; target21 is inside full-source but outside without21. All four replacements77,45,118,105 are entropy-inside, although three violate some other feature's without21 range. All126 row details and every coordinate's outcomes remain available, preventing a post hoc focus on only the successful flag.

## Interpretation and next test

The influence diagnosed185 is consistent with a missing source feature regime: a single negative example constrains how the linear model extrapolates to low/asymmetric left-context entropy. This explains the geometry without proving a causal linguistic category or that the range mask is optimal. Ordinary coordinate ranges ignore correlations and can include unsupported combinations; outside-range status does not establish an incorrect prediction.

Next freeze a range-aware abstention diagnostic across **all53 source-endpoint omissions**, comparing no abstention, all-coordinate ranges and the already-declared two-entropy-coordinate ranges. Derive each range from retained source features only; keep fixed184 models/probabilities, cutoffs and complete outputs. Report coverage, applicable pairs lost, selected-list size, and any separately declared refill-to-top10 behavior, distinguishing improved conditional scores from reduced coverage. No target-favorable thresholds or coordinate selection; development exposure and possible useful-pair rejection remain explicit.

No new case labels, general POS tags, lexical nuclei, syntactic links or algorithm repair are obtained here. The source-trained grammatical interface remains a development finding on two Cicero passages with shared vocabulary; this audit narrows a confidence failure mechanism.

## Verification

Independent scalar reconstruction verified38 source-coordinate range sets,4,788 target-coordinate geometry comparisons, all extrema/masks/distances,116 cohort/coordinate aggregations and every126 target detail records. Frozen input/geometry hashes passed. The broader test suite was not rerun for this reference-only audit; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_feature_ranges_iteration186.py`; reviewer: `benchmarks/grammar_case_feature_ranges_iteration186_review.py`. Frozen design, ranges, full geometry, cohorts, summaries, per-target details, audit and verification manifest: `experiments/results/grammar-restoration/iteration186/`.
