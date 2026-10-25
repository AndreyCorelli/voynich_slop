# Iteration 124: better opaque word classes, worse hard-tag PP precision

**Preserve the class result:** class-balanced first-stage training improves opaque ADP/CCONJ type classification from **12/16 (75%) to 14/16 (87.5%)**, with seven of eight types correct in each class. This is a potential grammatical input for another decipherment method, not lexical nucleus recovery. Directly treating these classes as certain in the existing PP model worsens precision, so the class result and integration result must be tracked separately.

## Frozen experiment

Only the first-stage training loss changes: ADP and CCONJ each receive half the total likelihood weight. The thirteen training types (ten ADP, three CCONJ), sampled occurrences, feature vocabulary, regularization, optimizer settings, and three type-held-out folds match iteration 116. All sixteen target types remain excluded from training labels and globally masked in contextual inputs. The balanced scalar offset is refitted exclusively on the thirteen new out-of-fold type profiles, giving 0.4963496828; models are frozen before test predictions.

Evaluation reuses the exact iteration-118 source-test input: 770 sentences, 9,956 tokens, all sixteen target types retained. Target lexical identities and classes are hidden; other surrounding anchor mappings and the candidate function-word catalogue are supplied. Test references are modal type classes, not token-level POS labels. No new annotations, author contexts, reserve features, or sealed lexical tests are consumed. This is adaptively reused development data, not independent confirmation.

## Class information

| Metric | Previous frozen predictor | Balanced first-stage predictor |
|---|---:|---:|
| Correct types | 12/16 | **14/16** |
| Type accuracy | 75% | **87.5%** |
| Type-mean negative log likelihood | 0.61083 | **0.57430** |
| AUC | 0.81250 | **0.921875** |
| Frequency-weighted type-class accuracy | 93.53% | **88.80%** |

The new model correctly changes `c` and `uel` to CCONJ and `sine` to ADP, but incorrectly changes `que` to ADP. Its remaining errors are `per` and `que`. The latter's frequency explains why frequency-weighted accuracy falls despite improved type accuracy. Neither weighted percentage measures general token POS accuracy. The prior gets 8/16 types correct; the uncalibrated balanced-loss model gets 9/16, so scalar calibration still matters.

AUC improvement demonstrates that training changes the ordering, unlike an intercept alone. The thirteen-type pool and sixteen-type evaluation are small, and this result does not establish high-confidence selection or transfer to other texts.

## Downstream structural integration

All target identities remain hidden. New hard classes enter the same frozen original and augmented PP models, with every old threshold and cohort retained. At the primary original-model threshold 0.80:

| Fixed cohort / predictor | Correct PP | Wrong PP | Precision |
|---|---:|---:|---:|
| All, unknown target classes | 23 | 0 | 100% |
| All, previous inferred classes | 235 | 34 | 87.36% |
| All, new inferred classes | 244 | 59 | **80.53%** |
| Originally unmapped, previous | 174 | 33 | 84.06% |
| Originally unmapped, new | 183 | 56 | **76.57%** |

Against the previous inferred classes, the new model adds eleven correct selections, loses two correct selections, adds forty-four false selections, and removes nineteen false selections. Overall F1 changes only slightly, from approximately 0.4493 to 0.4519; the 90% precision requirement still fails. Correct-selection retention exceeds 80%, so precision is the failing requirement. All secondary settings and fixed cohorts are saved without selecting a favorable alternative.

This separates useful grammatical classification from its utility under a particular downstream treatment: type-average improvement does not ensure improved structure when frequent errors are asserted as certain. No model is adopted as a default, and no lexical words or Voynich plaintext are recovered.

## Verification and next step

The independent review verifies 25 frozen hashes, retrains all four class models, checks identical sampled rows to iteration 116, replays thirteen out-of-fold and sixteen test profiles, recomputes both PP score vectors, and checks sixteen confusion/transition groups. Retrained weights agree within 1e-4; frozen-model profile and PP-score replay uses 1e-12 tolerance, allowing optimizer sensitivity to sparse feature summation order without weakening prediction verification. A finite-difference gradient check has error below 6e-9, and all 33 focused tests pass.

Next: freeze this model and test class transfer on the same cached Jerome/Caesar contexts as iteration 119, retaining all present types, missing/support flags, old-model comparisons, and common-type volume comparisons. This checks whether the potential grammatical input transfers before attempting further PP integration. Soft uncertainty propagation is a separate later proposal, not an evaluated improvement.

Artifacts: `experiments/results/grammar-restoration/iteration124/`.
