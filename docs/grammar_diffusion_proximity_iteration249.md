# Iteration 249: fixed diffusion weighting restores useful proximity

**HIGHLIGHT: fixed time-one diffusion removes the equal-distance collapse and substantially improves Jerome's retained-pair proximity.** Mean conditional closeness rises from55.67% to95.31%; missing/ineligible-as-zero mean rises from37.89% to64.88%. This is a promising representation change for subsequent extraction, not POS accuracy or recovered words.

## Frozen change

Use every normalized-Laplacian eigenvector with weight `exp(-lambda/2)`, then row-normalize. The resulting Gram matrix is the diagonally normalized heat kernel `exp(-L)` at fixed time1. There is no diffusion-time search, favorable-author selection or new data.

Everything else matches iteration248: all five full graphs and190 random-half graphs; graph eligibility>=17 nodes; all24 original strict-core pairs; rank against all unordered graph-node pairs; tie tolerance1e-10; explicit missing/ineligible outcomes scored zero unconditionally. Conditional ranks remain undefined when unavailable. All graph geometry and pair records are saved before aggregation, and paired comparisons retain exact case identity.

## Complete proximity comparison

The values below are mean **distance-closeness ranks**, not accuracy, precision or restoration percentages. Larger means nearer relative to other pairs in the same graph. Coverage is identical in both methods.

| Author | Available half pair-cases / all | Previous conditional mean | Diffusion conditional mean | Previous missing-as-zero mean | Diffusion missing-as-zero mean |
|---|---:|---:|---:|---:|---:|
| Aquinas |159/266|97.05%|97.04%|58.01%|58.00%|
| Caesar |4/38|50.00%|98.15%|5.26%|10.33%|
| Cicero |8/38|50.00%|98.70%|10.53%|20.78%|
| Jerome |388/570|55.67%|95.31%|37.89%|64.88%|
| Dante |No original pairs|Undefined|Undefined|Undefined|Undefined|

Among available Jerome cases,271 improve,10 tie and107 worsen; conditional median rises from95.42% to96.85%. The large mean gain reflects recovery of many previously poor cases, not uniform improvement of every pair. Aquinas has126 improved,1 tied and32 worse cases, but large opposite effects nearly cancel in the mean. Every original pair and its per-half/both-half distributions remains recorded; no winning subset is adopted.

The half-graph collapse count falls from **70/145 eligible graphs to0/145**. All150 eligible full/half graphs now have nonconstant pair distances; the45 ineligible half-graphs remain unavailable. Using all modes with different eigenvalue weights avoids the equal-weight full-basis identity. In `graph-geometry.json`, the inherited `saturated` flag merely records full dimension; `equal_distance_collapse` separately measures actual degeneracy. Full dimension is expected and no longer erases distance information.

## What this establishes and what it does not

The identified representation defect is fixable without a tuned spectral cutoff, and the selected original Jerome relations recover substantial graph proximity under the fixed alternative. Preserve this change as a promising proposed component of the algorithm.

However, original pairs were selected by an earlier full-text extractor and include known mixed or wrong relations: Caesar/Cicero's pairs were not fully pure, and Aquinas includes the PRON/NOUN error. Their high diffusion ranks demonstrate that proximity does not certify grammatical compatibility. No matched new-representation order controls, new strict-core recurrence, gold-free confidence, named POS or exact nuclei are established here. Missing graph endpoints are unchanged, so support coverage remains a separate limitation.

This is a selected-pair mechanism diagnostic on reused development data, not independent validation or a probability that a decoder constraint is correct. Dante remains consumed development, and sealed Seneca/reserves/raw annotations are untouched.

## Next frozen proposal

Rerun the **full strict-core pipeline** with only this embedding replacement, fixed time1. Include all five full texts and all190 existing random halves, keeping graph thresholds, eligibility,31 initializations,31 deletion samples, K=17 and strict intersection unchanged. Recompute diffusion geometry in every deletion graph rather than reusing the original representation.

Freeze every anonymous output and cross-half intersection before cached POS evaluation; retain every mixed/empty/unclusterable result. Report full-text and half/shared core yield, coverage, all-core profile compatibility/purity and original-pair retention against the old pipeline. No time/K/criterion scan or favorable-author selection. This checks whether the affinity repair survives hard clustering and stability requirements; any useful extraction result then needs matched order controls before decoder use.

## Independent audit and artifacts

Independent SciPy **matrix exponentiation**, rather than eigenvector weighting, reconstructs normalized kernels and distances for all150 eligible graphs. All195 geometry logs, 936 pair distance/rank/missing records, five full aggregate/per-pair summaries, paired changes and217 hash checks pass; no graph collapses. Previous246/248 artifacts remain unchanged. The final manifest freezes both runners, this report and all new outputs.

Artifacts: `experiments/results/grammar-restoration/iteration249/`; runner: `benchmarks/grammar_diffusion_proximity_iteration249.py`; reviewer: `benchmarks/grammar_diffusion_proximity_iteration249_review.py`.
