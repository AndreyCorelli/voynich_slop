# Actual government/phrase membership and Case — iteration 81

**Positive conditional grammatical result:** supplied structural membership improves nominative-versus-other Case classification beyond supplied POS and nearest-cue features. On the held-out source split, F1 rises53.51%→56.56%; the corresponding sham structural bundles give49.40%. A source-calibrated selective policy returns79correct nominatives and8wrong (90.80%precision,10.76%recall), across81word types.

The structural inputs and center POS are **supplied**, not recovered. This is useful evidence about what structural restoration could contribute, not an inferred parser result or a claim of fine-grained Case recovery.

## Source-only controlled experiment

Use only the previously declared source49fold0splits:2,471fit sentences,829calibration and770held-out source sentences, from Cicero/Palladius. **No Caesar target scoring** occurs. Evaluate NOUN/PROPN/ADJwith a known atomic Case in Nom/Acc/Gen/Dat/Abl/Voc/Loc;10unknown/non-atomic nominal Case labels are excluded from fit, zero from calibration/test. Resulting counts:8,840fit,2,880calibration and2,783test positions, including734test nominatives.

Every arm receives the same supplied center coarse POS and nominal evaluation membership. The baseline is refit with80's readable government/proximity features under this controlled POS setting. Its53.51%F1 is not directly comparable with80's25.50%on a different all-content Caesar cohort without supplied center POS.

## Structural oracles

**PP membership:** identify actual ADP dependents linked by the reference `case` relation to the nominal. Permit inheritance only through declared amod/conj/flat/fixed phrase links, at most8edges. Encode membership, ADP identity/distance and whether inherited.

**Structure:** add the actual unlabeled head's candidate-derived POS and distance, or root status. No head word identity, reference head Case/Number, reference center Case/Number or subject/object role is provided. The `case` and permitted phrase-membership relation labels are explicit oracle privileges; reference nsubj/obj/nmodlabels are not score features.

The baseline already has readable words, predicted surrounding POS/finite-carrier proxies and sentence boundaries. These inputs, supplied center POS and source structural oracles must all be stated when interpreting the result.

Train the three logistic models on fit only, retaining minimum feature count3andL2=.001. Source calibration selects F1 thresholds and independent precision90policies using the unchanged grid/support rule. Models and policies are frozen before held-out predictions. The sham arms apply the trained oracle models after permuting oracle bundles among eligible nominals within each sentence; baseline features stay fixed. They have their own source-calibrated policies. Such permutations preserve bundles but cannot change single-nominal sentences; they are descriptive controls, not exhaustive significance tests.

## Results

| Evidence | F1 | Brier | Binary NLL | Selective correct / wrong | Selective precision / recall |
|---|---:|---:|---:|---:|---:|
| Supplied POS + nearest-cue baseline | 53.51% | .15740 | .47348 | 61 / 13 | 82.43% / 8.31% |
| Actual PP membership | 55.18% | .15384 | .45839 | 60 / 9 | 86.96% / 8.17% |
| PP + actual head category/distance | **56.56%** | **.14521** | **.43646** | **79 / 8** | **90.80% / 10.76%** |
| Sham PP bundles | 51.62% | .16756 | .53111 | 53 / 8 | 86.89% / 7.22% |
| Sham structure bundles | 49.40% | .17524 | .55110 | No supported source policy | — |
| Source prior | 41.74% | .19418 | .57694 | No supported source policy | — |

At F1 policies, structure raises true positives499→565but also false positives632→699. Precision is44.70%versus44.12%; recall76.98%versus67.98%. Thus the overall F1 gain is primarily recall, while the separate selective policy is the high-precision result.

The structure selective threshold0.79was fixed from calibration:67correct/7wrong (90.54%precision;67types). The held-out79/8result is small and conditioned on supplied inputs; it does not guarantee90%transfer precision.

Cicero dominates the test cohort (2,632positions): F153.00%→56.22%, selective73correct/7wrong. Palladius has151positions: F160.15%→60.99%, selective6correct/1wrong (85.71%). The latter sample does not establish a high-precision result for both authors. This is reused source development material, not fresh independent confirmation.

## Decision and next work

Preserve the structural-information finding alongside74/76and78. Actual membership has value beyond mere proximity; PP membership alone supplies a smaller gain than the fuller unlabeled-head information. Do not adopt the oracle inputs as an inferred grammar algorithm.

The next concrete step is to learn **coarse structural membership**—PP membership and head category—on source annotations, initially under this same supplied-POS setting. Use out-of-fold structural predictions for any downstream Case-model training so that perfect or in-sample structure cannot masquerade as attainable input. Compare predicted structure, oracle structure, nearest-cue baseline and sham controls, with source-only confidence/coverage calibration. Only afterwards remove supplied POS or test transfer to the previously explored target. Full parsing is not yet justified by this modest oracle gain.

## Verification

All calibration/test predictions and policies replay. Fit objectives/gradients pass; split disjointness and source-only author scope are checked. Changing Case values and non-membership subject/object relation labels leaves predictions unchanged, while oracle-bundle shams preserve each sentence's bundle multiset. Audit verifies1,610prior input hashes.

Four new tests cover actual versus nearby membership, Case/subject-role nonleakage, restricted inheritance and cycles; all56focused tests pass. Grammar reserve and sealed lexical final test remain unscored. No new target annotations or dictionary search.

Artifacts: `experiments/results/grammar-restoration/iteration81/`; implementation: `src/voynich_smt/government_oracle.py`; runner/audit: `benchmarks/grammar_government_oracle_iteration81*.py`.
