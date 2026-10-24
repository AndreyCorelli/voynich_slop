# Shared-inventory source-order fixtures

Seven plan → test → assessment iterations remove the previous generator's access to manuscript vocabulary as a comparison advantage. Both sources receive exactly the same prose words per block, position bin and length class, then use the same reversible encoding. **Global one-edit density no longer offers the previous apparent distinction.** Original prose has higher excess suffix gain in all six pairs; locally reordered text produces more adjacent repetition. These are candidate source-order differences, not general encoding-versus-generation signatures.

The comparison deliberately separates source ordering from representation. Original prose and generated ordering are both encoded, and both decode correctly. Encoding and generation can compose; they are not mutually exclusive historical causes.

## Seven iterations

| Iteration | Plan/test | Assessment → next action |
|---|---|---|
| 1 | Freeze two prose inventories, common keys/schedule and local-order rules; verify decoding | Equal payload resources and representation pass. Score first German 113 pair. |
| 2 | Prose/local ordering pair, seed 33001 | Both positive; original prose larger. Replicate keys/streams. |
| 3 | German 113, seeds 33002/33003 | Original prose remains larger. Test preset German 133 source. |
| 4 | German 133, all three seeds | Same ordering difference. Compare matched shuffles. |
| 5 | Three refitted shuffles of every fixture | Both order types retain positive excess. Inspect structural checks. |
| 6 | Payload and encoded structural metrics | Payload global features invariant by construction; encoded one-edit densities close. Adjacent repetition differs. |
| 7 | Freeze paired contrasts and interpretation | No classifier or manuscript ranking. Predeclare ordering statistic for independent fixtures. |

There are twelve active fixtures and 36 shuffled controls, or **48 scored cases**. Each has 1,024 training and 2,848 evaluation words. The original selected character predictor is frozen and refitted to each case; no source, dose, rule or model is chosen on evaluation results. No Z3 calls occur.

## Exact matching and construction

Sources are cached German 113 and 133 primary excerpts from the historical-prose benchmark, retaining its normalization and source limitations. For each source, derive the ending-to-initial mapping only from its original training transitions, using the previously fixed position-adjusted excess-count rule. No manuscript vocabulary or manuscript ending mapping is used.

The local generator assigns supplied words without replacement within **block × position-bin × length** pools, favoring the training-mapped initial of the preceding output's final unit at eligible within-line transitions with fixed probability 0.5. If a desired word is unavailable, fall back to random assignment. It preserves exact words, frequencies, slot lengths and layout in each block.

This generator receives the evaluation block's public word inventory. It generates an ordering, not new lexical spellings, and is not an independent-vocabulary text generator. This explicit resource assumption makes matching exact and must not be mistaken for unseen-text prediction.

Both original prose and local ordering receive the same bijective 26-letter payload key, marker key and public 1/16 within-line block-position schedule. Thus keys, prefix counts, output slot lengths and layout match exactly. Marker identities can differ because preceding words differ; resulting encoded word/frequency inventories are not necessarily equal between order types. All genuine fixtures decode to their own known payload sequence.

For each active fixture, three nulls shuffle its encoded words independently in training and evaluation within folio × position-bin × length pools. They preserve exact encoded inventories and baseline folio losses, but can retain dependencies tied to preserved constraints. Contrast means original gain minus the mean of its three refitted shuffle gains.

## Prediction results

Excess gains are folio-equal bits/character over matched controls; original gains are measured against a position-aware within-word model. End-of-word cost is included in loss.

| Source | Seed | Original prose excess | Local-order excess | Local minus prose |
|---|---:|---:|---:|---:|
| German 113 | 33001 | +0.006758 | +0.003461 | −0.003296 |
| German 113 | 33002 | +0.008862 | +0.006483 | −0.002378 |
| German 113 | 33003 | +0.006280 | +0.004444 | −0.001836 |
| German 133 | 33001 | +0.005462 | +0.004161 | −0.001301 |
| German 133 | 33002 | +0.007457 | +0.003433 | −0.004024 |
| German 133 | 33003 | +0.005645 | +0.003645 | −0.002000 |

The local rule adds its own preference while destroying original prose associations; a smaller gain does not imply it creates no dependence. Both output types also carry the common explicit boundary-conditioned encoding. Three seeds and two sources do not establish an effect-size classifier or general natural-language signature. Neither type is tuned to match the manuscript gain.

## Structural results

Examples below use seed 33001 after common encoding. Metrics average 32-word blocks equally, unlike folio-equal predictive scores.

| Source / ordering | Mean length | Unique ratio | Adjacent repeats | One-edit pair fraction |
|---|---:|---:|---:|---:|
| German 113, prose | 4.1896 | 0.8480 | 0.00000 | 0.012980 |
| German 113, local | 4.1896 | 0.8476 | 0.00652 | 0.013026 |
| German 133, prose | 4.5453 | 0.8669 | 0.00109 | 0.013841 |
| German 133, local | 4.5453 | 0.8666 | 0.00689 | 0.013796 |

Before encoding, mean length, unique ratio and global one-edit density are identical in every paired block by the inventory constraint. This is a mathematical invariant, not evidence for either mechanism. After sparse context-marker encoding, one-edit density remains close across types. The earlier comparison's generator/manuscript closeness therefore supplies no portable structural discriminator once vocabulary access is equalized.

Adjacent repetition changes with ordering and is a candidate for a future test. It is not independent of available word frequencies; absolute repeat fractions cannot be compared as if inventories were irrelevant. Local exact-repeat and one-edit excess metrics are also retained for all fixtures, without result-based feature weighting or classification.

## Limits and next priority

Only one preset local-order rule/strength, two German sources and three keys/streams are tested. Corpus chronology, edited normalization and artificial layout remain. The generator uses supplied evaluation inventories; it cannot invent forms or independently predict their frequencies. Common representation means the study compares payload order under encoding, not exclusive encoding/generation families. Refitted contrasts include model-regularization effects and three controls do not calibrate significance or power.

Next: **predeclare frequency-adjusted adjacent repetition as a candidate ordering statistic**, then evaluate it on disjoint excerpts, additional sources and several ordering generators under the common representation. Test whether it adds a reproducible distinction after word-frequency matching, before applying it to manuscript mechanisms. Freeze the feature before new fixture evaluation; keep current results as development evidence.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.shared_inventory_mechanisms --run
.venv/bin/python -m benchmarks.shared_inventory_validation
.venv/bin/python -m benchmarks.shared_inventory_assessment
.venv/bin/python -m pytest tests/integration/test_shared_inventory_mechanisms.py -q
```

Two tests pass. Independent validation reconstructs **273,408 context/position-model word scores**, **46,464 decoded words**, all seven plan/result chains and aggregates. It checks exact block/position/length payload inventories, common keys and output lengths, null inventory/baseline invariance, paired contrast arithmetic and independent structural metrics. Mapping and random-order generation reuse earlier tested implementations rather than separate independent implementations; other stored gains are summarized from the frozen predictor.

Artifacts: `experiments/results/shared-inventory-mechanisms/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. Prior frozen modules/results remain intact.
