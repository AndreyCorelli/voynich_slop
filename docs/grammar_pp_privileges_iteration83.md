# PP membership without supplied POS or nominal selection — iteration 83

**The partial grammatical result survives removing both supplied center POS and nominal-cohort selection on the source benchmark.** Across all9,956stored test tokens, the inferred-center-POS model's source-calibrated selective policy finds490correct PP memberships and54wrong: **90.07%precision,63.06%recall**. Its source-F1policy achieves77.20%F1, versus69.36%for nearest-left-preposition proximity. The proximity controls have no qualifying high-precision source policy in the all-token setting.

This is an inferred grammatical result with no reference POS or structural links in inference features. **Readable candidate words remain inputs** to learned POS/finite predictors and marker features. It is not yet an opaque-cipher or Voynich result. Aggregate precision is Cicero-dominated; Palladius does not reproduce90%precision.

## Controlled stages

Use the same declared source49fold0fit/calibration/test sentences and frozen upstream feature models as81–82. No Caesar or reserve scoring occurs. Refit the same3-inner-fold ensemble of8-class PP/head-category probes for each setting; retain mincount3/L2=.001. No downstream Case model is trained here.

**A: matched nominal cohort.** Retain82's atomic-Case NOUN/PROPN/ADJcohort, but remove the supplied center-POS feature. Compare a masked-center model with one receiving only predicted center POS from the frozen71candidate-word POS predictor. Neither receives reference POS as a feature. This stage still has supplied nominal selection for evaluation/training.

**B: all stored token positions.** Train and evaluate with no POS, Case or content-cohort filter. Counts are31,884fit,10,917calibration and9,956test positions. These are all stored source tokens; punctuation removed by the older annotation pipeline is not reintroduced.

The positive label is defined for every token by the same structural rule as81: its node has an ADP dependent linked by reference `case`, or inherits that membership through amod/conj/flat/fixed paths up to8edges. No arbitrary POS restriction applies. The ADPmarker itself and every descendant in a PP subtree are not automatically positive. This is governed-node membership, **not a full PP span or an exact governor attachment**.

Test positives increase561→777when the nominal filter is removed:358NOUN,100PROPN,103ADJ,178PRON,27VERB,10ADVand1DET. Thus the all-token stage both adds genuine memberships and exposes previously excluded negative positions. Gold labels/links are used for source supervision and evaluation only.

## Matched-cohort results

| Center POS input | Source-F1policy F1 | Selective correct / wrong | Precision | Recall |
|---|---:|---:|---:|---:|
| Supplied82reference | 80.73% | 337 / 33 | 91.08% | 60.07% |
| No center POS feature | 80.93% | 337 / 33 | 91.08% | 60.07% |
| Inferred center POS | 80.55% | 342 / 33 | 91.20% | 60.96% |
| Nearest-left proximity | 80.07% | 318 / 27 | 92.17% | 56.68% |

Supplying center POS was not necessary for this conditional nominal-cohort result. The small differences do not establish one learned variant as generally superior.

## All-token results

| Input/model | Source-F1policy F1 | Selective correct / wrong | Precision | Recall |
|---|---:|---:|---:|---:|
| Masked center | 70.75% | 423 / 56 | 88.31% | 54.44% |
| Inferred center POS | **77.20%** | **490 / 54** | **90.07%** | **63.06%** |
| Nearest-left proximity | 69.36% | No supported source policy | — | — |
| Either-side nearest proximity | 51.95% | No supported source policy | — | — |
| Source prior | 14.48% | No supported source policy | — | — |

The masked-center arm is weaker once it must distinguish all token types. Learned center POS helps, but is inferred from readable candidate words rather than supplied from reference annotations.

Every cohort/arm has its own source-only calibration. The high-precision rule remains empirical90%calibration precision with at least20predictions across10types; no held-out threshold selection occurs. For the all-token inferred-POS model, threshold0.65is fixed from calibration:587correct/65wrong (90.03%precision,64.79%recall;362types). Test yields490/54. This is an observed90.07%, not a guaranteed90%transfer precision or fresh confirmatory result.

High-precision false positives are not hidden:23NOUN,9PROPN,8DET,5ADJ,4ADV,2VERB,2PRONand1NUM.

## Author scope

The test is highly imbalanced:

| Author | Test tokens | PP positives | Selective correct / wrong | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| Cicero | 9,573 | 755 | 480 / 51 | 90.40% | 63.58% |
| Palladius | 383 | 22 | 10 / 3 | 76.92% | 45.45% |

Palladius is small and visibly weaker. Do not describe the aggregate result as robust across authors. All material is reused source development data, although fit/calibration/test sentence sets remain disjoint.

## Decision and next step

Preserve this as a candidate **partial grammatical-restoration module** for governed membership on readable Latin. It no longer needs gold center POS or a nominal filter, and improves the strong proximity baseline on the all-token task. It does not recover Case values, full phrase boundaries, exact attachments or whole grammatical structure.

The next practical test is an **anchor-only input setting**: keep explicitly supplied function-word anchors but replace content forms with opaque identities; derive any POS evidence from context/repetition rather than true-form dictionary lookups. Retain the same source-only calibration and proximity controls. This isolates the remaining readable-content-word privilege before claiming cipher-side grammatical restoration. Author transfer also needs further validation; the grammar reserve stays closed during these diagnostics.

## Verification

All models/policies and both cohorts' predictions replay. All12probe fits pass objective/gradient checks. Replacing every reference POS/Case/head/relation with arbitrary annotations leaves all-token inference scores unchanged. Every stored token is evaluated, and the matched cohort exactly reproduces82's positions and labels. Fit/calibration/test provenance remains disjoint; audit verifies1,653prior input hashes.

Four new tests cover all-token eligibility, gold-annotation feature invariance, absence of supplied-POS features and use of inferred rather than reference center POS; all65focused tests pass. No new target grammar queries, reserve, sealed lexical final test or dictionary search.

Artifacts: `experiments/results/grammar-restoration/iteration83/`; runner/audit: `benchmarks/grammar_pp_privileges_iteration83*.py`.
