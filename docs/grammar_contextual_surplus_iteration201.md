# Development contextual-surplus supervision — iteration201

Changing the target alone is **not a general repair** with the existing19 anonymous features. Rich surplus regression improves Cicero, but Aquinas loses Case-applicable/positive-surplus pairs, Caesar has negative mean selected surplus and Jerome selects no positive-surplus pairs. Preserve the200 contextual association; do not adopt this selector as a reliable way to extract it.

## Frozen design

Use the four non-sparse193 development authors (Aquinas, Caesar, Cicero, Jerome), excluding each target from fitting/scaling and retaining the same other-three source policy and source-weighted scales as196. Project only their admitted Case/POS references; no Dante, Seneca or other reserved text/reference enters this experiment. Inputs remain the existing19 rich or3 frequency/support anonymous features.

For each edge, average over its shared frames the mean across all Cartesian comparisons of observed recognized-Case equality minus its analytic expectation under word×POS Case profiles. Profiles include missing Case, with missing matches contributing zero. Different endpoint words have independent shuffle buckets, so the expectation is the sum over recognized cases of the two profile probabilities' products. This is an unconditional joint-match residual, different from the earlier conditional equality/joint-yield metrics, and avoids random conditional denominators. Zero surplus is not evidence of context-dependent agreement.

Train equal-author ridge regression: half weighted mean squared error plus.1/2 slope norm squared, unpenalized intercept; no tuning. Reuse196 matched pointwise/ranking outputs as controls. Freeze all learned models/outputs/tiedtop10/20 before metric aggregation; source/held-out labels are procedurally cached but held-out labels never enter fitting, scaling or predicted selection. Gold-surplus oracle lists are evaluation-only headroom, constructed after prediction freeze; no oracle is a method.

## Rich top-ten results

Mean surplus is measured on the new unconditional frame-macro scale. Positive means greater than1e-12.

| Held-out author | Previous ranker mean / positive pairs / applicable pairs | Surplus regression mean / positive pairs / applicable pairs |
|---|---:|---:|
| Aquinas |.067776 /5 /7|.067818 /2 /2|
| Caesar |−.002814 /3 /8|−.006400 /3 /9|
| Cicero |.108691 /6 /9|.123815 /7 /10|
| Jerome |.060000 /1 /9|.000000 /0 /9|

Each list contains ten. Aquinas's negligible mean gain accompanies substantial coverage loss; Cicero is the sole clear joint improvement on these primary measures. Frequency/support surplus regression is also mixed: top-ten mean/positive counts Aquinas0/0, Caesar.152216/4, Cicero.102644/6 and Jerome.023810/1; Jerome retains14 tied candidates, not ten. All20-pair lists, negative/zero counts, Case equality/joint yield/type costs and classifier controls remain in artifacts.

There is target headroom: the four graphs contain141/10/19/50 positive-surplus edges out of565/51/93/300, respectively. Gold top10 reaches ten positives for each author with means.702/.294/.372/.563. This only shows that potentially informative comparisons exist; it neither demonstrates their anonymous predictability nor justifies using gold profiles at inference. Oracle top20 can expand to22/48/91/20 candidates because ties are retained.

## Next feature diagnostic

Freeze a compact block describing queried shared slots themselves: anchor frequencies, slot count/fanout/entropy, pair occupancy/balance/comparison support, distinct anchors and pair context overlap. These use only anonymous token counts, not target POS/Case. The existing19 features deliberately exclude queried occurrences from context distributions, so it is plausible—but not proved—that they omit relevant local structure.

Compare the existing19 versus19+fixed slot block under both ordinary Case-applicability classification and surplus regression, with source-author exclusion, balancing, ridge and datasets unchanged. This factorial diagnostic separates a feature effect from an objective effect; keep simple controls and all authors visible, no target-selected feature subset or winner, and no Dante retuning or fresh-validation claim.

## Verification

Independent rational arithmetic replays all1,009 edge labels from122,846 admitted integer-row references. Four analytic expectation checks agree with199 word×POS permutations per author within the predeclared Monte Carlo tolerance. Independent augmented least-squares refits verify all8 regressions and source-only scales/gradients, with16 exact copied baseline outputs and all60 metric/oracle groups replayed. All62 input/freeze/baseline hashes pass; no reserve input is used. Dedicated audit passed; broader tests were not run.

Artifacts: `experiments/results/grammar-restoration/iteration201/`; code `benchmarks/grammar_contextual_surplus_iteration201.py` and `benchmarks/grammar_contextual_surplus_iteration201_review.py`.
