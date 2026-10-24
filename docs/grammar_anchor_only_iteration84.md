# PP membership with opaque content and supplied function anchors — iteration 84

**The grammatical signal survives hiding content forms, but the90%precision result does not.** With strict fold-local pooling, PP-governed membership reaches **73.68%F1**, versus69.03%for nearest-left proximity. Its source-calibrated selective policy returns464correct memberships and70wrong: **86.89%precision,59.72%recall**. On hidden forms alone it returns333correct/56wrong (85.60%precision,55.41%recall).

This is a conditional partial-grammar result with **195supplied function-word anchors**, not discovered anchors or blind Voynich restoration. Preserve the signal and its failed precision transfer together.

## Public input and frozen anchors

Build the anchor list using source fit only: frequency at least5andmodal source UPOS in ADP/CCONJ/SCONJ/PRON/DET/PART. Reveal these forms' identities and source-modal POS. These are supplied mappings/tags; their identification is not inferred in this experiment. Ambiguous words retain one source-modal tag, not reference token POS.

Every other form—including unrecognized function words—is replaced by an opaque equality ID. IDs have fixed length and split-specific rekeying; no ID value is a classifier feature. Models see only anchor identity/tag, opaque equality, positions and supplied sentence boundaries. There are3,327visible anchor positions and6,629hidden positions among9,956test tokens (33.42%visible). This is a substantial anchor budget, not a minimal-known-word setting.

No hidden-form dictionary, source-word POS, suffix, length or finite-verb lookup occurs. The49morphology model and71word/POS lookup model are not loaded for inference. Finite probabilities are zero throughout. Feature code consumes a public interface with only token ID/anchor/tag, separate from private training/evaluation annotations.

## Models and supervision

Use the same source49fit/calibration/test sentences and all stored token positions as83 (31,884/10,917/9,956). Source annotations supervise a context-only POS classifier and joint PP/head-category probes; no reference POS or structure enters inference features. Head-category training labels use the source gold head POS, rather than83's candidate-POS category, and the context representation also changes, so83vs84is not a perfectly isolated single-feature ablation.

Base features are government/marker context computed from anchor tags with hidden X, center known-anchor tag/identity and visible anchor identities at±4. Hidden IDs never become lexical features. Context POS probabilities come from3sentence-blocked source inner folds; known anchors use their frozen source-modal tags. An additional arm pools probabilities over opaque equality within the split. Three PP ensembles compare anchor features alone, plus local context POS probabilities, and plus pooled POS probabilities, with continuous probability inputs and fixed mincount3/L2=.001.

PP labels retain83's all-token governed-node definition: own case-linked ADP, or inherited membership via amod/conj/flat/fixed up to8edges. ADPmarkers and arbitrary PP subtree descendants are not automatically positive. This is not exact attachment, full span recovery or Case-value prediction.

Source-only F1/precision90policies retain the fixed grid and20prediction/10type support rule. Models and policies are frozen before held-out policy outcomes. No Caesar target, reserve or sealed lexical final-test scoring occurs.

## Cross-fitting correction

The initial run correctly excluded each position's sentence fold when producing its POS probabilities, but then pooled across all fit folds. Another occurrence's prediction could come from a POS model trained on the current fold, indirectly reintroducing POS-label exposure into pooled fit features. The held-out source test was never used in fitting, but this weakened the intended training cross-fitting.

Preserve the initial run frozen. A separately designed `fold-local-pool` control refits only the pooled PP models, pooling training probabilities **within each held-out POS fold**. Every resulting training pool then uses a POS model that excluded that entire fold. Cal/test pooling still uses its own entire split; training pools contain fewer contexts, a remaining distribution difference. No model hyperparameters or target thresholds are tuned in this correction.

Use the corrected result as the pooling reference. Initial pooled F1was74.51%; strict corrected F1is73.68%. Neither version reaches90%selective target precision.

## Results

| Input/model | Source-F1policy F1 | Selective correct / wrong | Precision | Recall |
|---|---:|---:|---:|---:|
| Anchor features only | 72.91% | 473 / 76 | 86.16% | 60.88% |
| Anchor features + contextual POS | 73.45% | 472 / 72 | 86.76% | 60.75% |
| Pooled POS, strict fold-local training | **73.68%** | **464 / 70** | **86.89%** | **59.72%** |
| Initial pooled fit, indirect cross-fold exposure | 74.51% | 470 / 74 | 86.40% | 60.49% |
| Nearest-left anchor ADP | 69.03% | No supported source policy | — | — |
| Either-side nearest anchor ADP | 51.78% | No supported source policy | — | — |
| Source prior | 14.48% | No supported source policy | — | — |

At the corrected F1policy, counts are508true positives,94false positives and269false negatives (84.39%precision,65.38%recall). The high-precision threshold0.70is fixed from source calibration569correct/62wrong (90.17%precision;361types), then transfers to86.89%test precision. This is an observed calibration shortfall, not a90%restoration achievement.

The gain from pooled POS beyond local contextual POS is small after correction (0.23F1points). Most of the anchor-only signal is already present in the anchor features. Hidden-form POS accuracy improves40.34%local→44.12%pooled, but is not itself a reliable POS restorer. Known-anchor tags and all-token accuracy must not conceal that limitation.

## Where the corrected selective result holds

| Cohort | Correct / wrong | Precision | Recall |
|---|---:|---:|---:|
| Hidden forms | 333 / 56 | 85.60% | 55.41% |
| Visible anchors | 131 / 14 | 90.34% | 74.43% |
| Cicero | 453 / 66 | 87.28% | 60.00% |
| Palladius | 11 / 4 | 73.33% | 50.00% |

Cicero dominates the material, and Palladius is small/weaker. These are reused source-development results, not independent confirmation or a calibrated guarantee across authors.

## Decision and next work

Preserve the anchor-conditional grammatical signal, but do not promote it as solid90%precision restoration. No lexical nuclei, exact attachments or full grammatical structures are established. The privacy/input control removes a real limitation of83, while exposing a weaker precision-transfer result.

The next realistic check is a **source-frozen anchor-budget curve**: a few frequent prepositions/conjunctions versus the195-anchor upper setting, with opaque equality maintained, strict pooling and all budgets declared before evaluation. Report every budget, not just the best target outcome. Precision/coverage calibration should also be assessed conservatively rather than assuming empirical90%source precision transfers. Neither improvement is implemented here; reserve data remains closed.

## Verification

All original and corrected model objectives/gradients, OOF provenance, policies and predictions replay. Re-keying opaque IDs and changing private evaluation labels leave inference scores unchanged. Tests additionally show hidden spelling/length/reference POS do not affect features, unknown function words remain hidden, and finite lookups are absent. Corrected pooling is checked to remain within each held-out POS fold. Audit verifies1,671prior input hashes.

Eight new tests pass; all73focused tests pass. The corrected control is preserved separately with its design/models/policies/predictions. No new target annotation queries or dictionary search.

Artifacts: `experiments/results/grammar-restoration/iteration84/` and `fold-local-pool/`; implementation: `src/voynich_smt/anchor_grammar.py`; runner/control/audit: `benchmarks/grammar_anchor_only_iteration84*.py`.
