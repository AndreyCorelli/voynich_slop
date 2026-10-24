# Iteration 30: false-positive candidate support stress test

**Support errors cause gradual degradation rather than an immediate collapse in this diagnostic.** With one false class added to 10% of word types, objective-selected random starts retain 97.46% query token accuracy. At 25% noisy types they retain about 95%; at 50%, about 89%; and at 100%, about 77%. This remains a privileged experiment: every reference-supported class is retained, and the fixed transition chain comes from the same development reference labels. It establishes a controlled tolerance curve, not a candidate learner or restored cipher grammar.

## Frozen experiment

The corpus is unchanged: the previously inspected 200 background +40 query sentences (2,052 tokens; 473 query tokens). The oracle development chain from iteration28, support-conditioned priors from iteration29, two emission arms, five initializations 2601–2605, cap 600, and relative objective tolerance 1e-7 remain fixed. No new targets, parsing evaluation, or reserved-sentence scoring occurs.

Each perturbation seed 3001–3005 draws a random ordering of all863 word types and one uniformly chosen reference-forbidden class per type. At rates 1/5/10/25/50/100%, add that one extra class to the first `floor(rate × 863)` types. Masks are nested within each perturbation seed, and all reference-supported classes remain available. At 100%, a formerly singleton type has two classes, not all eight. The seven originally ambiguous types gain a third or fourth candidate. Type sampling is uniform, so affected token counts vary substantially with which frequent words are selected.

Each of 30 masks has word-only and factorized-ending arms, each with one supervised oracle initialization and five random starts: 60 cells and 360 new fits. All 360 meet the original convergence tolerance. Support-conditioned priors and supervised emission initialization are recomputed under each mask; the fixed-chain likelihood, emission parameterization, and prior strengths are unchanged. The primary result selects the highest regularized objective among the five **random** starts in each cell, without gold-accuracy selection. Oracle starts are separate diagnostics. Objectives are not compared across masks or arms. The rate 0 reference reuses iteration29.

The noise only adds false candidates. It never removes the true class, estimates support from actual ciphertext, or simulates systematic morphology/ending-correlated errors. The masks and chain contain strong reference-label information; this differs substantially from an anonymous unconstrained model.

## Whole-query results

All values are percentages, averaged equally over the five perturbation seeds. Brackets show minimum–maximum across these seeds, **not population confidence intervals**. Every query has 473 tokens, so full-query averages also equal pooled accuracy across the five perturbed copies. The same query sentences are reused throughout.

| Word types with one extra class | Word query accuracy | Ending query accuracy | Word query balanced accuracy | Ending query balanced accuracy |
|---|---:|---:|---:|---:|
| 0% (exact support) | 98.52 | 98.52 | 98.21 | 98.21 |
| 1% | 98.44 [98.31–98.52] | 98.44 [98.31–98.52] | 98.17 | 98.17 |
| 5% | 97.80 [97.25–98.10] | 97.80 [97.25–98.10] | 97.76 | 97.76 |
| 10% | 97.46 [97.04–97.89] | 97.46 [97.04–97.89] | 97.47 | 97.47 |
| 25% | 95.05 [94.71–95.77] | 95.22 [94.71–95.98] | 94.82 | 94.92 |
| 50% | 89.39 [86.68–93.23] | 89.64 [87.32–93.45] | 88.44 | 88.55 |
| 100% | 76.70 [74.42–78.65] | 76.79 [74.00–79.07] | 73.53 | 73.89 |

Ending sharing provides little additional benefit under these masks; at low noise its predictions match the word arm. This does not establish a general null effect for endings, but supplies no strong reason to expand that mechanism here.

![Support-noise response](../experiments/results/grammar-restoration/iteration30/support-noise-response.svg)

Shading on the whole-query plot is perturbation-seed minimum–maximum. Affected-token curves average conditional accuracies over nonempty perturbations; their denominators differ by seed.

## Affected tokens and candidate-only baselines

High whole-query accuracy at low noise partly reflects untouched singleton tags that remain forced correct. The table therefore isolates query tokens whose word type received an extra class. All baselines use the **same candidate masks**.

The class-frequency baseline chooses the highest oracle corpus class frequency among a word's allowed classes, with fixed class-index tie-breaking. It uses the same privileged aggregate class frequencies available in the oracle chain, but no word/count EM or neighboring-token inference. The uniform baseline reports **expected** accuracy under uniform candidate choice, not an arbitrary tied argmax. The correct class is always present, so this expectation is exactly 1 divided by candidate count per token.

| Noisy types | Affected query tokens, range | Word accuracy on affected | Ending accuracy on affected | Candidate class-frequency | Uniform candidates, expected |
|---|---:|---:|---:|---:|---:|
| 1% | 0–7 | 71.43 | 71.43 | 68.75 | 50.00 |
| 5% | 10–49 | 82.06 | 82.06 | 51.68 | 47.43 |
| 10% | 23–70 | 87.86 | 87.86 | 59.37 | 48.63 |
| 25% | 87–154 | 84.32 | 84.99 | 62.37 | 48.62 |
| 50% | 207–275 | 80.58 | 81.18 | 59.78 | 48.91 |
| 100% | 473 | 76.70 | 76.79 | 61.27 | 48.73 |

Conditional means weight each nonempty perturbation equally, not each token. At 1% one seed affects no query tokens, leaving only four nonempty replicates; conditional accuracies range 0–100%. That row is too small for a meaningful robustness claim. The rise from 5% to 10% affected-token mean reflects different selected word cohorts, not evidence that more noise helps. These affected cohorts change as the nested masks expand.

At 100%, the model's advantage over the class-frequency baseline is about 15.4 percentage points. Accuracy restricted to affected **originally singleton** query words is 76.48% / 76.62%, close to the full-query result; originally ambiguous words alone do not explain the result. This advantage concerns the complete fitted HMM versus this simple baseline. It does not independently isolate word repetition from ordered context; a shuffled-context control would be needed for that claim.

## Oracle initialization and objective drift

All oracle initializations start at 466/473 correct query tags (98.52%). Their mean final query accuracies are:

| Noisy types | Word oracle-start final | Ending oracle-start final |
|---|---:|---:|
| 1% | 98.44 | 98.44 |
| 5% | 97.80 | 97.80 |
| 10% | 97.46 | 97.46 |
| 25% | 95.22 | 95.31 |
| 50% | 89.98 | 90.36 |
| 100% | 81.73 | 81.86 |

Every oracle-start trajectory contains a strictly improving update with a net loss of correct development tags. At 100%, the objective-selected random solution has a higher objective than the oracle-start final solution for all five perturbations in both arms, despite roughly five percentage points lower query accuracy. The earlier objective/basin problem therefore remains once support becomes permissive. All runs converge under the declared tolerance; this is not an iteration-cap explanation or proof of global optimality.

The results are less fragile than an immediate failure after a few false positives, but even one false class per word produces substantial damage. The 100% row has 871 original true-supported pairs plus 863 false pairs: candidate-pair precision 50.23% with 100% reference-support recall. Those pair statistics do not determine token performance by themselves: frequent words, candidate identity, class transitions, and systematic error patterns matter. The observed curve should not be turned into a universal support-precision requirement.

## What to check next

The next useful control is missing true candidates. The current diagnostic guarantees perfect support recall, while a learned support model could exclude the reference class outright. On the same development data, deliberately remove selected true candidates while retaining a nonempty inventory, calculate the resulting token-level coverage ceiling, and separate unavoidable excluded-class errors from additional damage to still-covered tokens. This would distinguish candidate-retrieval coverage from contextual selection before investing in learning category support. A later context-shuffling control could measure how much of the observed baseline advantage depends on word order.

No result here establishes practical POS recovery on a new corpus or an unknown cipher. The oracle candidate inventory, oracle class-chain parameters, and repeated development evaluation must remain explicit.

## Reproduction and verification

Artifacts are under `experiments/results/grammar-restoration/iteration30/`: frozen perturbation schedules/configuration, 60 cell files containing 360 trajectories, emission matrices, objective-based selections, baseline/conditional summaries, a standalone SVG curve, and validation report. Existing frozen artifacts are unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_noisy_support_iteration30
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/voynich-matplotlib .venv/bin/python -m benchmarks.grammar_noisy_support_iteration30_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_noisy_support_iteration30_validate
```

Runners preserve existing outputs. Three new tests verify nested perturbations, exact false-candidate counts, retention of all reference candidates, deterministic schedules, class-renaming behavior given a renamed schedule, and cohort scoring including empty subsets. Validation checks every final fit/objective/cohort metric, all monotonic objective traces, selection and initializations, mask nesting, uniform/count baselines, and prior hashes, then fully replays all 12 oracle/random trajectories in the 100%-noise/seed 3001 cells. Independent flattened-token checks reproduce conditional counts. The combined relevant suite passes 302 tests. The 200 reserved sentences remain unscored.
