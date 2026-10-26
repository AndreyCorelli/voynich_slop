# Within-author ranking objective — iteration196

**A modest objective-specific improvement, not a general repair:** rich pairwise ranking gives7/10 applicable shortlisted pairs for Aquinas and9/10 for Jerome, versus6/10 and8/10 for matched-source classification. Caesar stays8/10 and Cicero9/10. The simpler control still gives10/10 for Aquinas under either matched objective, so the richer ranker is not a universally preferred model. All results are reused development-author diagnostics; no exact word identities, named cases or new reserved validation are obtained.

## Frozen comparison

Reuse iteration193's opaque graphs,19 context/frequency features and case-reference scores. For each target author, exclude it from training. A source can supply ranking contrasts only if it has both positive and negative candidate pairs, where positive means at least one recognized-case occurrence comparison in shared frames. This admits Aquinas, Caesar, Cicero and Jerome when they are not the target; Palladius has only one negative example and Tacitus no candidates. No target outcome determines source eligibility.

Compare three fixed pipelines, each with the rich19 and frequency/support3 columns:

- Original193 pointwise classifier, including its original source policy.
- Matched pointwise classifier using exactly the contrast-eligible training authors.
- Within-author pairwise logistic ranker using those same authors and scaling.

Both matched pipelines use equal total source-author weight, the same source-only row-weighted mean/standard deviation and .1 slope ridge. The ranker averages `log(1 + exp(-(x_positive - x_negative) · beta))` over all positive×negative pairs within each author, then averages authors. It has no intercept because an intercept cancels in contrasts. All model settings are fixed; all model outputs are frozen before target metric aggregation. Raw rank scores are not probabilities and receive no.5 threshold, NLL, Brier or calibration interpretation. Top10/20 retain exact boundary ties; all six authors remain reported.

## Top-ten applicability

| Held-out author | Original rich | Matched pointwise rich | Pairwise rich | Original control | Matched pointwise control | Pairwise control |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |5/10|6/10|7/10|9/10|10/10|10/10|
| Caesar |8/10|8/10|8/10|8/10|8/10|8/10|
| Cicero |9/10|9/10|9/10|9/10|9/10|9/10|
| Jerome |9/10|8/10|9/10|6/11|6/11|6/11|
| Palladius |0/1|0/1|0/1|0/1|0/1|0/1|
| Tacitus |0/0|0/0|0/0|0/0|0/0|0/0|

The11-pair control lists retain ties. Palladius/Tacitus are still too sparse to support restoration performance claims. No row-dependent model choice is adopted.

| Held-out author | Matched rich AUC | Pairwise rich AUC | Pairwise rich applicable endpoint types | Conditional case equality | Joint yield across all ten |
|---|---:|---:|---:|---:|---:|
| Aquinas |.7770|.8042|10|100%|70%|
| Caesar |.9232|.9216|15|93.06%|74.44%|
| Cicero |.9283|.9235|9|77.78%|70%|
| Jerome |.6065|.6102|12|100%|90%|

Pairwise rich top20 contains13/20,17/20,17/20 and17/20 applicable pairs, respectively. Conditional case equality is not applicability precision, and neither output identifies a named case or direct dependency. This run adds no new within-word-profile null control for equality. Although the four non-sparse texts now all have at least7/10 under one common rich ranking pipeline, this is not four-text exact nucleus restoration or an unbiased accuracy estimate after many development probes.

## What the comparison establishes

Aquinas's original5→7 gain divides into one extra applicable pair from changing source eligibility and one from changing the objective on matched sources. Jerome's8→9 matched gain restores the original193 count rather than surpassing it. The comparison therefore supports retaining ranking as a candidate modification while rejecting an explanation based solely on the pooled classifier's loss. It improves some lists but does not dominate the simple control or all-author AUC; the same .1 penalty on a different loss is a fixed comparison, not proof that either objective has been optimally tuned.

Ranking source evidence remains highly correlated: for example, the Aquinas fold has24,553 contrasts made from only445 source edges, not24,553 independent grammatical observations. Across folds there are five distinct eligible source sets. The196 source eligibility removes the sparse-source mass problem, but previous194 removal effects were mixed; do not infer a universal sparse-source repair from this experiment.

## Next proposal: check whether the reserved Seneca material is usable

The next informative step is **label-blind admission/coverage for reserved Seneca**, before more tuning on these same development outcomes. Freeze the193 normalization, MWT rejection, punctuation/sentence boundaries, word-frequency floor and two-shared-frame rule. Compare normalized FORM sentences with all admitted development texts for exact duplicates and verbatim12-word overlap, without decoding Seneca Case/POS fields; remove matching reserved sentences by the frozen rule and retain provenance/counts. Do not relax eligibility to create a favorable graph. Report fewer than ten candidates as insufficient for the planned top-ten benchmark, not as model failure or success; keep empty graphs visible.

Prepare a later one-shot evaluation protocol with all four matched pointwise/pairwise rich/control variants trained on the same four eligible development authors and frozen before opening reserved labels. No winner is selected using Seneca. This preparation does not itself authorize an unfrozen reserved-label analysis, and the current run opens no reserves. Seneca has consistent recorded provenance/licensing declarations; UDante's declaration discrepancy remains unresolved and its reserve remains untouched. Earlier raw-author exposure means “reserved” concerns new annotations/current models, not guaranteed globally unseen literature. Coverage/deduplication is necessary before making a held-out restoration claim.

## Verification

Independent review reconstructs every fold's source eligibility/evidence, source-only scaling and all positive-negative contrast indices. It refits12 pointwise and12 pairwise models with Newton's method, checks objectives/gradients and outputs, and replays all72 shortlist metric groups, scalar AUC/classification metrics and contrasts. All24 original/matched pointwise model/output replays match193/194 exactly. The959,870 contrast rows enumerated across rich/control/folds are repeated correlated comparisons, not independent samples. All54 input/freeze/prior-manifest hashes pass; no new raw text or reserved annotations are read. Dedicated audit passed; the broader project suite was not run for this isolated diagnostic.

Artifacts: `experiments/results/grammar-restoration/iteration196/` contains frozen design/proposal, source trials, models/raw scores, selected pairs, summaries/contrasts/details, audit and verification manifest. Code: `benchmarks/grammar_within_author_ranking_iteration196.py` and `benchmarks/grammar_within_author_ranking_iteration196_review.py`.
