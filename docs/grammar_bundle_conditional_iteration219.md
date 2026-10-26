# Iteration219: source Case-only support training does not repair extraction

Removing non-Case source negatives does not improve the full model under the fixed anonymous target gate: Aquinas stays1/5 supported, Cicero2/5, and Jerome falls1/5→0/5; Caesar remains0. The limited oracle improvements do not survive removing target annotations. Do not adopt the conditional model or continue choosing scalar variants against these targets.

## Frozen experiment

Fit source support classifiers only on cached Case-bearing source centers:83 Aquinas,11 Caesar,15 Cicero,65 Jerome before each target exclusion. Every target uses all other three authors, including Caesar's zero-positive source. Equal total source-author weights, source-only weighted standardization, logistic mean NLL plus.05 squared slope norm and free intercept; full12/count4 feature sets unchanged. Source Case eligibility changes both the training population and fitted scaling, so the result is not a loss-only contrast.

Compare each new model with its frozen207 counterpart under the identical216 balanced anonymous applicability>=.5 target gate. Also compare applicability×support products over all centers and clearly oracle globalCase>0 target filtering. Freeze copied features before labels, all models/predictions/lists before evaluation. No target Case/POS eligibility in deployed selection, threshold search, author-specific winner, new raw annotation or reserve use. Products are ranking heuristics, not calibrated joint probabilities.

## Top-five support yield

All cells select five centers; numbers show supported centers before→after conditional training.

| Author | Full12 anonymous gate | Full12 product | Full12 oracle | Count4 anonymous gate | Count4 product | Count4 oracle |
|---|---|---|---|---|---|---|
| Aquinas |1→1|1→1|5→5|1→1|1→1|5→5|
| Caesar |0→0|0→0|0→0|0→0|0→0|0→0|
| Cicero |2→2|2→2|2→2|2→2|1→2|2→2|
| Jerome |1→0|1→0|1→2|0→0|0→0|2→1|

Cicero count4 product improves1/5→2/5, but the full model already achieved2/5 and the hard-gate result is unchanged. Jerome full12 oracle improves1/5→2/5 while anonymous-gate/product yield declines to0/5. This separates a conditional ranking improvement from a usable annotation-free pipeline gain. Aquinas's oracle5/5 remains, while its anonymous extraction remains1/5.

All models share the same target gate, retaining6/7 supported Aquinas centers,2/3 Cicero,3/3 Jerome, and no Caesar positives. Failure to place retained centers at the head therefore remains despite better admissibility retention. Each author/variant's top3, complete metrics and source Case-only in-sample classification are preserved in artifacts. Whole-universe classification for conditional models is descriptive: their training condition and changed prior do not guarantee calibrated probabilities outside Case-bearing centers.

This rejects the simple remedy of removing irrelevant source negatives under the present features and model. It does not establish that grammatical structure is absent: earlier gold-reference contextual evidence and controlled retention gain remain intact. No named cases, POS or exact Latin nuclei are restored.

## Audit and direction

Independent source eligibility/weights/scales and eight Newton refits reproduce all models;64 prediction groups,96 tied lists, scalar support/classification metrics, exact207 baseline scores,216 full-model pipeline baselines and28 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration219/`.

Next move beyond independent node counts and entropies. Audit whether the replacement graph's **relationships** carry Case-applicability information: on the unchanged193 word-pair graph, measure endpoint Case-bearing agreement and Case-bearing/non-Case mixing, with frequency-stratified label-permutation controls and all four authors retained. Include degree/connected-component heterogeneity and where the fixed applicability mistakes sit. This is a gold-reference diagnostic, not an inferred grammar result; if there is usable controlled homophily, freeze a graph-based propagation experiment using only anonymous edges and source-trained scores at inference. If mixing defeats that premise, do not impose graph-wide grammatical equality or proceed with smoothing by assumption.
