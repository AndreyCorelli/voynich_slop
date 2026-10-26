# Consensus cores — iteration195

**Source/model agreement is not a general confidence filter.** The joint core contains three applicable pairs out of three for both Cicero and Jerome, but only one out of three for Caesar; Aquinas's joint core is empty. Caesar's two false positives survive both models and every source-author omission. Preserve the small correct cores as observations, but do not adopt consensus as a reliable grammatical constraint rule or choose different policies per author using these outcomes.

## Frozen test

Use only iteration194's saved probabilities on the fixed193 graphs. Reconstruct each top-ten list, including every exact boundary tie, for the baseline and all five source-author omissions. Intersect those lists separately for the19-feature rich model and the three-feature frequency/support control; the joint core is the intersection of these two cores. No refill, source-view selection, retraining, threshold search, new labels/raw texts or reserved evaluation. Freeze every author/candidate membership before loading cached case-reference scores.

The five empty-source Tacitus omissions duplicate the corresponding baselines; these duplicates cannot change an intersection. Per-author source sets and view memberships are retained in artifacts. All six authors and all three core policies are reported, together with the two original baseline comparators.

## Precision and retained coverage

Cells show applicable pairs / selected pairs. Applicable means at least one recognized-case comparison in the pair's shared two-sided frames; it does not identify a named case or a direct syntactic dependency.

| Author | Rich baseline | Rich core | Control baseline | Control core | Joint core |
|---|---:|---:|---:|---:|---:|
| Aquinas |5/10|2/5|9/10|5/5|0/0|
| Caesar |8/10|4/6|8/10|6/8|1/3|
| Cicero |9/10|5/5|9/10|4/5|3/3|
| Jerome |9/10|7/8|6/11|6/10|3/3|
| Palladius |0/1|0/1|0/1|0/1|0/1|
| Tacitus |0/0|0/0|0/0|0/0|0/0|

An empty result has undefined precision, not100% precision. Jerome's baseline control has11 candidates because of an exact boundary tie. Palladius/Tacitus remain too sparse for restoration performance claims.

The rich core is less precise than its original list for Aquinas, Caesar and Jerome; only Cicero improves. The control core gives Aquinas5/5 case-comparable pairs involving10 types, but loses four of its nine useful baseline pairs. The rich Cicero core gives5/5 involving six types, retaining five of the baseline's nine applicable pairs. Neither observation supplies a label-free rule for deciding which model to trust in another text.

Joint cores retain only1/8 of Caesar's useful rich-baseline pairs and3/9 each for Cicero/Jerome; Aquinas loses all five. Their applicable endpoints involve2,5 and5 types, respectively. Conditional case equality is100% Caesar,66.67% Cicero and100% Jerome, while joint yield over all selected pairs is33.33%,66.67% and100%. In particular, Cicero's3/3 applicability does not mean perfect morphological agreement. No new within-word-profile null control is run here, and none of these pairs are restored exact word identities or named cases.

## Implication and next proposal

The194 finding survives: full shortlists have partial source robustness in three texts. The195 refinement fails: selecting only stable pairs can concentrate systematic errors, with two Caesar false positives surviving every model/view, and even the single negative Palladius candidate receiving unanimous support because it is the only available candidate. Rank unanimity is neither a calibrated probability nor a universal precision guarantee. Do not highlight the two3/3 results while omitting Caesar or the empty Aquinas result.

Next test a **within-author ranking objective**, comparing positive versus negative training pairs within each source author rather than learning only pooled applicability probabilities. This addresses a possible mismatch between pooled probability fitting and the desired per-text shortlist ordering; it does not promise that improving ranking loss will improve top-ten precision. Keep all193 features/target graphs, .1 ridge and author-held-out evaluation fixed. Source authors with no positive-negative comparisons cannot contribute ranking pairs: compare the ranker against a matched pointwise model using exactly those same eligible sources, as well as the original193 baseline, so that removing the singleton Palladius source is not confused with changing the loss. Freeze equal-author pairwise loss, source-only scaling, all rich/control models and top10/20 tie handling before predictions; report every author and no gold-chosen winner. Treat ranking scores as scores, not probabilities, and keep named-case/exact-word/reserved-evaluation milestones distinct.

## Verification

Independent review rebuilds all1,010 candidate memberships directly from probability ranks, using per-candidate strict-greater counts rather than the runner's set intersection. Independent scalar aggregation replays all30 policy metric groups,60 baseline-retention comparisons and12 exact baseline metric replays, including stable false positives, ties, zeros and undefined ratios. All26 input/freeze/source-manifest hashes pass. No model is fitted, no new raw/annotation/reserved data is read, and no broad project test-suite claim is made.

Artifacts: `experiments/results/grammar-restoration/iteration195/` contains frozen design/proposal, selections, membership/views, detailed scored selected rows, metrics, comparisons, audit and integrity manifest. Code: `benchmarks/grammar_consensus_core_iteration195.py` and `benchmarks/grammar_consensus_core_iteration195_review.py`.
