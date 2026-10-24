# Seven-stage line-position controls for context prediction

This loop tests whether the preceding-suffix signal persists after accounting for transcription line position. It retains the prior development text and evaluates a new, disjoint folio cohort. The results preserve a raw predictive signal but fail to replicate the selected within-line improvement over its position baseline. No solver or cipher-model changes occur.

## Frozen data and models

Development remains 16 clean, nonoverlapping 64-word blocks on 12 folios. No unused blocks remained on the earlier evaluation folios. The new evaluation contains **all 11 eligible blocks on five other folios** in the same SHA256-reserved partition, with no overlap with development or either earlier evaluation set. This yields 704 fresh words.

A line is proxied by the record's folio, transcription locus and physical transcription line. `word_in_locus` provides ordinal position. These are transcription layout proxies, not a newly established interpretation of manuscript layout. The two-position baseline distinguishes position zero from later positions; the four-bin baseline uses 0, 1, 2–3 and 4+. No future line-ending information or current target spelling is used to define position.

Every training fold retains vocabulary count≥2, singleton/novel `<UNK>` handling, unigram pseudocount 0.5, contextual prior strength 50 and mixture weight 0.5. Positional distributions back off to unigram. Joint suffix distributions back off to the position distribution. A suffix refers to the last atomic EVA unit of the preceding observed word. First words of extracted blocks have no preceding context; no transition crosses a block/barrier.

Within-line gates use only same-line transitions; cross-line gates use only transitions between line proxies. All gates remain fixed in permutation diagnostics. Strong smoothing reduces, but cannot eliminate, sparse-context overfitting.

## Seven iterations

1. Freeze layout annotations, cohort and line/ordinal definitions; count development transition strata.
2. Cross-validate global frequency, line-start frequency and four-bin frequency by leaving out one development folio. Four-bin position wins among the two positional candidates.
3. Test suffix prediction on all, within-line and cross-line transitions without positional conditioning. Most development gain comes from within-line suffixes.
4. Add suffix prediction to the development-selected position baseline. Within-line suffixes provide the largest incremental development gain, about 0.0164 bits/token over that baseline.
5. Test the selected controlled context on development permutations preserving each block's exact word multiset within ordinal bins. This breaks neighboring-word order while holding positional lexical frequencies fixed; it does not alter selection.
6. Freeze two selections: overall predictive winner `suffix-all`, and the controlled diagnostic `position+suffix-within`. Both are chosen from development only.
7. Evaluate all nine frozen models on the five new folios, keeping selections unchanged. Repeat the position-bin-preserving permutation diagnostic on heldout blocks.

All stages have frozen plans and preceding-result digest chains. Ordinal grids and smoothing are fixed before testing. Earlier code, source data and scored experiments remain unchanged.

## Fresh heldout result

Positive gain means better log prediction. Overall gains weight each folio equally. Known-word gains weight the known-token subset and should not be algebraically combined with the folio-weighted overall metric.

| Model | Gain over unigram, bits/token | Gain over matching position baseline |
|---|---:|---:|
| Unigram | 0 | 0 |
| Line-start position | +0.0441 | 0 |
| Four-bin position | +0.0258 | 0 |
| **Selected overall: suffix-all** | **+0.0498** | +0.0498 (no positional conditioning) |
| Suffix-within | +0.0314 | +0.0314 (no positional conditioning) |
| Suffix-cross | +0.0327 | +0.0327 (no positional conditioning) |
| Position + suffix-all | +0.0129 | -0.0129 |
| **Selected controlled: position + suffix-within** | **-0.0007** | **-0.0266** |
| Position + suffix-cross | +0.0395 | +0.0136 |

The raw suffix effect replicates against global frequency on this new cohort. However, the development-selected within-line controlled model worsens its matching position baseline by **0.0266 bits/token**, improves on only one of five folios, and also has negative known-word gain (-0.0282 bits/known word). This controlled result does not support a robust additional within-line suffix advantage under the tested smoothing and data regime.

The cross-line joint model has a positive heldout incremental gain, but it was not the development-selected controlled model. That is an exploratory observation, not grounds to replace the selected diagnostic or claim successful replication. Likewise, the simpler line-start model beats the four-bin model on heldout data; the original position selection remains unchanged.

The selected controlled model loses a further **0.0461 bits/token** after position-bin-preserving shuffling. Its position baseline is invariant to those permutations, as independently verified. This illustrates why a model beating shuffled versions does **not** establish that it improves a sensible predictive baseline.

There are 610 within-line transitions, 83 cross-line transitions and 11 block starts. **334/704 targets map to `<UNK>`**, so the scores are not full-spelling prediction losses. Five folios provide a small cohort; no universal significance or causal attribution is claimed.

## Assessment and next priority

Line position is a useful predictive covariate. Raw suffix context also carries information relative to global frequency. The current joint within-line model does not improve its baseline reliably. This could reflect positional confounding, insufficient training, an overly fine context model or cohort differences; the experiment does not distinguish these explanations and does not prove position explains all order-dependent structure.

Do not expand suffix/smoothing grids to rescue this failed controlled replication. The next useful measurement improvement is **open-vocabulary character-level prediction**, so novel word spellings are scored directly rather than collapsed into one unknown class. Freeze a small within-word model and position-aware variants, compare the incremental effect of preceding-word context, and retain folio-level evaluation. Use compatible controls before attributing any character-pattern success to language, copying or encryption. This is a change in the measurement bottleneck, not evidence for any mechanism.

## Reproduction and checks

```sh
.venv/bin/python -m benchmarks.line_context_prediction --run
.venv/bin/python -m benchmarks.line_context_validation
.venv/bin/python -m benchmarks.line_context_assessment
.venv/bin/python -m pytest tests/integration/test_line_context_prediction.py tests/integration/test_context_prediction.py -q
```

Three new focused tests and five existing predictive tests pass. All seven stages and nine models validate. The independent checker reconstructs vocabulary, position counts, suffix counts, every prediction loss, all permutation diagnostics and baseline invariance without using the model's fit/probability functions. Source/code provenance, disjoint folios, selection and stage chains are checked. Artifacts are under `experiments/results/line-context-prediction/`, including protocol, plans/results, validation and assessment. Zero solver calls or downloads.
