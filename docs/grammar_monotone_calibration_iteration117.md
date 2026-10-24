# Iteration 117: scalar calibration helps classes, not the repair veto

**Preserve two findings.** A simple class-balanced scalar calibration improves the new model's class predictions on the eight reused evaluation types, from4/8 to7/8. But no tested scalar calibration makes the endpoint veto safe with adequate coverage; a calibration-only dominance certificate shows why this veto cannot succeed with the existing scalar scores.

The experiment reuses116's13 training types, disjoint eight calibration/eight evaluation types, frozen class model, contextual masks, and restricted eight-candidate repair banks. It adds no new class-model training, text, annotations, authors, PP predictions, reserve access, or lexical test access. Evaluation types were already inspected in116; this is developmental evidence, not fresh confirmation.

## Three small monotone calibrations

Each calibration maps raw mean probability `p` to `sigmoid(logit(p)+b)`, with slope fixed at one and just one fitted intercept. The convex type-level negative log likelihood is solved by bisection; repair outcomes do not fit the intercept.

- `offset13`: equal weight for each of the13 out-of-fold training types.
- `balanced13`: the same13 types, with equal total weight for ADP and CCONJ.
- `offset8`: the eight volume-matched calibration types. This secondary arm uses calibration labels for both probability calibration and subsequent veto selection; it is not an independently calibrated model.

All maps preserve the raw ordering. Veto cutoffs are chosen on calibration types only, using the unchanged116 precision, zero-unsupported-error, and80%-coverage requirements. All maps and cutoffs are frozen before117 evaluation predictions are computed. A type-mean intercept still cancels in the original summed pair score; here it is applied only to an endpoint-specific veto.

| Eight evaluation types | Class accuracy | Mean negative log likelihood | AUC |
|---|---:|---:|---:|
| Raw |50%|.7881|.9375|
| Equal-type offset13 |50%|.7093|.9375|
| **Class-balanced offset13** |**87.5%**|**.5826**|.9375|
| Calibration-type offset8 |87.5%|.5821|.9375|

The balanced training-only intercept is1.40742; it does not use either catalogue type pool's labels for fitting. On the eight calibration types it gives6/8 correct versus4/8 raw. Thus useful ordering survives without116's unstable six-feature calibrator. The eight-type evaluation and overlapping contexts remain too small for a general reliability claim. This is binary function-class inference, not exact lexical identity or expanded clean PP coverage.

## No qualifying repair veto

All three arms select OFF. No existing repair policy is changed. The separate evaluation baseline remains10/0 complete,61/0 catalogue,62/0 literal; there are no baseline mistakes in this evaluation fold, so it cannot show independent false-repair rejection.

A calibration-only oracle considers every lower raw-score threshold for desired CCONJ and every upper threshold for desired ADP. Any global monotone mapping followed by this common weaker-endpoint cutoff induces such two thresholds. The oracle uses the known calibration outcomes and is **never evaluated as a deployment policy**.

| Calibration regime | Baseline correct / wrong | Maximum safe correct retained | Required correct retained |
|---|---:|---:|---:|
| Complete |14 /0|4|12|
| Catalogue omission |84 /2|24|68|
| Literal loss |91 /2|26|73|

All224 threshold combinations are enumerated; none qualifies. There are135 explicit domination witnesses:10 complete,60 catalogue,65 literal correct repairs have desired-class scores no easier to accept than an unsupported wrong call. Accepting any of those correct repairs must accept a forbidden mistake under this veto family. The best safe thresholds simultaneously attain the remaining4/24/26 correct calls, so these are exact bounds for this fixed bank and selector family.

The wrong calls are `ac/sed` fallbacks. For example, after `sine` deletion, the innocent `ac` has raw CCONJ probability.168583, below the genuine ADP `de` at.168663. A threshold willing to flip `de` back to ADP cannot reject flipping that innocent `ac` back to ADP based on this scalar alone. The paired `sed` score is also sufficiently favorable. High aggregate class AUC therefore does not guarantee separation of the rare cases the repair gate must distinguish.

This ceiling applies only to the existing scalar score, fixed proposals, fixed contexts, and global monotone/weaker-endpoint veto. It does not rule out new contextual information, reranking, other repair objectives, or grammatical restoration more broadly. Raising a cutoff, fitting another scalar monotone map, or adding a word exception does not solve this particular coverage problem.

Next: validate the frozen class-balanced scalar model as a **class predictor** on cached source-test text, without refitting or using reserved annotations. This tests the positive class-inference finding directly rather than asking it to satisfy a repair gate whose scalar-score ceiling is now established. Further repair work needs information beyond this scalar; masking and training-type-budget effects remain candidates for a separate controlled test.

Verification:29 focused tests pass. The audit verifies15 input hashes, independently refits all three intercepts, replays61 calibration cutoffs, checks423 calibrated type probabilities and ordering, independently enumerates224 oracle settings, and verifies135 dominance witnesses. Artifacts are in `experiments/results/grammar-restoration/iteration117/`.
