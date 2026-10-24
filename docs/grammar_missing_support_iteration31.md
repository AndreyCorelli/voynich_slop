# Iteration 31: missing true candidates and spillover

**Candidate omissions cause both unavoidable tag errors and additional damage to still-covered tokens.** At 10% of word types with one true class removed, the mean query coverage ceiling is 91.12%, and the fitted word/ending models achieve 69.13% / 69.05%. Their accuracy on still-covered query tokens is close to the matched baseline. At 50% deletion, the ceiling falls to 51.04%, accuracy to 31.88% / 32.39%, and still-covered accuracy loses another 13.37 / 12.41 percentage points relative to the same tokens under the baseline. Those larger losses also occur on words whose candidate sets were never changed.

These are repeated-development, oracle-chain diagnostics. They do not demonstrate practical candidate retrieval or grammatical restoration.

## Matched design

The experiment keeps the existing 240 development sentences (200 background +40 queries), 2,052 tokens total and 473 query tokens. The fixed eight-class chain is the oracle development chain from iteration28. Emission priors, word/ending parameterizations, five initialization seeds 2601–2605, 600-update cap, and relative stopping tolerance 1e-7 are unchanged.

The matched **zero-deletion baseline** is iteration30's 100%-addition condition: every word already has one uniformly sampled false class in addition to its reference-supported classes. It gives 76.70% / 76.79% query accuracy from objective-selected random starts. Starting with a false fallback permits true-class removal without creating an empty inventory and provides enough ambiguous tokens to measure downstream effects. This is a different baseline from iteration29's nearly forced 98.52% oracle-support result, and from iteration30's 10%-addition condition. Do not compare their percentages as if only candidate recall changed.

For each perturbation seed 3001–3005, retain its original random word-type ordering and false candidate. Independently choose one **reference-supported** class per word, uniformly among its attested classes, using seed(maskseed+100). At deletion rates 1/5/10/25/50/100%, remove that class from the first `floor(rate × 863)` word types. Masks are nested within seed; all 863 candidate inventories remain nonempty because the false fallback is retained. For an originally ambiguous word, removing one class can exclude some of its tokens while other tokens of that same word remain covered. Thus affected-type rate is not the token coverage loss.

Each mask has two arms, one privileged surviving-label initialization and five random starts: 60 cells /360 fits. All 360 converge. Random starts use the same Gamma draws, masked and normalized. The separate oracle initialization uses only gold word/class counts that survive the mask, plus the supported prior; it cannot initialize a forbidden reference class. The primary fit is selected solely by the highest regularized objective among the five random starts within the cell. No objectives are compared across masks/arms. No fresh target or reserved sentences are scored.

The reference support, deliberate omissions, and chain parameters remain privileged. This is a controlled coverage challenge, not a realistic learned-candidate error distribution.

## Query accuracy and its ceiling

A token is *covered* when its reference class is still allowed. Because emissions outside the mask are exactly zero, excluded tokens cannot be tagged correctly. Therefore candidate coverage is an exact model-independent upper bound for token accuracy under these hard inventories. It is an upper bound, not a guarantee that this HMM can attain it.

The following are equal-weight means over five perturbation seeds. Full-query denominators are 473 in every replicate. These seeds reuse the same sentences; they do not provide independent population samples.

| Types with one true class removed | Query coverage ceiling | Word query accuracy | Ending query accuracy | Word balanced accuracy | Ending balanced accuracy |
|---|---:|---:|---:|---:|---:|
| 0%, matched iteration30 baseline | 100.00% | 76.70% | 76.79% | 73.53% | 73.89% |
| 1% | 99.41% | 76.19% | 77.12% | 72.85% | 74.18% |
| 5% | 95.43% | 72.64% | 72.52% | 68.91% | 68.62% |
| 10% | 91.12% | 69.13% | 69.05% | 65.72% | 65.50% |
| 25% | 75.77% | 53.57% | 53.36% | 48.97% | 48.58% |
| 50% | 51.04% | 31.88% | 32.39% | 27.43% | 28.04% |
| 100% | 4.14% | 0.89% | 0.85% | 1.19% | 1.14% |

At 100%, every originally singleton word has lost its only true class; only some tokens of the seven originally ambiguous words remain covered. Coverage across seeds ranges 1.48–6.13% (7–29 query tokens). At 1%, the omitted query-token count ranges 0–7. These endpoints should not be interpreted as stable conditional-accuracy estimates.

![Coverage and spillover curves](../experiments/results/grammar-restoration/iteration31/missing-support-response.svg)

## Still-covered tokens: paired comparison

The baseline is rescored on **exactly the same covered token subset** as each deletion run. This prevents a changing mixture of easy/hard tokens from masquerading as a model change. Negative deltas mean worse accuracy after deletion, relative to the matched baseline predictions. Conditional means average per-seed accuracies; they are not token-weighted averages.

| Deletion rate | Word covered accuracy | Word covered Δ | Ending covered accuracy | Ending covered Δ | Covered query-token range |
|---|---:|---:|---:|---:|---:|
| 1% | 76.64% | +0.00 points | 77.58% | +0.85 points | 466–473 |
| 5% | 76.06% | −0.60 | 75.93% | −0.76 | 425–463 |
| 10% | 75.82% | −0.35 | 75.75% | −0.40 | 410–450 |
| 25% | 70.35% | −4.73 | 70.08% | −4.69 | 323–388 |
| 50% | 62.63% | −13.37 | 63.58% | −12.41 | 222–270 |
| 100% | 27.02% | −43.79 | 26.25% | −44.56 | 7–29 |

At 10%, perturbation-seed deltas range −2.68 to+2.82 points for word and−2.30 to+4.00 for ending: there is little consistent extra damage at that level. At 25%, the mean harm increases, but one perturbation still improves covered-token accuracy. At 50%, **every seed** has negative covered-token deltas in both arms: word −20.43 to−3.15 points, ending −18.72 to−4.05. This makes the high-deletion spillover more consistent than the low-deletion fluctuations in this finite sweep.

To distinguish the effect from a remaining ambiguous class of the altered word itself, we also score tokens of **untouched word types**. Their mean changes at 10/25/50% deletion are −0.32/−4.93/−13.76 points for word and −0.36/−4.88/−12.88 for ending. Candidate removal elsewhere can therefore damage words whose own inventories did not change. There are no untouched types at 100%, so that statistic is undefined rather than zero.

Covered tokens immediately adjacent to an excluded token lose about 6.03/6.46 points at 10%, 11.05/10.96 at 25%, and 15.31/14.84 at 50% (word/ending). These subsets are small and changing; the experiment does not prove that adjacency alone causes the effect. The deletion run refits all emissions and reselects an initialization, so “spillover” includes contextual inference, global emission reestimation, and basin changes. It is not an isolated message-passing measurement.

## Exact error accounting

For each run:

`all query errors = excluded reference-class tokens + errors among still-covered tokens`

The excluded component is unavoidable under the mask. The covered component includes pre-existing selection errors as well as any new damage; it must not all be attributed to candidate removal. The paired deltas above measure the additional net damage on the same tokens, including compensating gains.

Mean error counts for the word arm:

| Deletion rate | Unavoidable excluded errors | Covered-token errors | Total query errors |
|---|---:|---:|---:|
| 1% | 2.8 | 109.8 | 112.6 |
| 5% | 21.6 | 107.8 | 129.4 |
| 10% | 42.0 | 104.0 | 146.0 |
| 25% | 114.6 | 105.0 | 219.6 |
| 50% | 231.6 | 90.6 | 322.2 |
| 100% | 453.4 | 15.4 | 468.8 |

Absolute covered-error counts can fall as the covered population shrinks even while conditional accuracy deteriorates. Error decomposition and conditional accuracy answer different questions. Candidate exclusion also does not necessarily create a *new* error: the baseline may already have tagged an excluded token incorrectly. Saved paired lost/gained counts retain this distinction for every cohort.

The surviving-label oracle initialization does not remove the coverage limit or the broader decline. Mean oracle-start query accuracy at 10/25/50% deletion is 71.33/55.22/33.02% for word and 72.39/55.10/32.64% for ending. Those supervised starts are diagnostics, not an available fitting method, and do not establish global optimality.

## Implication and next step

Candidate coverage is a real bottleneck: hard exclusion makes some errors unavoidable, and sufficiently widespread omissions also disrupt still-covered words. At modest deletion rates, most of the new deterioration is consistent with lost coverage rather than a large further decline on covered tokens. At higher rates, both problems need attention. Ending sharing again provides no substantial rescue.

The next small diagnostic is a **soft fallback outside the candidate inventory**, compared with these hard masks. It should permit some probability for excluded classes while keeping a preference for supplied candidates, rather than silently treating all candidates as equally plausible. Measure recovered excluded tokens, additional errors on covered tokens, and spillover at fixed settings on this same development material. Earlier unrestricted HMM drift shows why simply reopening every class without a meaningful prior is not an established fix. Abstention/coverage reporting should remain separate from tag recovery.

## Reproduction and verification

Artifacts: `experiments/results/grammar-restoration/iteration31/` contains frozen deletion schedules, 60 cell files with 360 trajectories, model-based selections, matched-baseline/cohort audits, a standalone SVG curve, and validation report. Earlier frozen files remain unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_missing_support_iteration31
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/voynich-matplotlib .venv/bin/python -m benchmarks.grammar_missing_support_iteration31_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_missing_support_iteration31_validate
```

Runners preserve artifacts. Three new tests check nested deletion/nonempty fallback, token-specific coverage for ambiguous words, sentence-bounded adjacency, empty cohorts, and exact coverage/conditional-accuracy accounting. Validation checks all 360 final fits and objective traces, initialization/selection, mask nesting and true-pair deletion counts, exact forbidden zeros, independent token coverage/cohort counts, matched-baseline lost/gained counts, and all frozen input hashes. It fully replays all 12 trajectories for 50%-deletion/seed 3001 (both arms, oracle plus five random starts). The combined relevant suite passes 305 tests. The 200 reserved sentences remain unscored.
