# Matched null contrasts for weaker boundary mechanisms

Seven plan → test → assessment iterations improve calibration but **do not identify a mechanism**. All twelve weaker known encoding/generation fixtures have larger gains than each of their three matched refitted shuffles. Both families can therefore produce an excess ordering signal. The earlier independent word generator's apparent +0.00330 gain becomes only **+0.000245 above its matched shuffles**, showing why absolute gain was misleading.

## Seven iterations

| Iteration | Plan/test | Assessment → next step |
|---|---|---|
| 1 | Three matched shuffles of each earlier mechanism-specific null | Zero-preference generator's shuffled gains are also approximately +0.003. Test weaker encoder schedules. |
| 2 | Encoder schedules 1/16 and 1/8, seed 32001 | Smaller absolute gains. Score weak generators. |
| 3 | Generator probabilities 1/16 and 1/8, seed 32001 | Smaller gains; compare exact-inventory controls. |
| 4 | Three refitted shuffles of each of the four fixtures | Each original exceeds all three shuffles. Replicate 1/8 fixtures. |
| 5 | 1/8 fixtures, seeds 32002/32003, three shuffles each | Both families retain positive excess. Replicate 1/16 fixtures. |
| 6 | 1/16 fixtures, seeds 32002/32003, three shuffles each | All twelve originals exceed controls. Record descriptive structure. |
| 7 | Freeze paired contrasts and structural checks | Excess gain is more informative than absolute gain, but not a mechanism discriminator. |

All doses, seeds, fixture construction and the seven-stage schedule are frozen before scoring. There are 54 newly scored cases: twelve active fixtures, 36 matched shuffles and six shuffles of the earlier null fixtures. Their original scores are reused with frozen provenance. An initial dependent-stage launch failed before scoring; the ordered resumable run completed the saved plan/result chain without changing fixtures or duplicating completed experiments.

## Matched controls and score

The previous known mechanisms remain unchanged. The encoder substitutes letters bijectively and inserts a preceding-output-dependent marker on a public within-line block-position schedule. The generator samples manuscript development words by position bin, sometimes preferring the training-fixed mapped initial for the preceding final unit. Encoder schedule fractions and generator probabilities are different strengths, not an equal-effect parameterization.

For every active fixture, three shuffles independently reorder whole words without replacement within folio × position-bin × word-length pools. They preserve exact word/spelling/frequency inventories per pool, every slot length, layout, novelty counts and position-only baseline losses. Separate train/evaluation streams are derived from shuffle seed and split name. The frozen predictor and baseline are refitted on each shuffled training set.

The reported contrast is:

`active suffix gain − mean of three refitted shuffled suffix gains`

Each gain is folio-equal bits/character over the matched position-only model, with end-of-word cost included. This contrast includes refitting and regularization effects; it is not a direct entropy or causal-effect estimate. Preserved length/position/folio dependencies can survive shuffling. Three controls are insufficient for a calibrated significance or power claim.

## Results

| Family / preset strength | Excess over mean matched shuffle, three seeds | Mean excess | Originals exceed all three shuffles |
|---|---|---:|---:|
| Encoder 1/16 | +0.008018, +0.006882, +0.007052 | +0.007317 | 3/3 |
| Encoder 1/8 | +0.015946, +0.014176, +0.013200 | +0.014441 | 3/3 |
| Generator 1/16 | +0.001731, +0.001560, +0.000559 | +0.001283 | 3/3 |
| Generator 1/8 | +0.005587, +0.002501, +0.002856 | +0.003648 | 3/3 |

For scale, earlier manuscript contrasts were approximately 0.00928 in the original character cohort and 0.00868 in the new-folio replication, using their respective refitted controls. Those manuscript results are reused, not newly scored here. The weaker encoder approaches that scale, whereas the tested generator doses remain smaller; neither family is selected or fitted to hit the target. Larger preset strengths from the preceding loop overshot it. No equal-effect comparison has been achieved.

| Earlier mechanism-specific null | Absolute original gain | Mean matched shuffled gain | Excess |
|---|---:|---:|---:|
| Random-prefix encoder | −0.000100 | −0.003214 | +0.003114 |
| Zero-preference generator | +0.003298 | +0.003053 | +0.000245 |

The zero-preference generator samples independently by position; its apparent gain mostly persists after shuffling. This is consistent with baseline/position-fitting or sampling effects, without isolating the cause. Conversely, randomizing encoder markers does not remove its German plaintext ordering; its positive contrast can include that residual ordering and model refitting effects. Neither mechanism-specific null is a universal “no dependence” null.

## Structural checks and limits

Seed 32001 examples:

| Metric | Encoder 1/16 | Generator 1/8 | Earlier manuscript |
|---|---:|---:|---:|
| Mean word length | 4.190 | 4.971 | 4.969 |
| Unique-word ratio per 32-word block | 0.8480 | 0.9108 | 0.8961 |
| Adjacent repeat fraction | 0.0000 | 0.0087 | 0.0112 |
| One-edit pair fraction | 0.0130 | 0.0239 | 0.0270 |

These examples illustrate separate structural measurements, not an effect-matched contest or selected best cases. Full metrics for every active weak fixture are retained. The generator directly accesses manuscript vocabulary, while the encoder uses German 113 prose; apparent structural closeness remains confounded. Metrics average blocks equally, whereas predictive contrasts average folios equally. No combined distance, classifier, historical likelihood or language ranking is fitted.

All keys/streams reuse the same source inventories. Three key/stream realizations are not independent corpora. The encoder's block-reset prefix schedule is constructed rather than historically justified. Shuffled ciphertext need not satisfy the original reversible rule; decoding is checked for genuine encoder fixtures only. Neither contractions nor new glyph segmentation are introduced. No Z3 calls occur.

Next priority: **stop tuning suffix gain and equalize vocabulary access before testing structural discriminators**. Compare known encoding and generation fixtures built from the same prose vocabulary/normalization, then check whether one-edit density or repetition still distinguishes them on independently seeded fixtures. Do not interpret the present generator advantage as evidence for manuscript generation.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.boundary_null_contrasts --run
.venv/bin/python -m benchmarks.boundary_null_contrasts_validation
.venv/bin/python -m benchmarks.boundary_null_contrasts_assessment
.venv/bin/python -m pytest tests/integration/test_boundary_null_contrasts.py -q
```

Three tests pass. Independent likelihood reconstruction verifies **307,584 context/position-model word scores**, **23,232 decoded words**, all seven result chains, aggregates, paired inventories/layout/slot lengths, invariant baselines, exact contrast arithmetic and independently reconstructed structural metrics. Other stored gains are summarized from the frozen predictor rather than independently reconstructed here. Earlier raw-source extraction and random generator implementations are reused, not independently reimplemented.

Artifacts: `experiments/results/boundary-null-contrasts/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. All earlier frozen modules/results remain intact.
