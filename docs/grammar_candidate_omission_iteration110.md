# Iteration 110: missing repair candidates expose false fallback calls

The frozen long-context rule makes **16 false substitute repairs in 128 cases where a true endpoint is omitted** from the repair pool: a 12.5% false-call rate in the unavailable-partner stratum. It remains correct in all 896 omission cases where the true pair remains available. Overall omission precision is nevertheless 98.25%, showing why pooled precision cannot replace an explicit availability guard.

This is a source-only stress diagnostic, not a new restoration policy. Iteration 109's conditional author finding is preserved with this boundary made explicit.

## Frozen exhaustive omission test

Take all 67 full-source cases from iteration 102: 64 cross-class errors and three clean/same-class controls on the same 829 sentences. For each, evaluate the complete sixteen-candidate pool and every single-candidate omission, independent of which type is actually wrong. This gives 1,139 views: 67 complete controls and 1,072 omission views.

Remove only the cached pair-score/bootstrap columns containing the omitted opaque ID. Keep all text tokens, public context assignments, occurrence probabilities, point gains, count eligibility and 256 resamples unchanged. Recompute the unique winner, runner-up gap and rank stability against the remaining competitors. Do not automatically abstain when the original winner is omitted. Attach the true-pair support flag after blind selection; keep the true-pair reference and all error cases.

This isolates repair-catalogue availability. It is not literal deletion of a word from the text or loss of its contextual anchor features, so it is an approximation to the author-side absence mechanism.

Primary rule: unchanged iteration-109 long-context gate (gain 0.354845920096932, gap zero, stability 0.50). Secondary control: unchanged iteration-95 point-gain cutoff 0.6174674057358475 without a stability gate. No refitting, author scoring, PP integration, new classifier predictions, annotations, reserve scoring or lexical test access occurs.

## Results

| Stratum | Cases | Long rule: correct / wrong / abstained | Old point cutoff: correct / wrong / abstained |
|---|---:|---:|---:|
| Complete pool, all cases | 67 | 64 / 0 / 3 | 50 / 0 / 17 |
| Omission, true pair available | 896 | 896 / 0 / 0 | 700 / 0 / 196 |
| Omission, true partner unavailable | 128 | 0 / 16 / 112 | 0 / 15 / 113 |
| Omission, clean/same-class controls | 48 | 0 / 0 / 48 | 0 / 0 / 48 |

All omission views together give 896 correct / 16 wrong (98.25% recommendation precision), compared with 700 / 15 (97.90%) under the older cutoff. The long rule gains 196 correct recommendations and one net additional wrong recommendation, while failing the zero-unavailable-wrong guard. It is not globally worse than the older cutoff; its failure is specifically unsafe fallback in some unavailable-partner cases.

The 896 available-pair successes are not independent new confirmation: the original full pool already selects all 64 true pairs. Removing an unrelated competitor preserves their point gains and cannot reduce their bootstrap winning frequency. The informative new condition is the 128 endpoint omissions, two per original error pair. Alternative views reuse the same source text and probability arrays.

## Mechanism and reciprocal-evidence diagnostic

Wrong long-rule calls occur under omissions of twelve different candidate types; this is not an isolated `c` problem. The complete wrong-action list and per-omitted-type counts are retained. Two recurring substitutes are `ac` and `ex`. Some wrong pairs compensate for a negative endpoint margin using a stronger positive margin at the other endpoint; others have both endpoint margins positive because the class model itself is imperfect.

A descriptive sign audit rejects the obvious hard reciprocal rule as a low-cost fix:

- Of 64 correct complete-pool repairs, 34 have at least one nonpositive endpoint flip margin. Requiring both margins to be positive would retain only 30.
- Of sixteen false omission repairs, seven have a nonpositive endpoint. The same condition would still retain nine false repairs.
- Across omission views, that condition would retain 420 correct / 9 wrong, versus the current 896 / 16. It discards more than half the correct calls and does not eliminate false substitutes.

This is an exact sign decomposition of saved predictions, not calibration or adoption of a new gate. It does not rule out every calibrated endpoint model, but it argues against simply imposing positivity at both ends.

## Verification and next experiment

Independently replay all 1,139 rankings and stability estimates, 3,482 endpoint-margin checks and 252 aggregate count fields; verify 1,743 input hashes. Retain all 128 unavailable-partner error views and 48 control views. Both new omission tests pass, including a missing-true-partner case that must expose a wrong fallback rather than force an artificial abstention. No classifier inference or policy refit was required. Artifacts and the frozen tracker/design are in `experiments/results/grammar-restoration/iteration110/`.

Next calibrate the existing gain/gap/stability rule against these source-only omission negatives. Keep the old grids, require complete-pool coverage and coverage across distinct original omission cases, and enforce zero clean-control and unavailable-partner false calls before author replay. Do not choose an omission type or threshold from the six inspected author failures. This adds missing negative examples rather than a word-specific exception. Independent confirmation and true word-absence/context-loss stress remain separate future requirements.
