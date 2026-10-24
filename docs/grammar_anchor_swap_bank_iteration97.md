# Complete remaining-swap bank — iteration 97

**The larger challenge overturns the zero-wrong impression from the small bank.** Frozen joint scoring finds41correct/4wrong pairs on source,4/0Jerome, and5/14Caesar. The source-only repair signal is substantial, but the current rule is not reliable across authors and should not be adopted as a general correction step. The five successful earlier repairs remain valid conditional examples.

## Frozen bank and pipeline

Start with the same source-fit-defined16 candidate types:8ADP×8CCONJ gives64 possible cross-class swaps. Exclude exactly the five previously tested cross-class pairs (in/et, ad/que, ad/sed, de/que, de/sed), leaving59 newly tested error pairs. Add clean, ad/de andque/sed controls for each dataset:62×3=186scenarios, including177cross-class error probes. No pair is selected using its outcome.

Keep the93class models, all six95pair policies, five-occurrence/three-sentence support requirement and tie-abstention rule fixed. Enumerate all candidate pairs in each corrupted public input; neither the injected pair nor reference classes select the recommendation. Apply every recommendation, including wrong ones. Rerun original85 PP0.80 and augmented89 PP0.71/0.80; no training, calibration, threshold changes or reference-correctness gates.

PP predictions are cached only within a fixed dataset, keyed by its public type assignments. Dataset positions/equality groups remain fixed. Compact score arrays, reconstructible public deltas and prediction freezes preserve every unique inference; no repair is evaluated from counts alone. Other supplied anchors remain a privilege.

The cached source/Jerome/Caesar texts have been reused in development; the59 error-pair configurations are new probes, not fresh independent documents. Repeated word pairs and overlapping tokens make the scenarios correlated. The task still assumes one injected bijective ADP/CCONJ swap, not unknown vocabulary or arbitrary dictionary error. No reserve, sealed lexical test, new annotation or lexical search.

## Pair recommendations

| Dataset | Arm | Correct pairs | Wrong pairs | Abstentions | Precision among recommendations | True pair supported |
|---|---|---:|---:|---:|---:|---:|
| source | joint_context | 41 | 4 | 14 | 91.11% | 59/59 |
| source | independent_context | 42 | 8 | 9 | 84.00% | 59/59 |
| Jerome | joint_context | 4 | 0 | 55 | 100.00% | 5/59 |
| Jerome | independent_context | 4 | 3 | 52 | 57.14% | 5/59 |
| Caesar | joint_context | 5 | 14 | 40 | 26.32% | 21/59 |
| Caesar | independent_context | 6 | 18 | 35 | 25.00% | 21/59 |

All prior/permutation policies remainOFF. Both context rules make no recommendation on all nine clean/same-class controls. Clean false-alarm success therefore does not ensure correct repairs after an error: an injected error can make a different, incorrect partner look best.

Primary joint scoring totals50correct/18wrong/109abstentions across177correlated error probes. These totals are descriptive, not independent trials or a precision guarantee. Source correct-pair coverage is41/59 (69.49%), while precision among its45recommendations is91.11%. Caesar precision is only5/19 (26.32%); the result fails the intended cross-author reliability claim.

## Missing and unsupported partners

| Dataset | Reference-pair state | Cases | Correct | Wrong recommendation | Abstain |
|---|---|---:|---:|---:|---:|
| source | supported | 59 | 41 | 4 | 14 |
| Jerome | present_unsupported | 32 | 0 | 0 | 32 |
| Jerome | absent | 22 | 0 | 0 | 22 |
| Jerome | supported | 5 | 4 | 0 | 1 |
| Caesar | present_unsupported | 16 | 0 | 5 | 11 |
| Caesar | absent | 22 | 0 | 5 | 17 |
| Caesar | supported | 21 | 5 | 4 | 12 |

Ten of Caesar's14wrong recommendations occur when the true pair is absent or unsupported; four occur even when it is supported. Every selected pair itself passes the existing support requirement. Thus the failure is not fixed by checking support of the selected pair: the decoder can choose a supported substitute when the real partner is unavailable. Reference-pair availability is known only for this diagnostic and cannot be used as an oracle repair filter.

Jerome has22cases with an absent endpoint and32with present but insufficiently supported endpoints; only5true pairs are supported. Its4correct/0wrong result has very low overall coverage and is not broad author robustness. Caesar has two swaps with zero affected tokens because both endpoints are absent; these are retained and reported rather than credited as detection successes.

Wrong source recommendations repeatedly substitute atque for the true partner. Wrong Caesar recommendations repeatedly involve per or aut. This indicates structured class/ranking confusion as well as sparse evidence; missing support alone does not explain the errors. All wrong recommendations and their PP effects are preserved in wrong-repairs.json.

## Downstream grammatical effects

All50primary exact-pair hits reproduce their clean PP decisions, and all primary abstentions preserve their uncorrected decisions. Larger-bank losses remain visible. For original PP0.80:

| Dataset | New correct decisions | Lost correct decisions | New wrong decisions | Removed wrong decisions | Cases with net correct loss | Cases with net wrong increase |
|---|---:|---:|---:|---:|---:|---:|
| source | 1767 | 197 | 185 | 1538 | 4 | 6 |
| Jerome | 42 | 1 | 0 | 70 | 0 | 0 |
| Caesar | 94 | 50 | 27 | 44 | 0 | 5 |

These are summed decision changes across repeated perturbations of the same tokens, not counts of distinct restored words. Correct repairs can also recover ordinary baseline false positives or remove accidentally correct corrupted predictions, so clean restoration does not mean every individual flip improves gold accuracy.

Concrete wrong-repair damage: source ex/ac changes349correct/34wrong→349/38; source sine/atque changes348/42→347/41. Caesar ab/ac changes68/5→68/6; per/et70/6→71/8. Other wrong repairs improve some PP counts despite leaving the dictionary wrong. Aggregate grammatical gains cannot certify mapping correctness.

Augmented0.71 and0.80 policies, hidden-token effects, clean-decision differences and frozen nearest-left F1 are all preserved for every case. No target-selected model or cutoff replaces the predeclared primary. Inactive controls are retained, and the independent arm's higher coverage comes with more wrong recommendations (8source,3Jerome,18Caesar).

## Decision and next bottleneck

Keep the source-only conditional repair signal, but withdraw any implication that the small bank's zero wrong recommendations established reliable correction. Do not use this rule as a default or move to the untouched reserve. The current calibration saw one known in/et error in a large source-calibration set and constrained false proposals only on clean input; that does not constrain wrong-partner recommendations after diverse errors or under sparse author evidence.

Next calibrate abstention against diverse corrupted-source examples, including fixed100-sentence source blocks that create missing/unsupported partners, and explicitly penalize wrong repairs there. Keep correct-mapping controls and an unrepaired/NONE option. Freeze the policy before any new evaluation and compare against the current absolute-gain threshold; do not pick a support limit or margin from these Caesar outcomes. This is the next hypothesis, not an implemented fix.

Validation: all186scenarios and six detector arms replayed; 426 unique PP model/input predictions replayed; complete59-pair bank verified against the source inventory and prior exclusions; blind actions, public ID preservation, caching, all token-loss metrics and aggregate summaries verified; 2,860 prior frozen-input hashes verified;101 focused tests passed. Artifacts: experiments/results/grammar-restoration/iteration97/.
