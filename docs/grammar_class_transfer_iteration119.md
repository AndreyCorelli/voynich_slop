# Iteration 119: frozen class inference across authors and context volumes

**Preserve the conditional transfer finding:** without refitting, the predictor classifies11/16 types correctly in expanded Jerome and13/15 present types in expanded Caesar, compared with8 correct types for the raw model and class priors in each expanded input. This extends the earlier source-test class result to two cached authors. It is not fresh-data confirmation or a repair/PP-restoration result.

## Frozen inputs and inference

The model is exactly116's class model trained on13 non-catalogue source types, followed by117's class-balanced one-parameter intercept. Neither uses the16 target types' class labels for fitting. The catalogue and other supplied anchor mappings remain given; every present target type is masked globally as an opaque identity with unknown class during prediction. Reference classes are attached only after predictions are frozen.

Jerome inputs are exactly112's original100 sentences and829-sentence FORM-only expansion. Caesar inputs are exactly107's original100 and largest2494-sentence admitted expansion, including the uniform initial-abbreviation correction. Original100 inputs are identical prefixes of their expansions. No books, sentences, models, cutoffs, or types are selected from these outcomes. Missing and unsupported types are reported, not counted as successes.

There are no new annotations, raw-text projections, reserve features, lexical test queries, pair repairs, or PP predictions. Reference classes remain the supplied source modal ADP/CCONJ classes, not new token-level POS labels. Both authors' texts were used in earlier development. Expanded volumes and segmentation conventions differ, so comparing author accuracy does not isolate author difficulty or context length.

## All present types: primary results

| Author / context | Sentences | Types present | Raw correct | Calibrated correct | Prior correct | Calibrated NLL |
|---|---:|---:|---:|---:|---:|---:|
| Jerome original |100|13|6|7 (53.85%)|8|.8656|
| **Jerome expanded** |829|16|8|**11 (68.75%)**|8|.6292|
| Caesar original |100|13|7|12 (92.31%)|7|.5307|
| **Caesar expanded** |2494|15|8|**13 (86.67%)**|8|.6420|

Both the3/13 training prior and.5 balanced prior make the same hard ADP prediction at the frozen threshold; their losses differ. In expanded inputs, the calibrated predictor beats the balanced-prior NLL.6931 as well as raw NLL (Jerome.8293, Caesar.8079). Expanded type AUC is.7344 for Jerome and.8393 for Caesar; calibration preserves raw ordering.

Jerome original does not beat the prior:7/13 versus8/13, and its NLL is worse than both priors. Transfer is therefore not uniformly reliable at low volume. Supported-type results are3/5 original and10/13 expanded for Jerome;9/10 original and13/15 expanded for Caesar. The expanded Jerome unsupported types remain included in the primary11/16 result.

Expanded Jerome gets5/8 ADP and6/8 CCONJ types correct. Its errors are `ab`, `ac`, `atque`, `ex`, `per`; `ac` and `atque` have only four and one occurrences. Expanded Caesar gets7/8 ADP and6/7 CCONJ types correct. Its errors are `sine` (56 occurrences) and `uel` (10 occurrences), so adequate count support does not eliminate errors. `c` is absent from the corrected Caesar context and is not inferred or scored.

## Compare the same types before claiming a volume gain

The original Jerome input lacks `atque`, `que`, `uel`. Over its13 common types, calibration improves7/13→9/13: it gains `ad`, `aut`, `sed` but loses `ab`. The expansion adds correct `que`/`uel` and incorrect `atque`, giving11/16 overall.

The original Caesar input lacks `c`, `sine`, `uel`. Over its13 common types, calibration improves12/13→13/13, correcting `de` with no losses. The expansion adds incorrect `sine` and `uel`, while `c` remains absent. This gives13/15 overall: **the overall percentage falls even though every common type is now correct**. Neither raw accuracy fractions across changing type sets nor the two expansions establish monotonic context-length effects.

These are repeated word types across overlapping author views, not independent samples to pool into a general accuracy guarantee. The result supports conditional binary grammatical-class inference with supplied surrounding anchors. It does not identify plaintext nuclei, recover full morphology/dependencies, improve clean PP coverage, validate the failed endpoint veto, or change a default algorithm.

Next: test whether these inferred classes have downstream grammatical value. On cached source data only, hide target surface identities and classes, then compare PP membership inference with no target classes, predicted classes, supplied classes as an oracle ceiling, and shuffled classes. Keep identities hidden in every arm and freeze PP models/thresholds before evaluation. This would measure actual structural benefit rather than extrapolating from class accuracy. Matched-volume class validation remains a separate useful control.

Verification:29 focused tests pass. The audit verifies17 input hashes, independently recomputes57 type probabilities and108 metric groups, confirms target identity/class poisoning invariance in all four views, and replays both common-type volume comparisons. Artifacts are in `experiments/results/grammar-restoration/iteration119/`.
