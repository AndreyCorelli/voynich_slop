# One-shot Dante Case transfer — iteration199

**Preserve a reserved-author grammatical signal, with limited shortlist precision.** The primary frozen ranker selects6/10 case-comparable pairs on Dante, against19/76 (25%) in the full graph; AUC is.781. More importantly for the underlying contextual hypothesis, the full graph's conditional case equality is92.98%, above all199 within-word Case-profile permutations (maximum75.46%). The selected top-ten equality does not beat those controls, and the richer feature set does not beat the simpler ranking control.

These are separate findings: transferable applicability ranking and a conditional contextual association. Neither is general POS restoration, named-case inference, a set of exact word nuclei or a Voynich translation.

## Protocol and reserve state

Use the same198 primary76-pair graph from966 admitted DVE+Mon sentences/26,083 lexical words. All four models come unchanged from the saved196 Tacitus fold, trained on Aquinas/Caesar/Cicero/Jerome before Dante FORM was projected; their matched Palladius-fold models are identical. Copy the194 source-prior comparator with the same four authors (probability.3778134). No fit, source choice, standardization update, feature/ridge change or model selection occurs.

Freeze all19 anonymous query-excluded features, all four outputs and tied top10/20 selections before decoding Case. Threshold.5 applies only to pointwise probabilities; pairwise outputs remain raw ranking scores. Primary outcome is rich ranking top10 applicability; all models and controls are mandatory, not a target-selected winner. Decode Case from FEATS only for198 admitted sentences, treating missing/unrecognized/multivalue Case as unscored; no POS or other gold fields enter this evaluation.

**The admitted Dante Case reserve is now consumed.** Further Case analyses of these texts are follow-up/development evidence, not fresh validation. POS remains unprojected, as do attributed letters, quarantines and Seneca grammatical annotations. Prior raw-literature exposure and UDante's unresolved declaration conflict remain documented; no redistribution/relicensing claim is made.

## All model results

| Frozen model | Top10 applicable | Top20 applicable | AUC | Top10 applicable endpoint types | Top10 conditional equality | Top10 joint yield |
|---|---:|---:|---:|---:|---:|---:|
| Pointwise rich19 |5/10|10/20|.7812|10|80.00%|40%|
| Pointwise frequency/support3 |6/10|10/20|.7950|12|83.33%|50%|
| Pairwise rich19 — primary |6/10|10/20|.7812|12|83.33%|50%|
| Pairwise frequency/support3 |6/10|10/20|.7987|12|83.33%|50%|
| All-candidate baseline |19/76|—|—|26|92.98%|23.25%|

The76-pair candidate graph involves76 endpoint types;12 case-involved shortlisted types are not12 correctly identified lexical words or POS labels. Applicability means at least one recognized-case Cartesian occurrence comparison in shared frames. Conditional equality averages matching-case fractions within eligible frames and then applicable edges. Joint yield averages that conditional score over **all** selected edges, assigning zero to nonapplicable edges; it is not word accuracy or calibrated probability.

The primary list has2.4 times the all-candidate applicability fraction but still contains four nonapplicable pairs and finds only6/19 applicable graph pairs. This supports soft candidate ranking, not reliable hard grammatical constraints. Rich ranking gains one applicable pair over its frozen pointwise counterpart, but neither rich variant improves on the simpler control. The previous7–9/10 development results do not establish that precision on this reserved author.

| Probability model | NLL | Brier | At.5: applicable / selected | Recall of19 applicable pairs |
|---|---:|---:|---:|---:|
| Pointwise rich19 |.5539|.1873|14/32|73.68%|
| Pointwise frequency/support3 |.5174|.1700|8/15|42.11%|
| Frozen source prior |.5992|.2038|0/0|0%|

Both pointwise models beat the fixed source prior on loss, but their.5 selections remain too impure for confident constraints. Calibration bins/confusion counts are preserved in the artifacts. Raw rank scores receive no probability metrics.

## Word-profile controls: preserve the full-graph finding

The protocol also freezes199 seeds19900–20098 before Case decoding. For each, shuffle Case values—including missing values—among all lexical occurrences of each opaque word type. This preserves every word's Case inventory/frequencies while disrupting its assignment to contexts. Graphs, model outputs and all eleven selections stay fixed. These controls do **not** condition on POS; results are a word-profile baseline, not the stronger within-word-and-POS test used in some earlier development work.

| Fixed selection / metric | Observed | Null mean | Null maximum | Nulls at least observed |
|---|---:|---:|---:|---:|
| All76: conditional equality |92.98%|59.20%|75.46%|0/199|
| All76: joint yield |23.25%|13.69%|17.87%|0/199|
| Primary top10: conditional equality |83.33%|83.99%|100%|117/199|
| Primary top10: joint yield |50.00%|44.77%|60%|39/199|
| Primary top10: applicability |60.00%|53.42%|60%|68/199|

All-candidate applicability under these nulls ranges16–19/76, versus19/76 observed. Missing-case placements can therefore change the conditional denominator; word profiles themselves are preserved exactly. The wide full-graph equality separation is worth retaining, but the tail counts are not a universal confidence estimate or evidence that the selector identifies the context-dependent portion of the signal. Correlated edges share words/frames, and this is one author-level test.

## Next diagnostic

Freeze a reference-only POS-composition audit of these already fixed graphs/lists and repeat Case shuffles **within word×POS**, opening no model input or making any new predictions. Use the preexisting PRON/DET strata (both, exactly one, neither, and involving) and report all strata with sparse/empty denominators; do not choose favorable word families after looking. This tests whether the preserved full-graph effect survives a stricter profile control and clarifies what sort of grammatical candidates were ranked. Keep all outputs unchanged, label the audit as follow-up of a consumed Case reserve, and do not treat this as target-driven training or fresh POS restoration. Only after that should a development-only selector modification be proposed to capture the graph signal more selectively.

## Verification

Independent review reconstructs all76 feature vectors and all four frozen model outputs, the source prior, score/tie/threshold selections and every raw admitted Case reference (30,806 integer rows). Its scalar Cartesian scorer replays76 real and15,124 permuted edge scores, all11 real and2,189 null list metric groups, classification/calibration/AUC, selected details and null comparisons. Every per-word Case profile is preserved. All64 input/freeze/prior-manifest hashes pass, and the prediction-freeze artifact precedes the first gold-reference artifact. This is procedural code/artifact isolation, not a physically separated annotation store. No POS values, refits or retuning are used; dedicated audit passed, with no broad project-suite claim.

Artifacts: `experiments/results/grammar-restoration/iteration199/` contains frozen design/proposal/models, features, outputs/selections/prediction freeze, Case references and detailed scores, summaries/calibration, all word-profile nulls/comparisons, audit and integrity manifest. Code: `benchmarks/grammar_dante_case_transfer_iteration199.py` and `benchmarks/grammar_dante_case_transfer_iteration199_review.py`.
