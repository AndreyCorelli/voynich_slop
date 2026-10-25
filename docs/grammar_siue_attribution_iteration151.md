# Iteration 151: the failure is entirely in siue's own training vector

The middle-occurrence substitution changes only siue's training vector. The other12 training vectors are exactly unchanged, including their occurrence counts. Two predeclared hybrid interventions therefore give exact attribution: changing only siue reproduces the entire perturbed model, while restoring siue reproduces the original full model. This is equality of fitted parameters and all target probabilities, not just similar accuracy.

The frozen interventions combine iteration150 full and middle-only perturbed feature caches. The focal-only hybrid uses the changed siue vector and every other original vector; the others-only hybrid uses the original siue vector and every other perturbed vector. Both retain the original13 labels, two scalar features, class-balanced regularized fitting, recomputed training standardization and raw0.5 cutoff. Hybrids were frozen before fitting, models before predictions, and predictions before evaluation. These are diagnostic feature interventions rather than realizable source streams or deployable restoration fixes.

| Text | Full = others-only | Middle perturbation = focal-only |
|---|---|---|
| Caesar | 12/15 | 10/15 |
| Jerome | 12/16 | 8/16 |
| Gellius | 12/15 | 4/15 |
| Livy | 10/14 | 5/14 |
| Apuleius | 6/13 | 6/13 |
| Curtius | 12/15 | 5/15 |
| Suetonius | 12/16 | 6/16 |

The changed siue vector has count6→5, corrected overlap.151515→0, and role similarity.706479→.004914. Count is metadata, not a model input. Both model inputs change, so this experiment does not assign the resulting coefficient reversal to one scalar independently. Recomputed standardization and the fitted boundary propagate that one vector's change to all predictions.

The diagnostic closes the collateral-graph explanation for the original13 training types: none of their other vectors changes under this particular perturbation. It does not say the complete opaque graph is unchanged, nor establish that the original grammatical exemplar is invalid. The current estimator and small supervised sample permit a genuine repeated coordination pattern to dominate the learned boundary.

The positive full-text milestone remains measured conditional development evidence, with a clear robustness limitation. Neither hybrid is adopted as a production model, and this is no new POS recovery or lexical nucleus discovery. No additional annotations, reserved material, sealed works or target-label-driven selection were used.

Next proposed algorithm test: constrain both standardized feature slopes to be nonnegative, reflecting the explicit hypothesis that greater corrected context overlap and greater role similarity should support CCONJ rather than ADP. Keep the same loss, regularization, source data and raw cutoff, then compare against the unconstrained model on source held-out types, all13 training-type omissions and the already frozen focal substitutions. This is a hypothesis to test, not an established linguistic law. Freeze the constrained implementation and comparisons before running, report every perturbation/text, and retain accuracy plus NLL so preventing a sign reversal is not mistaken for improved recovery. No author-specific choice or strength tuning on target labels.

Verification checked all13 vector identities, retrained both hybrids, verified exact parameter identities against the full/perturbed references, independently replayed416 probabilities and28 metric groups, and replayed all paired changes. The prior iteration150 manifest was verified. The focused suite passed18 tests. Frozen artifacts and verification manifest: `experiments/results/grammar-restoration/iteration151/`.
