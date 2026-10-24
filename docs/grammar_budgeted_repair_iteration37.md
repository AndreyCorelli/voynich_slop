# Iteration 37: freeze old emissions and budget candidate repair

**Freezing the old model sharply reduces collateral errors, at the cost of recovering fewer missing tags.** With a 1% repair-channel budget and the same context K2 proposals, the word arm recovers 7/23 excluded query tags at low/high deletion while spoiling 1/3 previously correct tags. The global refit recovered 23/153 but spoiled 73/77. A 10% budget recovers more—20/71—with 11/12 spoils. This is a useful recovery/protection tradeoff in the controlled experiment, not high-accuracy grammatical restoration.

## Frozen design

The corpus, oracle development eight-class chain, original models, iteration35 flags, and iteration36 proposals are unchanged. There are 200 previously inspected background sentences and 40 queries, 2,052 total tokens including 473 query tokens. Context K2 is primary; matched random K2 is the control. This experiment does not propose new classes, change the flags, or fit a new chain. No fresh or reserved sentences are scored.

For each scenario, let `E_old` be the **full** fitted iteration32 emission distribution, including its .01 generic fallback. Freeze this matrix exactly. A new repair distribution `R` is permitted only on the newly added word/class pairs from iteration36. Each active state's repair row is normalized; states with no new candidate pairs have an all-zero repair row and allocate no repair mass.

The normalized total emission is:

`E_new(s,w) = (1 − delta_s) E_old(s,w) + delta_s R(s,w)`

`delta_s` equals the fixed repair budget for states with new pairs and zero otherwise. The primary budget is .01; .001/.05/.10 are frozen sensitivity settings. This budget is independent of the .01 generic fallback already inside `E_old` and the .01 flag calibration risk budget. There is no query-based selection of the repair budget.

Only `R` changes during EM. Its prior is corpus word frequency conditioned on the new pairs in each active state, with pseudocount mass 1 per active repair row. The E-step computes grammatical-state and repair-channel responsibilities; the M-step receives only expected repair-channel counts. The objective is observed-data likelihood plus the repair prior. Old emissions and chain parameters remain constants throughout.

Five random repair starts use the same initialization seeds as before; selection maximizes the objective within a fixed scenario/budget only. The control without repair EM sets `R` to the conditioned corpus-frequency prior. No gold labels enter either repair update or initialization. Word/ending arm names refer to the frozen old models; the new repair channel uses the same simple word-frequency prior in both.

There are 160 cells and 800 fitted repair runs: five perturbations × two deletion rates × two old-model arms × two proposal types × four budgets × five starts. All runs converge under the unchanged 600-update cap/tolerance 1e-7. Labels are used for diagnostic scoring, not EM or start selection. Upstream oracle candidate inventories and class-chain information, transductive corpus fitting, and repeated query inspection remain explicit limitations.

## What “fixed old emissions” guarantees

The old matrix is fixed as a **mixture component**. Total old-cell probabilities are not entrywise unchanged: active rows allocate a fraction of their mass to repair. Every total row still sums to 1.

For a word with no new pair, its state emission is multiplied by either `1 − budget` (active repair row) or 1 (inactive row). Thus its pairwise class-emission odds can change only by factors between `1 − budget` and `1/(1 − budget)` before contextual propagation. If both states are active, the direct odds remain identical. This constrains direct drift, but does not guarantee unchanged tag predictions: changed evidence at repaired words can affect neighbors, and small odds changes can affect close decisions. No unused artificial word or unnormalized probability bonus is introduced.

## Primary 1% repair budget

Counts sum five perturbation scenarios (2,365 query-token exposures over the same 40 unique query sentences). Context K2 proposals are exactly those from iteration36.

| Old model | Deletion | Excluded tags recovered | Corrected query tags, all | Previously correct tags spoiled | Net correct tags | Query accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Word | 10% | 7 | 9 | 1 | +8 | 69.26% |
| Ending | 10% | 7 | 9 | 2 | +7 | 69.60% |
| Word | 50% | 23 | 27 | 3 | +24 | 33.32% |
| Ending | 50% | 23 | 27 | 3 | +24 | 33.28% |

Unchanged baselines are 68.92/69.30% at low deletion and 32.30/32.26% at high deletion (word/ending). Most tags remain unrecovered, especially in the severe condition. Recovery of originally excluded query tags is 7/210 (3.33%) at low deletion and 23/1158 (1.99%) at high deletion. This denominator includes all excluded tags, not only those offered a repaired candidate.

The global iteration36 refit at the same proposals gave:

| Old model | Deletion | Excluded recovered globally | Corrected globally | Spoiled globally | Global net gain | Global accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Word | 10% | 23 | 78 | 73 | +5 | 69.13% |
| Ending | 10% | 23 | 84 | 76 | +8 | 69.64% |
| Word | 50% | 153 | 263 | 77 | +186 | 40.17% |
| Ending | 50% | 150 | 260 | 69 | +191 | 40.34% |

At low deletion the primary restricted update gives nearly the same net gain with far fewer changes. At high deletion it is much more conservative but sacrifices most of the full refit's recovery and net accuracy gain. There is no universally dominating method in these results.

Only 0/1 primary spoils occur on word types without any new proposal at low/high deletion for the word arm; ending has 1/1. The global refit spoiled 60/64 such word-arm tags and 62/58 ending-arm tags. This directly supports reduced spillover, while also showing it is not eliminated.

## Fixed budget sensitivity

Word arm, context K2, same frozen proposals and priors:

| Repair budget | Low-deletion accuracy | Low: excluded recovered / spoiled | High-deletion accuracy | High: excluded recovered / spoiled |
|---|---:|---:|---:|---:|
| 0 (unchanged) | 68.92% | 0 /0 | 32.30% | 0 /0 |
| .001 | 69.09% | 3 /0 | 32.56% | 7 /1 |
| **.01 primary** | **69.26%** | **7 /1** | **33.32%** | **23 /3** |
| .05 | 69.56% | 19 /8 | 34.42% | 45 /8 |
| .10 | 69.56% | 20 /11 | 35.52% | 71 /12 |
| Global refit | 69.13% | 23 /73 | 40.17% | 153 /77 |

At .10 in the severe condition, about46% of the word arm's globally recovered excluded tags are retained (71/153), with about84% fewer spoils (12 versus77). Ending yields72 recovered and10 spoils, compared with150/69 globally. At .05 low-deletion net gains exceed the global-refit net gain with fewer spoils, but this is a frozen sensitivity finding, not a new budget chosen from the queries.

![Repair tradeoff](../experiments/results/grammar-restoration/iteration37/budgeted-repair-tradeoff.svg)

Counts on this figure pool repeated perturbation scenarios. They do not represent distinct newly recovered words or independent test examples. The larger budgets reveal a tradeoff, not calibrated deployment risk.

## Controls and uncertainty

The frequency-only repair control uses the same proposed pairs and budget but leaves `R` at the corpus-frequency prior. At primary .01, word-arm accuracy is 69.18% low and32.81% high, versus learned 69.26/33.32%. Ending is 69.51/32.94% versus 69.60/33.28%. Most of the small low-deletion gain is therefore available without repair EM; learning adds a modest amount, more visibly at high deletion. At .10 high deletion, frequency-only accuracy is 34.71/34.76% versus learned 35.52/35.52%.

With **matched random K2 proposals**, primary learned-repair accuracy is 69.18/32.94% for the word arm and 69.51/32.94% for ending, at low/high deletion. Context's advantage over random is only +0.08/+0.38 percentage points for word and +0.08/+0.34 for ending. All corresponding sentence-cluster 95% intervals include zero. The experiment does not establish a robust primary-budget contextual-proposal advantage beyond reopening candidate mass on flagged words.

Paired sentence-cluster bootstrap intervals jointly resample the 40 query IDs across all five perturbations (1,000 replicates). Primary word-arm gains over the unchanged model are +0.34 points (95% interval [+0.082,+0.649]) at low deletion and +1.01 ([+0.602,+1.490]) at high deletion. These intervals describe the finite reused query set, not fresh generalization, and do not account for earlier inspection or upstream oracle information.

## Fixed abstention remains available

Keeping the original flags after primary repair yields pooled retained accuracy 69.98/70.32% at low deletion and 35.59/35.54% at high deletion (word/ending), at the same 98.31/89.94% token coverage as before. The flags are not recalibrated for the repaired model; some repaired correct tags remain withheld. These are selective tag results, not restored dependency structures, and high-deletion retained predictions remain mostly incorrect.

## Interpretation and next action

The comparison supports restricting global emission reestimation to reduce the collateral changes seen in iteration36. A normalized, fixed-base repair channel preserves far more existing decisions. It also demonstrates the price of a tight update budget: very little missing-tag recovery. Stronger fixed budgets offer intermediate points, but class proposals are still noisy and most reference classes remain unavailable or poorly selected.

The next useful step is to **calibrate the repair budget on background labels under an explicit correction/spoil constraint**, with a no-update option, rather than promote a sensitivity setting because it looks better on these queries. Freeze the resulting choice before any further evaluation. A separate fresh declared slice would be needed to confirm the repair mechanism, and the 200 reserved sentences should remain untouched. The larger unresolved task is obtaining candidate support and class context without oracle information; this experiment does not solve that problem.

## Artifacts and checks

Artifacts: `experiments/results/grammar-restoration/iteration37/` contains frozen K2 proposals/configuration, 160 fit cells with 800 trajectories, frequency-only and random-proposal controls, recovery/collateral/abstention audits, clustered comparisons, a standalone tradeoff figure, and validation report. Earlier verified artifacts are unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_budgeted_repair_iteration37
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/voynich-matplotlib .venv/bin/python -m benchmarks.grammar_budgeted_repair_iteration37_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_budgeted_repair_iteration37_validate
```

Runners preserve outputs. Four new tests independently enumerate grammatical-state/repair-channel paths to verify repair counts and the M-step, check inactive states/normalization/zero-budget equivalence, verify the untargeted emission-odds bound, and confirm monotonic EM with immutable old emissions. Validation checks all 800 final fits and objective traces, exact repair support and normalized distributions, old-matrix/zero-budget identities, source priors/initializations, recovery and fixed-abstention accounting, frequency controls, 36 bootstrap replays, and prior hashes. It fully replays 10 primary high-deletion/context trajectories. The combined relevant suite passes 329 tests. No fresh targets or reserved sentences are scored.
