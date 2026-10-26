# Iteration228: tie-robust structural enrichment is not universal

Shared-context support robustly enriches endpoint-disjoint pair compatibility in Aquinas and Cicero, with positive paired differences against random selection in all199 runs. Jerome is positive but variable; Caesar is the counterexample. Preserve a conditional structural selector, not a reliable four-text result or a per-pair confidence guarantee.

## Frozen check

For seeds22800–22998, one generator visits Aquinas/Caesar/Cicero/Jerome and shuffles edge indices. Use the resulting random priorities only within exact score ties for each of the four227 rankings; use the same priorities alone for a uniform-edge-order greedy matching control. Greedily select disjoint10/20, keeping the word-disjoint restriction in every method/control. Freeze every list before gold compatibility evaluation. No fitting, selected direction, new annotation, raw text, reserve or author-specific winner.

Mean/min/max and5th/95th quantiles describe algorithmic tie-order sensitivity. Paired positive fractions are not label-null p-values, statistical confidence levels or independent trials. The random-matching baseline is important because disjoint selection changes the edge/word sampling distribution relative to whole-graph means.

## Shared-support disjoint10

| Author | Mean compatibility | Range across tie orders | Uniform matching mean | Mean paired gain | Runs beating paired uniform |
|---|---:|---|---:|---:|---:|
| Aquinas |66.84%|49.10–79.16%|23.46%|+43.38pp|199/199|
| Caesar |50.72%|44.56–64.65%|49.11%|+1.61pp|112/199|
| Cicero |83.75%|78.23–93.82%|38.26%|+45.49pp|199/199|
| Jerome |74.92%|58.62–79.17%|53.56%|+21.36pp|175/199|

The prior single edge-index tie-break is not a stable point estimate: for example Aquinas was59.14%, now mean66.84% with a broad range. Caesar's modest benefit against whole-graph44.24% largely disappears against the more appropriate disjoint-control49.11%. Tie-order repeats do not rescue that author's claim.

## Shared-support disjoint20

| Author | Mean compatibility | Uniform matching mean | Runs beating paired uniform |
|---|---:|---:|---:|
| Aquinas |55.70%|25.45%|199/199|
| Caesar |45.88%|49.63%|25/199|
| Cicero |61.12%|38.95%|199/199|
| Jerome |76.08%|55.70%|194/199|

Caesar becomes worse than random on average at20. No request shortfalls occur in any of the7960 lists across methods, controls, authors and seeds. This is failure of selection quality, not inability to construct enough disjoint pairs. Its conservative graph is sparse and score ties are broad; that is a possible mechanism to investigate, not justification to relax rules only for this author.

## Other fixed rankings

Jaccard disjoint10 mean53.12/46.75/70.30/85.08% across Aquinas/Caesar/Cicero/Jerome; positive paired fractions99.50%,38.19%,100%,98.49%. Frequency-low Jerome mean87.69% beats its paired control193/199 times, while frequency-high is weak in Caesar/Cicero/Jerome. Keep all these outcomes without selecting a different winner per author. A model chosen after looking at target gold would not be a transferable selector.

Useful structural POS-compatibility preferences survive changes to arbitrary word-ID-related ordering in some authors. They do not infer a named POS, restore words/nuclei, establish calibrated edge confidence or yield the desired consistent four-text demonstration. Global-profile compatibility and context independence limitations remain unchanged.

## Audit and next step

Independent RNG/priority, greedy endpoint matching,7960 lists,40 summary groups, quantiles/paired differences and19 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration228/`.

Next evaluate the unchanged selector family on the additional already-admitted Dante graph, retaining all methods rather than routing by author. Train any learned comparator on all four existing development authors only; freeze features, models and predictions before reading Dante's cached POS reference. Include the fixed support method and count/rich comparators, tied and disjoint10/20 plus the same199 tie-order controls. Dante Case/POS was consumed in199/200, so this is an additional-author development transfer test, **not a fresh sealed holdout**. Keep Seneca labels sealed and do not relax graph eligibility to manufacture coverage. This adds a transfer check before more local tuning of the four repeatedly used authors.
