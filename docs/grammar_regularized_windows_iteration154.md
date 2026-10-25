# Iteration 154: stronger regularization does not solve short-context transfer

The frozen source-selected regularization model gives modest mixed changes on matched-length windows:16 improve in correct-count accuracy,38 tie and9 worsen against the fixed weak-penalty monotonic model. NLL improves in27 of63 windows. This does not establish reliable short-context grammatical restoration or justify further target-driven penalty tuning.

No fitting was performed. The iteration153 source-selected model, iteration152 fixed-penalty monotonic model and original iteration144 joint baseline were applied to exactly the existing63 nested windows and seven full references using cached features. Window positions, candidate presence, thresholds and models were frozen. Predictions were frozen before evaluation. No new annotations, reserved material or sealed works were used.

Each entry below gives previous correct count→selected correct count/present types for all three predeclared positions.

| Text | 1,000 tokens | 3,000 tokens | 4,000 tokens |
|---|---|---|---|
| Caesar | 10→10/12; 9→9/11; 5→4/12 | 11→11/13; 11→11/13; 7→6/13 | 12→12/13; 11→11/13; 9→8/13 |
| Jerome | 5→5/11; 8→8/13; 7→7/12 | 12→12/15; 10→10/15; 10→10/15 | 10→10/15; 10→10/15; 7→9/15 |
| Gellius | 6→5/14; 8→9/14; 4→3/12 | 8→9/15; 9→10/15; 9→9/15 | 11→10/15; 9→10/15; 9→10/15 |
| Livy | 4→4/11; 8→8/14; 4→4/10 | 7→8/13; 9→10/14; 5→6/14 | 9→9/14; 11→11/14; 6→7/14 |
| Apuleius | 7→7/10; 7→7/11; 7→7/11 | 7→6/13; 7→6/13; 7→6/13 | 7→7/13; 6→7/13; 7→7/13 |
| Curtius | 4→4/9; 6→6/9; 6→6/13 | 7→8/13; 8→8/14; 8→8/14 | 9→9/15; 9→10/15; 8→9/14 |
| Suetonius | 9→9/14; 7→7/12; 7→7/14 | 10→10/16; 7→9/15; 8→8/15 | 11→11/16; 8→9/15; 9→9/15 |

At1,000 tokens, improvements/ties/losses are1/17/3; at3,000,7/10/4; at4,000,8/11/2. NLL improves in9 of21 views at each length. These overlapping windows and repeated types are correlated diagnostics, not63 independent replications. The fixed-penalty monotonic model and original joint model have identical hard decisions here; their tiny numerical probability differences are retained as separate arms.

Full references reproduce the preceding experiments exactly: selected-model correct counts are12/15 Caesar,12/16 Jerome,13/15 Gellius,10/14 Livy,7/13 Apuleius,11/15 Curtius and12/16 Suetonius. The six-author full-text signal remains useful conditional evidence. The window failures show that source calibration progress does not guarantee reliable passage-level transfer.

Primary metrics use all present supplied candidate types. Artifacts also retain occurrence-supported and previously fixed common14 subsets, missing members of the full16 catalogue, and full-text comparators restricted to exactly the same present types. No favorable author, window or candidate subset was selected. This remains ADP-versus-CCONJ classification with class-set membership supplied, not general token POS tagging or recovered word identities.

Next proposed direction: challenge that supplied-membership privilege directly. Using only existing source-fit modal POS annotations, test whether the same two anonymous structural features can distinguish ADP/CCONJ types from ordinary vocabulary under held-out-word-type evaluation, excluding all16 target types from fitting. Predeclare occurrence/purity eligibility, deterministic folds, the source-only model-selection rule and precision/recall metrics before running. Any performance should be compared with frequency alone, since frequent-word selection could masquerade as structural detection. This is a separate candidate-detection diagnostic, not a claim that arbitrary POS are already recoverable; it is more directly relevant to finding useful words in Voynich than further tuning the present binary cutoff.

Independent verification replayed both frozen model probabilities for every view, all subgroup accuracy/NLL/AUC calculations, missing-candidate accounting and same-present full comparators. Both full reference arms match their historical predictions exactly. No production feature/model code changed; model tests were not rerun after the preceding18-test pass, and this cached-inference change is verified by the dedicated audit. Artifacts and verification manifest: `experiments/results/grammar-restoration/iteration154/`.
