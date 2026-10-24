# Iteration 115: pre-existing false evidence in swap recommendations

**Preserve the diagnostic: two mechanisms explain the observed wrong repairs.** Some pairs combine genuine corruption evidence with a pre-existing false signal at the innocent endpoint. Others pass despite negative evidence at that endpoint, because the other endpoint dominates the sum. This experiment changes no repair policy and adds no restoration claim.

All frozen109 and111 actions are preserved over110's complete/catalogue-omission cases and113's literal-loss cases:2211 input conditions, including all errors and controls. Selections are frozen before computing matched-clean scores. For every selected pair, the same two IDs are jointly masked in the clean and corrupted versions of exactly the same physical context, including any suffix deletion. Existing corrupt probabilities are reused from102/113; clean probabilities are computed with the frozen93 classifier. No new grammatical labels, author evaluation, PP inference, reserved data, or sealed lexical test is used.

Each endpoint receives a clean flip margin relative to its supplied correct class, and an observed margin relative to its proposed class. If corruption changes that endpoint's class, its sign change is separated from changes in contextual probabilities. Positive clean evidence at an unchanged endpoint is a false-flip signal relative to the supplied anchor-class reference. These known clean counterparts are diagnostic oracles, never proposed deployment features.

| Frozen109 wrong calls | Total | Innocent endpoint positive | Positive already in clean context | Innocent endpoint nonpositive |
|---|---:|---:|---:|---:|
| Catalogue omission |16|10|10|6|
| Literal context loss |8|5|5|3|

Every wrong call has one class-changed endpoint and one unchanged endpoint. **All15 positive innocent-endpoint signals are at `ac`; all nine nonpositive ones are at `ex`.** None of the positive innocent-endpoint signals is newly created from a nonpositive clean score by corruption. Five of five literal-loss positives and one of ten catalogue positives are numerically unchanged within1e-10; the remaining catalogue positives change in magnitude but were already positive. Thus both pre-existing model error and changes in surrounding evidence matter.

These counts are correlated probes, not24 independent failures. The16 catalogue wrong calls involve only four distinct physical-view/pair combinations; the eight literal wrong calls involve eight. For111, complete and catalogue conditions remain zero-wrong; its one literal-loss mistake is the same `ac/sed` fallback already identified, with an invariant positive `ac` signal. No additional strict-policy failure was discovered by this attribution.

Correct/wrong actions remain exactly10964/0,896/16,914/8 and11148/0,674/0,667/1 for complete, catalogue, and literal regimes respectively. All control actions remain abstentions. Correct repairs mask both corrupted endpoints, so their clean/corrupt contextual inputs coincide; attribution does not establish a new way to identify these successes blindly.

## Clean-type prevalence, without selecting only wrong repairs

With only its own type masked, the original clean input has four false-flip types out of16 supported candidates: `ac`, `c`, `aut`, `que`. All four are supplied CCONJ types. Across the original input plus16 clean deletion views,64 of266 supported type/view observations have positive false-flip scores; every one is CCONJ. These17 views strongly overlap and are not independent samples. False preference is not unique to `ac`, although only `ac` supplies positive innocent-endpoint evidence in these selected wrong pairs.

The original clean sample therefore contains systematic contextual class errors, beyond the single missing-partner case. Literal deletion can also change which supplied CCONJ types favor a flip (`atque`, `et`, or `uel` in some views). This does not prove that every grammatical use has the source modal class; the diagnosis is relative to the constant supplied anchor-class task.

A generic class-prior/intercept correction applied to each **type-mean logit** cannot fix pair ranking: adding the same offset adds it to the proposed-ADP flip margin and subtracts it from the proposed-CCONJ margin, leaving their sum unchanged. Per-occurrence nonlinear recalibration is a different intervention and is not tested here. Word-specific `ac` or `ex` exceptions are not justified.

Next: test a source-trained reliability estimate for endpoint evidence, with types held out during calibration and controls for class imbalance. It must address persistent false positives and domination by one endpoint while preserving correct-repair coverage; another global offset or an oracle clean subtraction is not a solution. Freeze source splits and coverage/unsupported-error guards before evaluating any new selector.

Verification:25 focused tests pass. The audit verifies3759 input hashes, replays4422 frozen actions, independently recomputes2249 clean endpoint scores, checks3796 selected-endpoint attributions, and reconstructs990 distinct clean pair/view inferences. Detailed endpoint scores, all selected conditions, unselected clean-type prevalence, and summaries are stored in `experiments/results/grammar-restoration/iteration115/`.
