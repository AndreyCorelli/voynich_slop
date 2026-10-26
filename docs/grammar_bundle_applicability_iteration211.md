# Iteration211: learned applicability does not reproduce the oracle gain

The fixed anonymous applicability predictor fails to recover Aquinas's oracle5/5 supported shortlist. Full12 applicability×support gives1/5 in Aquinas,2/5 Cicero,0/5 Jerome and0/5 Caesar. Cicero's improvement is preserved as a limited result, but Jerome loses its earlier hit and neither model is adopted as a reliable selector.

## Frozen design

Reuse all305 conservative centers and the207 twelve anonymous features; count4 uses the first four. Binary source applicability label is at least one recognized global Case occurrence in the cached209 reference. Each target author is excluded from training and scaling; all other three have equal total weight. Logistic loss is weighted mean NLL plus .05 squared slope norm, with free intercept and source-only weighted standardization. No new raw annotations, reserves, target-gold filter, feature choice, threshold search or per-author winner selection.

Freeze the feature copy before loading labels and all models/predictions/tied top3/top5 lists before evaluation. For each model compare unchanged207 support score, learned applicability score alone, and their fixed product. The product is a ranking heuristic, not a calibrated joint probability. Separately report applicability classification and205 support-teacher yield. The latter teacher is conditional gold-reference evidence, not grammatical truth or word identity.

## Applicability transfer

| Author | Full12 AUC | Count4 AUC | Full12 precision at .5 | Full12 recall at .5 |
|---|---:|---:|---:|---:|
| Aquinas |.6304|.6697|.8000|.3373|
| Caesar |.8561|.7727|.7143|.9091|
| Cicero |.8807|.8140|.8333|.3333|
| Jerome |.6498|.5738|.6354|.9385|

Case-bearing counts are83/136,11/23,15/34 and65/112. Full12 NLL is .8250,.5789,.5700,.8853; source-author transfer is uneven, and a good AUC does not guarantee a useful common threshold. These are reused-development binary Case-bearing labels, not restored named cases or POS. Machine-readable output retains all confusion, Brier and calibration metrics for both models.

## Supported-center shortlists

Cells show supported/selected for top3, then top5.

| Author | Original full12 support | Full12 applicability×support | Count4 applicability×support |
|---|---|---|---|
| Aquinas |0/3;1/5|0/3;1/5|0/3;1/5|
| Caesar |0/3;0/5|0/3;0/5|0/3;0/5|
| Cicero |0/3;1/5|1/3;2/5|0/3;0/5|
| Jerome |0/3;1/5|0/3;0/5|0/3;0/5|

Applicability-only top5 contains **zero supported centers for every author and both models**. This remains true even when the list is entirely Case-bearing: full12 selects5/5 Case-bearing centers in Aquinas and Cicero, but0/5 supported centers. Recognizing applicability and ranking contextual evidence are distinct tasks.

Full12 product top5 is Case-bearing in2/5 Aquinas,3/5 Caesar,3/5 Cicero and2/5 Jerome. Thus the soft product still retains many centers excluded by the oracle. It also need not preserve a supported hit when it increases Case-bearing coverage. Compare these with210 oracle-filtered full12 support5/5,0/5,2/5,1/5; the oracle uses hard admissibility, whereas this pilot deliberately tested a soft product, so the two interventions differ as well as their information sources.

No exact nuclei or cross-text word intersection is demonstrated. Caesar's teacher has no positives, so support recall/AUC remain undefined. Even an oracle cannot produce five teacher-supported centers in Cicero or Jerome, where only three exist.

## Audit and next diagnostic

Independent source-weight/scale reconstruction and eight Newton refits reproduce the models; prediction/product replay,48 tied lists, scalar support metrics, applicability classification, exact207 baselines and46 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration211/`.

Next isolate the intervention difference using the **unchanged** applicability predictions: fixed probability>=.5 hard admissibility followed by original support order, both full12/count4, tied top3/top5, all authors and all rejected supported centers reported. Keep the existing soft-product and oracle results as comparators; no threshold search, refit or claimed confidence. Report applicability false exclusions of supported centers separately from residual support-ranking errors. This determines whether product mixing hides useful gating or whether the applicability predictor itself must improve before more composition experiments.
