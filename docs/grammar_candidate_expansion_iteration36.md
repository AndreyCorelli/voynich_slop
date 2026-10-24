# Iteration 36: limited candidate expansion for flagged words

**Candidate expansion improves the severe-deletion condition, with substantial collateral errors and only a modest advantage over random expansion.** The primary two-class context proposal raises query word-tag accuracy from 32.30% to 40.17%, and ending-arm accuracy from 32.26% to 40.34%. Matched random expansion reaches 38.86% /37.97%. At low deletion, gains are only 0.21/0.34 percentage points. The result is useful evidence that some missing candidate coverage can be repaired, not reliable grammatical restoration.

## Frozen repair experiment

The experiment keeps the previously inspected 200-background/40-query corpus (2,052/473 total/query tokens), oracle development eight-class chain, original perturbed candidate sets, and fixed iteration35 outside-mass flags. Primary fallback epsilon and flag calibration budget both remain .01; these are separate parameters. No new query-label threshold selection, fresh-target scoring, or reserved scoring occurs.

A word is eligible if any occurrence is flagged by the existing scalar rule. On each flagged occurrence, take the original target-masked HMM posterior and condition it on classes **outside that word's current candidate set**. Average these distributions equally across the word's flagged occurrences, then add the topK outside classes, with class-index tie-breaking. Additions are capped per word across the entire corpus, not unioned without a cap across contexts. Unflagged occurrences do not influence proposals.

The primary setting is K=2. K=1/3 are fixed sensitivity checks. A matched random control adds two uniformly sampled outside classes without replacement to **exactly the same word types**, with the same per-word candidate counts. It uses a fixed per-perturbation seed. Neither proposal method receives reference classes, excluded-token labels, oracle neighbors, or true candidate-removal flags. Reference support is used only to reconstruct the old simulated inventory and to audit new proposals.

Proposals use unlabeled context from both background and queries, and expand a shared word-level inventory. A flag in one occurrence can therefore repair an unflagged occurrence of the same word. This is transductive repair, not a model applied to an untouched query vocabulary. The underlying reference-derived inventory and class chain remain privileged.

## Refitting and controls

Every expanded mask refits the same normalized .01 fallback HMM, with fixed chain parameters and support-conditioned priors recomputed for the larger candidate set. Five original random initialization seeds are repeated; selection uses only the within-cell regularized objective. There is no comparison of objective values across different masks/K/settings.

A separate warm-start diagnostic takes 99% of the old fitted candidate component plus 1% of the new support-conditioned prior. That small opening mass makes all newly supported entries positive, avoiding an infinite log prior at a zero initialization. The warm start uses old fitted probabilities, not supervised repair labels, and does not compete in primary random-start selection.

There are 80 cells: five perturbations × two deletion levels × two emission arms × four proposal settings. Each has one warm and five random runs, totaling 480 fits. All converge under the original 600-update cap/tolerance 1e-7. The full proposal file and choices were frozen before refitting or scoring repair outcomes.

The original abstention flags stay fixed. There is no recursive flagging, second-round candidate proposal, or query-driven change in K. Only eight POS classes are restored here; dependency structure, case/number morphology, and word translation are not evaluated.

## Candidate retrieval: primary K=2

Counts below sum five perturbation scenarios, not globally distinct word types. Query denominators are 2,365 scenario-token exposures over the same 40 unique sentences. A “true” added pair means word/class attested in the original corpus's reference inventory; an unattested pair is called false for this benchmark, not necessarily linguistically impossible.

Word arm:

| Deletion | Proposal | Flagged word-type exposures | Added pairs | True / false added pairs | Missing query tags whose class becomes a candidate |
|---|---|---:|---:|---:|---:|
| 10% | Context top2 | 173 | 346 | 88 /258 | 49/210 (23.33%) |
| 10% | Random2 | 173 | 346 | 36 /310 | 18/210 (8.57%) |
| 50% | Context top2 | 706 | 1412 | 364 /1048 | 270/1158 (23.32%) |
| 50% | Random2 | 706 | 1412 | 174 /1238 | 190/1158 (16.41%) |

Context proposals have pair precision 25.43/25.78% at low/high deletion versus 10.40/12.32% for random. Thus most new classes remain false competitors, but context adds more reference-supported pairs than an equally sized random expansion. The strong flag precision from iteration35 does not imply equally precise replacement-class proposals.

Query candidate coverage increases from 91.12% to 93.19% at low deletion and 51.04% to 62.45% at high deletion for context K=2. Random coverage becomes 91.88/59.07%. These are **candidate-component coverage** figures, not hard accuracy ceilings for the full mixture model, whose fallback already gives every class positive probability.

Shared word-level repair matters: 26 of the 49 regained query candidates at low deletion and 164 of 270 at high deletion belong to originally **unflagged query occurrences**. Their word was proposed for expansion from another occurrence. The ending arm is similar: 50/210 and 274/1158 regain their class under context K=2, versus 14/210 and 177/1158 for random.

## Tag accuracy after refitting

Mean full-query token accuracy over five perturbations; equal 473-token query sizes make this also the pooled accuracy:

| Arm | Deletion | Original model | Context K1 | **Context K2 primary** | Context K3 | Random K2 |
|---|---:|---:|---:|---:|---:|---:|
| Word | 10% | 68.92% | 69.68% | **69.13%** | 69.18% | 69.09% |
| Ending | 10% | 69.30% | 70.06% | **69.64%** | 69.47% | 69.30% |
| Word | 50% | 32.30% | 38.60% | **40.17%** | 42.37% | 38.86% |
| Ending | 50% | 32.26% | 38.90% | **40.34%** | 42.88% | 37.97% |

K3 improves the high-deletion scores further but adds more false competitors and is not promoted to primary after inspecting queries. At low deletion the smaller K1 happens to score better. The curve does not establish a universally preferred K.

Paired sentence-cluster bootstrap intervals resample the 40 query IDs jointly across perturbations (1,000 replicates). Primary K2 minus original accuracy gains at high deletion are +7.86 points for word (95% interval [+6.13,+9.75]) and +8.08 for ending ([+6.53,+9.79]). Low-deletion intervals include zero. These are finite internal-development intervals; the queries were previously inspected and upstream oracle information remains.

Against **matched random K2**, context gains are much smaller:

| Arm | Deletion | Context−random accuracy | Paired sentence 95% interval |
|---|---:|---:|---:|
| Word | 10% | +0.04 points | [−0.76,+0.96] |
| Ending | 10% | +0.34 | [−0.48,+1.15] |
| Word | 50% | +1.31 | [−0.09,+2.83] |
| Ending | 50% | +2.37 | [+0.90,+3.88] |

A substantial fraction of the severe-deletion gain comes from reopening candidates on flagged words even randomly. Context improves retrieval and the ending-arm result in this sample, but the word-arm comparison remains uncertain. Neither comparison proves transfer to new text.

Warm-start K2 scores are 69.13/69.73% at low deletion and 40.55/40.34% at high deletion (word/ending), close to the primary results. This sensitivity check does not remove optimization concerns or prove global optimality.

## Corrected tags, spoiled tags, and remaining ranking errors

Primary context K2 counts over five scenarios:

| Arm | Deletion | Corrected query tags | Spoiled query tags | Net gain | Originally excluded tags recovered |
|---|---:|---:|---:|---:|---:|
| Word | 10% | 78 | 73 | +5 | 23 |
| Ending | 10% | 84 | 76 | +8 | 23 |
| Word | 50% | 263 | 77 | +186 | 153 |
| Ending | 50% | 260 | 69 | +191 | 150 |

All these recovered originally excluded tags have their reference class in the expanded inventory; the .01 generic fallback does not account for additional uncovered recovery in these query runs. Word-arm recovery is 23/49 (46.94%) among newly covered query tokens at low deletion and 153/270 (56.67%) at high deletion. Candidate availability therefore still leaves a substantial ranking problem.

Collateral changes are material. The word arm spoils 73/1,630 (4.48%) originally correct covered query tags at low deletion and 77/764 (10.08%) at high deletion. Ending figures are 76/1,639 (4.64%) and 69/763 (9.04%). These rates are far above the original flag-stage 1% calibration budget, which **does not constrain a subsequent global emission refit**. Other covered mistakes are also corrected, so these spoils do not equal the final net harm on all covered tokens.

At low deletion, genuine recovery of 23 missing tags is largely offset by degradation elsewhere: the word arm's net change on originally covered tokens is −18. At high deletion, missing-tag recovery 153 plus a covered-token net gain 33 gives the overall +186. The improvement is not uniformly localized to proposed words, because emissions are globally normalized and re-estimated and the objective-selected basin can change.

## Keeping the old abstention flags

The original flags from iteration35 are retained as a conservative alternative, without recalibrating them after repair. Pooled conditional accuracy on the originally unflagged query tokens:

| Arm | Deletion | Before repair + old abstention | After K2 repair + old abstention | Same retained coverage |
|---|---:|---:|---:|---:|
| Word | 10% | 69.89% | 69.72% | 98.31% |
| Ending | 10% | 70.28% | 70.19% | 98.31% |
| Word | 50% | 35.45% | 41.51% | 89.94% |
| Ending | 50% | 35.40% | 41.80% | 89.94% |

At high deletion this yields more correctly asserted unflagged tags; at low deletion it gives no gain. Old flags may now withhold some repaired correct tags, and their original calibration does not certify the repaired model. The conservative branch demonstrates an option, not an optimized new abstention policy. Even the retained high-deletion tags remain mostly wrong.

## Interpretation and next step

The repair channel recovers real candidate coverage and some tags without supplying new gold classes to the proposal function. Its current quality is limited by low proposal precision, unresolved selection among newly available classes, large changes from global refitting, and upstream oracle information. The matched random control shows why an apparent post-repair gain alone is insufficient evidence of a strong contextual repair mechanism.

The next controlled change should **preserve existing emissions while allocating a small explicit probability budget to repaired candidates**, rather than globally relearning all word/class probabilities. Compare that restricted update with this full refit using the same frozen proposals and flags. Measure whether it retains excluded-tag recovery while reducing losses on already-correct tags. The emission distribution must remain normalized; merely adding probability or masking after an unconstrained M-step is not a valid implementation. More complex grammar or fresh confirmation should follow only a concrete improvement in that recovery/collateral-error tradeoff. The reserved 200 sentences remain untouched.

## Artifacts and verification

Artifacts: `experiments/results/grammar-restoration/iteration36/` contains frozen proposals/configuration, 80 fit cells with 480 trajectories, candidate and tag-recovery audits, matched random comparisons, fixed-abstention results, and validation report. Existing verified files remain unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_candidate_expansion_iteration36
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_candidate_expansion_iteration36_evaluate
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_candidate_expansion_iteration36_compare
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_candidate_expansion_iteration36_validate
```

Runners preserve outputs. Four new tests check word-level caps, aggregation of flagged-only contexts, outside conditioning, preservation of existing candidates, and matched deterministic random controls. Validation replays all 80 proposals, checks all 480 final fits and 54,522 monotonic objective rows, fully replays 12 primary high-deletion trajectories, verifies candidate retrieval/false-pair/error accounting and frozen abstention, reproduces 20 bootstrap comparisons, and checks prior hashes. The combined relevant suite passes 325 tests. No reserved or fresh target sentences are scored.
