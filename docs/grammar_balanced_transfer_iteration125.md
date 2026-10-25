# Iteration 125: improved class ranking transfers, fixed-cutoff accuracy is mixed

**Preserve the transferable ranking signal:** the frozen balanced-training model improves expanded-context ADP/CCONJ AUC on both cached authors: Jerome **0.7344→0.8906**, Caesar **0.8393→0.9821**. Hard class accuracy improves for Jerome but regresses for Caesar. This is useful conditional grammatical evidence, not a generally improved POS tagger or a recovered lexical nucleus.

## Fixed design and inputs

The model and thirteen-type out-of-fold scalar calibration are exactly iteration 124's, with no refitting or cutoff selection. Inputs are exactly iteration 119's four cached contexts: Jerome 100/829 sentences and corrected Caesar 100/2,494 sentences. Original samples remain identical prefixes of their expansions. All present target types are retained; support of at least five occurrences in three sentences is a secondary reporting stratum only.

All sixteen catalogue types remain excluded from training labels and globally hidden as identities/classes during inference. Their candidate membership, opaque occurrence grouping, surrounding anchor mappings, and existing segmentation are supplied. References are supplied modal type classes, not new token POS labels. These author texts have already been used in development; no new annotations, reserve features, sealed lexical evaluation, PP inference, or synthetic repair tests are added. Predictions are frozen before attaching reference classes.

## Results

| Context | Previous correct | New correct | Previous NLL | New NLL | Previous AUC | New AUC |
|---|---:|---:|---:|---:|---:|---:|
| Jerome 100 | 7/13 | 7/13 | 0.8656 | 0.8140 | 0.3750 | 0.4500 |
| **Jerome 829** | 11/16 | **13/16 (81.25%)** | 0.6292 | **0.5969** | 0.7344 | **0.8906** |
| Caesar 100 | 12/13 | 11/13 | 0.5307 | 0.5473 | 0.9524 | 0.9524 |
| **Caesar 2,494** | 13/15 | **11/15 (73.33%)** | 0.6420 | **0.6329** | 0.8393 | **0.9821** |

Expanded-context prior baselines get eight types correct for each author. NLL is better than the balanced-prior 0.6931 in both expanded contexts. Jerome's short input still fails to beat its eight-correct prior, and its AUC remains below 0.5. There is no uniform small-context success.

Expanded Jerome gets six of eight ADPs and seven of eight CCONJs correct; errors are `atque`, `ex`, and `per`. The sole `atque` occurrence lacks support, but is retained. Supported-type accuracy improves from 10/13 to 11/13.

Expanded Caesar gets four of eight ADPs and all seven CCONJs correct; errors are `a`, `ad`, `in`, and `sine`. Their occurrence counts are 253, 858, 1,122, and 56, respectively, so insufficient count support is not the explanation. Frequency-weighted type-class accuracy drops from **98.87% to 60.64%**, while Jerome improves from **93.05% to 95.31%**. These remain weighted comparisons against constant type classes, not general token-POS accuracy.

## Context volume and the calibration boundary

Over the thirteen types common to each author's original and expanded inputs, the new model improves Jerome **7/13→11/13**, gaining `ac`, `ad`, `aut`, and `sine` without losses. The three newly present types contribute two correct and one wrong prediction.

For Caesar's thirteen common types, accuracy falls **11/13→10/13**: `de` becomes correct, while `a` and `ad` become wrong. Of the two newly present types, `uel` is correct and `sine` wrong. More context is therefore not monotonically beneficial at the fixed class cutoff.

Caesar's expanded predictions put the four mistaken ADPs just above the fixed P(CCONJ)=0.5 cutoff (approximately 0.503–0.540), despite the very strong overall ranking. This is descriptive evidence of a class-decision/calibration problem coexisting with useful separation, not permission to choose an author-specific cutoff from answers. No target-selected cutoff or word-specific exception is adopted.

## Implication for decipherment research

Together with iteration 124, the experiment supports preserving a probabilistic binary-class signal as a possible input to another decoder, rather than equating success with the current hard-tag PP integration. It does not yet establish reliability without supplied anchors, general POS recovery, exact Latin word identity, or Voynich applicability. Models must not be chosen per author using these results.

Next proposed diagnostic: source-only context-volume robustness of class calibration, using the existing thirteen training types and their held-out folds, before any author retest. Measure whether pooled scores drift as context changes and whether a frozen calibration can retain useful separation without damaging frequent-type decisions. Propagating class uncertainty into PP inference remains a separate proposal; this experiment does not test it.

Verification: the independent audit verifies 19 frozen input hashes, independently checks 57 type probabilities and 135 metric groups, confirms target identity/class poison invariance in all four views, checks reserve exclusion and unchanged prefixes, and replays common-type transitions for both authors. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration125/`.
