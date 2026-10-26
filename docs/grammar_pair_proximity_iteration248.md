# Iteration 248: proximity partly survives, but full-basis embeddings erase it in sparse graphs

**A concrete representation failure is now identified:**70/145 eligible half-graphs use the entire unweighted eigenbasis. This makes all distinct node distances equal, leaving no proximity information for k-means. It affects every eligible Caesar, Cicero and Dante half-graph and one Jerome half. It does not explain all failures: Aquinas loses coverage despite mostly preserved proximity, while Jerome loses proximity in many available cases.

This is a diagnostic on selected original full-text pairs, not a new grammatical accuracy result. No POS labels, raw text, reserves, tuned distance cutoff or changed extraction rule were used.

## Frozen measurement

Use the same corrected pre-k-means representation: all zero Laplacian modes plus17 positive modes, extending a tied boundary to its complete eigenspace, then row-normalizing. Graphs below17 nodes remain ineligible rather than receiving a relaxed representation. Reconstruct all five full graphs and190 fixed random-half graphs from the previously frozen artifacts.

For each original iteration238 pair, rank its squared Euclidean distance against all unordered node pairs in that graph. Closeness is `1 - (strictly closer pairs + half the tied pairs) / total pairs`, with fixed absolute tie tolerance1e-10. Larger is closer relative to that graph. Missing endpoints or ineligible geometry score zero unconditionally; their conditional rank is undefined. Retain every pair, author, split and half; save dimension, zero-mode and tie diagnostics. Full and half ranks use different node universes, so comparisons are descriptive.

## Selected-pair proximity

| Author | Original pairs | Full-text mean closeness | Available half pair-cases / all | Conditional half mean | Conditional half median | Missing/ineligible-as-zero mean |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |7|99.43%|159/266|97.05%|99.23%|58.01%|
| Caesar |1|99.77%|4/38|50.00%|50.00%|5.26%|
| Cicero |1|99.55%|8/38|50.00%|50.00%|10.53%|
| Jerome |15|99.03%|388/570|55.67%|95.42%|37.89%|
| Dante |0|Undefined|0/0|Undefined|Undefined|Undefined|

These percentages are **distance-rank scores, not grammatical precision, POS accuracy or recovery percentages**. Original pairs were selected by the full-text pipeline, so high full-text ranks are not independent validation. Aquinas's original list also includes the known wrong PRON/NOUN pair; proximity alone cannot certify grammar.

Aquinas retains strong conditional proximity on average, with a few large failures and substantial missing coverage. Jerome's high conditional median but much lower mean exposes a mixture: some old relations remain near neighbors, while many cease to be close. Hard clustering is therefore not the only lost-information stage, though it may further fragment the surviving proximity. The full per-pair distributions and both-half minimum scores remain in `summary.json`; no favorable subset is selected.

## Why full-basis saturation matters

| Author | Eligible half-graphs | Full-basis half-graphs |
|---|---:|---:|
| Aquinas |38|0|
| Caesar |7|7|
| Cicero |34|34|
| Jerome |38|1|
| Dante |28|28|

When the selected eigenvector matrix is the full orthonormal basis U, `U Uᵀ = I`. Row norms are one, and every distinct pair has squared distance2. Including all modes with equal weight therefore removes all graph-specific distances, regardless of the graph's actual edges. Tied boundary expansion can cause this even when nominally requesting only17 positive directions. The independent audit verifies this collapse in all70 saturated graphs; every available Caesar/Cicero pair has a100% distance tie and closeness0.5.

This is a property of the representation, not an eigensolver failure. It explains why some small eligible graphs cannot support meaningful partition geometry. It is not a complete explanation for Jerome, where37/38 eligible half-graphs are not saturated, or Aquinas, where none is. Missing endpoints and other representation/partition changes remain material.

## Next proposed modification

Test a **fixed diffusion-weighted embedding** instead of equal-weight truncated modes: use every eigenvector with weight `exp(-lambda/2)`, corresponding to a normalized heat-kernel Gram matrix `exp(-L)` at fixed time1. Row-normalize as before. Keep the graph, eligibility, all original pairs, all full/random-half cases, rank definition and missing-case accounting unchanged; do not scan diffusion times or select a favorable author.

Different eigenvalues then contribute different weights even when every mode is retained, so complete-basis inclusion no longer automatically produces identity geometry. First compare the same continuous proximity diagnostic with iteration248 and independently reconstruct the heat kernel by matrix exponentiation. This tests the identified representation defect before rerunning strict-core extraction or claiming a restored grammatical constraint. It cannot restore absent graph endpoints, and any later extraction gain still needs matched controls and gold-free group confidence.

## Audit and artifacts

Independent SciPy evd reconstruction passed 150 eligible eigensolves, all195 graph logs, all936 pair distances/ranks/missing flags, all70 exact saturation checks, five complete aggregate/per-pair summaries and217 hash checks. The previous246/247 frozen artifacts remain unchanged. The final manifest freezes both runners, this report and all new outputs.

Artifacts: `experiments/results/grammar-restoration/iteration248/`; runner: `benchmarks/grammar_pair_proximity_iteration248.py`; reviewer: `benchmarks/grammar_pair_proximity_iteration248_review.py`.
