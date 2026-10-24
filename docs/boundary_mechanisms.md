# Known encoding versus local-generation fixtures

Seven plan → test → assessment iterations compare a known reversible boundary-conditioned encoding with a known local word generator. **Both produce positive preceding-suffix prediction gains.** The tested strengths overshoot the manuscript signal; structural differences exist, but neither the predictive gain nor this uneven fixture comparison identifies a manuscript mechanism.

An additional finding matters: the generator null with **no explicit preceding-word dependence** still gains +0.00330 bits/character. Absolute gain over the current position baseline is therefore not a universal dependence or mechanism diagnostic. Refitted distribution-preserving null contrasts are the next measurement priority.

## Known mechanisms

The encoder takes the cached German 113 primary excerpt used in the historical-prose comparison. A fixed random permutation substitutes all 26 plaintext letters. At eligible within-line slots on a public block-position schedule, it prepends one unit chosen by a fixed permutation of the previous output word's final unit. Quarter schedule uses indices divisible by four; half schedule uses even indices. Block starts and cross-line transitions are not marked.

Decoding uses public word/line/block boundaries and schedule: verify and strip the scheduled marker, then invert the payload substitution. This is a constructed reversible encoding, not a claim of historical practice; resetting its schedule at arbitrary 32-word experiment blocks is especially artificial. It expands selected words by one unit, without contractions. Three seeds change keys. The encoder null substitutes a uniformly random marker on the same schedule, preserving lengths but not the original marker distribution.

The generator samples entire original manuscript development words with replacement from four position-bin pools. At eligible within-line transitions, with probability 0.25 or 0.5, it prefers words beginning with the frozen training-only mapping of the preceding final unit, falling back to the position pool if none exist. This is genuine known text generation, not reversible encoding. It generates word sequences, not new lexical spellings. It uses independent random streams for training/evaluation and does not use evaluation spellings or lengths. Its null uses preference probability zero.

Both produce 1,024 training words and 2,848 evaluation words in the same layout slots over 26 labels plus EOS. Word lengths, vocabulary, novelty and mechanism dose definitions differ. The generator learns manuscript vocabulary; the encoder learns no manuscript vocabulary. This advantage makes structural closeness unsuitable for historical mechanism ranking.

## Seven iterations

| Iteration | Plan/test | Assessment → next action |
|---|---|---|
| 1 | Freeze all fixtures; verify encoding round trips | Reversible construction passes. Score quarter-schedule encoder. |
| 2 | Encoder, quarter schedule, seed 31001 | Gain exceeds manuscript scale. Score quarter-strength generator. |
| 3 | Generator, quarter preference, seed 31001 | Also positive and above manuscript scale. Test nulls. |
| 4 | One mechanism-specific null each | Encoder null near zero; independent position-conditioned word generator also gains. Replicate active fixtures. |
| 5 | Quarter fixtures, seeds 31002/31003 | Both families remain positive. Test preset half strengths. |
| 6 | Half fixtures, all three seeds | Both gain more, further exceeding target. Record structural checks. |
| 7 | Length, repetition and one-edit metrics for all fixtures | Differences are descriptive; separate gain from vocabulary/shape advantages. No classifier or mechanism rank fitted. |

The frozen second-order/position/preceding-suffix predictor is refitted on each fixture's synthetic training words. No model selection, dose fitting, historical inference or Z3 calls occur.

## Predictive results

Gains average folios equally in bits/character over a position-aware within-word model; EOS event cost is included in loss. Positive means lower loss, without a significance threshold.

| Fixture | Gain range over three seeds | Positive runs |
|---|---:|---:|
| Encoder, quarter schedule | +0.03884 to +0.04610 | 3/3 |
| Generator, quarter preference | +0.01621 to +0.01923 | 3/3 |
| Encoder, half schedule | +0.10384 to +0.11222 | 3/3 |
| Generator, half preference | +0.04600 to +0.05221 | 3/3 |
| Encoder random-prefix null, one seed | −0.00010 | 0/1 |
| Generator zero-preference null, one seed | +0.00330 | 1/1 |
| Earlier manuscript, reused | approximately +0.009 | — |

All twelve active fixtures have positive novel-spelling gains relative to their own fitted training vocabulary. For the generator, such “novel” words are original development vocabulary entries absent from its sampled synthetic training set; they are not newly invented spellings or truly unseen source vocabulary.

The null generator draws independently by position, yet its score gains over the current baseline. Partial positional shrinkage in that baseline and finite-sample effects are possible explanations, not isolated causes. Do not read its gain as evidence of an explicit neighboring-word rule. Neither mechanism null is distribution matched to its active counterpart, and only one null realization was scored. These limitations motivate exact-inventory refitted controls rather than a threshold on absolute gain.

## Structural checks

The following show seed 31001 at quarter strength. Metrics average 32-word blocks equally, unlike folio-equal predictive gains. Local excess compares pairs separated by at most eight words with all pairs in the same block. One-edit pairs exclude exact repeats.

| Metric | Reused manuscript | Encoder | Generator |
|---|---:|---:|---:|
| Mean word length | 4.969 | 4.354 | 5.038 |
| Unique-word ratio per block | 0.8961 | 0.8880 | 0.9182 |
| Adjacent repeat fraction | 0.01124 | 0.00000 | 0.00544 |
| Local exact-repeat excess | +0.00038 | −0.00132 | +0.00054 |
| One-edit pair fraction | 0.02705 | 0.01244 | 0.02465 |
| Local one-edit excess | +0.00104 | −0.00105 | −0.00029 |

The generator has closer word lengths and one-edit density in this example, which is unsurprising given its direct access to manuscript words. The encoder is shorter, produces fewer near-word pairs and no adjacent repeats in these fixtures. Neither matches all features. No weighted structural distance, learned classifier or historical likelihood ratio is reported. The full tables for all seeds/strengths/nulls are retained in stage seven and assessment artifacts.

## Assessment and next priority

Known encoding and known generation can both create the observed kind of predictive gain. These concrete fixtures do not yet match its magnitude, and the positive independent-generator null shows why absolute gain is insufficient. Structural features may supply additional constraints, but vocabulary access, plaintext corpus, artificial schedule, expansion and differing strengths confound a comparison between these families.

Next: **compare excess gain over frequency/position/length-preserving refitted shuffles for each fixture**, using several null streams, then test preset weaker strengths near manuscript scale. Keep mechanisms and selection rules frozen before evaluation. Only after gain and nuisance distributions are calibrated should a candidate structural discriminator be evaluated on independent fixtures; do not tune a classifier on the manuscript.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.boundary_mechanisms --run
.venv/bin/python -m benchmarks.boundary_mechanisms_validation
.venv/bin/python -m benchmarks.boundary_mechanisms_assessment
.venv/bin/python -m pytest tests/integration/test_boundary_mechanisms.py -q
```

Three tests pass. Validation independently verifies **79,744 context/position-model word scores**, **27,104 decoded words**, all seven plan/result chains and aggregates. A separately implemented edit-distance test and pair-count metrics reconstruct all structural checks. Generator outputs are checked against training vocabulary. This is independent likelihood/construction verification, not an independently implemented random generator or corpus parser. Other stored gains are summarized from the frozen predictor rather than independently reconstructed here.

Artifacts: `experiments/results/boundary-mechanisms/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. Fourteen synthetic cases; prior modules/results remain intact. Cached corpus/source-quality limitations in the historical-prose comparison continue to apply.
