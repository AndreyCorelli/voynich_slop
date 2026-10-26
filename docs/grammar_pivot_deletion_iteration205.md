# Bundle robustness to a central occurrence — iteration205

**All ten previously supported bundles survive the central-occurrence deletion test.** The predeclared combined edge-or-pivot statistic detects7 Aquinas,0 Caesar,3 Cicero and3 Jerome bundles, retaining all5/0/3/2 from204 and adding2/0/0/1 under the recalibrated null. This strengthens pooling as a way to localize contextual Case evidence; it remains gold-reference evaluation, not an annotation-free grammar predictor or exact word recovery.

## Frozen test and decomposition

Keep193 development graphs,201 word×POS Case profiles,204 anonymous memberships and203's199 joint permutations. Freeze all305 centers with at least two incident edges and two distinct queried pivot occurrences before reference projection. No raw/new/reserved annotation, model output or source choice changes.

For a comparison between positionsi,j within edgee/framef, use original weight `1/(number_of_frames(e) × count_a(f) × count_b(f))`. Its residual contribution is that weight times observed recognized-Case match minus its analytic word×POS-profile match expectation. Sum all terms involving a given central position across all incident edges to obtain that pivot occurrence's contribution. The sum of pivot contributions must reconstruct the sum of edge residuals for the real text and every permutation.

Profiles, graph and denominators stay fixed: deletion removes a weighted contribution without renormalizing or re-estimating profiles. This is an influence/robust-statistic test, not rebuilding the text/model after deleting a word. Test three predeclared statistics on the same eligible centers:

- Edge only: total minus largest edge contribution, exactly reproducing204.
- Pivot only: total minus largest pivot-occurrence contribution.
- **Primary, edge or pivot:** total minus the larger of those two maxima; equivalently the minimum remaining sum under either single-deletion operation.

The primary test does not delete an edge and a pivot simultaneously. Apply the same operation to every reproduced203 permutation, including all word×POS Case-profile dependencies. Compute raw and per-author maximum-over-eligible-bundles adjusted tails at the fixed.05 threshold, with1e-12 ties and positive-statistic requirements. Statistic families/authors remain separate; no favorable family is selected after inspection.

## Results

| Author | Eligible bundles | Edge-only detections | Pivot-only detections | Primary edge-or-pivot | Previous204 retained / lost | Primary gained |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |136|5|5|7|5 /0|2|
| Caesar |23|0|0|0|0 /0|0|
| Cicero |34|3|3|3|3 /0|0|
| Jerome |112|2|3|3|2 /0|1|

Although the primary observed statistic cannot exceed either comparator, its **null distribution and correction threshold also change**. The combined null maximum can decrease enough to add detections; detection sets need not be nested. No extra observations were added, and the three gains are not three independent new confirmations. Aquinas's new detections have adjusted tails.050/.045, and Jerome's.030; finite199-permutation resolution remains relevant.

The primary detections span:

| Author | Incident-edge degrees | Unique queried pivot occurrences |
|---|---|---|
| Aquinas |27,21,34,21,52,20,13|32,56,43,27,116,21,22|
| Cicero |5,2,7|26,5,16|
| Jerome |8,12,6|11,11,13|

Order follows opaque center IDs. Shared edges/observations and overlapping bundles still exist; this test only establishes survival of the specified single-deletion statistic under the conditional null. It does not prove independent support, robustness against every larger deletion, named Case/POS labels or reliable unseen-text selection.

## Implication and next experiment

The204 pooling finding is not explained away by one reused central occurrence: its original ten detections all survive both the pivot-only and primary tests. That is a useful structural evidence unit to preserve. Caesar still has no primary detections, however, and none of these oracle evidence tests tells a decoder which bundles to trust without Case/POS annotations.

Next test **single-context matches as evidence inside bundles**, on development data only. Keep the frequency≥5 endpoint universe and source text unchanged; compare the existing two-context edge graph with all word pairs sharing at least one valid lexical-neighbor frame. Do not call a one-frame pair a reliable constraint by itself. Pool only anonymous centers with at least two incident edges, two distinct shared frames and two queried pivot occurrences, using the same combined edge-or-pivot statistic and full word×POS-profile null procedure.

Recalibrate maxima over all eligible centers for each graph, preserve the old graph as an exact comparator, and report every author, retained/lost/new centers, overlap, occurrence reuse and whether Caesar's coverage improves. No target-chosen frequency/support threshold, statistic, source subset or gold-derived grouping; no Dante/Seneca evaluation or claim of a new predictor. This tests whether the edge-level two-context requirement discards weak observations that become useful only when pooled robustly. If it adds usable support, bundle-level supervised selection can be tested afterward against frequency/degree controls; it is not assumed to work.

## Verification and artifacts

Independent scalar code reconstructs305 bundles'11,367 weighted comparison terms using rational profile probabilities, replays the same word×POS Case assignments and checks61,000 real/null pivot-sum reconstructions. It explicitly enumerates edge/pivot deletions rather than using the runner's maxima formula, and replays all statistics, corrections and retained/lost/gained sets. All36 input/candidate-freeze/prior-manifest hashes pass; a separate full comparison reproduces all305204 edge-only rows/tails. No model fitting or reserve input is used; dedicated audits passed without a broad project-suite claim.

Artifacts: `experiments/results/grammar-restoration/iteration205/` contains frozen design/proposal/candidates, comparison blueprints, all pivot contributions, observed/null statistics, detailed tails/transitions, independent audits and integrity manifest. Code: `benchmarks/grammar_pivot_deletion_iteration205.py`, `grammar_pivot_deletion_iteration205_review.py`, `grammar_pivot_deletion_iteration205_baseline_review.py`.
