# Iteration 54: cross-fitting morphology confidence

Cross-fitting reveals genuine optimism in training morphology scores, but does not materially improve attachment. Selected-sentence F1 changes **64.87%→65.03%**, while full-source F1 falls **56.79%→56.52%**. Keep iteration 53 as the working performance baseline; cross-fitting is a useful methodological control, not an established algorithm improvement here.

## Controlled experiment

Retain iteration 53's source data, five outer partitions, broad morphology candidates, inference features, attachment optimizer and MAP/free NONE calibration grids. Only the four morphology-probability features on attachment **fit** sentences change. Structural features, neighboring POS, targets and candidate predicates remain identical. Outer calibration/test inference still uses the frozen outer morphology model.

For each outer fit portion, use its three original sentence folds as inner folds. Fit three morphology models, each on two folds:

- **Cross-fit:** a sentence receives probabilities from the model excluding its entire inner fold.
- **Two-fold exposed control:** assign those same three models cyclically so that the probability model includes the sentence's fold and excludes the next fold instead.

This compares annotation exposure at approximately matched training size. Fold sizes differ slightly, so it is not exact token-count matching. Both arms use the same set of two-fold models, and both use less morphology training data than the original three-fold baseline. The split excludes sentences, not recurring word types; learning a spelling from other sentences is allowed.

Fit 15 inner expanded-feature morphology models and ten local + morphology attachment models. Inner probability fits contain no outer test/calibration sentences. No inner conformal calibration is needed because candidates stay frozen. Recalibrate each attachment model's MAP/free NONE policies on the outer calibration portion only, with unchanged F1 and empirical precision90 objectives.

This is **probability-feature cross-fitting**, not full-pipeline cross-fitting: training candidates still use the original outer morphology model, and their conformal policies already use outer calibration annotations as in iteration 52. That fixed dependency is retained, not presented as newly independent calibration. No test outcome sets a hyperparameter.

## Results

The primary evaluation is unchanged: 304 selected sentences, 1,858 nominal frames and 470 gold finite-subject edges. F1 policies below all allow calibration-selected negative NONE cutoffs.

| Probability features during attachment fitting | Correct | Wrong | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Original three-fold in-sample, iteration 53 | 301 | 157 | 65.72% | 64.04% | 64.87% |
| Two-fold exposed control | 294 | 151 | 66.07% | 62.55% | 64.26% |
| Two-fold cross-fit | 304 | 161 | 65.38% | 64.68% | 65.03% |

Relative to iteration 53, cross-fitting adds five correct outputs and loses two, while adding nine wrong outputs and removing five: net **three more correct and four more wrong**. Against the exposed control it adds 18 correct and removes eight, but also adds 25 wrong and removes 15. These small differences do not establish a reliable gain.

Exact finite-subject edge sets in selected sentences decrease from 127/304 to 126/304; the exposed control also has 126. Original-reference recovery rises 220→223 out of 326, with wrong-governor predictions 27→28 and abstentions 79→75. All original candidate links remain fixed; reference candidate survival is still 324/326.

Broader F1 operating points:

| Scope / fit features | Precision | Recall | F1 |
|---|---:|---:|---:|
| All source / original | 51.62% | 63.10% | 56.79% |
| All source / exposed control | 52.16% | 62.20% | 56.74% |
| All source / cross-fit | 51.01% | 63.35% | 56.52% |
| Cicero selected / original | 65.78% | 65.26% | 65.52% |
| Cicero selected / exposed control | 66.49% | 65.26% | 65.87% |
| Cicero selected / cross-fit | 65.96% | 65.79% | 65.88% |
| Palladius selected / original | 65.43% | 58.89% | 61.99% |
| Palladius selected / exposed control | 63.89% | 51.11% | 56.79% |
| Palladius selected / cross-fit | 62.79% | 60.00% | 61.36% |

Full-source cross-fit output has 1,535 correct and 1,474 wrong edges, versus 1,529 correct and 1,433 wrong originally: six more correct for 41 more wrong. Full-source evaluation is the same 4,070 reused sentences, with 3,910 containing task frames and 2,423 gold links. The lower precision outside the selected subset remains material.

At the MAP-restricted operating point, cross-fit predicts 179 correct and 53 wrong links on selected sentences (F1 51.00%); the exposed control predicts 180 correct and 53 wrong (51.21%), and the original predicts 175 correct and 53 wrong (50.14%). This does not remove the need to calibrate below the MAP cutoff. No arm finds a margin cutoff meeting calibration precision90 with 20 predictions; those policies abstain.

Cross-fit free cutoffs are −1 in folds 0–3 and −1.5 in fold 4, the same as iteration 53. The exposed control uses −1.5 in fold 0 and −1 in folds 1–4. Some output differences therefore reflect legitimate calibration changes as well as fitted scores; no test-based threshold adjustment was made.

## Does exposure bias exist?

Yes. On the same 90,459 known-eligibility token exposures across outer fit portions, mean eligibility negative log likelihood is 0.1211 under the original in-sample model, 0.1249 under the two-fold exposed control, and 0.1831 under the two-fold cross-fit model. Corresponding Brier scores are 0.0362, 0.0365 and 0.0562. Lower is better. These are repeated training-token exposures, not 90,459 independent observations or an outer test score.

The exposure control supports optimism beyond merely using fewer folds. But removing it from attachment training barely changes generalization. For this model, it is not the main performance bottleneck. The smaller inner models and unchanged larger outer inference models also leave a training/inference feature-distribution difference; the control reduces, rather than eliminates, that concern.

Cross-fit misses 166 primary gold edges: three absent candidates, 71 whose wrong predicate ranks first and 92 correctly ranked edges rejected by the gate. This resembles iteration 53's three/70/96 decomposition. Eligibility and acceptance remain the larger problem than candidate retrieval.

## Decision and next diagnostic

Do not replace iteration 53 on performance grounds. Keep the cross-fit implementation and its exposed control for later model development, while retaining candidate/feature isolation when interpreting its results. Nothing here is fresh confirmation or cipher grammar restoration; readable Latin and supplied POS remain inputs.

Next, audit iteration 53's false positives using endpoint annotations **as diagnostics only**: distinguish non-nominative candidate subjects, nominative non-subjects, nonfinite candidate predicates and wrong attachment between eligible endpoints. Then measure oracle-mask upper bounds without changing learned scores. This will identify whether the next useful modification belongs in occurrence morphology, subject eligibility or attachment, rather than adding another undirected scoring feature. The audit is proposed, not yet run.

## Artifacts and checks

Code: `src/voynich_smt/crossfit_morphology.py`, `benchmarks/grammar_crossfit_attachment_iteration54.py` and its `_audit` module. Inner plans, models, training-role diagnostics and predictions are under `experiments/results/grammar-restoration/iteration54/`. The pre-evaluation tracker snapshot is frozen separately so the living tracker can be updated.

Validation checks 24,420 fit-sentence candidate/structural invariances and inference mutation invariance on all 304 selected sentences. Independent audit checks 30 frozen hashes, refits all 15 inner morphology and ten attachment models, reselects 20 calibration policies, replays 35,350 scores and 141,400 decisions, and reproduces 32 aggregate metrics. It verifies inner exclusion and unchanged prior candidate/prediction fields. Four new tests cover exposed/unexposed plans, feature-only replacement, annotation-independent probability inference and invalid plans; 50 relevant tests pass. The 200-sentence reserve remains unscored, with no prior target queries scored.
