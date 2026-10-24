# Iteration 108: combining gain, gap and stability still selects OFF

The combined source-calibrated rule does not qualify. Among 11,910 settings, 2,422 meet the call-count minima, but none reaches 90% exact-pair precision in both full and sparse source regimes, even before clean-control and unavailable-partner guards. This adds no restoration gain and leaves iteration 107's conditional representation finding intact.

## Frozen calibration

Use all 603 cached iteration-102 source-calibration cases: full 829 sentences and eight 100-sentence blocks, with sixteen candidates, 64 cross-class swaps and three controls each. Keep classifier, counts, bootstrap draws and unique-top selection unchanged. Select only when point gain, runner-up gap and sentence-bootstrap rank stability all pass.

Search attainable nonnegative top gains plus zero; gaps 0 / 0.1 / 0.25 / 0.5 / 1; stabilities 0.50 / 0.75 / 0.90 / 0.95 / 0.99 / 1.00. Retain the prior gap-None behavior for an unopposed candidate. Require 90% empirical precision in each regime, at least ten full and twenty pooled sparse calls, zero clean/same-class false calls and zero wrong repairs with an unavailable true partner. Maximize correct repairs, then fewer wrong repairs, smaller gap, smaller stability cutoff and higher gain cutoff. Freeze the selected policy before loading corrected Caesar features.

## Outcome

The best worst-regime precision with the required call counts is still the iteration-102 setting: gain 1.0596124720630975, gap zero, stability 0.75 gives full 19 correct / 0 wrong and sparse 31 / 8 (79.49%). Seven of the eight sparse errors have unsupported true partners. Adding a gap requirement does not improve this optimum.

The largest zero-wrong sparse subset while retaining ten full calls is likewise unchanged: gain zero, gap zero, stability 0.90 gives full 24 / 0 and sparse 11 / 0. Eleven calls remain below the twenty-call requirement. No guard is relaxed after inspecting these results.

The selected policy is OFF. Replay all 201 corrected iteration-107 author cases; it abstains everywhere, so every PP probability, decision and original token assignment equals the corrupted no-repair input. All original cutoffs and prior author outcomes remain available as comparators; a newly source-calibrated active rule is not claimed. No new annotation, reserve scoring, sealed lexical test, model fitting or nucleus recovery occurs.

## Verification and next diagnostic

Independently check every grid setting with vectorized masks, refit calibration identically, replay all author interventions and independently verify their PP confusion counts against cached score arrays. The audit verifies 2,313 input hashes, 11,910 independent policy checks, 201 author actions, 1,206 confusion-count checks and 65 unchanged cached prediction payloads. Both new tests pass. The new tests cover a constructed case where neither two-component rule can reject both error types but the joint rule can, and a clean-control case that must force OFF despite high precision. Artifacts and the frozen tracker/design are in `experiments/results/grammar-restoration/iteration108/`.

Next test the assumption that one operating point must serve both context volumes. Calibrate a short-context and a long-context policy separately, retaining each regime's existing precision, call-count, clean and unavailable-partner guards. Route only within the source-observed bands (at most 100 sentences or at least 829); abstain between them. Freeze routing and policies before author replay. This is a distinct conditional-policy experiment, not a claim that iteration 108 passed its shared-policy requirement. Raw segment counts do not guarantee reliable per-type evidence; the rare `uel` failures remain a relevant challenge.
