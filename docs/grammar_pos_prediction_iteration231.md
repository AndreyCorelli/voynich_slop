# Iteration231: pair compatibility does not yet improve reliable named-POS prediction

The direct downstream test is weak: source-trained node features yield12.85–33.08% type-macro top1 POS mass across five authors. Averaging over fixed compatible pairs gives small or mixed effects, including losses in Jerome. High pair agreement is therefore not sufficient to deliver named POS restoration with this predictor. Preserve the earlier relational findings separately; do not call this a reliable grammatical restorer.

## Frozen method

Predict the fixed17 UPOS categories using the existing12 anonymous node features. Train on all graph endpoints of the other three development authors, or all four for Dante; Dante is never a source. Target is the global word-POS profile. Use equal total source-author mass, uniform source-word weights within each author, source-only standardization, free intercepts and multioutput ridge minimizing half weighted squared Euclidean error plus.05 squared slope norm. Clip negative predicted components to zero and normalize. Source-prior baseline is the same author-balanced mean profile.

Use the fixed support- and rich-selected disjoint10 pair lists from227/226 or229 Dante. Average the two node probability vectors half-self/half-partner, synchronously; all other nodes remain unchanged. No target labels in prediction, averaging or pair selection; no fits, thresholds or author-specific winners after evaluation. Features, source models, all predictions and pairs are frozen before target evaluation. POS source supervision is explicit; there are no exact-word anchors.

Evaluate argmax over alphabetically sorted17 tags, retaining absent classes. Main metric is the mean true POS-profile mass of the predicted tag, weighting graph word types equally. This equals expected token correctness when independently sampling an occurrence per word; it is not hard dominant-POS word-type accuracy. Separately report accuracy on all occurrences of covered words, and graph coverage. No whole-text POS claim follows. Dante POS was consumed previously; no new raw annotation, other reserves or Seneca gold is accessed.

## Type-macro top1 POS mass

| Author | Source prior | Node model | Support-pair averaging | Rich-pair averaging |
|---|---:|---:|---:|---:|
| Aquinas |7.43%|25.09%|25.58%|25.58%|
| Caesar |20.00%|20.31%|20.31%|20.27%|
| Cicero |10.67%|28.45%|28.45%|28.45%|
| Jerome |14.32%|33.08%|32.13%|32.13%|
| Dante |5.57%|12.85%|11.57%|14.17%|

The node model exceeds the source prior, but that prior transfers poorly and is not an oracle majority baseline. Beating it is insufficient for useful recovery. Source prior predicts PRON for Aquinas/Jerome and NOUN for Caesar/Cicero/Dante; target class distributions differ. Compatible edges cannot automatically orient a mistaken cluster toward the right named class.

On the20 selected endpoints, support averaging changes type-macro mass12.30→17.29% Aquinas,29.48→29.48% Caesar,36.34→36.34% Cicero,49.56→39.56% Jerome,17.64→12.77% Dante. Rich averaging changes32.30→37.30%,20.21→20.09%,43.84→43.84%,39.29→29.29%,16.27→21.27%. These local effects explain the diluted all-graph changes; no universally beneficial pair refinement appears.

## Coverage and token-weighted results

| Author | Graph nodes / text word types | Covered tokens / admitted tokens | Node accuracy on covered tokens | Support-refined | Rich-refined |
|---|---|---|---:|---:|---:|
| Aquinas |202 /4.35% of types|16140/30000 (53.80%)|15.03%|20.42%|16.02%|
| Caesar |60 /0.90% of types|6714/27386 (24.52%)|16.15%|13.18%|13.08%|
| Cicero |75 /0.92% of types|10418/30000 (34.73%)|27.65%|27.65%|27.65%|
| Jerome |209 /3.49% of types|13263/30000 (44.21%)|33.21%|31.45%|32.34%|
| Dante |76 /1.12% of types|8277/26083 (31.73%)|7.56%|6.58%|7.90%|

Graph node counts and text word-type coverage are separate quantities in the first column. Frequent-word mistakes can dominate token accuracy even when type-macro mass improves slightly. The model predicts nothing for most text types, and no extrapolation to uncovered tokens is justified.

## Audit and next diagnostic

Independent rational profiles verify622 graph nodes, prior weights, five augmented least-squares fits, normalization, fixed pair averaging,40 metric groups and27 hashes. Newly projected Dante features are independently reconstructed; four-author features exactly reuse the audited221 projection. All pass. Artifacts: `experiments/results/grammar-restoration/iteration231/`.

Next separate incorrect **class naming** from poor **grouping**. On these unchanged predicted argmax groups, compute explicit target-gold oracle relabeling ceilings: one-to-one17-class assignment and many-to-one group purity, both type-macro and token-weighted, alongside target-majority and identity-label baselines. Keep all authors/methods, no fitted or deployed target-gold mapping. If oracle relabeling remains weak, the groups themselves mix grammatical classes; if much stronger, unlabeled grouping may still be a useful decoder input despite failed names. This is a diagnostic ceiling, not restored POS, and must not obscure the current poor direct result.
