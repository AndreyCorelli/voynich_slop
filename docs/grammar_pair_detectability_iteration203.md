# Individual-pair versus aggregate detectability — iteration203

**Some local evidence exists, but much less than the pooled association suggests.** Under the frozen per-author maximum-statistic correction, only1/1/0/2 development pairs pass the.05 threshold for Aquinas/Caesar/Cicero/Jerome. Aggregate mean surplus passes the same fixed one-sided tail threshold in all four texts. This supports preserving the contextual association while rejecting the idea that every positive residual is a reliable individual constraint.

The result does not prove that other pairs lack real structure: maximum-statistic correction can be conservative, these samples offer limited observations, and199 permutations give.005 tail resolution. It also does not provide an annotation-free way to identify the detected pairs; significance here uses gold Case/POS and is an evaluation diagnostic, not an inference input.

## Frozen test

Reuse193 development graphs,201 Case/POS profiles and analytic surplus labels, and unchanged201/202 predicted lists plus explicitly gold-oracle lists. No Dante, reserve annotations, new raw projection, model fit or selection change enters this run. Freeze all108 list groups before null computation.

For each of199 seeds20300–20498, independently permute Case—including missing values—within every opaque word×POS bucket. Edge statistic is unconditional frame-macro recognized-Case matching minus its fixed analytic profile expectation, exactly as in201. Compute both its raw tail and a corrected tail against the maximum surplus over **all edges in that author** for every permutation. Use `(1 + count(null >= observed - 1e-12))/200`, fixedalpha.05 and strictly positive observed surplus>1e-12. These are conditional exchangeability-baseline tails; the maximum correction accounts for searching the author's graph under the joint null, not universal correctness probabilities or automatic strong error control under arbitrary partial alternatives. No correction across the four authors is claimed.

## Local and aggregate results

| Author | Graph pairs | Positive residuals | Raw local detections | Max-stat local detections | Detected endpoint types | Aggregate mean surplus | Aggregate tail |
|---|---:|---:|---:|---:|---:|---:|---:|
| Aquinas |565|141|18|1|2|.073410|.005|
| Caesar |51|10|2|1|2|.034774|.025|
| Cicero |93|19|2|0|0|.039176|.005|
| Jerome |300|50|5|2|3|.051335|.005|

The four corrected edge detections have surplus/tail:

- Aquinas edge353: .750538 / .035, two shared frames.
- Caesar edge9: .782609 / .010, three shared frames.
- Jerome edges7 and232: both.768421 / .015, two shared frames each.

The Jerome pair detections share an endpoint (three types total); they are not two independent confirmations. All correlations induced by shared word/POS Case profiles remain in each joint permutation. No exact word identity or named case is inferred by the model.

Across all1,009 pairs,769 have zero sampled null variance, coinciding here with the zero-residual count; do not interpret finite-sample zero variance as a proof about all possible permutations. Only220 pairs have positive residual and20 negative. The201 supervision therefore contains a large profile-trivial component, and a positive label is still weaker than localized permutation evidence.

## What existing selectors retain

| Fixed top-ten policy | Aquinas detections | Caesar detections | Cicero detections | Jerome detections |
|---|---:|---:|---:|---:|
|196 rich ranker, copied in201 |0|0|0|0|
|201 rich surplus selector |0|0|0|0|
|202 augmented surplus selector |0|1|0|0|
|202 augmented applicability selector |0|0|0|0|
|201 gold-surplus oracle — evaluation only |1|1|0|2|

The3-feature surplus control also selects Caesar's one corrected detection. Several twenty-pair lists contain it; none of the predicted top10/20 lists contains the Aquinas or Jerome corrected detections. Every list, including controls, ties and oracle headroom, remains in the artifacts. The oracle finds10 positive residuals per author but only1/1/0/2 corrected detections: “positive surplus exists” substantially overstates the present supply of individually supported constraints.

Thus two bottlenecks coexist: few pairs meet this stringent local evidence test, and the current selectors generally miss those that do. This is neither evidence that the whole signal is noise nor proof that a better anonymous selector is impossible. It is not the desired five nuclei in four texts, general POS restoration or a reliable list of named grammatical anchors.

## Next proposal: structurally defined bundles

Before training another point scorer, test pooling **ego bundles** defined without annotations: for each endpoint word type, group all graph edges incident to it. Reuse the203 observed/null surplus matrices, preserving their correlations. This does not assert transitive Case equality or assign one Case/POS to an entire word type.

Freeze three statistics: sum and mean of incident-edge surplus, plus a primary robust sum after dropping the largest edge contribution (equivalently the minimum sum over all single-edge deletions). The robust statistic uses degree≥2 bundles and is evaluated with the same nonlinear operation in every null. It asks whether support persists beyond one favorable edge, while sum/mean are explicit comparators rather than target-selected alternatives. Shared occurrence evidence can still be redundant; report overlap and degree, not independent counts.

For each statistic, correct against its per-author maximum over all eligible endpoint bundles, using the same.05 tail rule and all non-detections. Report endpoint-type coverage and which bundles are supported beyond individual-edge detections. These remain oracle evidence-localization diagnostics, not a deployable selection algorithm or exact word recovery. If pooling adds stable support, it motivates learning bundle-level grammar; if not, sample size or a different representation deserves priority over more local feature additions.

## Verification and artifacts

Independent count-product scoring replays all1,009 observed edges and200,791 permuted edge scores, preserving every word×POS Case profile. All raw/corrected tails, null means/variances/maxima, aggregate summaries and108 fixed-list groups are reconstructed, including the invariant that adjusted tails never undercut raw tails. All47 input/selection/prior-manifest hashes pass. Dedicated audit passed; no broad project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration203/` contains frozen design/proposal/lists, all null surplus matrices, every edge's observed/null/tail detail, aggregate and list summaries, audit and verification manifest. Code: `benchmarks/grammar_pair_detectability_iteration203.py` and `benchmarks/grammar_pair_detectability_iteration203_review.py`.
