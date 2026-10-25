# Iteration 131: sparse-context class inference drives the author coverage collapse

The controls identify a concrete bottleneck: the PP model can recover a substantial subset with five surrounding mappings **if target classes are supplied correctly**, whereas sparse-context class inference usually fails to supply useful preposition classes. Full PP context alone does little to rescue those sparse-context predictions. This motivates matched sparse-context classifier training, not another author-selected threshold.

These are diagnostic controls, including explicit privileged inputs. Correct classes are not newly restored information, and full-context class inference still requires many known mappings. No low-anchor decipherment solution is established.

## Frozen factorial

Cross two independently varied inputs: class inference with five versus all remaining surrounding anchors, and PP inference with five versus all remaining surrounding anchors. At each PP budget, also test unknown target classes and supplied correct modal type classes as an oracle. Every target lexical identity remains hidden, including oracle arms.

The five known mappings are unchanged: `ut`, `me`, `cum`, `quod`, and `te`. Reuse cached class probabilities from iterations 124–125 and 129–130; no class model or calibration is fitted. The PP model and 0.80 cutoff stay frozen. All eight inputs per context are frozen before scoring, and all scores before metrics.

Evaluate the source's 770 sentences and all four existing author context views. For authors, PP positions remain the original 100 sentences only; expanded text affects class profiles, not PP pooling or labels. Fixed cohorts match the earlier experiments. These are reused development data and supplied modal type classes, not new token POS annotations. No new annotations, reserve features, sealed lexical evaluation, author tuning, default changes, or lexical nuclei are introduced.

## Complete PP results

Each cell gives correct / wrong selections at 0.80. “Class 5” and “class full” describe context used to infer classes, independently of the PP context shown.

| Context | PP 5, unknown | PP 5, class 5 | PP 5, class full | PP 5, oracle | PP full, unknown | PP full, class 5 | PP full, class full | PP full, oracle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Source | 0/0 | 60/2 | 154/43 | 164/14 | 23/0 | 105/6 | 244/59 | 255/16 |
| Jerome original | 0/0 | 5/0 | 20/2 | 25/0 | 0/0 | 4/1 | 27/4 | 34/0 |
| Jerome expanded | 0/0 | 0/0 | 24/0 | 25/0 | 0/0 | 0/1 | 32/0 | 34/0 |
| Caesar original | 0/0 | 0/0 | 12/1 | 32/3 | 2/0 | 4/0 | 20/0 | 40/1 |
| Caesar expanded | 0/0 | 0/0 | 9/0 | 32/3 | 2/0 | 4/0 | 14/0 | 40/1 |

The same author's oracle and unknown rows repeat across class-profile volumes because those PP inputs do not depend on the class predictor's context. They are not independent replications.

## What the controls establish

1. **Sparse PP context does not force zero coverage.** Correct target classes with five known surrounding mappings give Jerome 25/0 and Caesar 32/3. Their fixed originally unmapped subsets give **22/0** and **30/0**, respectively. These remain oracle ceilings, not restored grammar.
2. **Correct classes do not eliminate the PP-context cost.** The five-anchor oracle retains 25/34 of full-context correct selections for Jerome (73.53%), 32/40 for Caesar (80%), and 164/255 for source (64.31%). Rich surrounding context still contributes useful information and sometimes suppresses errors.
3. **Full PP context does not repair bad class inputs.** Keeping sparse class predictions but restoring surrounding PP anchors yields Jerome original 4/1, expanded 0/1, and Caesar 4/0 in both views. This differs sharply from the correct-class ceilings.
4. **Better class inputs can unlock sparse-context PP predictions.** Inferred full-context classes give 24/0 on expanded Jerome even with only five surrounding PP mappings. Caesar remains limited at 12/1 or 9/0, showing that the existing full-context classifier is also imperfect.

Source results retain an important qualification: full-context inferred classes produce more five-anchor PP coverage (154 correct) than sparse inferred classes (60), but introduce substantially more errors (43 versus two). More class input information does not guarantee a better selective subset at this fixed cutoff.

## Implication for decipherment and next experiment

The result preserves a plausible path toward a grammatical input for another decoder: relatively few known mappings may support useful structure **if** the needed opaque classes can be inferred reliably. The class inference step is currently the main cause of the near-zero author coverage. Oracle outcomes are not evidence that this step has been solved.

Next train the existing thirteen-type binary classifier under the same five-anchor masking used at inference, retaining strict exclusion of all sixteen target types, the same type-held-out folds, sampled occurrences, class balancing, and regularization. Fit any scalar calibration only on the resulting thirteen out-of-fold profiles and freeze it before source or author evaluation. Compare against the existing full-context-trained classifier at exactly the same sparse inputs, without tuning budgets or thresholds on author answers. This tests a specific training/inference mismatch while reusing the current framework and labels.

## Verification

Independent review verifies 65 frozen input hashes, reconstructs all five contexts and forty PP inputs, recomputes all forty score vectors, and checks 160 fixed-cohort confusion/transition groups. It verifies target identity masking in oracle arms, reserve exclusion, previous sparse results, and source full-context reproduction. Nine focused tests pass. Frozen artifacts are in `experiments/results/grammar-restoration/iteration131/`.
