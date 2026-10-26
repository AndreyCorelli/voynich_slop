# Iteration208: count-driven hubs explain much of the failed ranking head

The frozen bundle selector ranks large, frequent bundles ahead of the supported ones. This explains its good broad discrimination but poor top-three precision; it does not prove those leading bundles lack grammatical information. The teacher is the205 gold-reference significance test, and failing that test is not a ground-truth grammatical negative.

## Fixed descriptive audit

No new fit, feature, threshold, teacher or author selection. Reuse all207 predictions, models and labels after verifying its entire manifest. For each of the13 supported centers, all four rankings retain its tied rank interval and the indices of every unsupported center strictly above or tied with it. For every author/model, retain all unsupported top-five centers including cutoff ties; compare all12 feature medians against supported centers and the full unsupported population. For full12, decompose the mean logit difference between unsupported top-five centers and all supported centers using the frozen source scaling and coefficients. These are algebraic descriptions of a learned score, not causal effects or fresh validation.

## Results

| Author | Full12 supported ranks, sorted | Unsupported top-five degree greater than supported | Frequency greater than supported | Mean logit advantage of unsupported head |
|---|---|---|---|---|
| Aquinas |4,7,8,10,11,19,31|89.29%|89.29%|.7186|
| Caesar |none|undefined|undefined|undefined|
| Cicero |5,6,28|100%|100%|.6015|
| Jerome |5,21,31|91.67%|91.67%|.8382|

Percentages compare every unsupported top-five center with every supported center within that author, using strict greater-than comparisons. There are four unsupported head centers for each author with positives; Caesar has five and no supported comparison group. Shared centers and observations mean these comparisons are not independent samples.

For Aquinas, shared-frame count, queried-pivot count and degree contribute +.3130,+.2537,+.1564 to the .7186 logit gap. For Cicero, degree/shared-frame/pivot counts contribute +.3366,+.1404,+.0998; for Jerome, pivot/shared-frame/degree counts contribute +.3087,+.2927,+.1527. These three count terms alone sum to .7231,.5768,.7542 respectively. Other terms sometimes offset and sometimes reinforce them; the decomposition is model-specific and correlated features prevent causal attribution.

The full-model unsupported head has larger median frequency and degree than the supported set in all three authors. Yet supported centers themselves often exceed the much larger unsupported population in degree: removing the count signal wholesale would discard useful broad discrimination too. Count4 improves some supported ranks but does not solve the head; its supported ranks are2,7,9,11,12,15,24 for Aquinas;4,8,30 for Cicero;9,12,16 for Jerome. The full model puts one supported center near30 in each of the three positive authors, so the problem extends beyond a few leading hubs. No universal rank cutoff or hub exclusion follows from this audit.

## Verification and next check

Independent scalar replay verifies52 supported rank records,72 unsupported head records across16 ranking groups, all feature medians, pairwise size comparisons, coefficient decompositions and summary values;21 input/frozen-manifest hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration208/`. No raw text, reserved labels, word identities or new predictions were opened.

Next distinguish why the leading hubs fail the teacher: insufficient recognized Case coverage, profiles with little possible context-specific surplus, or enough profile variation but weak observed contextual association. Audit these reference properties over all eligible centers, retaining the fixed heads and supported groups as descriptive summaries; do not treat unsupported hubs as known grammatical mistakes or filter them using gold at inference. This should determine whether the next learner needs better grammatical applicability features or whether predicting the particular surplus-significance teacher is itself a poor proxy for useful decoding constraints.
