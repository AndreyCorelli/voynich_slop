# Case/Number attribution and direct nominative prediction — iteration 79

**Case is the dominant supplied feature for subject roles; the tested direct predictor does not restore it reliably.** Both planned phases ran with fixed source splits and target material. The grammatical objective remains independent of word identity.

## Matched oracle attribution

Condition the frozen iteration70role/profile posterior on correct POS alone, POS+Case, or POS+Number. Missing fields are exact categories. Compare context, the saved shuffled context and the source prior, with each policy calibrated on source data only. No reference role enters the score.

| Supplied information | Context subject F1 | Shuffled F1 | Prior F1 |
|---|---:|---:|---:|
| POS | 35.14% | 29.44% | 28.65% |
| POS + Case | **67.31%** | 62.24% | 68.66% |
| POS + Number | 37.54% | 29.06% | 28.65% |
| POS + Case + Number, frozen78reference | 68.25% | 62.69% | 68.66% |

Case accounts for most of the overall oracle improvement. Number adds little F1 once Case is supplied, although it can still affect selective precision: the source-calibrated POS+Case high-precision policy yields34correct/5wrong target predictions (87.18%precision), versus78's full-profile31correct/3wrong (91.18%). These are different source-selected policies; neither supplies an inferred-morphology restoration result. A nominal90%source policy does not guarantee90%precision after transfer.

The Case-conditioned prior again slightly beats contextual F1. Context's extra information should therefore be assessed separately from the large benefit of supplied Case.

## Direct contextual nominative model

Train a binary logistic model for the explicitly annotated nominal-nominative event: NOUN/PROPN/ADJ with Case=Nom, over the same source-fit content positions. This predicts morphological eligibility, not actual subjecthood. The source data's absent Case fields do not count as explicitly nominative.

Use only candidate-derived neighboring POS at offsets−2,−1,+1,+2and a flanking POS pair. Center word, center POS, word suffixes and reference morphology are excluded. Feature count minimum3andL2regularization0.001are fixed in advance; no tuning or pretrained lexical model. This is a direct predictor, contrasted with the earlier many-class joint role/profile estimator, although the flanking interaction also changes the representation slightly; the comparison is not a pure loss-function ablation.

Softly replace the frozen role model's probability of nominal-nominative versus other profiles with the direct predictor's probability. Preserve role conditionals within each group rather than forcing a subject label. Evaluate the morphological prediction and the downstream subject score separately.

| Task | Local F1 | Direct F1 | Direct shuffled F1 |
|---|---:|---:|---:|
| Nominal-nominative eligibility | 24.79% | **24.45%** | 18.91% |
| Subject role after soft transfer | 23.66% | **20.63%** | 17.62% |

The nominative probability losses improve only slightly: Brier0.08498→0.08419andbinary NLL0.30348→0.30123. Subject Brier0.07521→0.07522is effectively unchanged. At source-selected F1 thresholds, direct subject precision rises16.60%→19.83%but recall falls41.12%→21.50%; true positives44→23andfalse positives221→93. None of the non-oracle direct/local/shuffle/prior arms obtains a qualifying precision90calibration policy with20predictions across10types. Do not adopt this predictor/transfer as solid grammatical restoration.

## Calibration, scope and next work

All learned parameters use source49fold0fit only. Policies use the disjoint829source-calibration sentences/7,034content positions, with the unchanged0.01threshold grid, source-F1 selection and precision90support rule. Model parameters are frozen before calibration, and policies before target predictions. Both phases use the same1,273content positions in100previously declared Caesar sentences. Correct surrounding plaintext and sentence boundaries remain supplied; pronoun subjects and full attachments remain outside this task.

Preserve78's conditional morphology result: useful role inference becomes possible when morphology is supplied. This experiment narrows the missing inferred information primarily to **Case**, while rejecting the simple direct context-only nominative replacement. It does not establish that Case alone is sufficient or that more context-only parameter tuning will solve it.

The next useful change is contextual **government and clause evidence**, rather than another scorer for the same four POS neighbors: preposition identity and distance, intervening markers and predicted finite-carrier boundaries. Any such features must be source-trained and use inferred or explicitly supplied anchor inputs, never reference target links/features. Keep the current direct model as a matched baseline, calibrate confidence on source only and require grammatical precision/coverage gains under appropriate shuffle controls. This richer representation is proposed, not tested.

## Verification

Source-calibration and target predictions replay with numerical tolerances for sparse floating-point summation; oracle conditional masses are independently reconstructed. Fit/calibration disjointness, fit objective/gradient and target-annotation invariance of non-oracle scores are checked. All prior input hashes are verified by the audit.

Four new tests cover masked-center invariance, analytic-gradient finite differences, conditional-preserving nominal reweighting and preservation of role uncertainty; all47focused tests pass. The grammar reserve and sealed lexical final test remain unscored; no new target annotations, model-weight tuning or dictionary search occurs.

Artifacts: `experiments/results/grammar-restoration/iteration79/`; implementation: `src/voynich_smt/contextual_nominative.py`; runner/audit: `benchmarks/grammar_direct_nominative_iteration79*.py`.
