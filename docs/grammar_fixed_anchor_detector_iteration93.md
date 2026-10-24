# Fixed contextual anchor-class detector — iteration 93

The single classifier removes hidden-identity-dependent fold routing, but the inherited coarse calibration grid selects OFF for every arm. No PP integration or mapping correction is made.

Training uses all 29 source-fit ADP/CCONJ anchor types. Each type is hidden throughout its own view; up to 20 deterministic occurrences train a binary classifier. Other anchors stay visible. One context model, a sampled-label prior and three type-label permutation controls are frozen before calibration. Opaque IDs only group/mask occurrences; they never select a model or enter classifier features. This includes the candidate types in training and is sentence-disjoint validation, unlike iteration92's separate type-held-out diagnostic.

Calibration uses the 16 common-budget candidates on clean and known in/et-swapped source inputs. Support requires five occurrences and three sentences. All 16 now have support; the binary model no longer suffers iteration91's function-class mass collapse. Error labels are original source-modal classes under simulated swaps, attached after public predictions; no target reference POS/dependencies enter inference.

The inherited threshold grid is 0, 0.5, 1, 2, 3, 4, 8, OFF. Keep at most one clean false-flagged type and at most 5% of clean candidate occurrences flagged; maximize known-error detections, then minimize corrupted false flags and clean flagged occurrences, tie higher threshold. Freeze all five policies before evaluating the same eight scenarios on source test and cached Jerome/Caesar.

At zero, context detects both known errors but falsely flags four clean types (247 occurrences), violating the guard. At 0.5 or higher it detects neither error. OFF therefore wins. All five arms and the old frozen-POS control flag zero mappings in all 24 evaluation scenarios. Complete abstention is not successful detection.

There is a specific grid limitation: the strongest clean disagreement is 0.273, while the mistaken CCONJ assignment to in scores 0.469. A finer cutoff could separate them on calibration. The mistaken ADP assignment to et scores only 0.021 and is not clearly distinguishable. Do not describe the OFF result as proof that no admissible calibration operating point exists.

Next run a separately frozen refinement over all attainable nonnegative source-calibration scores, keeping the model, support requirements, false-alarm limits and tie rules unchanged. Choose each arm's cutoff before applying it to cached evaluation scores. Preserve this coarse-grid experiment unchanged; the refinement is development on previously scored material, not independent confirmation. Do not pick cutoffs from author or source-test performance.

Validation: four fit objectives reconstructed; all 26 scenarios and five arms replayed; policies replayed; reference-annotation removal and rekeying leave evidence unchanged; 2,439 prior frozen-input hashes verified; 93 focused tests passed. No new annotation queries, reserve/sealed-test evaluation, lexical recovery or PP integration. Artifacts: experiments/results/grammar-restoration/iteration93/.
