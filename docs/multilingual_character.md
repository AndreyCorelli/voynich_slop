# Historical prose comparison with the frozen character statistic

Seven plan → test → assessment iterations compare the frozen preceding-suffix statistic across cached medieval Latin, fifteenth-century German and medieval Italian texts. **The results do not support a language ranking.** German sources sometimes show a small gain, but it varies with source, excerpt and artificial layout. All seven primary prose cases fall below the reused manuscript gain; all have negative novel-spelling gains.

## Seven iterations

| Iteration | Plan/test | Assessment → next action |
|---|---|---|
| 1 | Audit cached sources and freeze sample selection | Seven full-size prose cases selected; Czech coverage gap explicit. Score medieval Latin. |
| 2 | Aquinas and Vita Caroli IV | Both incremental gains negative. Score four preset German sources. |
| 3 | German source IDs 113, 133, 233, 243 | Three positive, one negative; all novel-spelling gains negative. Score Italian. |
| 4 | Decameron, day-one stories | Gain negative. Test refitted surrogates. |
| 5 | Position/length-inventory-preserving shuffled versions of all seven sources | All gains negative. Test artificial layout sensitivity. |
| 6 | Same words, eight-word artificial lines | German 243 changes sign; other German positives shrink. Test disjoint excerpt replication. |
| 7 | Disjoint tail excerpts of Caroli, German 113/133 and Italian | German 113 stays positive; 133 changes sign; Latin/Italian remain negative. Retain source heterogeneity. |

There are 25 scored cases. The character order, smoothing, position bins and suffix model remain frozen from `character-prediction/iteration-6.json`; each case refits model counts. No model selection or Z3 calls occur.

## Results

Gains are folio-equal incremental bits per character over a position-aware within-word character model. Positive means lower loss. Prose “folios” are copied evaluation grouping slots, not historical source folios. Numerical losses include end-of-word event costs.

| Source | Primary gain | Eight-word-line gain | Refitted shuffle gain | Disjoint excerpt gain |
|---|---:|---:|---:|---:|
| Aquinas, De ente et essentia | −0.000967 | −0.001550 | −0.001722 | — |
| Vita Caroli IV | −0.004441 | −0.003224 | −0.003684 | −0.002727 |
| German 113, Kottanerin recollections | +0.002314 | +0.001202 | −0.002444 | +0.003901 |
| German 133, Pillenreuth text | +0.000733 | +0.000158 | −0.002560 | −0.000391 |
| German 233, Cirurgia | −0.001979 | −0.000701 | −0.003634 | — |
| German 243, Hortus sanitatis | +0.002318 | −0.000349 | −0.003082 | — |
| Italian, Decameron day one | −0.001192 | −0.001285 | −0.003777 | −0.001914 |
| Manuscript, earlier result reused | **+0.009152** | not evaluated here | earlier controls reported separately | not evaluated here |

All seven primary prose novel-spelling gains are negative. German 113's disjoint excerpt has positive novel-spelling gain (+0.002688); it is not a universal prose failure. The largest overall prose gain in these cases, +0.003901, remains below the earlier manuscript result. This is an empirical comparison of selected passages, not a language posterior or rejection of their encryption.

## Coverage, matching and normalization

Each scored case uses 1,024 training words and 2,848 evaluation words, assigned to the existing 32 development and 89 evaluation blocks. Source selection is fixed before scoring: the first 121 eligible nonoverlapping 32-word blocks from each selected work/collection, with first 32 training and next 89 evaluation. Four replication cases use the last 121 blocks, disjoint from their primary samples.

Blocks never bridge source-segment boundaries, excluded tokens or non-ASCII forms. Gaps between selected blocks are allowed, so these are ordered block excerpts rather than a continuous 3,872-word passage. Source-slot indices identify the selected original blocks; surrogate word permutations preserve their inventories but do not retain individual word-origin indices.

The shared alphabet is the frozen model's 26 lowercase labels plus EOS. The existing historical parser strips diacritics and expands ligatures. Additional Latin normalization joins j/i and v/u while retaining historical lexical spellings. German retains historical spellings, expands known abbreviations and ß to ss, treats graphical umlauts as one base vowel, and excludes unresolved abbreviation-bearing forms/editorial insertions as barriers. Italian keeps apostrophized written words together without inventing omitted letters. Non-ASCII normalized words are barriers, not silently dropped tokens.

The frozen coverage audit includes all nine cached German sources, both Latin works, Italian and Czech sources. Selected German IDs were preset, not chosen by predictive gain. Each needs at least 121 blocks. Czech Bible prose excerpts provide only 8–9 blocks each; Dalimil provides 48 blocks and is verse. They are recorded as coverage gaps, not forced into a smaller, unmatched comparison.

The copied manuscript positions/gates are artificial layout for prose. The sensitivity assigns each 32-word block four eight-word lines, preserving words and source blocks while changing position bins/gates. Surrogates instead reorder words within folio/position-bin/length pools, preserving exact inventories, every slot length and baseline losses; independent train/evaluation random streams are used.

## Source-quality caveats

Source files and manifests are cached and checksum-verified. The historical parser is reused and hash-pinned; its extraction is not independently reimplemented in this experiment. Comparisons have different word lengths, alphabets in use, vocabularies, novelty rates and genres, despite equal word counts.

German normalization is the earlier length-study convention, **not** the corrected solver-vocabulary quarantine. The selected primary 133 sample contains no previously questioned k/x forms. Primary 233 includes one standalone v in evaluation whose lexical interpretation was previously unresolved. One-letter counts for primary/replication cases are saved in the assessment; marked-initial and other editorial-normalization effects may remain. Preserve these qualifications before treating results as clean historical-language evidence.

Works are independently sourced, but not representative language samples. Two Latin texts share an editorial pipeline, Italian comes from one collection, and German represents selected editions/genres. Four replications are disjoint excerpts within the same works, not independent authors. The manuscript result is reused, and there is one surrogate realization per prose source. No historical folio uncertainty interval or significance test is claimed.

## Assessment and next step

Positive German gains show that natural prose can produce this statistic. Their source/layout sensitivity and lower magnitudes do not identify German as the manuscript language. Neither negative Latin/Italian gains nor the tested prose encodings reject those languages or encryption families.

Next priority: **replicate the manuscript signal on untouched eligible text using a frozen protocol and explicit layout sensitivity**. The prose comparisons show why a single reused manuscript effect should not be treated as a stable language discriminator. Keep corpus-specific results and coverage failures so broader normalization or language controls can be revisited without repetition.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.multilingual_character --run
.venv/bin/python -m benchmarks.multilingual_character_validation
.venv/bin/python -m benchmarks.multilingual_character_assessment
.venv/bin/python -m pytest tests/integration/test_multilingual_character.py -q
```

Three tests pass. Independent reconstruction validates **142,400 context/position-model word scores** across 25 cases, all seven plan/result chains, aggregates, train/evaluation and replication disjointness, surrogate inventories, baseline invariance and layout-sensitivity words. The validator reuses the frozen preparation/source parser, so it is not an independent source-extraction audit. Other stored gains are summarized from the shared predictor rather than independently reconstructed here.

Artifacts: `experiments/results/multilingual-character/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. Prior frozen modules/results remain intact; no downloads or solver runs were needed.
