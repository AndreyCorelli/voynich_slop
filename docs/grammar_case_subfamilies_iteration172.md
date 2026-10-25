# Iteration 172 — within-family substitution dominates, with limited cross-family evidence

**Preserve the narrower grammatical finding:** pairs where both occurrences are PRON/DET account for most recognized-case comparisons and exceed the existing word-shuffle maxima in both Cicero passages. Mixed-family compatibility has encouraging replication-passage evidence but is too sparse in the earlier passage to establish replication.

## Frozen diagnostic

Keep the same primary floor-five/two-frame graphs and sixteen word-shuffle controls. Partition occurrence pairs into both PRON/DET, exactly one PRON/DET, and neither. Retain all-pair and PRON/DET-involving unions as exact historical controls. Evaluate recognized case equality using the unchanged occurrence-within-frame, frame-within-edge, and edge-macro weighting. Include empty and sparse groups; labels only stratify evaluation and never change inference.

Additionally freeze all 153 unordered POS-pair categories from the fixed 17 UD tags, including zero categories, and count all occurrence pairs, recognized-case pairs and matching cases in each original/null view. These pooled counts describe composition; they are not macro agreement estimates. Opaque endpoint order does not provide grammatical direction. Shared-frame endpoints are different word types used in separate occurrences, so this is substitution compatibility, not an assertion that two co-occurring words agree or have an antecedent relation.

## Results

| Passage | Pair group | Case edges | Case comparisons | Matching | Macro agreement | Nonempty nulls | Maximum null | Nulls at least actual |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Earlier | Both PRON/DET | 16 | 69 | 57 | 71.88% | 15 | 50.00% | 0 |
| Earlier | Exactly one PRON/DET | 2 | 4 | 3 | 75.00% | 8 | 100.00% | 1 |
| Earlier | Neither | 0 | 0 | 0 | — | 0 | — | — |
| Replication | Both PRON/DET | 24 | 85 | 63 | 67.01% | 16 | 64.29% | 0 |
| Replication | Exactly one PRON/DET | 11 | 31 | 24 | 75.13% | 15 | 50.00% | 0 |
| Replication | Neither | 1 | 2 | 2 | 100.00% | 2 | 100.00% | 1 |

All/PRON-DET-involving/neither baselines exactly reproduce iteration171 for every view. Both-family comparisons account for 69/73 (94.52%) earlier and85/118 (72.03%) replication case comparisons. The replication both-family margin over the largest word-shuffle score is only2.73 percentage points; no calibrated significance or confidence claim follows from exceeding sixteen controls.

### Exact POS composition of case comparisons

Each cell gives matching/eligible occurrence pairs; these are pooled counts, not the primary macro score.

| Unordered POS pair | Earlier | Replication |
|---|---:|---:|
| PRON/PRON | 53/65 | 55/74 |
| DET/PRON | 2/2 | 6/9 |
| DET/DET | 2/2 | 2/2 |
| NOUN/PRON | 3/4 | 16/19 |
| ADJ/PRON | 0/0 | 4/7 |
| PRON/PROPN | 0/0 | 4/5 |
| NOUN/NOUN | 0/0 | 2/2 |

Every remaining POS-pair category has zero recognized-case comparisons in the actual graphs; all 153 categories and null counts remain in `composition.json`. There is no mixed DET comparison with recognized cases in either actual graph.

## Interpretation and next check

The robust part is chiefly compatibility among pronominal forms in the same repeated contexts. Replication mixed-family results are worth retaining as a separate lead, with limited sample size and absent earlier null separation explicit. Nothing here supplies a pronoun detector, named-case assignments, syntactic links, or lexical nuclei; applicability still depends on gold reference labels, and both passages are reused same-author development data.

Next proposed diagnostic: keep the graph, word identities and POS references fixed, and permute cached case labels among tokens of the same exact POS within each passage. Retain missing and unrecognized cases in that permutation, preserving each POS's entire case inventory. Use a predeclared seed set, report all groups and coverage changes, and compare the same macro score without selecting labels or edges. This tests whether observed compatibility goes beyond POS-specific marginal case frequencies; it is a label-randomization diagnostic rather than a text-cipher model or fresh replication. Do not tune the graph based on its outcome.

## Verification

Independent brute-force replay checked reference-to-word-stream alignment, 34 graph views, 3,899 edge records, 10,000 Cartesian occurrence pairs, 170 stratum metric groups, all 153 POS-pair inventories per view, disjoint count identities, every contrast, and exact iteration171 historical baselines. Input/reference/score hashes passed. The broader test suite was not rerun for this reference-only diagnostic.

Runner: `benchmarks/grammar_case_subfamilies_iteration172.py`; reviewer: `benchmarks/grammar_case_subfamilies_iteration172_review.py`. Frozen proposal, references, full scores, composition counts, summaries, contrasts, audit and verification manifest are under `experiments/results/grammar-restoration/iteration172/`.
