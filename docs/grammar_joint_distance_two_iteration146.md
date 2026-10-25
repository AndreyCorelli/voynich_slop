# Iteration 146: distance-two overlap does not improve transfer

Reject the proposed distance-two addition. With the same fitting procedure and 13 non-target training types, the augmented classifier loses type accuracy in five of seven texts and improves it in none. The frozen two-feature baseline remains the better supported model; its demonstrated full-text classifications remain useful grammatical evidence, subject to supplied catalogue membership and development-data reuse.

The design was frozen before fitting. Exactly one feature was added: corrected overlap between neighbors at distance two, with the same pooled-neighbor random-split expectation as the adjacent-word feature. Parity subsequences implement this without changing the existing feature modules. The augmented model uses the existing class-balanced regularized logistic fitting, fold-specific standardization, three existing type folds, and a final fit on the same 13 types; all 16 target labels remain excluded from training. Raw probability greater than 0.5 predicts CCONJ, with no offset or author-specific selection. Models were frozen before target features and all predictions before evaluation.

| Text | Baseline correct/types | Augmented correct/types | Baseline AUC | Augmented AUC | Baseline NLL | Augmented NLL |
|---|---|---|---|---|---|---|
| Caesar | 12/15 | 10/15 | .9821 | .9643 | .4731 | .5375 |
| Jerome | 12/16 | 11/16 | .7031 | .6406 | .6669 | .7828 |
| Gellius | 12/15 | 12/15 | .8929 | .8929 | .5068 | .5077 |
| Livy | 10/14 | 8/14 | .6875 | .5417 | .6274 | .8340 |
| Apuleius | 6/13 | 5/13 | .6500 | .3000 | .7357 | .8173 |
| Curtius | 12/15 | 11/15 | .8214 | .7143 | .5704 | .5698 |
| Suetonius | 12/16 | 12/16 | .7812 | .7344 | .5824 | .5810 |

AUC falls in six texts and is unchanged in Gellius. Small NLL improvements in Curtius and Suetonius do not justify selecting the augmented arm for those authors. Source out-of-fold accuracy is 7/13 for both models; NLL worsens from 2.0611 to 2.2408. The already weak source type generalization does not improve with this feature.

Both arms were also evaluated on 16 predeclared global word permutations per author, seeds14600–14615. These preserve exact vocabulary and token counts. Counts of shuffled AUCs at least as high as the actual AUC are:

| Text | Baseline | Augmented |
|---|---|---|
| Caesar | 0/16 | 0/16 |
| Jerome | 0/16 | 1/16 |
| Gellius | 0/16 | 0/16 |
| Livy | 3/16 | 6/16 |
| Apuleius | 7/16 | 15/16 |
| Curtius | 0/16 | 1/16 |
| Suetonius | 1/16 | 1/16 |

This fresh null batch qualifies the historical claim that the original rankings exceeded all 16 shuffles: that statement remains true of the earlier fixed batches, but does not hold for Livy and Suetonius under these new seeds. Do not interpret the earlier maxima as universal null separation or pool correlated author/type results into independent evidence. The full-text 71–80% accuracy in six authors still replays exactly, but ranking evidence is uneven across authors.

Next proposal: investigate the very small supervised training set rather than add more context distances. Using only existing source-modal annotations, predeclare eligibility for additional ADP/CCONJ training types outside the entire 16-type target catalogue, retain the existing two features and regularization, and assess grouped held-out-type performance before transfer. This would test whether 13 training types, including only three conjunctions, provide an unstable decision boundary. It is an untested proposal; no expansion or new annotations were performed here.

Verification independently reconstructed the distance-two feature using direct index offsets and combinatorial probabilities, recomputed adjacent overlap and dictionary-based role similarities, retrained all four augmented models, replayed out-of-fold probabilities, and checked target logits and metrics. All seven baseline references match iteration144. The focused suite passed 18 tests. Artifacts, freezes and verification manifest: `experiments/results/grammar-restoration/iteration146/`. This remains binary classification of supplied candidate types, not lexical recovery or general token POS tagging.
