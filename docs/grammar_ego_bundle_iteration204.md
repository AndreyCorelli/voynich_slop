# Endpoint bundles and strongest-edge deletion — iteration204

**Pooling gives more localized grammatical evidence than isolated pairs.** The predeclared strongest-edge-deletion statistic detects5 word-centered bundles for Aquinas,0 for Caesar,3 for Cicero and2 for Jerome under per-author max-statistic correction. Eight of the ten detected centers are not endpoints of203's individually detected edges. Preserve this as support for changing the evidence unit, not as an annotation-free selector or recovered lexical nuclei.

The key counterexample to an edge-only view is Cicero:203 finds no corrected individual edge, yet three bundles pass the primary test. Caesar remains a limitation; the result does not supply five anchors per text or three shared exact words across four texts.

## Frozen, anonymous grouping

For every endpoint word type in the unchanged193 development graphs, group all incident word-pair edges. Construct and freeze these memberships, degree, shared-frame counts and pivot-occurrence reuse before loading203's observed/null surplus matrices. Group formation uses only anonymous graph structure. No Case/POS is predicted, and grouping does not assert that all neighboring words have one Case or even that the center has a single POS across occurrences.

Reuse203's199 jointly permuted word×POS Case-profile matrices unchanged, preserving all their dependencies. Compare three statistics:

- Sum of incident-edge surplus, degree≥1.
- Mean of incident-edge surplus, degree≥1.
- **Primary:** minimum sum after any single edge is deleted, degree≥2; equivalently total minus the largest contribution.

Apply the same operation within every permutation, then compare each bundle with the per-author maximum across all eligible bundles for that statistic. Keepalpha.05, positive observed statistic>1e-12 and `(1 + exceedances)/200` tails with1e-12 comparison tolerance. The statistic families are separate; no correction across families or authors is asserted and no favorable family is selected afterward. These are conditional joint-profile baseline diagnostics with finite resolution and potentially conservative correction.

## All statistic outcomes

| Author | All endpoint bundles | Degree≥2 bundles | Sum detections | Mean detections | Primary deletion-robust detections | Primary centers additional to203 detected-edge endpoints |
|---|---:|---:|---:|---:|---:|---:|
| Aquinas |202|136|6|0|5|4|
| Caesar |60|23|0|2|0|0|
| Cicero |75|34|3|0|3|3|
| Jerome |209|112|3|0|2|1|

Caesar's two mean detections are degree-one endpoints of the same already detected edge, not new multi-edge evidence. Sum/primary success combined with weak mean results suggests accumulated evidence is useful here; it does not demonstrate high average edge purity or an inference-time method for choosing these centers.

The primary detections have:

| Author | Incident-edge degrees | Unique queried pivot occurrences | Distinct incident edges across detections | Edges shared between detected bundles |
|---|---|---|---:|---:|
| Aquinas |21,34,21,52,20|56,43,27,116,21|140|8|
| Cicero |5,2,7|26,5,16|11|3|
| Jerome |12,6|11,13|18|0|

Rows preserve opaque-word sort order; none is selected by a gold word identity. Detected bundles overlap, and edges can repeatedly use the same pivot occurrence: use/unique-occurrence ratios reach5.30 in these detections. Joint permutations retain that dependency, but deleting one edge does not necessarily remove the shared annotation observation responsible for several edges.

The primary statistic passes its calibrated worst-single-edge-sum test; this is not a claim that separately recalibrating every fixed edge-deletion hypothesis would give the same detections. Nor does it establish independence between bundles or test robustness against removing a pivot occurrence.

## Meaning for the restoration goal

The previous contextual association is not merely a whole-graph average: it can be localized to some structurally defined bundles, including three Cicero centers invisible to the corrected individual-pair test. This is a promising granularity hypothesis for future grammatical learning. It remains an **oracle evidence-localization result** because Case/POS annotations are used to compute surplus and null tails; only the group definitions are annotation-free.

No model currently identifies these groups reliably without those annotations. Do not equate ten detected center types across three authors with ten restored words, count overlapping bundles as independent confirmations, or call this the four-text nucleus milestone. No Dante or other reserve data are read and no existing model output or selected list is changed.

## Next robustness test: central-occurrence reuse

Reconstruct each bundle sum as the sum of contributions from its distinct pivot occurrences. Each comparison contributes its recognized-Case-match residual weighted by the original edge's frame/Cartesian denominators; do not renormalize after deletion. This representation must reproduce the old edge-sum statistic exactly.

Freeze a primary statistic equal to the minimum remaining sum after removing either one whole incident edge or one whole pivot-occurrence contribution: total minus the larger of the largest edge contribution and largest pivot contribution. Use degree≥2 and at least two unique pivots; keep the existing edge-only statistic and a pivot-only counterpart as explicit comparators. This tests the two single-deletion operations, not simultaneous deletion of an edge and a pivot. Apply identical operations under the reproduced203 joint permutations and the same per-author max-statistic correction, retaining all losses/non-detections.

If the detections survive, the case for bundle-level learning strengthens; if they collapse, the evidence is too concentrated to treat edge multiplicity as robust support. This remains reference-only robustness, not a predictive model or fresh validation.

## Verification and artifacts

Independent review reconstructs all546 anonymous endpoint bundles, membership/degree/frame/pivot-use diagnostics,1,397 observed statistic groups and278,003 null statistic groups. It implements the primary statistic by explicitly enumerating every edge deletion rather than using total minus maximum, and replays maxima/tails/detections/overlap exactly within numerical tolerance. All19 input/bundle-freeze/prior-manifest hashes pass. Dedicated audit passed; no broad project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration204/` contains frozen design/proposal/memberships, detailed statistics/tails for every candidate, all null bundle statistics, overlap/summaries, audit and integrity manifest. Code: `benchmarks/grammar_ego_bundle_iteration204.py` and `benchmarks/grammar_ego_bundle_iteration204_review.py`.
