# Iteration 27: does unlabeled EM corrupt oracle grammatical classes?

**Yes. Both emission models lose correct classes on their first strictly improving EM update.** From supervised oracle initialization, word-model query token accuracy falls from 98.52% to 54.55% at convergence; ending-sharing accuracy falls from 98.73% to 53.07%. Both likelihood and the regularized objective improve. Several random starts end with higher objectives and much worse grammatical accuracy. This demonstrates objective misalignment in this fixed-transition HMM, alongside initialization sensitivity; a better starting point alone does not preserve grammatical classes.

## Scope and frozen choices

This is a diagnostic on **already inspected development material**, not another fresh test. It reuses iteration26's calibration 40 plus background 200: 240 sentences, 2,052 tokens, including 473 query tokens. Fixed pooled transitions come from the same 767 source sentences and eight POS classes. No fresh target scoring, dependency evaluation, threshold changes, or new sentence selection occurs. The 200 reserved sentences remain unscored.

The two arms retain their original priors: word-only emissions and factorized ending-sharing emissions. For each arm, supervised counts from all 2,052 development tokens initialize the same smoothed oracle-emission estimate used in iteration26. Gold labels are then removed from the EM updates; they are used to measure the trajectory. Oracle initialization is privileged and in-sample. It is nearly correct, **not an exact 100%-correct token assignment**, because an emission table can retain ambiguity and contextual decoding can disagree with the annotated tag.

Each arm also repeats the original five random initializations, with the same seeds 2601–2605. The cap is 600 updates and relative regularized-objective tolerance1e-7, frozen before these runs. Both oracle runs and nine of ten random runs converge; word seed2605 reaches the cap. There is no selection by gold accuracy. The objective-selected random run is seed2601 in each arm. Comparisons of objective values are only within an arm because the priors differ.

## Whole trajectory

Percentages below use the previously inspected 473-token query subset. Balanced accuracy averages the eight class recalls.

| Arm/start | Updates | Token accuracy, initial → final | Balanced accuracy, initial → final | Objective, initial → final |
|---|---:|---:|---:|---:|
| Word/oracle | 325 | 98.52 → 54.55 | 98.24 → 50.89 | −12923.54 → −12365.80 |
| Ending/oracle | 221 | 98.73 → 53.07 | 98.48 → 48.44 | −13128.92 → −12603.61 |
| Word/best random objective | 445 | — → 17.76 | — → 14.56 | — → −12354.79 |
| Ending/best random objective | 370 | — → 17.76 | — → 14.85 | — → −12587.61 |

Across all development tokens, oracle-initialized word accuracy falls from 2,035/2,052 (99.17%) to 1,140/2,052 (55.56%). Ending accuracy falls from 2,036/2,052 (99.22%) to 1,141/2,052 (55.60%). These are large trajectory losses, not merely seed-to-seed fluctuations or a handful of first-step homographs.

Three of five random runs finish above the oracle-start final objective in each arm. Oracle initialization still preserves substantially more grammatical information than the objective-selected random start, so there is also a basin/initialization effect. Neither result identifies the global optimum, and objective values do not certify grammatical quality.

## The first corruption

The first accuracy-losing update is iteration 1 for both arms. It is also the first update with a net loss in total correct tokens.

| Arm | Changed tokens | Correct → wrong | Wrong → correct | All-corpus correct, before → after | Query correct, before → after |
|---|---:|---:|---:|---:|---:|
| Word | 12 | 9 | 2 | 2035 → 2028 | 466 → 464 |
| Ending | 13 | 10 | 2 | 2036 → 2028 | 467 → 464 |

One additional change in each arm remains wrong under both assignments. Detailed per-token records include sentence ID, position, anonymous word ID, plaintext for inspection, reference/before/after classes, eight posterior probabilities, and eight emission probabilities before/after. These labels and plaintext belong only to the audit, not the EM update.

The word arm's first changes involve `quod` (pronoun/determiner → conjunction), `hic` (pronoun/determiner → adverb), and `cum` (adposition → conjunction). Two `quod` occurrences improve and several deteriorate. Query losses are one pronoun `quod` and one adposition `cum`; another query `quod`, annotated adverb, remains wrong while switching classes. The ending arm additionally changes a correctly tagged query `septies` from adverb to verb. These are contextual token decisions, not a single global word-to-class dictionary substitution. Some distinctions involve homographs and annotation conventions; the claims here concern agreement with the fixed eight-class reference inventory.

## Why the score improves

Changes in objective components at the first update, in natural-log units over all development sentences:

| Component | Word Δ | Ending Δ |
|---|---:|---:|
| Expected start log probability | +0.518 | +3.067 |
| Expected transition log probability | +10.879 | +34.541 |
| Expected termination log probability | +1.793 | +3.593 |
| Expected emission log probability | −85.408 | −188.248 |
| Posterior path entropy | +83.942 | +179.599 |
| **Observed-data log likelihood** | **+11.724** | **+32.552** |
| Emission log prior/regularizer | +4.320 | +18.270 |
| **Regularized objective** | **+16.044** | **+50.821** |

An independent log-space computation verifies `log likelihood = expected log joint + posterior entropy`. Start, transition, and termination parameters never change; their expected contributions change because the posterior over class paths changes. Entropy is an identity term in marginal likelihood, not a separately added entropy bonus. The model raises the summed probability of observed words by redistributing probability over latent paths, although decoded reference tags get worse. The table does not attribute every changed token to a unique causal component.

A second, fixed-old-posterior identity verifies the EM accounting:

| Identity term | Word | Ending |
|---|---:|---:|
| Expected emission-log change under old posterior | +2.007 | +3.392 |
| KL(old path posterior ∥ new path posterior) | +9.717 | +29.159 |
| Sum: observed-likelihood change | +11.724 | +32.552 |

Regularization contributes to the gain but does **not** explain it alone: the unregularized observed likelihood also rises on these same damaging moves. This does not predict what a separately fitted zero-prior model would do; its update would differ.

For the **fixed reference class paths**, the joint log probability instead falls 9.084 / 33.715 units. Adding the prior still gives a loss of 4.764 / 15.445. Reference-path log posterior falls 20.808 / 66.266. Thus the improvement is not an improvement to the reference path: marginalization over alternative class paths rewards a different solution. The oracle initialization already maximizes the smoothed complete-label emission objective; unconstrained EM optimizes a different, unlabeled criterion.

## Implication and next diagnostic

This experiment rules out “we only need a good initialization” as a sufficient explanation for this model's failure. It also shows that turning off a smoothing advantage is not an established fix: likelihood itself accepts the first corrupting update. The evidence applies to this source-transition HMM and development corpus, not to every possible grammatical objective.

The next controlled check should separate **source-transition mismatch** from the information lost by a first-order class chain. On the same development data, repeat oracle-start drift with (1) source transitions, (2) oracle development transition counts, and (3) a richer contextual class model, keeping the emission parameterization fixed. Oracle development transitions are a diagnostic upper bound. If even that first-order oracle chain corrupts classes, changing the source domain alone is insufficient. Measure first-update losses and full trajectories before proposing another unlabeled fitting criterion; reserve richer-model work until this cheap chain control is understood.

## Artifacts and verification

New artifacts live in `experiments/results/grammar-restoration/iteration27/`: the frozen manifest, all 12 trajectories, initial/final emissions, first-corruption emission tables, component decompositions, changed-token audit, and validation report. Earlier iteration26 files remain unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_oracle_emission_challenge_iteration27
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_oracle_emission_challenge_iteration27_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_oracle_emission_challenge_iteration27_validate
```

Runners preserve existing artifacts. Independent exhaustive-path tests verify all likelihood-decomposition components and the posterior-KL identity on tiny variable-length examples. Validation replays all 12 full trajectories, checks every objective trace entry, initial/final class scores, both first-corruption updates, and all frozen input hashes. The combined relevant suite passes 295 tests. No grammatical restoration claim follows from the objective gains.
