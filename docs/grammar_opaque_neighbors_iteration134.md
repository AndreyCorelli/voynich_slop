# Iteration 134: opaque-neighbor feature additions fail author transfer

Reject the tested feature addition as a transferable improvement. Recurrence features improve source binary class accuracy from **11/16 to 12/16**, but downstream precision falls and author predictions become substantially worse. Expanded Jerome changes from **17 correct / one wrong PP selection to 15/29**. The frequency-only control also fails to provide a consistent improvement. Earlier iteration-132 findings remain intact; neither new arm is adopted.

## Frozen representation experiment

Both arms retain the exact iteration-132 five-anchor masking, thirteen noncatalogue training types, three held-type folds, sampled occurrences, class-balanced loss, regularization, optimizer settings, and fixed 0.80 PP cutoff. All sixteen target types remain excluded from training labels and hidden in contextual inputs.

The frequency control adds binned relative frequencies of the center and its immediately adjacent opaque IDs. The primary recurrence arm adds directional neighbor diversity, normalized entropy, concentration, the current pair's conditional share, whether that pair recurs, and equality of the two flanking IDs. The added features use only ID equality and sentence boundaries: arbitrary consistent ID renaming or poisoning private anchor/tag fields leaves them unchanged. Existing five-anchor features are retained separately.

Unsupervised counts use each admitted context, including held-out types' occurrences but not their labels. This is a transductive contextual feature computation, not extra grammatical supervision. Global frequency and rate boundaries are fixed before evaluation. Sampled training positions match iteration 132; feature vocabularies are rebuilt from the new training rows.

Each arm trains three fold models and a final model. Balanced scalar offsets are fitted only on the thirteen out-of-fold profiles and frozen before all source/author predictions. Offsets are **0.88599** for frequency and **3.94626** for recurrence. The latter is large, but does not by itself establish the cause of failure.

All five cached contexts remain included. Author class profiles use original/expanded context as before; PP inference scores only original 100 positions. All class predictions and PP views are frozen before PP scores, and scores before metrics. No annotations, reserve features, sealed lexical tests, budget/author-specific tuning, or defaults change.

## Binary class results

Cells show correct / present types. “Old” is the matched sparse model from iteration 132 at identical inputs.

| Context | Old | Frequency | Recurrence |
|---|---:|---:|---:|
| Source | 11/16 | 8/16 | **12/16** |
| Jerome original | 8/13 | 5/13 | 5/13 |
| Jerome expanded | 10/16 | 7/16 | 10/16 |
| Caesar original | 7/13 | 7/13 | 4/13 |
| Caesar expanded | 7/15 | 7/15 | 6/15 |

Source recurrence mean NLL improves from 0.6424 to 0.6190, with AUC unchanged at 0.8125. Frequency improves source AUC to 0.90625 but classifies only eight types correctly. These source-local changes do not transfer consistently.

Recurrence NLL is **3.216 on original Jerome** and **3.659 on original Caesar**, indicating confident wrong predictions; expanded values are 0.783 and 1.270. Recurrence ranking degrades to AUC 0.35 and 0.3333 on the original author samples, so shifting only the decision cutoff cannot address all observed failures. Expanded Jerome AUC improves to 0.7969, but that does not rescue its hard-class PP integration.

The thirteen labeled training types include only three conjunction types, while the new type-level contextual statistics add many candidate predictors. This is a plausible overfitting and context-composition sensitivity concern, not a mechanism proved by this experiment. No posthoc feature pruning or author-specific recalibration is performed.

## Downstream PP results at 0.80

Each cell is correct / wrong selections.

| Context | Old | Frequency | Recurrence |
|---|---:|---:|---:|
| Source | **95/9** | 0/0 | 126/19 |
| Jerome original | **19/1** | 2/1 | 0/0 |
| Jerome expanded | **17/1** | 0/1 | 15/29 |
| Caesar original | 1/0 | 1/0 | 4/9 |
| Caesar expanded | 0/0 | 0/0 | 2/4 |

Source recurrence precision is **86.90%**, below the old 91.35%; extra correct coverage does not make it a better high-precision component. Expanded Jerome precision falls to **34.09%**. All fixed originally-unmapped and anchor cohorts, along with gross changes against iteration 132, are retained in the artifacts. No favorable arm is selected per text.

## Implication and next proposal

This does not invalidate the use of opaque equality in principle, but it supplies no transferable improvement to the current grammatical component. There is no new shared lexical nucleus or evidence of blind Voynich recovery. The usable conditional subsets and their proximity limitation remain those documented in iterations 132–133.

A smaller next hypothesis is a single directional statistic: overlap between a type's left- and right-neighbor ID distributions, testing whether conjunction-like versus preposition-like contexts differ in symmetry. A source-only analysis with the same strict type exclusion, minimal fitted parameters, and count-matched controls would test this without another large feature bundle. Frequency and sample-size confounding must be measured explicitly; no benefit is assumed. This is a proposal, not an evaluated result.

## Verification

Twelve focused tests pass, including new checks for ID-renaming/private-field invariance, repeated pairs, sentence boundaries, and empty input. Independent review verifies forty frozen hashes, retrains eight models with identical sampled positions, replays 26 out-of-fold and 146 target probabilities, verifies invariance on ten arm/context combinations, recomputes ten PP vectors, and checks forty metric/transition groups. Maximum retraining objective difference is below 3e-11 and sampled-row probability difference below 1.4e-5; frozen predictions are replayed at 1e-12 tolerance. Strict target exclusion and reserve separation are checked. Artifacts are in `experiments/results/grammar-restoration/iteration134/`.
