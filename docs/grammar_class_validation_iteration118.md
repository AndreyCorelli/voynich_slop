# Iteration 118: frozen class predictor on cached source-test words

**Preserve the positive conditional result:** the frozen class-balanced predictor gets **12/16 function-word types correct (75%)**, versus8/16 for the raw model and class-prior baselines. It gets6/8 ADP and6/8 CCONJ types correct. The eight-type evaluation subset from116/117 remains7/8 correct on this different sentence split. This supports the class-calibration finding; it does not validate a repair gate or recover lexical nuclei.

## Frozen validation

The test uses all770 sentences/9956 tokens in the existing49 source-test partition, disjoint from source fit/calibration and all200 reserved IDs. These exclusions are checked before projecting cached word forms. The inference input uses only words and sentence/author metadata from existing44 cache; it consumes no token POS, morphology, dependencies, or new annotations.

The class model is exactly116's final model trained on13 non-catalogue types. Its intercept is exactly117's `balanced13` calibration,1.4074229894692558, fitted on those13 types' out-of-fold profiles. All16 catalogue types are excluded from both models' training labels. Every occurrence of all16 types has its anchor identity/class hidden in the predictor's input; opaque IDs group occurrences. Other supplied anchor mappings remain visible. The catalogue, segmentation, and those other anchors are privileges, so this is conditional class inference rather than blind anchor discovery.

There is no refitting, threshold selection, candidate filtering, repair enumeration, or PP prediction. Class probability above.5 means CCONJ; ties mean ADP. Predictions are frozen before reference classes are attached. The reference is the supplied source modal class for each type, not a newly consumed token-level annotation. The source-test text has been used in older experiments; it is not a fresh corpus, although this predictor and intercept were frozen before these predictions.

## Primary result

All16 types are present and satisfy the existing support threshold (five occurrences in at least three sentences).

| Predictor | Correct types | Type accuracy | Mean negative log likelihood | AUC |
|---|---:|---:|---:|---:|
| Raw |8/16|50%|.8465|.8125|
| **Frozen balanced13** |**12/16**|**75%**|**.6108**|.8125|
| Training-type prior,3/13 CCONJ |8/16|50%|.8644|.5000|
| Balanced prior,.5 |8/16|50%|.6931|.5000|

The unchanged AUC is expected from a monotone offset. The raw model predicts all16 types as ADP; calibration trades two lost ADP classifications for six newly correct CCONJ classifications. Its four errors are `c`, `per`, `sine`, `uel`.

| Type | Reference | Occurrences | Sentences | Calibrated P(CCONJ) |
|---|---|---:|---:|---:|
| a |ADP|67|57|.3919|
| ab |ADP|22|22|.2842|
| ac |CCONJ|11|11|.6290|
| ad |ADP|105|94|.4341|
| atque |CCONJ|16|15|.5997|
| aut |CCONJ|55|30|.5203|
| c |CCONJ|34|21|.4528|
| de |ADP|96|75|.4689|
| et |CCONJ|262|184|.5647|
| ex |ADP|37|35|.4163|
| in |ADP|198|156|.4113|
| per |ADP|17|16|.6109|
| que |CCONJ|111|84|.5111|
| sed |CCONJ|89|85|.5858|
| sine |ADP|12|11|.5134|
| uel |CCONJ|11|6|.4452|

Token-weighted accuracy against the same constant type-class reference is1069/1143=93.53%. This is descriptive and frequency-dominated; **75% type accuracy remains primary**, and neither number is token-POS accuracy against new gold annotations. Several probabilities are close to.5, and these results do not establish high-precision selective classification.

## Author and subset limits

The source-test partition is strongly imbalanced:740 Cicero sentences and30 Palladius sentences. Cicero gives12/16 correct types (12/15 among supported types); Palladius gives7/11 present types, with five types missing and only three supported. These author subsets overlap the full result and are not independent author-transfer confirmations.

For the earlier116 split, the calibration eight types now give5/8 correct and the evaluation eight give7/8. Evaluation-eight AUC is1 on these source-test sentences, but there are still only eight types. No significance or general zero-error claim follows. The experiment establishes no new full grammatical structure, clean PP coverage, exact word identity, or repair robustness; the117 monotone-veto ceiling remains intact.

Next: evaluate this same frozen class predictor and intercept on the already cached Jerome and corrected Caesar public contexts. Keep all present types, report missing/support and original100 versus largest admitted context, and consume no additional grammar annotations. This tests author transfer and evidence volume without tuning the scalar on those authors.

Verification:29 focused tests pass. The audit verifies16 frozen input hashes, reconstructs the word-only test projection and public inputs, independently checks43 type probabilities and80 metric groups, and confirms that poisoning all target identity/class fields leaves inference features unchanged. Artifacts are in `experiments/results/grammar-restoration/iteration118/`.
