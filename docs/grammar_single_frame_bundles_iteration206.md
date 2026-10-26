# Single-context evidence inside robust bundles — iteration206

**Expansion helps Aquinas but is not a general improvement.** With all other settings fixed, corrected bundle detections change7→12 for Aquinas,0→0 for Caesar,3→2 for Cicero and3→1 for Jerome. Keep the conservative two-context graph as the foundation for the next predictive test, while preserving the Aquinas gain as a corpus-specific observation. No graph policy is adopted per author using these gold outcomes.

## Frozen graph comparison

Use exactly the same193 four development streams, normalized words, punctuation/sentence boundaries and frequency≥5 endpoint universe. Build every word pair sharing at least one valid lexical-neighbor frame. Its subset with at least two shared frames must reproduce the existing graph exactly. Group all incident edges around each anonymous word type, requiring at least two edges, two distinct shared frames and two pivot occurrences in **both** views. A one-context pair is never treated as a reliable standalone constraint.

Freeze both graphs and all memberships before loading201 Case/POS references. Reproduce the same203199 word×POS-preserving Case permutations. Use205's combined statistic unchanged: total edge surplus minus the larger of the largest edge contribution and largest pivot-occurrence contribution, with original edge/frame/Cartesian weights and no renormalization. Recompute per-author maximum-statistic correction over every eligible center in each graph, fixedalpha.05/positive statistic/tolerance1e-12. No target-chosen threshold, statistic, source, feature or winner; no Dante/reserve data or new annotations enter the experiment.

## Coverage and supported centers

| Author | Two-context edges | One-or-more-context edges | Eligible bundles: old→expanded | Supported centers: old→expanded | Retained / lost / gained |
|---|---:|---:|---:|---:|---:|
| Aquinas |565|4,305|136→437|7→12|7 /0 /5|
| Caesar |51|1,280|23→271|0→0|0 /0 /0|
| Cicero |93|1,787|34→273|3→2|1 /2 /1|
| Jerome |300|4,568|112→416|3→1|1 /2 /0|

All five additional Aquinas centers were already eligible under the old graph; new observations within their bundles strengthen their test result rather than merely introducing previously absent center types. Cicero's one gain is newly eligible. Adding more candidate comparisons changes both observed statistics and null maxima/test families, so fewer detections do not by themselves identify whether dilution, negative residuals or a correction change caused the loss.

The expanded detected bundles have11–92 distinct queried contexts for Aquinas,13/27 for Cicero and15 for Jerome. Their central-occurrence reuse ratios reach9.29 for Aquinas and7.13 for Jerome; joint permutations and the pivot-deletion statistic retain those dependencies, but neither makes detections independent. No new text observations were collected: “expanded evidence” means additional comparisons extracted from the same annotated streams.

Caesar remains without a supported robust center despite a25-fold edge-count increase. This blocks any claim that the one-frame change repairs the missing fourth text. The result also does not infer a center's exact word identity, POS or named Case; all support tests still use gold profiles.

## Interpretation

The204–205 finding survives: coherent bundles can localize Case-related structure, and their original detections survive a single pivot/edge influence test. The206 extension is a mixed optional hypothesis, not a reliable default. In particular, the larger graph is not automatically a better unit for learning merely because it provides more edges or teacher labels in one text.

The remaining practical gap is an **annotation-free bundle selector**. Further adjusting graph weights against these same gold tests would not close that gap. Test a small predictor before another evidence-policy change, using the original two-context graph to keep the teacher labels and inputs fixed.

## Next predictive pilot

Freeze the205 combined-test detection as a supervised source label on the conservative graph; it yields7/0/3/3 positives among136/23/34/112 eligible centers. Each target author is excluded from all fitting/scaling. Case/POS/tails are used for source labels and evaluation only, never as target features. This is a development pilot, and even a perfect prediction of this label would not decode which Latin word the center represents.

Use twelve fixed anonymous features: log word frequency; log1p bundle degree, distinct shared frames and queried pivots; occurrence reuse; queried-pivot/global-frequency fraction; mean log partner frequency; mean log1p partner degree; normalized left, right and joint-context entropy; joint-context unique fraction. Context distributions come from the full valid lexical-neighbor occurrences without Case/POS. Compare full12 with a learned frequency/degree/frame/pivot4 control, and label-free frequency-only/degree-only rankings. Fixed source-author-balanced logistic loss with.1 slope ridge and source-only standardization; no hyperparameter/feature/source selection.

Report tied top3/top5 (matching the earlier small-anchor goal), all positive-label recall/precision and ranking outcomes for every author. Preserve Caesar's zero-positive target and the three-positive ceilings for Cicero/Jerome, including undefined AUC rather than dropping such cases. Do not call the teacher's p-value a prediction confidence or declare exact nuclei/POS restored. If anonymous features cannot select these teacher-supported units better than frequency/degree, keep that failure explicit; bundle evidence localization alone is not a decoder.

## Verification and artifacts

Independent code rebuilds11,940 expanded edges via per-word context-set intersections, checks every old graph exactly, and replays2,388,000 real/null edge scores with count-product Case arithmetic. It reconstructs all1,702 eligible view bundles and340,400 pivot-sum identities, all original205 two-frame statistics/tails/detections and all graph transitions/shared-edge counts. Every word×POS Case profile is preserved. All29 input/graph-freeze/prior-manifest hashes pass. Dedicated audit passed; no broader project-suite run is claimed.

Artifacts: `experiments/results/grammar-restoration/iteration206/` contains frozen design/proposal, compressed expanded graphs/memberships, view indices, compressed edge/component matrices, detailed tails, summaries/transitions, independent audit and integrity manifest. Code: `benchmarks/grammar_single_frame_bundles_iteration206.py` and `benchmarks/grammar_single_frame_bundles_iteration206_review.py`.
