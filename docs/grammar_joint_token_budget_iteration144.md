# Iteration 144: matched token budgets for the frozen joint classifier

The full-text milestone survives exact replay, but it does not imply reliable classification of short passages. At 4,000 tokens, several other texts also perform poorly, making limited context a plausible contributor to Apuleius's failure rather than evidence of an exclusively Apuleius-specific problem. This experiment cannot separate length from every local composition effect or establish a universal minimum length.

The frozen iteration142 joint raw classifier and its two single-feature controls were applied without refitting or offsets. Three SHA-selected 4,000-token windows per text contain centered 1,000- and 3,000-token windows; all seven full streams are references. Window indices were frozen before feature computation and predictions before evaluation. The 63 windows overlap and are not independent replications.

Primary results are correct/present candidate types, using existing source-modal ADP/CCONJ references. Each cell lists all three predeclared windows, without choosing a favorable position.

| Text | Full | 1,000 tokens | 3,000 tokens | 4,000 tokens |
|---|---|---|---|---|
| Caesar | 12/15 | 10/12; 9/11; 5/12 | 11/13; 11/13; 7/13 | 12/13; 11/13; 9/13 |
| Jerome | 12/16 | 5/11; 8/13; 7/12 | 12/15; 10/15; 10/15 | 10/15; 10/15; 7/15 |
| Gellius | 12/15 | 6/14; 8/14; 4/12 | 8/15; 9/15; 9/15 | 11/15; 9/15; 9/15 |
| Livy | 10/14 | 4/11; 8/14; 4/10 | 7/13; 9/14; 5/14 | 9/14; 11/14; 6/14 |
| Apuleius | 6/13 | 7/10; 7/11; 7/11 | 7/13; 7/13; 7/13 | 7/13; 6/13; 7/13 |
| Curtius | 12/15 | 4/9; 6/9; 6/13 | 7/13; 8/14; 8/14 | 9/15; 9/15; 8/14 |
| Suetonius | 12/16 | 9/14; 7/12; 7/14 | 10/16; 7/15; 8/15 | 11/16; 8/15; 9/15 |

Caesar improves with each larger nested window at every position. Other authors do not show universal monotonic improvement: Jerome worsens from 3,000 to 4,000 at all three positions. Even the three almost-full Apuleius windows vary between 6/13 and 7/13; small boundary changes can flip a decision. Candidate presence also changes, so the artifacts include full-text scores restricted to exactly the same present types, missing members of the complete 16-type catalogue, occurrence support, and the previously frozen common14 subset. Full candidate-set membership is still supplied; these are neither general POS-tagging results nor recovered lexical nuclei.

The next useful diagnostic is whether a prediction's stability under contiguous block deletion distinguishes correct from incorrect full-text decisions. Predeclare the deletions and a simple agreement measure, examine all seven texts, and treat this as a diagnostic rather than selecting a confidence cutoff on their labels. This tests whether the positive full-text signal can yield a defensible subset for a later deciphering stage.

Artifacts: `experiments/results/grammar-restoration/iteration144/`. Independent combinatorial overlap and dictionary role implementations checked every feature; separate linear-logit replay checked probabilities, and direct accuracy/NLL/AUC calculations checked every reported subgroup. All seven full references match iterations142/143 exactly; the focused suite passed 18 tests. No new annotations, reserved material, sealed works, or plaintext training were used.
