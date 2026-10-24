# Frozen character-prediction calibration

Seven plan → test → assessment stages compare the previously selected manuscript predictor with Latin prose, reversible encodings, refitted surrogates, and an explicit boundary-dependent positive control. The predictor detects the positive control and loses its incremental benefit on shuffled manuscript words. Neither of two Caesar samples, nor their tested encodings, reproduces the manuscript's positive preceding-suffix gain. This supports an order-dependent statistical signal; it does not distinguish encryption from generation or identify a language.

## Stages and results

The model is frozen from `character-prediction/iteration-6.json`: second-order within-word character model, four position bins, preceding-word final-unit context affecting the first character only. No new model selection or Z3 calls occur.

| Stage | Plan/test | Assessment and next action |
|---|---|---|
| 1 | Score plain Caesar sample A | Suffix context hurts slightly. Test a representation invariant. |
| 2 | Bijective letter substitution of A | Every loss and gain is unchanged. Separate expansion from homophonic choice. |
| 3 | One unique two-character code per letter | Incremental context still hurts. Add random homophones. |
| 4 | Two unique two-character codes per letter, uniform random selection | No positive incremental gain. Check surrogates. |
| 5 | Shuffle Latin and manuscript words within position bins; refit both models | Manuscript gain falls approximately to zero. Test known boundary dependence. |
| 6 | Set each within-line word's first unit to its preceding output word's final unit | Strong positive gain on all 50 evaluation layout groups. Replicate prose controls. |
| 7 | Repeat plain/substituted/expanded/homophonic/shuffled Latin on disjoint sample B | All five incremental gains remain negative. Retain results without mechanism ranking. |

Positive gain means lower loss than the matched position-aware model. Per-character gains average evaluation groups equally; per-word gains independently normalize each group's sum by its word count. They are not obtained by multiplying the per-character mean by the pooled mean word length.

| Case | Gain, bits/character | Gain, bits/word | Mean word length |
|---|---:|---:|---:|
| Prior manuscript, reused | +0.00915 | +0.04448 | 4.97 |
| Refitted manuscript shuffle | −0.00012 | −0.00086 | 4.97 |
| Artificial manuscript boundary dependence | +0.18261 | +0.87908 | 4.97 |
| Plain Latin A | −0.00162 | −0.00925 | 5.88 |
| Bijective substitution A | −0.00162 | −0.00925 | 5.88 |
| Deterministic expansion A | −0.00062 | −0.00720 | 11.77 |
| Random homophonic expansion A | −0.00136 | −0.01572 | 11.77 |
| Refitted Latin shuffle A | −0.00268 | −0.01546 | 5.88 |
| Plain Latin B | −0.00207 | −0.01238 | 6.07 |
| Bijective substitution B | −0.00207 | −0.01238 | 6.07 |
| Deterministic expansion B | −0.00057 | −0.00672 | 12.13 |
| Random homophonic expansion B | −0.00134 | −0.01536 | 12.13 |
| Refitted Latin shuffle B | −0.00276 | −0.01625 | 6.07 |

The manuscript-minus-refitted-shuffle gain contrast is +0.00928 bits/character, with a descriptive paired-folio bootstrap interval [0.00553, 0.01305]. The original manuscript model improves on 37/50 folios; its shuffled counterpart on 27/50, with a slightly negative overall mean. The positive control improves on all 50.

## Matching, normalization, and limitations

Every case has 1,024 training words and 2,848 evaluation words. Latin comes from cached `caesar-latin-v2.json`, using its existing lowercase/diacritic/j-to-i normalization and applying v-to-u here. Each sample contains contiguous normalized prose, split into a training prefix and evaluation continuation. Samples A/B use seeds 26001/26002 and nonoverlapping source intervals. Each encoding and surrogate shares its sample's words and split; there is no claim that the Caesar excerpts have never appeared in earlier project experiments.

Latin words occupy copied manuscript layout slots: the same block sizes, position indices and within/cross-line gates. These are **artificial Latin lines**, not historically observed Latin layout. The 50 Latin evaluation groups are manuscript-shaped blocks, not independent Latin folios or texts. This matches the scoring design but cannot reproduce manuscript layout-content interactions.

Letter substitution permutes all 26 labels. Expansion assigns disjoint two-character codes: one per plaintext letter, or two with uniform random choice. Boundaries are preserved, making these encodings reversible; the audit decodes every training and evaluation word. The alphabet remains 26 lowercase labels and EOS. Expansion doubles length; it is not a manuscript-length-matched control. Character order two also spans a different plaintext scale after expansion, so total losses are not historical mechanism likelihoods.

The random homophone-choice generator restarts at the same seed for training and evaluation, reusing its choice stream. Choice events are random within each part, but the two streams are not independent. This implementation limitation is recorded rather than silently changing frozen artifacts; future random-choice calibration should use separate streams with one shared key.

Surrogates shuffle whole words separately in every block within four position bins, preserving exact word counts, spelling inventories, lengths and positional counts. Both context and baseline are refitted to surrogate training text, then scored on surrogate evaluation text. There is one surrogate realization per corpus/sample. The positive control injects a strong, artificial first-unit dependence; it demonstrates detection, not sensitivity at the much smaller manuscript effect size.

Only one language and author are used. The manuscript scores are reused, not independently replicated. The results do not show that Latin encryption is unlikely in general: the frozen statistic can miss other forms of dependence and the tested encodings are narrow.

## Reproduce

```sh
.venv/bin/python -m benchmarks.character_calibration --run
.venv/bin/python -m benchmarks.character_calibration --validate
.venv/bin/python -m benchmarks.character_calibration_assessment
.venv/bin/python -m pytest tests/integration/test_character_calibration.py tests/integration/test_character_prediction.py -q
```

Plans precede scoring; source/code hashes and prior selection are pinned. Seven tests pass. Independent probability reconstruction verifies **136,704 word/model scores**, all aggregate results, stage chains, bijective score invariance, matched layout/lengths and surrogate inventories. The assessment separately audits code reversibility and positive-control boundary changes.

Artifacts are under `experiments/results/character-calibration/`: prepared cases, seven plans/results, validation, and assessment. Prior frozen modules/results remain intact.

Next priority: **effect-size calibration** with several weak boundary-dependent controls and independent random streams, preserving manuscript lengths and spelling distributions as closely as possible. Determine whether the measured 0.00915 gain reliably separates a weak injected dependence from refitted surrogates before expanding language or cipher searches. A strong positive-control success alone is insufficient for that decision.
