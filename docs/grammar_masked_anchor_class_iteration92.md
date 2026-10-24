# Contextual anchor classes with whole-type masking — iteration 92

**Positive source-only diagnostic: masking function-word types during training recovers class discrimination on excluded types.** Primary source-calibration type accuracy is23/29 (79.31%), versus18/29 (62.07%) for the prior and55.17% averaged over three context/class-association permutation controls. Probability loss also improves. The predeclared discrimination gate passes. This is neither an operational error detector nor a new lexical nucleus recovery.

## Frozen experiment

Use all29 source-fit-selected anchors with source-modal ADP or CCONJ class (18ADP,11CCONJ). Assign types to three deterministic SHA folds. Each fold model excludes every held type from its training labels and hides all those types throughout every input. For each remaining training type, also hide that entire type, then collect only its own occurrences. This removes both its own identity/tag shortcut and any held-type class disclosure through visible context anchors. Other supplied function anchors remain visible; content stays opaque.

Cap each training type at20 deterministically selected fit occurrences. Rare types are not oversampled, so contribution per type is capped rather than exactly equal. Fit the existing binary softmax with unchanged regularization/optimizer. Controls use the same features with three fixed permutations of class labels across whole training types, breaking the context/class association, plus a smoothed class prior from the same sampled rows. These are type-label permutation controls, not sentence-wise token shuffles. All12 models are frozen before calibration predictions.

Primary validation uses source-calibration sentences and each type's fold model, which has never received that type's labels. Pool probabilities across its occurrences and score each present type once. Secondary support requires at least5 occurrences across3 sentences. Fit-sentence held-type predictions are retained as a diagnostic, but can share sentences with other training types; the calibration result is the primary sentence-disjoint result. Source-modal class labels are evaluation/supervision targets, not per-token grammatical truth.

Gate: calibration type accuracy must exceed both prior and mean shuffled-control accuracy by at least10percentage points, and its NLL must be lower than both. There is no hyperparameter selection on calibration. This stage deliberately performs no error-detector calibration, swap evaluation, author transfer, source-test scoring, PP integration or reserve/sealed-test scoring. The source-calibration material was explored in earlier experiments, so this is not fresh independent confirmation.

## Results

| Model | Calibration types correct | Type accuracy | Type NLL | Supported-type accuracy (24types) |
|---|---:|---:|---:|---:|
| context | 23/29 | 79.31% | 0.5492 | 79.17% |
| prior | 18/29 | 62.07% | 0.6944 | 62.50% |
| shuffle0 | 16/29 | 55.17% | 0.7649 | 62.50% |
| shuffle1 | 18/29 | 62.07% | 0.6420 | 58.33% |
| shuffle2 | 14/29 | 48.28% | 0.8760 | 50.00% |

Mean permutation-control calibration accuracy55.17%, NLL0.7610; context NLL0.5492 versus prior0.6944. Context gains17.24percentage points over prior and24.14over mean permutation control. Supported-type accuracy19/24 (79.17%) versus15/24 (62.50%) prior. Fit held-type diagnostic accuracy22/29 (75.86%) versus18/29 prior. This is a small type sample; the three permutations are descriptive controls rather than a formal significance test.

The failure pattern matters: all18 ADP types are classified correctly, but only5of11 CCONJ types are. Balanced class accuracy is72.73%. The six mistakes are ac, atque, aut, et, ue, uel, all predicted ADP. A detector that flags every predicted/proposed disagreement would therefore wrongly challenge several correct conjunction mappings, including frequent et. Passing the discrimination gate does not establish safe false-alarm control.

| Type | Fold | Source-modal class | Calibration occurrences | P(CCONJ) | Predicted class |
|---|---:|---|---:|---:|---|
| a | 0 | ADP | 61 | 0.210 | ADP |
| ab | 2 | ADP | 29 | 0.377 | ADP |
| abs | 2 | ADP | 9 | 0.037 | ADP |
| ac | 1 | CCONJ | 23 | 0.432 | ADP |
| ad | 1 | ADP | 136 | 0.255 | ADP |
| an | 0 | CCONJ | 5 | 0.539 | CCONJ |
| apud | 1 | ADP | 14 | 0.341 | ADP |
| atque | 0 | CCONJ | 25 | 0.357 | ADP |
| aut | 2 | CCONJ | 74 | 0.441 | ADP |
| c | 1 | CCONJ | 29 | 0.510 | CCONJ |
| de | 1 | ADP | 88 | 0.396 | ADP |
| e | 1 | ADP | 2 | 0.408 | ADP |
| erga | 2 | ADP | 1 | 0.000 | ADP |
| et | 0 | CCONJ | 260 | 0.426 | ADP |
| ex | 1 | ADP | 65 | 0.456 | ADP |
| in | 2 | ADP | 227 | 0.324 | ADP |
| inter | 0 | ADP | 5 | 0.135 | ADP |
| ob | 0 | ADP | 2 | 0.010 | ADP |
| per | 1 | ADP | 19 | 0.340 | ADP |
| post | 2 | ADP | 8 | 0.423 | ADP |
| praeter | 0 | ADP | 7 | 0.399 | ADP |
| pro | 1 | ADP | 12 | 0.410 | ADP |
| propter | 0 | ADP | 12 | 0.301 | ADP |
| que | 2 | CCONJ | 121 | 0.517 | CCONJ |
| sed | 2 | CCONJ | 101 | 0.649 | CCONJ |
| sine | 2 | ADP | 18 | 0.256 | ADP |
| siue | 0 | CCONJ | 2 | 0.672 | CCONJ |
| ue | 2 | CCONJ | 3 | 0.089 | ADP |
| uel | 0 | CCONJ | 12 | 0.414 | ADP |

## Interpretation and next step

Iteration91 failed when a POS model trained almost entirely on visible function-word anchors was asked to identify those classes after masking. The new masked-training result supports that distribution-mismatch explanation: contextual evidence does distinguish classes once the training task matches inference. It does not isolate masking as the sole cause, because this experiment also uses a binary task, type-capped sampling and type-blocked fits rather than the old13-class token model.

Preserve this as a promising conditional grammatical-class result, alongside its conjunction weakness. Cross-validation routing uses known source validation-type metadata to choose the model that excluded that type; it is an offline measurement, not a deployable opaque-ID routing rule. A practical detector must not choose a model using a hidden true-word identity.

Next build one source-trained contextual classifier with a fixed masking policy and no type-dependent model selection, then calibrate disagreement/abstention on sentence-disjoint source data. Measure false flags on correct mappings before testing the unchanged unseen-swap challenges. Keep the prior/permutation and old frozen-POS controls. Do not couple to PP inference until this step supports useful detection without damaging correct anchors. This next detector is proposed, not yet tested.

Validation: all12 training objectives reconstructed; sampled rows, type splits and shuffled labels verified; all pooled fit/calibration predictions and metrics replayed; 2,422 prior frozen input hashes verified;92 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration92/.
