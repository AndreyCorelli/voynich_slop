# Iteration213: no single missing POS class explains applicability failure

The fixed applicability gate does not simply recognize nouns and miss pronouns. Rejected supported Aquinas centers are mostly nouns, while rejected supported Cicero centers are almost entirely pronouns; both classes also appear among accepted Case-bearing centers. Fixed-model score decompositions instead point to count-related penalties, especially frequency, plus occurrence reuse in Aquinas. These are descriptive model contributions, not established causes or restored POS.

## Frozen diagnostic

All305 centers,211 models and212.5 gate memberships remain unchanged. Freeze seven groups per author/model before loading cached201 POS: all centers, true Case-bearing centers, accepted/rejected true Case-bearing centers, supported retained/rejected centers, and admitted unsupported top-five centers. Reconstruct full-word global and unique queried-pivot POS counters from193 boundaries/205 memberships. Report center-macro fractions separately from pooled occurrence fractions, with explicit empty groups and probability ranges. Use no dominant-POS assignment, identities, new raw annotations, reserved labels, refits or threshold selection.

For each nonempty pair, compare rejected supported centers with all accepted true Case-bearing centers, including any supported centers there. Standardize with the frozen source-model means/scales; multiply mean feature differences by the frozen slopes. Their sum equals the difference in mean logits, with the intercept cancelling. Correlated features make these algebraic contributions unsuitable for causal attribution.

## POS composition

Percentages below average each center's global POS proportions equally; they are not counts of hard-labeled word types.

| Author/model | Rejected supported | Main rejected-supported POS fractions | Accepted true Case-bearing | Main accepted POS fractions |
|---|---:|---|---:|---|
| Aquinas full12 |7|NOUN55.78%,PRON20.01%,DET15.13%,SCONJ7.72%|28|NOUN32.60%,PRON22.54%,ADJ17.23%,DET16.75%|
| Aquinas count4 |7|same rejected group|63|NOUN37.61%,DET21.82%,ADJ13.78%,PRON12.41%|
| Cicero full12 |3|PRON98.84%,INTJ1.16%|5|PRON62.62%,NOUN20.00%|
| Cicero count4 |2|PRON98.26%,INTJ1.74%|7|PRON71.18%,NOUN14.29%|
| Jerome full12 |0|empty|61|NOUN43.93%,PRON29.18%,PROPN11.48%|
| Jerome count4 |1|PRON100%|57|NOUN47.02%,PRON26.10%,PROPN10.53%|

All supported Cicero queried pivots rejected by full12 are PRON; Aquinas's queried rejected-supported mix is NOUN57.14%,PRON21.92%,DET14.29%,SCONJ6.65%. All three Jerome supported centers have global PRON100%; full12 retains all, count4 rejects one. Caesar has no supported centers; both models accept ten true Case-bearing centers, whose center-macro profile is PRON47.27%,DET32.73%,NOUN20%. No universal absent grammatical class emerges, and it would be unjustified to hard-code a pronoun-only decoder from these labels.

## Fixed-score explanation

Negative values lower the mean applicability logit of rejected supported centers relative to accepted true Case-bearing centers.

| Contrast | Total logit gap | Frequency contribution | Other leading contributions |
|---|---:|---:|---|
| Aquinas full12 |−2.9605|−.4667|reuse−1.1025;sharedframes−.6024;leftentropy−.3704|
| Aquinas count4 |−1.1178|−.6968|sharedframes−.4968;degree−.2019;pivots+.2776|
| Cicero full12 |−.7918|−.3586|partnerfrequency−.1293;leftentropy−.1001;reuse−.0785|
| Cicero count4 |−.5958|−.5234|sharedframes−.2034;pivots+.0669;degree+.0641|
| Jerome count4 |−1.0329|−1.0003|sharedframes−.3108;degree+.2481;pivots+.0302|

Frequency contributes negatively in all five defined contrasts. The support selector earlier favored large/frequent hubs, while applicability now penalizes features also present among supported centers: the two binary objectives do not automatically compose into confidence. Removing a feature can shift coefficients onto correlated count features, so this decomposition does not promise that an ablation will fix extraction.

## Audit and next step

Independent position/counter reconstruction verifies305 center profiles,56 group summaries, five source-scaled feature/logit contrasts and22 hashes. Global and queried pooled/macro summaries and all empty groups pass. Artifacts: `experiments/results/grammar-restoration/iteration213/`. No POS predictions, named cases or Latin nuclei are restored by inspecting these gold references.

Next a targeted development-only ablation: retain the fixed source labels, weights, scales policy, ridge and LOAO authors; compare full12 baseline, removal of global log frequency, removal of occurrence reuse, and removal of both. Freeze all four variants and their.5 gates/products/top3/top5 before evaluation; retain all authors and all supported false exclusions. Do not choose an author-specific variant or tune a threshold. This directly tests the two largest recurring suspect contributions before adding a more complex classifier; no improvement should be claimed unless supported-center retention and actual shortlist yield improve together.
