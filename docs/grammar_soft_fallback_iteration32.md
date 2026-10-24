# Iteration 32: normalized soft fallback outside candidate sets

**The preselected small fallback does not recover missing reference classes.** At mixture mass .01, objective-selected random starts recover zero excluded query tags across both deletion levels and both emission arms. Accuracy stays close to the hard-mask results. A larger .30 fallback produces modest sensitivity-run gains, but recovers only about 3–6% of excluded tags and leaves substantial spillover. This particular state-independent fallback is insufficient; the experiment does not rule out other forms of soft candidate modeling.

## Model and information boundary

The experiment retains the same 240 inspected development sentences, 2,052 tokens including 473 query tokens, oracle development eight-class chain, reference-derived candidate masks, and nested deletion schedules. No fresh targets or reserved sentences are scored.

The candidate-constrained component `A(s,w)` is still row-normalized and exactly zero outside the supplied support. Full emissions are now a proper mixture:

`E(s,w) = (1 − epsilon) A(s,w) + epsilon q(w)`

Here `q(w)` is the observed corpus word-frequency distribution, **identical for all grammatical states**, and epsilon is fixed. Each full emission row sums to 1, with a positive floor at every word/class pair. The fallback has no separately learned word-to-class assignments: if the reference class is excluded, its evidence can come only through the generic word-frequency channel and class context. This is a specific constrained diagnostic, not a general learned escape model.

EM jointly accounts for latent grammatical states and emission channels. The candidate component's M-step receives expected counts multiplied by the posterior candidate-channel responsibility `(1 − epsilon) A / E`. It then uses the unchanged supported prior/M-step. The optimized objective is mixture observed-data likelihood plus the supported prior on `A`; epsilon and `q` do not update. This avoids applying an unnormalized penalty or clipping an ordinary M-step after the fact.

## Frozen comparison

Deletion levels are0/10/50% of word types, starting from the iteration30 mask that adds one false class to **every** word. Rate0 therefore has imperfect candidate precision but complete reference support. The hard comparison is iteration30 rate1 for zero deletion, and the corresponding iteration31 hard masks/fits for 10/50% deletion. The .01 mixture is fixed as primary before scoring; .001/.10/.30 are sensitivity settings, not values selected by accuracy or cross-model objective ranking.

Five perturbation seeds, both emission arms, and six starts (one surviving-label oracle + five original random starts) give 120 cells and 720 new fits. Every fit converges under the unchanged 600-update cap and relative tolerance 1e-7. Candidate-component initial matrices exactly match their hard-mask counterparts; full mixture emissions differ by construction. The primary fit in each cell maximizes the within-cell objective among the five random starts. Labels enter masks, oracle initialization, and evaluation, not EM updates or selection. Different epsilon objectives are never used to select epsilon.

All results remain privileged: the chain comes from the same corpus's reference class sequences, and candidate masks begin with its reference word/class support. The experiment tests a failure mechanism, not usable grammatical recovery on unknown ciphertext.

## Whole-query results

Mean query token accuracy across five perturbation seeds, each with 473 query tokens:

| True-class deletion rate | Hard word | Word epsilon .001 | **Word .01 primary** | Word .10 | Word .30 |
|---|---:|---:|---:|---:|---:|
| 0% | 76.70% | 76.70% | **76.83%** | 76.96% | 77.17% |
| 10% | 69.13% | 69.13% | **68.92%** | 69.73% | 70.15% |
| 50% | 31.88% | 31.92% | **32.30%** | 34.16% | 36.28% |

| True-class deletion rate | Hard ending | Ending epsilon .001 | **Ending .01 primary** | Ending .10 | Ending .30 |
|---|---:|---:|---:|---:|---:|
| 0% | 76.79% | 76.79% | **76.91%** | 77.59% | 77.93% |
| 10% | 69.05% | 69.13% | **69.30%** | 70.02% | 70.53% |
| 50% | 32.39% | 32.30% | **32.26%** | 34.04% | 36.32% |

At primary .01, changes relative to hard masks range from −0.21 to+0.42 percentage points for word, and −0.13 to+0.25 for ending. These small changes have no consistent direction. They do not constitute repair of missing candidates: **every selected primary run still tags all excluded query tokens incorrectly**. The .001 setting also recovers none.

![Soft fallback sensitivity](../experiments/results/grammar-restoration/iteration32/soft-fallback-response.svg)

At .30, mean accuracy improves by 1.02/1.48 points at 10% deletion and 4.40/3.93 at 50% (word/ending). These are sensitivity findings, not promotion of a gold-selected setting. They still fall far short of the earlier candidate-complete baseline. Perturbation ranges and individual cell results are saved; these five seeds reuse the same sentences and are not independent population confidence intervals.

## Recovery versus covered-token harm

There are, on average, 42 excluded query tokens at 10% deletion and 231.6 at 50%. Epsilon .01 recovers 0 in every selected fit. At .10, conditional excluded-token recovery averages 2.79% in both arms at 10% deletion, and 1.21% /1.12% at 50%. At .30:

| Deletion | Arm | Excluded query tokens, mean | Recovered excluded tags, mean | Conditional recovery, mean |
|---|---|---:|---:|---:|
| 10% | Word | 42.0 | 1.8 | 5.45% |
| 10% | Ending | 42.0 | 2.0 | 6.19% |
| 50% | Word | 231.6 | 6.8 | 2.99% |
| 50% | Ending | 231.6 | 7.2 | 3.16% |

Conditional percentages average the five per-seed recovery fractions, whereas token counts are averaged separately; dividing those mean counts need not give the mean conditional percentage. At zero deletion there are no excluded tokens, so recovery rate is undefined rather than zero.

The soft model can also change previously covered decisions. Compared with the matched hard fit, the exact accounting is:

`net additional correct tags = recovered excluded tags + covered gains − covered losses`

Mean counts at .30:

| Deletion | Arm | Recovered excluded | Covered losses | Covered gains | Net additional correct query tags |
|---|---|---:|---:|---:|---:|
| 10% | Word | 1.8 | 10.2 | 13.2 | 4.8 |
| 10% | Ending | 2.0 | 8.2 | 13.2 | 7.0 |
| 50% | Word | 6.8 | 6.2 | 20.2 | 20.8 |
| 50% | Ending | 7.2 | 6.0 | 17.4 | 18.6 |

Most of the high-deletion improvement is therefore better selection among still-covered tokens, not successful recovery of missing categories. At primary .01 the excluded recovery is zero; corresponding covered net changes are −1.0/+1.2 tags at 10% deletion and +2.0/−0.6 at 50% (word/ending). Different refits and objective-selected basins can produce small gains and losses even when no excluded class is recovered.

## Does fallback stop spillover?

To avoid crediting a general zero-deletion model change as repair, compare each soft deletion fit with the **same epsilon's zero-deletion soft fit** on exactly the still-covered tokens. At .01, deletion causes mean covered-token accuracy changes of −0.66/−0.26 points at 10% deletion, and −12.56/−12.75 at 50% (word/ending). The high-deletion spillover remains.

At .30, the analogous changes are +0.10/−0.17 points at 10%, and −8.21/−8.66 at 50%. A large fallback reduces but does not eliminate the high-deletion damage. This comparison includes emission refitting and initialization selection, not just local message passing. Matched untouched-word and neighboring-token audits are also retained in the artifacts.

## Fallback use is not recovery or abstention

At .01 with 50% deletion, expected fallback-channel use averages about 2.4% across query tokens, 1.1% on covered tokens, and 3.7% on excluded tokens, yet no excluded tag is recovered. At .30, these figures are about 32.4–32.6% overall, 24.4–24.6% covered, and 40.8–41.0% excluded; excluded-tag recovery is still only about 3%.

The fallback channel can emit a word even when its current grammatical state is inside the candidate set. Its posterior usage therefore does not mean the model selected an excluded class, recognized an error, or abstained. No confidence calibration, abstention threshold, or reliable detection claim is made here.

## Interpretation and next diagnostic

A generic word-frequency escape removes hard impossibility but supplies no word-specific information about which excluded class is correct. Small mass rarely changes the winning class; large mass gives only modest recovery and changes other decisions. This supports a narrow conclusion: **this normalized state-independent fallback does not solve the candidate-coverage problem**. It does not establish that every soft candidate model fails, or that the best possible contextual predictor cannot recover these tags.

Before fitting another escape mechanism, test the first-order context's information directly: mask the token's own lexical evidence and predict its class with true neighboring classes, then compare with inferred neighbors on the existing excluded-token cohorts. If even oracle neighboring classes rank the reference tag poorly, the current fallback lacks enough contextual information; if oracle neighbors work but inferred neighbors fail, propagation/context estimation is the sharper bottleneck. Keep such privileged probes separate from practical recovery claims. Learning a reliable word/category candidate channel remains unresolved.

## Artifacts, checks, reproduction

Artifacts under `experiments/results/grammar-restoration/iteration32/` contain the frozen configuration, 120 cell files with 720 trajectories and component matrices, all matched hard/soft cohort audits, a standalone sensitivity curve, and validation report. Prior frozen artifacts are unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_soft_fallback_iteration32
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/voynich-matplotlib .venv/bin/python -m benchmarks.grammar_soft_fallback_iteration32_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_soft_fallback_iteration32_validate
```

Runners preserve outputs. Four new mechanism tests check normalized floors/zero-epsilon equivalence, independently enumerate joint grammatical-state/mixture-channel paths to verify the M-step and channel posteriors, and verify monotonic EM for both priors. Validation checks all 720 final likelihoods/objectives/scores, monotonic traces, normalized mixtures, exact constrained-component support, matching hard initializations, fallback posterior summaries, and excluded-recovery/covered-loss accounting. It fully replays all 12 trajectories in the primary-epsilon/50%-deletion/seed3001 cells. The combined relevant suite passes 309 tests. The 200 reserved sentences remain unscored.
