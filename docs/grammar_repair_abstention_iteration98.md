# Repair abstention under diverse and sparse corruption — iteration 98

**Outcome: neither tested abstention rule supports useful90% precision on sparse source calibration.** Both new policies selectOFF before evaluation. This is not an improvement in restoration: coverage is zero and every PP output remains the uncorrected baseline. The failure is already visible on source data and is not solely caused by a strict unavailable-partner guard.

## Frozen calibration

Keep the93 contextual classifier,95joint pair scorer,16 candidates and support requirements (five occurrences/three sentences) unchanged. Source calibration has829 sentences. Hash-order their IDs with the fixed cal98 prefix and create eight disjoint100-sentence blocks; the remaining29 sentences appear only in the full regime. Each of the nine datasets receives all64ADP×CCONJ swaps plus clean and two same-class controls:603 scenarios total. No target author cases select parameters.

Primary family: a shared absolute-gain threshold. Secondary family: gain threshold plus a minimum gap to the runner-up supported pair, with fixed gap grid0,0.1,0.25,0.5,1. Gain thresholds enumerate every attainable nonnegative calibration top score plus0/OFF. The runner-up is computed before gain thresholding, so an ambiguous alternative does not vanish merely because it falls below the threshold. Ties abstain; a single supported pair has no finite runner-up restriction.

A qualified policy must have at least90% empirical exact-pair precision separately on the full regime and pooled sparse regimes, with at least10 full and20 sparse recommendations. It must make zero false recommendations on clean/same-class controls and zero wrong recommendations when the true partner is absent/unsupported. These last labels are permitted only during source calibration; inference does not receive reference availability. Choose maximum total correct recommendations, then fewer wrong, smaller gap, higher gain. If no candidate qualifies, chooseOFF.

All thresholds and both policies are frozen before loading evaluation cases. Candidate occurrence counts, fixed classifier and PP models are not changed. These empirical guards are diagnostic, not formal precision guarantees; the many synthetic scenarios overlap heavily.

## Why the existing calibration did not transfer

| Calibration input | Correct recommendations at frozen95 cutoff | Wrong | Precision among recommendations | Wrong with unavailable true pair | Clean/control wrong |
|---|---:|---:|---:|---:|---:|
| full | 50 | 0 | 100.00% | 0 | 0 |
| sparse0 | 7 | 15 | 31.82% | 13 | 0 |
| sparse1 | 14 | 7 | 66.67% | 7 | 0 |
| sparse2 | 11 | 14 | 44.00% | 8 | 0 |
| sparse3 | 12 | 20 | 37.50% | 16 | 0 |
| sparse4 | 17 | 11 | 60.71% | 11 | 0 |
| sparse5 | 7 | 49 | 12.50% | 28 | 2 |
| sparse6 | 22 | 9 | 70.97% | 9 | 0 |
| sparse7 | 6 | 47 | 11.32% | 30 | 1 |

At the old0.617467 cutoff, full calibration yields50correct/0wrong. Across eight100-sentence blocks, the same rule yields96correct/172wrong (35.82% precision), including122 wrong recommendations with an unavailable true partner and three false calls on clean/same-class controls. The rows are correlated resamplings of source calibration; they are not independent confidence estimates. More context and candidate availability change together here, so this does not yet isolate the causal role of text length.

## Policy search result

| Family | Candidate policies | Meeting minimum call counts | Meeting counts and90% precision in both regimes | New selected policy |
|---|---:|---:|---:|---|
| absolute | 398 | 303 | 0 | OFF |
| margin | 1990 | 1211 | 0 | OFF |

No candidate meets the minimum calls and90% precision even before enforcing either the zero-clean-false-alarm or zero-unavailable-wrong-repair guards. Therefore dropping those strict guards alone would not rescue the tried policy families.

Descriptive calibration-only maxima, not selected policies: among candidates meeting both call-count minima, the largest sparse precision is61/112 (54.46%) for absolute gain and30/42 (71.43%) for gain+gap. The latter still makes12 wrong sparse recommendations, seven with unavailable partners. These summaries explain the failure and are not used to relax thresholds or evaluate a substitute policy.

## Frozen evaluation and downstream effects

Both newOFF policies abstain on all177error cases and all nine controls in the reused97bank. All fixed PP predictions are unchanged. No correction is credited as a successful recovery merely because abstention avoids a new error. The frozen95 control exactly reproduces97: source41correct/4wrong/14abstain, Jerome4/0/55, Caesar5/14/40.

No new PP input is generated under these selected policies; prior frozen prediction caches are reused and verified. Original85PP0.80 and augmented89PP0.71/0.80 remain unchanged. This experiment adds neither grammatical membership coverage nor new lexical nuclei. It also does not invalidate the earlier clean-anchor PP or selected conditional repair findings.

## Decision and next diagnostic

Do not loosen the guards after seeing this failure, and do not deploy a dictionary-repair step from the small95bank. In the tried families, threshold and top-two-gap calibration cannot compensate for poor pair discrimination in short samples. This is a limit of these fixed models/rules, not a proof that all abstention methods fail.

Next run a controlled source-only context-length curve (100,200,400,800sentences) with the classifier and cutoff frozen. Include a candidate-availability-matched comparison: hold the candidate set and tested error pairs constant across lengths using source-only occurrence support. That separates changing evidence per type from missing true partners and will show whether pooling more text deserves priority over new scoring or training changes. Do not choose a length or threshold from author outcomes; no reserve is needed for this diagnostic. Proposed, not run here.

Validation: all603 calibration scenarios independently replayed, including joint-mask probabilities; all candidate searches and186 evaluation scenarios replayed; deterministic source blocking and blind repair effects verified; zero new PP inferences; descriptive aggregate diagnostics checked; 4,051 prior frozen-input hashes verified;104 focused tests passed. Existing source-calibration material and prior evaluation documents are reused development data. No new annotations, reserve or sealed-test scoring. Artifacts: experiments/results/grammar-restoration/iteration98/.
