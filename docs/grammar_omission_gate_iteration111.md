# Iteration 111: omission negatives justify a stricter selective repair branch

Calibration against generic candidate-omission negatives selects a stricter long-context rule. On its source calibration bank it gives **48 correct / 0 wrong complete-pool repairs and 674 correct / 0 wrong omission-view repairs**, covering fifty distinct original error cases. On Caesar it gives **15 correct / 0 wrong primary repairs and 25 / 0 Civil repairs**; every selected author repair affects the query and restores clean PP probabilities.

This is not new author performance beyond the earlier strict branch: its added-context actions exactly match iteration 107's gain-gap branch. The advance is a source-calibrated full-bank justification including unavailable-partner negatives. It sacrifices substantial coverage relative to iteration 109's 46 / 3 primary result. Preserve both tradeoffs; do not declare the stricter branch a universally better default.

## Frozen source-only selection

Use all iteration-110 source views: 67 complete-pool cases and 1,072 views formed by omitting each of sixteen repair candidates from every case. Keep context tokens, classifier scores, all error references, counts and bootstrap arrays fixed. The omissions change only candidate availability, not actual words or context features. This remains reused calibration data, not independent source validation.

Search nonnegative attainable top gains plus zero, the existing gap grid (0 / 0.1 / 0.25 / 0.5 / 1) and stability grid (0.50 / 0.75 / 0.90 / 0.95 / 0.99 / 1). Require:

- At least ten complete-pool calls and omission calls spanning at least twenty distinct original error cases. Repeated views of one case cannot satisfy this coverage requirement.
- At least 90% exact-pair precision separately in the complete and omission pools.
- Zero clean/same-class false calls and zero unavailable-partner false calls in both pools.

Maximize complete-pool correct repairs, then distinct correctly repaired omission cases, then fewer wrong calls, smaller gap and stability cutoffs, and higher gain cutoff. Freeze the selected policy before replaying author inputs. Keep the source-derived routing bands from iteration 109 unchanged: short contexts at most 100 sentences remain OFF, contexts at least 829 use the long rule, and intermediate sizes abstain.

Of 5,190 settings, 2,383 satisfy coverage and precision; 1,673 also satisfy the clean/unavailable-partner guards. The selected thresholds are gain **0.6174674057358479**, gap **0.25**, and stability **0.50**. It retains 48 / 64 complete-pool error repairs and 674 omission-view hits across fifty original cases. All 128 unavailable-partner views and all 48 omission-control views abstain. These zero-error counts are on the calibration bank that selected the thresholds.

## Author transfer and grammatical effects

Keep all 201 corrected iteration-107 cases, all sixteen candidate types and all 64 errors per context. No unavailable `c` errors are dropped. The original 100 sentences / 1,514 positions remain the only PP evaluation input; every recommendation is applied blindly, including any potential wrong action. No new annotation, model fit, reserve scoring or sealed lexical access occurs.

| Context | Higher-coverage iteration 109: correct / wrong | Omission-aware rule: correct / wrong / abstained errors |
|---|---:|---:|
| Original 100 | 0 / 0 | 0 / 0 / 64 |
| Civil-added | 49 / 3 | 25 / 0 / 39 |
| Primary expansion | 46 / 3 | 15 / 0 / 49 |

All clean/same-class controls abstain. All selected repairs affect scored positions, so the clean-probability restoration counts are fifteen primary and twenty-five Civil; there is no zero-affected success to subtract. Author cases were already inspected in earlier iterations, so this is an adaptive development replay, not fresh confirmation of perfect precision.

Every selected repair restores the full probability vector of both frozen PP models. The clean original model still selects 72 correct / 4 wrong memberships; the augmented model selects 62 / 4 at 0.71 or 27 / 1 at 0.80. This restores the same grammatical subset under alternative corruptions; it does not expand clean grammatical coverage or discover nuclei.

Across the 62 affected alternative errors, original-model outcomes at 0.80 are:

| Intervention | Correct PP selections | Wrong PP selections | Precision | Recall |
|---|---:|---:|---:|---:|
| Corrupted, no repair | 3,969 | 571 | 87.42% | 40.26% |
| Higher-coverage primary rule | 4,278 | 245 | 94.58% | 43.40% |
| Omission-aware primary rule | 4,036 | 489 | 89.19% | 40.94% |
| Omission-aware Civil rule | 4,090 | 457 | 89.95% | 41.49% |

The stricter primary rule adds 95 correct memberships, loses 28, adds three false memberships and removes 85: net +67 correct / −82 false versus corruption. Many more corruptions remain unrepaired, so the mixed-set PP precision and recall are lower than the higher-coverage branch despite zero observed wrong selected anchor repairs. A zero-wrong selective mapping result is not complete grammatical restoration. Totals reuse the same token positions under alternative mappings and are not independent or unique restored words.

## Component attribution

Disable only the selected stability cutoff, with no threshold refit and with gain, gap, routing and short-context OFF unchanged. This changes **zero actions across all 1,139 source views and all 201 author views**. At this fixed operating point, the gain/gap conditions reproduce all observed decisions; the bootstrap test is not responsible for these outcomes.

Record the gain/gap-only version as a possible faster baseline, not an adopted default or proof of equivalence on unseen inputs. Other operating points can still depend on stability, and a separately recalibrated family might choose differently.

## Verification and next step

Independently check all 5,190 source settings, including distinct-case coverage and the selected tie break. Verify 927 input hashes, replay all 201 conditional actions and routes, check 1,809 independent confusion counts and all gross transitions, and verify 65 unchanged cached PP payloads. Forty affected exact restorations across the two overlapping added-context views reproduce clean probabilities. No new PP inference was needed. All 69 focused tests pass, including tests that repeated omission views cannot fake distinct-case coverage and that unavailable-partner errors force rejection despite adequate precision.

Artifacts, frozen design, tracker snapshot, calibration curve, complete actions, score references and stability ablation are in `experiments/results/grammar-restoration/iteration111/`. Iterations 107 and 109 remain preserved as distinct performance points.

Next preflight a volume-matched cross-author replication on the already annotated Jerome 100-sentence sample, using only additional cached word forms as unlabeled context. If available, project FORM tokens and needed document/sentence metadata from the cached treebank without consuming extra POS, morphology, heads or relations; exclude original and reserved sentence IDs before projection. Predeclare a deterministic selection reaching the source-matched 829-sentence total, and freeze both source-derived policies before scoring. Such inputs inherit the treebank's segmentation, and the old Jerome sample is reused development data, so this is cross-author replication rather than fresh independent confirmation. True word-absence/context-loss stress and initial-period sentence segmentation remain open; omission-only calibration must not be presented as covering those conditions.
