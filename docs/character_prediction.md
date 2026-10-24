# Open-vocabulary character prediction

The seven-stage loop finds a small preceding-word predictive signal after controlling for within-word character patterns and line position. The development-selected model gains **0.00915 bits per EVA character** over its position-aware baseline on 2,848 fresh words across 50 reserved folios. It improves on 37/50 folios and also improves prediction of novel spellings. This is evidence of predictive dependence, not evidence for a particular language, encryption system, or text-generation mechanism.

## Plan → test → assessment

| Iteration | Test | Assessment / next action |
|---|---|---|
| 1 | Normalize spelling probabilities; include unseen lowercase characters and end-of-word events | Nonempty, open-vocabulary spelling distributions pass. Proceed to within-word models. |
| 2 | Leave-one-development-folio-out selection among IID, first-order, and two second-order character models | Second-order model with smoothing strength 10 wins: 2.26873 bits/character versus IID 4.58641. Test order sensitivity. |
| 3 | Shuffle letters independently within each development word, preserving length and letter multiset | Character model is order-sensitive; IID score remains invariant. Add position controls. |
| 4 | Add line-start or four-bin position conditioning to the first character | Four-bin model wins: 2.25637 bits/character. Test incremental previous-word suffix context. |
| 5 | Condition first character on previous word's final EVA unit, with all/within/cross-line gates | All-transition model wins: 2.23945; within-line 2.24127; cross-line 2.25455. Freeze selections. |
| 6 | Select using development results alone | Freeze second-order + four-bin position + all-transition suffix model for overall and incremental-context evaluation. |
| 7 | Score every complete spelling on fresh text; perform position-bin-preserving whole-word permutations | Incremental gain replicates, including novel spellings. Independent reconstruction passes. |

## Fresh-text results

Scores include end-of-word cost; denominator is actual EVA characters. Main results average folio scores equally. Lower loss is better.

| Model | Bits/character |
|---|---:|
| Character IID | 4.63994 |
| First-order | 2.78199 |
| Selected second-order within-word model | 2.60942 |
| Second-order + position bins | 2.60166 |
| Frozen model: position + preceding suffix, all transitions | **2.59250** |
| Position + within-line suffix (secondary comparison) | 2.59362 |
| Position + cross-line suffix (secondary comparison) | 2.60055 |

The selected model's incremental gain is 0.00915 bits/character, with a descriptive folio bootstrap interval of [0.00557, 0.01287]. Among 1,309 spellings absent from training, pooled incremental gain is 0.00521 bits/character. Novel-spelling scores use character probabilities directly; there is no unknown-word class or evaluation vocabulary.

Of the 50 evaluation folios, 38 have not been evaluated in the earlier statistical loops; their mean incremental gain is 0.00604. Twelve contain earlier evaluated words elsewhere; their gain is 0.01902. **All evaluation word occurrences are fresh**, disjoint from every earlier training/evaluation block. Shuffling words within position bins increases selected-model loss by 0.01232 bits/character while preserving the position-only baseline.

## Protocol and limits

Training retains the same 1,024 words on twelve development folios, splitting prior 64-word blocks into 32-word blocks. Selection uses leave-one-folio-out development scores. Evaluation uses all 89 remaining eligible 32-word blocks on reserved folios, selected by the earlier fixed folio hash rule. This shorter extraction broadens the cohort and introduces more block boundaries; it is not a matched replication of the earlier 64-word word-class experiment.

Models assign probabilities over 26 lowercase ASCII EVA units, plus an end event, with EOS forbidden before the first character. Character order means order **within a word**. External position and previous-word suffix affect only its first character. Training uses observed spellings; unseen spellings remain scoreable. Line identity and position are cached transcription proxies (`folio:locus:physical_line`, `word_in_locus`). Atomic EVA units are not established manuscript glyphs.

The bootstrap is descriptive; folios need not be independent historical samples. Model comparisons share training and evaluation data. The large within-word improvement mainly measures predictable EVA spelling structure; it does not diagnose its cause. This loop does not decrypt text or use Z3. Numerical losses cannot be compared directly with prior word-class bits/token scores.

## Reproduce and validate

```sh
.venv/bin/python -m benchmarks.character_prediction --run
.venv/bin/python -m benchmarks.character_prediction_validation
.venv/bin/python -m benchmarks.character_prediction_assessment
.venv/bin/python -m pytest tests/integration/test_character_prediction.py tests/integration/test_line_context_prediction.py tests/integration/test_context_prediction.py -q
```

The run resumes stored stages. Each plan is saved before scoring; stage six freezes selections before stage seven. Source/code hashes and result chains are checked on validation. An independent implementation reconstructs all 38,720 model/word scores, baseline gains, split provenance, raw words/layout fields, selection rules, and permutation diagnostics. Twelve combined integration tests pass.

Artifacts: `experiments/results/character-prediction/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`.

The next useful experiment is a matched calibration: apply this same frozen scoring protocol to ordinary prose, known encrypted prose, and structure-preserving surrogate text, with explicit symbol and length normalization. Establish which controls show a comparable incremental suffix signal before using it to rank manuscript mechanisms. Keep this successful predictive measurement frozen instead of tuning more context models on its heldout cohort.
