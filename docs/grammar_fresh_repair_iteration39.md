# Iteration 39: fresh confirmation of frozen candidate repair

The frozen contextual repair improves eight-class grammatical tagging on fresh sentences, especially with severe candidate deletion. It does **not** preserve the 1% spoil allowance in every condition: severe-deletion Jerome exceeds it. Mild-deletion Caesar shows no clear benefit. This confirms a limited repair mechanism, not restoration of grammatical structure.

## Frozen design

Before fitting, declare 100 previously unused sentences per author in treebank order: first 60 background, last 40 queries. Queries contain 304 Jerome and 566 Caesar tokens. All 200 IDs are disjoint from prior declaration/truth files and the separate 200-sentence reserve; reserved records are skipped before token annotations are parsed. Anonymous word IDs and ending groups are invariant under rekeying.

Keep iteration28's oracle development chain fixed; do not estimate it from fresh labels. Keep iteration35's outside-mass flag thresholds and iteration38's selected budgets: contextual K2 proposals use 0.10, random K2 proposals 0.05. Both use the same flagged word inventory, but the budgets differ, so this is a comparison of frozen policies rather than an isolated proposal-quality ablation. No fresh background labels calibrate thresholds or budgets.

Oracle support is generated from class occurrences across the fresh corpus. Each word receives one randomly added, reference-unattested candidate; one true candidate is deleted from 10% or 50% of types, using five frozen perturbation seeds. This is privileged candidate metadata, not a usable unsupervised retrieval system. Background and query observations are fitted transductively. The unchanged source class chain is also privileged. Sentence boundaries are supplied.

Fit normalized word and ending baseline emissions with 1% class-independent fallback. Freeze cavity flags and contextual/random proposals before fitting repairs. Only new candidate pairs receive an optimized repair distribution; the full baseline emission table remains fixed as a mixture component. Five random starts per fit, maximum regularized objective selection without labels, 600-iteration cap and relative tolerance 1e-7. Gold labels enter fitting only through the explicitly privileged support construction; the fitting function itself takes no labels. Freeze predictions before evaluating query outcomes.

## Fresh query results

Accuracy and gain are percentages/percentage points. Spoil is the percentage of originally correct query tags made incorrect. Values pool five perturbations of the same 40 query sentences; these are not 200 independent sentences.

| Author | Deleted types | Baseline arm | Baseline accuracy | Context accuracy | Context gain | Context spoil | Random gain | Random spoil |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Jerome | 10% | Word | 67.11 | 68.09 | +0.99 | 0.69% | +0.46 | 0.39% |
| Jerome | 10% | Ending | 67.30 | 68.36 | +1.05 | 0.59% | +0.33 | 0.29% |
| Jerome | 50% | Word | 39.80 | 42.63 | +2.83 | **1.82%** | +1.18 | 1.32% |
| Jerome | 50% | Ending | 39.80 | 42.76 | +2.96 | **1.65%** | +1.25 | 1.82% |
| Caesar | 10% | Word | 56.40 | 56.47 | +0.07 | 0.94% | +0.00 | 0.69% |
| Caesar | 10% | Ending | 56.68 | 56.78 | +0.11 | 0.87% | +0.07 | 0.56% |
| Caesar | 50% | Word | 31.66 | 34.45 | +2.79 | 0.89% | +0.99 | 1.45% |
| Caesar | 50% | Ending | 31.87 | 34.70 | +2.83 | 0.89% | +1.27 | 1.44% |

For contextual word repair, corrections/spoils across perturbations are 22/7 and 54/11 for Jerome mild/severe, versus 17/15 and 87/8 for Caesar. Thus mild Caesar is almost pure exchange of correct and incorrect tags.

A 10,000-draw sentence-cluster bootstrap, sharing each draw across the five perturbations, gives contextual gain intervals: Jerome mild word [0.32, 1.67], ending [0.40, 1.72]; Jerome severe word [1.77, 4.03], ending [1.91, 4.13]; Caesar mild word [-0.29, 0.44], ending [-0.24, 0.48]; Caesar severe word [2.09, 3.67], ending [2.06, 3.72] points. These intervals condition on the frozen fitted models and five masks; they do not include model refitting or establish population risk guarantees.

## Interpretation and next diagnostic

The improvement transfers under severe support loss, while the empirical calibration spoil constraint does not transfer uniformly. Ending sharing adds little. There is no evidence here that mild-deletion Caesar benefits, and severe accuracy remains only 35–43% despite oracle candidate metadata and a privileged chain. Dependency structure and grammatical consistency were not evaluated in this iteration.

Before another tuning round, attribute the fresh failures to detection, proposal retrieval, and repair decisions using the already frozen predictions: among incorrect tags, how many were flagged, received the correct missing class, and then selected it? Separately inspect why correct tags were spoiled. This can identify whether better detection or a more conservative repair acceptance rule is justified. Any resulting tuning makes these fresh slices development data; it must not be presented as another independent confirmation. Preserve the reserved 200 sentences.

## Verification and artifacts

600/600 fits converged across 120 fit cells. All objective traces are monotone within numerical tolerance; all 160 baseline/repair decodings replay exactly. Freshness, unchanged policies and source chain, normalized emissions, and 244 frozen-input hash checks pass. The regression suite has 335 passing tests, including label-free fit behavior and fresh declaration boundaries.

Reproduce with `python -m benchmarks.grammar_fresh_repair_iteration39` (refuses to overwrite), then `python -m benchmarks.grammar_fresh_repair_iteration39_validate` and `python -m benchmarks.grammar_fresh_repair_iteration39_intervals`. Artifacts are under `experiments/results/grammar-restoration/iteration39/`: declarations, observations, explicit oracle truth, source configuration, staged freezes, complete fit traces, proposals, predictions, evaluation, intervals, and validation. Prior artifacts and the shared todo remain unchanged; reserve remains unscored.
