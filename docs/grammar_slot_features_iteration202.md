# Query-slot features × training objective — iteration202

The fixed slot-feature block is **not a general repair** either. It gives some top-ten gains over201 surplus regression but leaves Caesar negative on average, changes the applicability costs unevenly and weakens most surplus top20 lists. Combined with201, this does not support adopting either a new training target alone or the full local-feature block as a reliable selector. The200 contextual graph signal remains preserved.

## Frozen factorial diagnostic

Use only the same four193 development authors and201 reference labels, excluding each target author from fitting/scaling. Append a predeclared14-feature block to the existing19: means of left/right anchor log frequencies and their absolute difference; slot count, distinct-center fanout and normalized entropy; queried-pair share, imbalance and comparison opportunities; total query occurrences and distinct anchors; endpoint context-set Jaccard and count-vector cosine. Counts include all lexical centers in valid slots, retaining193 punctuation/sentence boundaries. No POS/Case appears in features.

Compare19 versus33 features under two fixed objectives: ordinary Case-applicability logistic regression and201 contextual-surplus ridge regression. Keep source-author balancing, source-only scaling, .1 slope penalties and unpenalized intercepts unchanged; copy existing19-model and3-feature-control outputs exactly. Freeze features before loading201 labels, then models/outputs/tiedtop10/20 before scoring. No feature subset, objective, source or winner is chosen using target scores; no Dante or other reserve enters this run.

## Surplus-objective top ten

Each cell shows **mean surplus / positive-surplus pairs / Case-applicable pairs**; all lists here contain ten. Surplus is the unconditional frame-macro recognized-Case match residual above word×POS-profile expectation, with positive threshold1e-12, not conditional Case equality.

| Held-out author | Existing19 | Augmented33 |
|---|---:|---:|
| Aquinas |.067818 /2 /2|.068289 /3 /4|
| Caesar |−.006400 /3 /9|−.008139 /4 /9|
| Cicero |.123815 /7 /10|.139371 /7 /9|
| Jerome |.000000 /0 /9|.060000 /1 /5|

Aquinas's mean barely moves; Caesar gains one positive pair but has worse negative mean; Cicero improves mean at an applicability cost; Jerome finds one positive-surplus pair while losing four applicable pairs. The augmented surplus top20 means are.113406/.020461/.100650/.044062 versus.133750/.089869/.118603/.044062 originally. Positive counts fall8→6,8→6,11→10 and stay2; Case-applicable counts fall for all four authors. Hence the top-ten gains do not establish a stable broader shortlist benefit.

## Applicability-objective feature contrast

| Held-out author | Existing19 mean / positives / applicable | Augmented33 mean / positives / applicable |
|---|---:|---:|
| Aquinas |.051180 /4 /6|.039291 /3 /7|
| Caesar |−.002814 /3 /8|−.002814 /3 /8|
| Cicero |.108691 /6 /9|.119511 /7 /9|
| Jerome |.000000 /0 /8|.000000 /0 /7|

This contrast also fails to show a common contextual improvement: improving applicability can reduce surplus, and local inputs do not consistently change ranking in the desired direction. Simple3-feature controls and all20-pair lists remain in artifacts rather than being dropped when stronger than the new models. Outputs are supervised development diagnostics; raw regression scores are not probabilities, no model is adopted, and no exact word/POS/named-case restoration is claimed.

## Next question: can the aggregate association be localized?

Before more feature engineering, freeze an **edgewise detectability audit** on the four development graphs. The201 oracle shows positive residuals exist, but a positive residual alone can be sampling noise and does not establish a reliable local constraint. Reproduce word×POS-preserving Case permutations with the fixed unconditional frame-macro match statistic; hold all original selector lists unchanged.

Report every edge's raw permutation tail and a per-author max-statistic-adjusted tail using the maximum surplus over all its graph edges in each permutation. Fix199 seeds and threshold.05 before computation; use `(1 + exceedances)/(1 + permutations)`, include missing Case, report zero-variance edges and retain all non-detections. Also report the aggregate graph statistic and detectability within existing top10/20/oracle diagnostic lists. These are conditional permutation diagnostics with correlated edges and finite resolution, not universal probabilities of correctness or an inference-time algorithm.

This asks whether the present bottleneck is poor localization by the selector or insufficient evidence at individual-pair granularity despite a robust aggregate signal. Do not treat significance as a prediction input or choose a target-winning list. If local evidence is sparse, pooling coherent comparisons or obtaining more observations may be more useful than another point scorer; if it is plentiful, a model-capacity/transfer diagnostic becomes the next appropriate check. No Dante reuse is needed for this development audit.

## Verification and artifacts

Independent occurrence-based code rebuilds1,009 slot-feature rows/all14,126 new values, source-only scales and target exclusion. Four logistic Newton refits and four augmented least-squares refits verify new model outputs, with16 exact copied baseline score lists and48 scalar metric groups/contrasts replayed. All55 input/freeze/prior-manifest hashes pass. No annotation-dependent feature, new raw projection, reserve input or model tuning is used; dedicated audit passed without a broad project-suite claim.

Artifacts: `experiments/results/grammar-restoration/iteration202/`; code `benchmarks/grammar_slot_features_iteration202.py` and `benchmarks/grammar_slot_features_iteration202_review.py`.
