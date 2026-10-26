# Iteration210: oracle applicability repairs Aquinas, not all authors

**Perfect Case-bearing identification materially repairs one author's shortlist.** Filtering centers with no recognized global Case improves the frozen full12 Aquinas ranking from1/5 to5/5 supported centers; count4 and degree reach5/5 too. Cicero improves to2/5, Jerome remains1/5, and Caesar has no supported centers. Preserve the Aquinas ceiling as motivation for an anonymous applicability predictor, without treating an oracle filter as restored grammar.

## Frozen test

For all305 conservative centers, retain exactly those whose cached209 global recognized Case fraction is greater than zero. Preserve every207 score and ranking method; recompute top3/top5 including all exact cutoff ties and every supported center's rank interval. Compare all original lists exactly, retaining all four authors and all four ranking variants. No model fit, threshold search, teacher change, raw text, new annotation or reserve use. This gate explicitly uses target gold and cannot run on Voynich.

| Author | Original centers | Oracle eligible | Supported retained |
|---|---:|---:|---:|
| Aquinas |136|83|7/7|
| Caesar |23|11|0/0|
| Cicero |34|15|3/3|
| Jerome |112|65|3/3|

The gate rejects131 centers and retains all13 supported centers. Passing the gate means only that at least one occurrence has recognized Case; it does not imply correct Case names, POS, useful contextual support, or a known Latin word. Missing Case does not imply absence of other grammatical information.

## Gated shortlists

Cells show supported/selected for top3, then top5. All variants are retained, with no author-specific winner selection.

| Author | Full12 | Count4 | Frequency | Degree |
|---|---|---|---|---|
| Aquinas |3/3;5/5|3/3;5/5|1/3;3/5|3/3;5/5|
| Caesar |0/3;0/5|0/3;0/5|0/3;0/5|0/3;0/5|
| Cicero |2/3;2/5|2/3;2/5|1/3;2/5|1/3;2/6|
| Jerome |1/3;1/5|0/3;2/5|0/3;0/5|1/3;2/6|

The unchanged full12 original results were0/3 for all authors and1/5 Aquinas/Cicero/Jerome,0/5 Caesar. Oracle-gated full12 supported ranks are1,2,3,4,5,7,14 in Aquinas;1,2,11 in Cicero;2,6,13 in Jerome. Thus gating fixes the leading Aquinas errors but leaves supported centers outside even top5 in the other positive authors. Count4's Jerome ranks4,5,8 improve top5 while losing the full model's top3 hit; that tradeoff is not a reason to route authors using gold outcomes.

Machine-readable outputs include all64 original/gated lists, coverage relative to both candidate universes, precision/recall, rejected opaque IDs and all104 supported-center rank records. Caesar recall is undefined, rather than zero: the teacher has no positives. Even a perfect gate cannot create such positives or supply five supported centers where the teacher only has three.

## Interpretation and audit

This establishes a useful conditional ceiling in Aquinas, not an annotation-free result, independent validation, five restored Latin words, or common nuclei across texts. Applicability is a worthwhile component to test, with substantial residual support-ranking and coverage problems. The supported labels remain gold-reference205 detections under a finite conditional null, not grammatical truth.

Independent sorting/tie-group replay checks64 lists,104 rank records, filter membership, scalar metrics, exact207 baselines and30 hashes; all pass. Artifacts reside in `experiments/results/grammar-restoration/iteration210/`.

Next freeze a source-author-balanced applicability classifier using the existing anonymous12 features (and first4 count control), with binary source label “at least one recognized Case occurrence,” all other three authors and source-only standardization. Compare unchanged support ranking, applicability-only ranking and the fixed product of applicability and existing support scores at tied top3/top5; no target-gold gate or author-specific choice. Report applicability AUC/calibration and supported-center yield separately; a product of separately trained scores is a ranking heuristic, not a calibrated joint probability. This will test whether any of the oracle benefit survives removing target annotations.
