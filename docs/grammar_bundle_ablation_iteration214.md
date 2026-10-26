# Iteration214: removing frequency and reuse does not repair applicability

All four fixed applicability variants still reject every supported Aquinas and Cicero center at.5. Removing reuse improves Aquinas's soft-product top5 from1/5 to2/5, but Jerome remains0/5 and no universal extraction improvement appears. Preserve this limited ranking gain without adopting an ablation or interpreting earlier coefficient contributions as causal proof.

## Frozen experiment

Same305 centers, binary211 Case-bearing source labels, all other three authors with equal total training mass, source-only weighted standardization, logistic mean NLL plus.05 squared slope norm and free intercept. Compare full12, no global log frequency(column0), no occurrence reuse(column4), and neither. Each variant uses unchanged207 full12 support scores: fixed.5 hard gate then support order, or fixed applicability×support product. All tied top3/top5 lists, applicability metrics and support false exclusions are retained. No source/threshold/author-specific winner selection, new raw text, annotation, reserve or feature addition.

Features are frozen before label loading and all models/predictions/lists before support evaluation. Full12 reproduces211 predictions/models and212 hard lists exactly. Oracle210 comparisons remain explicit target-gold diagnostics, not deployed filters or probability bounds.

## Results

Entries are supported centers in top5; all these lists select five centers. Retained counts apply to the hard.5 gate over the entire candidate universe.

| Author | Variant | Applicability AUC | Supported retained | Hard top5 | Product top5 |
|---|---|---:|---:|---:|---:|
| Aquinas |full12|.6304|0/7|0/5|1/5|
| Aquinas |no frequency|.6215|0/7|0/5|1/5|
| Aquinas |no reuse|.6513|0/7|0/5|2/5|
| Aquinas |neither|.6449|0/7|0/5|2/5|
| Caesar |full12|.8561|0/0|0/5|0/5|
| Caesar |no frequency|.8485|0/0|0/5|0/5|
| Caesar |no reuse|.8561|0/0|0/5|0/5|
| Caesar |neither|.8409|0/0|0/5|0/5|
| Cicero |full12|.8807|0/3|0/5|2/5|
| Cicero |no frequency|.9263|0/3|0/5|2/5|
| Cicero |no reuse|.8947|0/3|0/5|2/5|
| Cicero |neither|.9088|0/3|0/5|2/5|
| Jerome |full12|.6498|3/3|1/5|0/5|
| Jerome |no frequency|.6399|2/3|1/5|0/5|
| Jerome |no reuse|.6560|3/3|1/5|0/5|
| Jerome |neither|.6547|2/3|1/5|0/5|

Cicero's no-frequency AUC.9263 coexists with rejecting all three supported centers. Better broad Case-bearing discrimination therefore does not establish retention of contextual grammatical evidence. Frequency removal loses one supported Jerome center and does not improve its top5. Count-related proxies and correlated features remain after removing two inputs; this experiment rejects the simple ablation remedy, not every possible role for frequency or reuse.

No new named grammar, POS or exact Latin nuclei are restored. Support labels remain205 detections under the conditional Case/POS-profile null, not grammatical correctness; non-Case words may support other decipherment strategies. Caesar's support recall/AUC stay undefined because it has no supported centers.

## Verification and next diagnostic

Independent source weights/scales and16 Newton refits reproduce predictions; products,64 tied lists, applicability/scalar support metrics, original/oracle comparators, exact211/212 baselines and55 hashes pass. Machine-readable summary also retains all top3 results, confusion, calibration, supported retention identities and coverage. Artifacts: `experiments/results/grammar-restoration/iteration214/`.

Next evaluate these frozen models on their **source** centers, explicitly as in-sample diagnostics: per-source-author applicability metrics and supported-center.5 retention/probability ranges, alongside held-out results. Do not refit, pick a winner or treat source success as validation. If supported source centers are already rejected, the objective/model neglects the relevant subpopulation during training; if retained at source but lost at target, transfer is the more direct bottleneck. Separate these explanations before another feature or model change.
