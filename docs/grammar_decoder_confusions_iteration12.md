# Distance-controlled decoder-confusion discrimination

## Fixed diagnostic plan

Test discrimination before composing another decoder score. Freeze `predicate-complex-v1`, all sentence groups, gold finite positions and the existing out-of-fold-trained interaction decoder for development. Development consists of the already inspected 66 source streams; this is not fresh confirmation. Neither confirmation/target decoding nor dictionary optimization is part of this iteration, regardless of the diagnostic outcome.

Generate training confusions by end-to-end four-fold source cross-fitting using the original blocked folds. For each outer fold, exclude its held streams from all marker vocabulary/model and parent fitting. Within its fitting streams, three inner blocked marker folds generate parent-training marker predictions without using the inner held stream. Fit one interaction parent ranker on these inner predictions; fit a marker model on the full outer fitting set; infer each outer held stream from tokens, gold predicate positions and predicted markers, with no gold boundaries/roles. This requires twenty source model fits. Save every fold membership and held prediction. A source classifier may subsequently use these held streams' labels; they must not have entered the decoder that generated their confusions.

Positive pairs are reference non-root parent edges; negatives are cross-sentence parents actually selected by the cross-fitted decoder. Match negatives to unused positives **within source author, exact intervening-predicate gap and floor(log2 token distance) bucket**, minimizing remaining absolute log-distance difference with deterministic stream/position tie-breaks. No positive is reused. Report all unmatched pairs. Fit ordinary regularized binary logistic models on the resulting balanced matched sample: two geometry features or the same 137 rich features from iteration 11. No new features, optimizer-negative forest objective, threshold/weight tuning or score composition. Include the two frozen all-pair classifiers from iteration 11 as controls.

Evaluate on: (1) all development reference edges versus the frozen decoder's selected cross-sentence parents; (2) development author/gap/distance-matched positive/negative pairs selected independently by the same rule; (3) true-parent versus selected-cross-sentence-parent contrasts **for the same child**, reporting all such contrasts and the tighter equal-gap/same-distance-bucket subset. These control schemes answer different questions; do not call pool matching same-child matching. Matching is an annotation-dependent evaluation selection, not an inference feature. The tight same-child subset is small (preflight indicates five cases), so report it descriptively rather than selecting it as the main result.

The richer refit is the primary model. Predeclared diagnostic screen: at least twenty matched development pairs and fifteen same-child contrasts; matched AUROC >=0.60 and at least +0.05 over the matched distance-only refit; matched paired preference accuracy >=0.60 and at least +0.10 over distance; same-child preference accuracy >=0.60 and at least +0.10 over distance. Give ties half credit. Report paired stream intervals and distance-balance diagnostics, not a binary success claim alone. Because the sample is deliberately balanced and conditional on decoder errors, classifier probabilities are **not calibrated general same-sentence probabilities** and must not be added to the parent objective.

Validate nested fold/vocabulary exclusion, marker and parent refits, held predictions, selected negative/reference-positive identities, deterministic matching without reuse, distance constraints, classifier refits and all discrimination metrics. Preserve previous artifacts and the negative results if the screen fails.

## Result: no reliable distance-controlled discrimination

The richer refit fails every quality check in the predeclared screen; both sample-size checks pass. It fits the sampled source confusions well but does not generalize to the development confusions. No score was composed with the decoder, and no confirmation/target inference or dictionary search was performed.

### Source generation and matching

Four outer folds generate all 266 source forests with full parent pools and unknown roles/boundaries. Each outer decoder uses three inner marker folds for parent-fitting evidence and a full outer-fitting marker model for its held inference: sixteen marker fits and four parent fits in total. Held inference receives only token strings, gold finite positions, independent morphology and fitted models. Source sentence labels are used afterward to identify positives and errors for the classifier, not by the held decoder.

| Sampling step | Source fitting cohort | Inspected development cohort |
|---|---:|---:|
| Reference parent pairs | 612 | 154 |
| Decoder-selected cross-sentence negatives | 131 | 41 |
| Matched positive/negative pairs | 131 | 40 |
| Unmatched negatives | 0 | 1 |
| Same-child true/cross-parent contrasts | 73 | 20 |
| Same-child contrasts with equal predicate gap and distance bucket | 18 | 5 |

The source match uses 65 Jerome and 66 Palladius negatives; development uses 17 and 23. Every match has the same author, exact predicate-index gap and token-distance bucket. **128/131 source matches and 37/40 development matches also have exactly equal token distance.** Mean absolute log-distance differences are 0.00218 and 0.02302, respectively. No positive or negative is reused within a match set. The single development unmatched negative is explicitly retained in the unfiltered evaluation; it is not silently called a successful discrimination.

The binary refits therefore see only **262 balanced training observations (131 pairs)**. A rich 137-feature classifier can overfit such a small, correlated sample despite fixed regularization. Decoder confusions may also change with source constructions and the decoder's fitting cohort; the experiment does not isolate these explanations.

### Development discrimination

Preference accuracy asks whether the positive logit exceeds its paired negative logit, awarding ties half credit. Matched-pool comparisons can pair different children; the same-child column holds the child fixed.

| Classifier | Matched AUROC | Matched-pool preference | Same-child preference |
|---|---:|---:|---:|
| Frozen all-pair distance classifier | 50.03% | 51.25% | 30.00% |
| Frozen all-pair rich classifier | 49.56% | 57.50% | 35.00% |
| Hard-pair distance refit | 49.47% | 48.75% | 60.00% |
| **Hard-pair rich refit, primary** | **42.50%** | **32.50%** | **35.00%** |

The primary wins 13 and loses 27 of the forty pool comparisons, with no ties. The distance refit wins one, ties 37 and loses two, so its 48.75% is predominantly the expected tie baseline after distance matching. On the twenty same-child comparisons, rich features win seven and lose thirteen; the distance refit wins eleven, ties two and loses seven (60% tie-adjusted accuracy). That latter score should not be mistaken for a strong learned grouping signal: the geometry model is essentially uninformative on the tightly matched pool and can only order the residual geometric differences in the broader same-child sample.

On the five tighter same-child contrasts, primary preference is 20%; the frozen rich classifier gets 60%. This tiny subset is descriptive only. For example, in source sentence **13287**, `uultis` has reference parent `est` at token distance three, while the decoder chose cross-sentence `prophetauerunt`, also at distance three and the same predicate-index gap. The refitted rich model still favors the cross-sentence pair (reference-minus-cross logit margin −0.843). This cannot be explained by a nearer alternative in that example.

The unfiltered 154-positive / 41-negative diagnostic reproduces the earlier frozen-rich AUROC of 48.13%; the new rich classifier scores 39.93%. Matching the fitting problem to the decoder's errors did not rescue the observed discrimination.

### Source fitting versus development

| Primary rich classifier metric | Matched source fitting pairs | Matched development pairs |
|---|---:|---:|
| AUROC | 92.33% | 42.50% |
| Paired preference | 92.37% | 32.50% |
| Brier score | 0.1163 | 0.3976 |
| Logistic loss | 0.3648 | 1.3384 |

Source numbers are **fitting performance of the pair classifier**, not an out-of-fold validation of that classifier. The source *decoder* was cross-fitted to produce its inputs; the final pair classifier subsequently trained on those source examples. Development is excluded from all fitting. This distinction prevents calling the 92% figure restored grammatical structure or evidence of transfer.

Because labels are balanced and conditional on this error-selection scheme, neither the new nor old probability scale is a calibrated general sentence-membership probability on this sample. The Brier/logistic-loss comparisons concern the selected balanced classification task only.

### Uncertainty

Descriptive stream-cluster bootstrap intervals (2,000 draws, seed 1729) are:

- Matched-pool rich preference: **32.50% [11.11%, 56.37%]**; rich minus matched distance: **−16.25 points [−36.59, +6.67]**.
- Same-child rich preference: **35.00% [10.51%, 60.00%]**; rich minus distance: **−25.00 points [−56.69, +5.26]**.

For matched pools, positive and negative examples can come from different streams. The bootstrap weights both stream endpoints (a shared stream receives one cluster weight); it holds the selected matching fixed. Same-child intervals use the common stream. Both are descriptive, omit uncertainty from refitting/reselecting matches and do not establish statistically worse-than-chance population behavior. They provide no convincing evidence of the required positive gain. The previously inspected development sample is small, and further tuning on it would need a separately labeled experiment and fresh validation.

## Interpretation and next work

This result narrows the problem: simply fitting the existing token-window/morphology/marker features to distance-controlled decoder errors does not yield useful held-out discrimination. It is not a candidate-retrieval problem—all positive parents were available—and no optimizer was allowed to corrupt a composed score in this test. It is a failure of the tested classifier to generalize on the relevant comparisons. That does not establish that the text lacks grammatical structure, or distinguish limited examples from a deficient representation or linear model.

Do not increase the failed grouping penalty or promote training accuracy. Before another learned score, inspect which **construction-level evidence** would distinguish the matched alternatives: parenthetical versus main clauses, coordination level, nested relative clauses, and a consistent morphological/argument analysis. A small source-only contrast set with explicit relevant cues, followed by a different held-out source cohort, would be more informative than another loss-weight adjustment. The current broad existence flags and short windows need not encode those distinctions even when their vectors differ numerically.

## Reproduction and independent verification

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_decoder_confusions_iteration12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_decoder_confusions_iteration12_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_decoder_confusions.py tests/unit/test_predicate_grouping.py tests/unit/test_parent_marker_interactions.py tests/unit/test_predicate_projection.py tests/unit/test_boundary_role_oracles.py tests/unit/test_training_alignment.py tests/unit/test_marker_oracle.py tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

Forty-seven focused tests pass. The [validator](../experiments/results/grammar-restoration/iteration12/validation.json) independently refits **all twenty nested source decoder models and both matched classifiers**, verifies each outer/inner membership and fold-local vocabulary exclusion, and reconstructs all **266 held source forests** from public observations only. Sixteen source optimum scores additionally match an independent Z3 calculation. It verifies reference-positive and actual selected-negative identities, deterministic one-to-one matching, unmatched accounting, every classifier logit and preference statistic, an independent AUROC calculation, the failed screen and paired uncertainty. Saved [diagnostics](../experiments/results/grammar-restoration/iteration12/diagnostics.json) distinguish fitting performance from development results and record distance balance, ties and bootstrap assumptions. Input/model/result hashes are retained. Benchmark runtime was 29.8 seconds; [report](../experiments/results/grammar-restoration/iteration12/report.json) and previous results are preserved.
