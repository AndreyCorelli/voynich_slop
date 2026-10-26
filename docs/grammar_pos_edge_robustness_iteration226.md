# Iteration226: pair enrichment survives endpoint separation, source-learning evidence is uneven

Endpoint-disjoint selection retains useful POS-profile compatibility, so repeated word endpoints do not explain the entire enrichment. But source-label shuffles narrow the learned-transfer claim: rich19 top10 has tails.015 Aquinas,.120 Caesar,.025 Cicero,.130 Jerome. Preserve the inferred pairwise output and stronger Aquinas/Cicero evidence without claiming robust source-learned improvement across all four authors.

## Frozen checks

Reuse225 anonymous features, model family, source-only scales, author weights and targets. For199 seeds22500–22698, shuffle target compatibility labels within each source author; visit authors in fixed Aquinas/Caesar/Cicero/Jerome order with one seeded generator. Use identical permuted author vectors in every held-out fold and both models. The target author is always excluded from fitting, even though its permutation is generated for other folds. Freeze all null predictions/lists before evaluating original target labels.

Separately select endpoint-disjoint pairs greedily using frozen real predictions, descending score then original edge index. Accept an edge only if neither endpoint was previously used, until10/20 pairs or a maximal-list shortfall. No gold selection, matching optimization, model/threshold/author-specific winner, new annotation, raw text or reserve. Distinct endpoints do not imply independent contexts or annotation errors.

## Source-label permutation results

Upper tails are `(1+#null means >= real mean)/200`; all199 fitted nulls are retained.

| Author | Rich top10 mean | Rich top10 tail | Rich top20 tail | Control top10 tail | Control top20 tail |
|---|---:|---:|---:|---:|---:|
| Aquinas |69.47%|.015|.005|.050|.065|
| Caesar |71.20%|.120|.055|.385|.015|
| Cicero |78.91%|.025|.005|.035|.040|
| Jerome |88.67%|.130|.315|.140|.410|

These are separate reused-development tests, not adjusted confidence levels or independent confirmations. Rich top10 does not separate at fixed.05 in Caesar or Jerome, despite high absolute compatibility. Some shuffled-label models already select good target pairs: rich top10 null mean54.23% Caesar,66.00% Jerome, with maxima84.38% and100%. This may reflect target feature/graph structure and chance source slopes; the high absolute mean alone cannot establish successful learning from real source labels.

Paired rich-minus-control gain is not separated at.05 for any author/top10/top20 in the fixed shuffle comparison. The rich model's apparent advantage should therefore not be presented as robust proof that its additional features improve transfer. Keep the simple control alongside it.

## Endpoint-disjoint compatibility

Every requested list is available: ten pairs span20 distinct words, twenty span40. No shortfalls occur.

| Author | Rich disjoint10 | Control disjoint10 | Rich disjoint20 | Control disjoint20 |
|---|---:|---:|---:|---:|
| Aquinas |79.18%|78.55%|69.27%|65.61%|
| Caesar |67.97%|51.89%|51.39%|49.62%|
| Cicero |78.91%|73.19%|66.16%|66.15%|
| Jerome |88.67%|88.67%|73.01%|83.20%|

The inferred rich disjoint10 remains above each whole-graph mean21.13/44.24/36.91/55.37%. This is a useful concentration check, not a formal null test for the disjoint selections: the source-label null above evaluates the original tied lists. Disjoint output still does not name POS, identify Latin words, establish calibrated per-edge confidence or prove cross-text nuclei.

## Audit and next check

Independent augmented least-squares operators replay1592 shuffled fits,3184 null lists,16 disjoint lists, actual/permuted means, paired gains and27 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration226/`.

Next compare with fixed **untrained** anonymous rankings: shared-frame support, mean log frequency high and low as separate predeclared controls, and lexical-neighbor-frame Jaccard overlap. Keep all authors, tied top10/top20 and greedy endpoint-disjoint variants, no gold-selected direction or winner. These tests ask whether useful pairwise grammar can be selected by simple manuscript-internal structure without source labels, and whether the regressor adds value beyond those cheap baselines. A strong untrained relation selector would remain valuable even if the supervised interpretation weakens; named POS and exact nuclei remain separate goals.
