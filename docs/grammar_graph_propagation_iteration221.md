# Iteration221: one soft graph step gives modest applicability gains

A single fixed graph update improves the balanced classifier's applicability AUC on the305 established centers in all four authors, and supported retention11/13→12/13. It does not improve any top-five support count; Cicero's product loses2/5→1/5. Preserve this modest annotation-free refinement result without treating it as reliable extraction or a new recovered nucleus.

## Frozen algorithm

For every conservative replacement-graph endpoint, project the same12 anonymous features from opaque counts, contexts and graph structure. This extends earlier305 degree>=2 centers to all546 endpoints, including241 degree1 nodes outside the prior training eligibility. Predict using unchanged source-trained211 baseline and216 relevance-balanced applicability models, each excluding its target author. No target labels enter features, seeds or propagation.

Apply exactly one synchronous step `p_new(w)=.5*p_original(w)+.5*mean(p_original(neighbor))`. No fit, strength/iteration search, label seeds, or component consensus. Freeze features, original/refined scores and all lists before metrics. Compare all-node and established-center applicability, supported-center retention, fixed.5 gates then unchanged207 full12 support ranking, and applicability×support products, tied top3/top5 in all authors. Gold labels are evaluation only; all authors remain reused development data.

## Established-center results

| Author | Baseline AUC, original→refined | Balanced AUC, original→refined | Balanced supported retention | Balanced admissions |
|---|---|---|---|---|
| Aquinas |.6304→.6333|.5694→.5810|6/7→6/7|95→104|
| Caesar |.8561→.8636|.7955→.8485|0/0→0/0|21→23|
| Cicero |.8807→.8912|.7789→.8596|2/3→3/3|13→13|
| Jerome |.6498→.6442|.6173→.6219|3/3→3/3|102→106|

Balanced center NLL improves in all four: .7167→.6602,.6572→.6531,.5995→.5926,.9496→.8897. Admissions expand231→246/305, so12/13 retention alone does not establish improved selectivity. Baseline supported retention remains3/13; a fixed propagation step does not repair its large original subpopulation losses.

All-node results differ: balanced AUC Aquinas.6277→.6251 declines, Caesar.8433→.9025 improves, Cicero.7464→.7629 improves, Jerome.5651→.5782 improves. Thus the all-four-center AUC gain is not a universal all-node claim, and degree1 extrapolation needs explicit caution. No probability-calibration guarantee follows from averaging scores trained under a reweighted prior.

## Support shortlist results

The baseline hard top5 remains0/0/0/1 supported across Aquinas/Caesar/Cicero/Jerome; baseline product remains1/0/2/0. Balanced hard top5 remains1/0/2/1; balanced product changes1/0/2/1→1/0/1/1. All these lists contain five centers. Complete top3 and scalar metrics remain in artifacts; no per-author choice between propagated/unpropagated scores is adopted.

The relation-based update therefore changes applicability ranking usefully in several settings but does not solve the precision bottleneck. Earlier conditional grammar evidence and controlled retention gain remain preserved. No exact Latin words, named cases or POS labels are restored by this pilot.

## Execution integrity and independent audit

The initial runner froze all features/predictions/lists, then stopped at an exact floating-point comparison against earlier seed probabilities. Batched matrix scoring changed existing-center probabilities by at most2.220446049250313e-16. Preserve that runner and artifacts unchanged. A separate frozen finalizer validates differences below1e-12 and confirms every original shortlist is exactly unchanged; it reads the frozen predictions without generating new ones.

Independent feature reconstruction verifies546 rows, scalar model scores, all16 original/refined variant-author groups,64 tied lists, applicability/support metrics and42 hashes. All pass. Frozen computation resides in `experiments/results/grammar-restoration/iteration221/`; finalization, summary and audit in `iteration221-finalization/`.

## Next control

Before adopting propagation, compare it with half-self/half-global-mean shrinkage and fixed degree-preserving random graph rewiring. Use the same original seeds, one-step rule and all outputs, with no new models, labels in graph generation, strengths or winner selection. The global-mean control preserves AUC ordering while testing threshold/calibration effects; rewiring tests whether actual relationships outperform generic degree-dependent averaging. Keep support retention and top-five precision separate from applicability AUC. The original frequency-controlled gold homophily does not by itself establish that this inference-time refinement beats these controls.
