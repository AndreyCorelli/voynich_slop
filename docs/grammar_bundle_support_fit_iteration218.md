# Iteration218: support-ranking limits already appear in source heads

The original support ranker has weak in-sample shortlists as well as weak held-out shortlists. With oracle Case-bearing admissibility, source and held-out pooled precision become similar: full12 top5 is25/60 versus8/20 (41.67% versus40%); count4 is27/60 versus9/20 (45% in both). This argues against explaining the entire bottleneck as author transfer, without proving that transfer is absent or that the remaining limitation is solely model capacity.

## Frozen diagnostic

Score all four authors with each of the eight frozen207 models, retaining three-source/one-held-out roles. Freeze all32 score vectors before metrics. Each author has two candidate universes: original conservative centers and explicit oracle globalCase>0. Report both full12/count4, tied top3/top5, all supported rank intervals and whole-universe support AUC. No fits, thresholds, raw text, new annotations, reserves or author-specific winner choice. Oracle gating uses target gold and is not an inference method; source evaluation is in-sample, not validation.

## Pooled shortlist results

Entries show supported/selected evaluation instances.

| Model | Source original top3 | Source original top5 | Held-out original top3 | Held-out original top5 |
|---|---|---|---|---|
| full12 |6/36|17/60|0/12|3/20|
| count4 |3/36|7/60|1/12|2/20|

| Model | Source oracle top3 | Source oracle top5 | Held-out oracle top3 | Held-out oracle top5 |
|---|---|---|---|---|
| full12 |18/36|25/60|6/12|8/20|
| count4 |15/36|27/60|5/12|9/20|

Source totals repeat the same authors/centers across overlapping training folds; they are not independent samples. Similar oracle precision does not establish equivalent generalization or justify a significance claim. All AUC values use the full author universe, even in an oracle-list record; list restriction is not a new AUC definition.

## Author-specific oracle top5

The three source values correspond to the three folds in which the author is in training; all select five centers.

| Author | Full12 source supported counts | Full12 held-out | Count4 source supported counts | Count4 held-out |
|---|---|---:|---|---:|
| Aquinas |5,4,4|5|5,5,5|5|
| Caesar |0,0,0|0|0,0,0|0|
| Cicero |2,2,2|2|2,2,2|2|
| Jerome |2,2,2|1|2,2,2|2|

The teacher itself limits pooled precision. Caesar has0 supported centers, Cicero/Jerome3 each, Aquinas7. Thus even a perfect top5 selector can obtain only11/20 held-out hits, and33/60 source hits, while selecting five per author. For top3 these ceilings are9/12 and27/36. The full12 oracle result8/20 is therefore8/11 available top5 hits, not an unrestricted40%-accuracy estimate for every text. No model currently supplies five reliable supported centers in four authors, much less five exact Latin words with a shared correct intersection.

Oracle Case filtering removes a major source-head problem: full12 source top5 improves17→25 supported instances, count4 improves7→27. Some residual support discrimination is useful, particularly Aquinas, but source fit itself leaves Cicero/Jerome supported centers below the head. The simple count model matches or exceeds the rich model in the oracle comparison; that is a retained comparator, not permission to route each target by gold results.

## Verification and next experiment

Independent scalar logits/sigmoids reproduce2440 predictions;128 lists,208 supported rank records, source/target roles, scalar metrics, exact207 held-out and210 oracle baselines, preserved217 correction and49 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration218/`.

Next train support conditionally on **source Case-bearing centers only**, contrasting against the frozen support model trained on all centers. Use both full12/count4, unchanged ridge/equal-author weights/source-only scales and all other three authors, including Caesar's zero-positive source. Keep the target216 balanced anonymous applicability gate fixed for both ranking methods; compare top3/top5 and their applicability×conditional-support products. An explicit oracle target gate remains diagnostic only. This tests whether source training against many irrelevant non-Case negatives impairs support ranking within the intended subpopulation. Target Case/POS and support labels must remain outside fitting and deployed selection; no target-specific threshold or winner choice.
