# Paired anchor-class consistency — iteration 95

**Promising restricted finding: blind paired scoring identifies five exact class-swap pairs with zero wrong recommendations in these development probes.** It abstains on every clean/same-class control, but misses many errors. The independent-score control finds eight correct pairs with two wrong recommendations. Preserve both as a precision/coverage tradeoff, not a validated general mapping-recovery method.

## Frozen paired experiment

Keep the fixed93 binary contextual classifier, prior and three type-label permutation controls. Enumerate every present proposed ADP×CCONJ pair among the16 common candidate types; no corrupted-pair identity is supplied to the scorer. Both endpoints require at least5 occurrences across3 sentences. Source inputs have64 supported pairs; sparse author inputs have fewer. Class labels and reference pair are attached only for calibration/evaluation after scoring.

Primary joint score: hide both candidate types throughout the public input, recompute their contextual probabilities with the fixed classifier, mean probabilities separately for each type, and sum log(opposite/proposed) across the two endpoints. This is an equal-type-weighted consistency score; it is not a normalized likelihood of the whole text. The independent control sums the existing93 single-type-masked scores. Prior and three permutation models use the jointly masked context.

At most one supported pair can be recommended: the unique highest gain above threshold; near ties abstain. This avoids opaque-ID-dependent tie selection. Calibrate thresholds only on source-calibration clean and the known in/et swap, enumerating all attainable nonnegative gains plus0 andOFF. Require zero clean false pair recommendations (a pair changes two types, so the earlier at-most-one-false-type rule implies zero false pairs). Maximize the known exact-pair hit, then minimize corrupted wrong-pair proposals, tie higher threshold. Freeze every arm before evaluation.

Joint threshold0.6174674057358475 and independent threshold0.4894962208942862 both identify the known calibration pair without a clean proposal. All prior/permutation policies selectOFF. One synthetic calibration error is very little evidence; the thresholds have no formal transfer precision guarantee.

Feature generation computes only the selected token rows but is tested against the original full-public feature interface. Masking preserves opaque equality IDs. A scorer may receive cached records containing unused evaluation flags, but never reads them; audit removes those flags and all private POS/dependency fields and independently rekeys IDs without changing semantic pair scores. There is no hidden-identity-dependent model routing.

## Exact-pair outcomes

| Dataset | Scenario | True pair supported | Joint recommendation | Joint result | Independent recommendation | Independent result |
|---|---|---|---|---|---|
| source | correct | n/a | — | abstain | — | abstain |
| source | rehearsed_in_et | yes | — | abstain | et / atque | wrong pair |
| source | unseen_ad_que | yes | que / ad | correct | que / ad | correct |
| source | unseen_ad_sed | yes | ad / sed | correct | ad / sed | correct |
| source | unseen_de_que | yes | — | abstain | que / de | correct |
| source | unseen_de_sed | yes | sed / de | correct | sed / de | correct |
| source | same_adp | n/a | — | abstain | — | abstain |
| source | same_conjunction | n/a | — | abstain | — | abstain |
| Jerome | correct | n/a | — | abstain | — | abstain |
| Jerome | rehearsed_in_et | yes | in / et | correct | in / et | correct |
| Jerome | unseen_ad_que | no | — | abstain | ad / de | wrong pair |
| Jerome | unseen_ad_sed | no | — | abstain | — | abstain |
| Jerome | unseen_de_que | no | — | abstain | — | abstain |
| Jerome | unseen_de_sed | no | — | abstain | — | abstain |
| Jerome | same_adp | n/a | — | abstain | — | abstain |
| Jerome | same_conjunction | n/a | — | abstain | — | abstain |
| Caesar | correct | n/a | — | abstain | — | abstain |
| Caesar | rehearsed_in_et | yes | in / et | correct | in / et | correct |
| Caesar | unseen_ad_que | yes | — | abstain | ad / que | correct |
| Caesar | unseen_ad_sed | no | — | abstain | — | abstain |
| Caesar | unseen_de_que | yes | — | abstain | que / de | correct |
| Caesar | unseen_de_sed | no | — | abstain | — | abstain |
| Caesar | same_adp | n/a | — | abstain | — | abstain |
| Caesar | same_conjunction | n/a | — | abstain | — | abstain |

Across the24 correlated scenarios, joint scoring recommends5correct/0wrong pairs: source ad/que, ad/sed, de/sed, plus in/et on Jerome and Caesar. There are15 injected cross-class error scenarios, nine with a fully present/supported true pair; the primary rule catches5/15 overall or5/9 supported. These ratios mix repeated word pairs and reused datasets and are not independent-sample confidence estimates. Zero observed wrong pairs among five proposals is not a precision guarantee.

All nine clean/same-class controls abstain under joint and independent scoring. Independent finds8correct/2wrong overall: its false pairs are et/atque for source in/et, and ad/de for Jerome ad/que where que is absent. The latter pair can have opposite proposed classes despite both original words being prepositions, illustrating why class-consistency alone must not be called lexical identity recovery. Every prior/permutation control remainsOFF.

## Ranking and coverage bottlenecks

Joint source de/que is correctly ranked first but its gain0.5788 misses the frozen0.6175 cutoff. Source in/et ranks second (true0.5384 versus best0.6048), and the rule safely abstains. On Caesar, joint ad/que and de/que rank second; both best gains stay below the cutoff. Independent scoring ranks both true Caesar que pairs first and accepts them, but also makes the two wrong recommendations elsewhere. Do not select a different threshold or the independent arm from these target results.

Jerome que is absent and sed lacks the minimum support; Caesar sed lacks support. Those error pairs count as misses, not successful abstentions. Lowering support after seeing those examples would be another experiment. Pair-rank diagnostics and all candidate gains are preserved.

## Interpretation and next step

Paired class comparison can use relative evidence even when the two independent flags do not both fire, addressing a weakness seen in94. It produces an exact two-endpoint class-swap recommendation without receiving the corrupted pair. The task still assumes a single bijective ADP/CCONJ class swap among supplied candidates. Same-class lexical swaps, missing/non-bijective mappings, several simultaneous errors and unknown dictionary candidates remain unsolved. No new lexical nuclei, blind anchor discovery or full grammar restoration is claimed.

Preserve the primary rule as an experimental high-abstention option; retain the independent control and its errors. Next perform a frozen shadow PP integration: apply every primary recommendation, swap the two public anchor assignments without consulting reference correctness, and rerun the existing fixed PP policies. Compare against uncorrected and original clean inputs, include all abstentions and controls, and record both recovered coverage and any newly damaged assignments. This is proposed, not performed here; it would test downstream grammatical value rather than declaring adoption from exact-pair counts.

This uses the same cached source/Jerome/Caesar development sets; no new annotation, reserve or sealed-test evaluation. No actual mappings were changed in stored prior artifacts and no PP inference was altered this iteration.

Validation: all26 calibration/evaluation scenarios and six arms replayed; no reference pair used by scorer; private-annotation/truth-flag removal and ID-rekey invariance verified; all source policies and rank diagnostics replayed;2,551 prior frozen-input hashes verified;97 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration95/.
