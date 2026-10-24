# Iteration 60: raw versus POS-normalized role probabilities

Removing POS normalization does not materially improve typed-unit restoration. The raw lexical condition changes full-source F1 **56.86%→56.91%** relative to the frozen baseline, with selected-sentence F1 unchanged at **64.85%**. Raw POS evidence improves one selected copular unit but loses four correct units overall. Keep the baseline; normalization is not the main bottleneck exposed by these tests.

## Controlled ablation

Freeze all ten iteration-59 role proxies, iteration-57 head scores/candidates and iteration-56 endpoint outputs. No model is refitted and no target changes. Use the same five source partitions, 519 selected gold units and 3,365 across source, with the same single ambiguous-frame exclusion.

Compare the previous normalized evidence with:

```
raw head evidence = log P(non-dependent | context)
raw type evidence = log P(carrier role | context)
```

Direct still maps to proxy class `other`; cop/aux use their corresponding classes. Clip probabilities at 1e−6, exactly as before. The only formula change is removing subtraction of the POS-prior log probability. There is no hard mask or added confidence gate.

For POS-context and lexical-context proxies, recalibrate head-only, type-only and joint weights on the unchanged grids 0, 0.5, 1, 2, 4. Selection is the same unique exact-unit calibration objective with true endpoints supplied and conservative tie-breaking. Zero remains an explicit control. Actual pipeline metrics use frozen predicted endpoints, including their mistakes.

All 30 normalized calibration policies and their active decisions reproduce iteration 59. Thus the comparison isolates normalization rather than changed fitting, calibration data or endpoint behavior. This follow-up was proposed after inspecting iteration-59 contrasts, so it remains development evidence, not fresh confirmation.

## Calibration and pipeline results

Raw lexical head weight 0.5 is selected in folds zero, two and four; the other folds select zero. Raw lexical type weights are always zero. Joint calibration chooses exactly those head-only settings.

Raw POS type weight 0.5 is selected only in fold one; all head weights are zero. Its joint condition therefore equals type-only. No raw joint setting activates both additions. The small nonzero calibration gains are one or two exact units per affected fold.

| Setting | Selected correct / wrong | Selected F1 | Full-source correct / wrong | Full-source F1 |
|---|---|---:|---|---:|
| Frozen baseline | 346 / 202 | 64.85% | 2,098 / 1,917 | 56.86% |
| Normalized lexical joint | 346 / 202 | 64.85% | 2,096 / 1,919 | 56.80% |
| Raw POS type-only / joint | 347 / 201 | 65.04% | 2,094 / 1,921 | 56.75% |
| Raw lexical head-only / joint | 346 / 202 | 64.85% | 2,100 / 1,915 | 56.91% |

Raw POS head-only and raw lexical type-only select zero everywhere and reproduce the baseline. All normalized controls reproduce their earlier outcomes; every ablation is retained in the artifacts. Output counts remain 548 selected units and 4,015 across source.

The raw lexical joint setting changes 49 full-source unit predictions: nine become correct and seven previously correct units become wrong, for a net gain of two. On selected sentences it changes two wrong predictions into other wrong predictions, leaving exact metrics unchanged. The raw POS joint setting adds six correct outcomes and removes ten across source; selected results add one correct and remove none.

## Predicate-type regressions

| Full-source gold kind | Baseline exact | Raw POS joint | Raw lexical joint |
|---|---:|---:|---:|
| Direct, 2,423 gold | 1,690 | 1,681 | 1,695 |
| Copula, 650 gold | 259 | 264 | 255 |
| Auxiliary, 292 gold | 149 | 149 | 150 |

The lexical condition's small aggregate gain does not solve the intended copular problem: it loses four exact copular units while gaining five direct and one auxiliary unit. The POS condition gains five copular units but loses nine direct units. Selected copular recovery changes seven→eight for raw POS and remains seven for raw lexical.

With true endpoints supplied, raw lexical changes exact units 2,870→2,872/3,365, but copular exact units 316→312/650. Raw POS changes the overall conditional count to 2,865 while copular exact units rise to 322. Conditional discrimination and actual pipeline effects are both small and mixed; neither justifies selecting a universal replacement on these results.

## Interpretation and next proposal

The higher pairwise ordering accuracy of raw probabilities in iteration 59 did not translate into a meaningful pipeline gain after calibration. Normalization affects which addition receives weight, but neither tested score form reliably realizes the phrase-role oracle headroom. Keep both variants as recorded experiments, without enabling a new default or spending more tuning effort on their normalization.

A more focused next test is **type-balanced training of the actual unit scorer**. Current source unit counts are 2,423 direct, 650 copular and 292 auxiliary; the fitting and calibration objectives emphasize the frequent direct class. That is a hypothesis about the remaining tradeoff, not established by this ablation.

Compare the original and type-balanced losses with the same features/candidates. Give both models the same calibration of role-specific score offsets, including zero, to distinguish better head ranking from a changed type prior. Report micro and per-type/macro performance, true-type head ranking diagnostics, and the frozen-endpoint pipeline. No gold role may enter inference. This proposed control is not tested here.

All evidence is still on reused Cicero/Palladius development data with readable Latin and supplied POS, not independently confirmed grammar restoration on ciphertext.

## Artifacts and checks

Code: `src/voynich_smt/raw_role_evidence.py`, `benchmarks/grammar_raw_role_evidence_iteration60.py` and its `_audit` module. Policies, full grids, predictions and per-kind changes are frozen under `experiments/results/grammar-restoration/iteration60/`. Existing output directories are rejected.

The benchmark replays 30 normalized policies, 44,286 active normalized decisions, 29,524 zero-weight decisions and 608 proxy mutation checks. Independent audit checks 20 hashes, reselects all 60 policies, replays 424,200 prediction fields, reproduces 52 metric groups and all 28 previous metric groups, and verifies unchanged prior fields. Four new tests cover raw probability formulas, the isolated normalization difference, clipping without deletion and calibrated type recovery; 78 relevant tests pass. No models are refitted. Previous artifacts remain intact; the 200-sentence reserve remains unscored, with no prior target queries scored.
