# Independent frequency-adjusted adjacency test

Seven plan → test → assessment iterations test a frozen adjacent-repetition feature on new prose excerpts and several ordering generators. **All four prose excerpts suppress adjacent repeats relative to the matched random-order expectation.** Repeat-seeking generation increases repeats, but repeat-avoidance generation also produces suppression. The feature's sign therefore does not identify natural prose, encoding or generation.

Prose suppression is stronger than the greedy avoidance generator in these runs; sharing a negative sign does not mean all numerical ranges overlap. No classifier threshold or manuscript inference is fitted.

## Frozen feature

For each 32-word block, measure:

`observed adjacent exact-repeat fraction − expected fraction under uniform position-bin/length-preserving permutation`

The expectation uses the observed word multiset in each pool. For adjacent slots in the same pool, with counts `c_w` and total `N`, equal-word probability is `sum(c_w*(c_w−1))/(N*(N−1))`. For distinct pools A/B, it is `sum(c_Aw*c_Bw)/(N_A*N_B)`. Repeated tokens are sampled without replacement; distinct pools are independent. Average the probabilities over all 31 edges, then subtract from the observed fraction. A companion uses within-line edges only. Main summaries average blocks equally.

The feature and all source/generator choices are frozen before evaluating new excerpts. The expectation is checked against exhaustive permutations of small fixtures. An independent implementation subsequently enumerates labeled slot-pair assignments instead of using the count formula.

Measure payload and encoded text separately. For encoded text the reference is a permutation of **observed encoded words** within encoded position/length pools, not randomizing plaintext and rerunning its context-dependent encoder. The two expectations need not agree.

## Seven iterations

| Iteration | Plan/test | Assessment → next action |
|---|---|---|
| 1 | Freeze feature, four excerpts, five ordering rules; exhaustive expectation check | Arithmetic passes. Test disjoint German 113 excerpt. |
| 2 | German 113, five orders and three keys/streams | Prose suppresses repeats; avoidance shares negative sign. Test German 133. |
| 3 | Disjoint German 133 excerpt | Same broad pattern. Test previously unscored German 253 source. |
| 4 | German 253 excerpt | Prose suppression and avoidance replicate. Test cross-language Italian excerpt. |
| 5 | Disjoint Italian excerpt | Smaller magnitudes, same sign pattern. Assess hard negative. |
| 6 | Compare deliberate repeat-avoidance generator | Sign-only specificity fails; no claim of complete numerical overlap. |
| 7 | Freeze multi-source assessment and limits | Retain feature as an ordering constraint, not mechanism identification. |

There are **60 cases**: four sources × five ordering types × three seeds. No character-predictor refits, Z3 calls, model/dose selection, weighted feature fitting or manuscript classification occur.

## Sources and independent excerpts

German 113/133 and Italian use eligible blocks 121–241, between the prior first-121 and last-121 samples. They are disjoint from earlier statistical training/evaluation excerpts. German 253 uses its first 121 blocks and is a new source for this statistical prediction branch. Earlier descriptive corpus-wide audits inspected these texts, so this is not complete data blindness.

For each source, the first 32 selected blocks supply 1,024 mapping-training words and the next 89 supply 2,848 evaluation words. Blocks do not cross source segments or excluded/non-ASCII token barriers. Cached historical normalization, manifests and parser hashes are retained. Italian pools are from the day-one Decameron collection; three German works and one Italian collection are not representative language samples.

## Ordering rules and common representation

All rules receive the same public word inventory in each evaluation block and preserve position-bin/length inventories, every slot's length, exact spellings and layout. They generate orders, not new lexical forms.

- **Prose:** retain original order.
- **Random:** uniform assignment without replacement within pools.
- **Mapped:** at eligible within-line edges, prefer the training-derived ending-to-initial mapping with probability 0.5, falling back when unavailable.
- **Repeat:** greedily choose an identical preceding word when available in the current pool.
- **Avoid:** greedily choose a different word when possible; later choices can be forced to repeat.

Every payload receives the same reversible representation: a seed-specific bijective payload key and preceding-output-dependent marker on the fixed public 1/16 within-line block-position schedule. Keys are common across ordering types within a source/seed; prefix counts and slot lengths match. Marker identities can differ, so encoded word inventories need not match across order types. Separate random-order streams are used; original prose across three keys is not three independent prose observations.

## Results

Values are mean adjusted adjacent-repeat fractions across three keys/streams, **not bits/character**. Negative means repeat suppression relative to the analytic reference; positive means excess repetition.

| Source, encoded representation | Prose | Random | Mapped | Repeat-seeking | Repeat-avoidance |
|---|---:|---:|---:|---:|---:|
| German 113 | −0.006214 | −0.000639 | +0.000856 | +0.011364 | −0.004224 |
| German 133 | −0.006048 | −0.001401 | +0.000360 | +0.007714 | −0.004370 |
| German 253 | −0.007571 | +0.001219 | −0.001435 | +0.010190 | −0.005108 |
| Italian | −0.002831 | −0.000459 | −0.000499 | +0.001233 | −0.001727 |

Payload results retain the same broad pattern. Uniform/mapped realizations vary around small signed values; the observed uniform cases are not exactly zero, as expected for finite samples. Repeat preference is positive and greedy avoidance negative in every source. Prose has stronger mean suppression than the tested avoid generator in all four, but a stronger avoiding algorithm could change that comparison. This is not a calibrated effect-size classifier or evidence against all generators.

## Assessment and limits

Frequency adjustment reproduces a natural-prose ordering constraint across disjoint excerpts and an additional language, beyond raw repeat frequency. It also detects deliberately added or removed repeats. The hard-negative generator shows why suppression alone is not a natural-language or historical mechanism signature.

Source-specific inventories, orthography, edited boundaries and fixed pool constraints remain. Generators know evaluation inventories and cannot predict new forms/frequencies. Greedy preference/avoidance are single strategies, not global optima. There are four selected excerpts and three streams, insufficient for a broad power or classification estimate. Common encoding means both original and generated sequences can be reversibly encoded; historical causes are not exclusive categories.

Historical parsing is reused rather than independently reimplemented. One-letter counts are saved in `assessment.json`. The German 133 held-out excerpt contains four `k` and two `x` tokens, previously flagged as unresolved prayer notations; its result therefore retains that source-quality caveat. The other three sources contain neither form. No new manuscript feature score is used to choose the statistic or classify its mechanism.

Next: **test a fixed stronger repeat-avoidance generator and a suffix-conditioned generator with avoidance jointly**. Check whether simple generated ordering can satisfy both frozen constraints without manuscript-based tuning. If so, park the features as descriptive constraints and seek a mechanism prediction they cannot share, rather than continuing classifier tuning on these statistics.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.adjacent_order_replication --run
.venv/bin/python -m benchmarks.adjacent_order_validation
.venv/bin/python -m benchmarks.adjacent_order_assessment
.venv/bin/python -m pytest tests/integration/test_adjacent_order_replication.py -q
```

Three tests pass. Independent validation checks **331,080 edge expectations** and **170,880 decoded words**, exact block/pool inventories and slot lengths, raw-known decoding relations, train/evaluation and prior-excerpt disjointness, all seven plan/result chains and grouped summaries. Source parsing and stochastic generation reuse earlier implementations; the feature's edge expectations are independently enumerated.

Artifacts: `experiments/results/adjacent-order-replication/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. Prior code/results remain unchanged.
