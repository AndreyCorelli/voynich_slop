# Frequency and mapping-constraint calibration

The large-budget covered experiment found incorrect dictionaries above truth
in every longer search. This refinement adds optional constraints and a
training-only frequency penalty while preserving the existing default objective.

## Objective and constraint

The frequency penalty is `N KL(q || p)`, where `q` is the decoded empirical
surface-word distribution over active tokens and `p` is the smoothed training
surface distribution normalized over frozen candidate forms. EOS, BOS and
UNKNOWN tokens do not contribute. Ciphertext token counts mapping to the same
surface are combined, including homophonic owners. With weight `w`, the objective
subtracts `w * N KL(q || p)` from language-model likelihood, in addition to any
existing collapse penalty. This measures departure from training frequencies;
it does not assume a short held-out passage has exactly the training distribution.

The injective option requires distinct active ciphertext types to use distinct
surface forms. Replacements into occupied forms become swaps; replacements into
unused forms remain possible. Initialization repairs duplicate assignments using
training candidates, or fails when there are too few candidates. This preserves
the constraint and reachability without accessing truth. The calibration schedules
injective arms only for declared one-to-one synthetic ciphers, never homophonic
ciphers or manuscript inputs. The generic API exposes the assumption explicitly.

Frequency updates are incremental over affected surface token counts. Independent
full scoring validates checkpoints and archived objectives. Checkpoints retain
the frequency accumulator to preserve exact resumed trajectories. Configurations
and source identities are hashed; historical runs remain preserved but their
checkpoints cannot be resumed using changed search code.

## Frozen development comparison

```sh
.venv/bin/python -m benchmarks.word_mapping_objective_refinement --plan
.venv/bin/python -m benchmarks.word_mapping_objective_refinement
.venv/bin/python -m benchmarks.word_mapping_objective_refinement --validate
```

The default output is `experiments/results/word-mapping/objective-refinement/`.
The experiment reuses the covered foundation's 120 tokens, 11 scored segments,
4,987 training-derived candidates and the same fixture seed. The training and
test positions, screened cohort, cipher realizations and active vocabulary remain
fixed. This retains the same-author and coverage-screening limitations described
in [the covered calibration](word_mapping_full_coverage.md). Final test is unscored.

Five search seeds use two restarts and paired budgets of 10,000 and 50,000
evaluations per restart. Baseline, frequency-weight-1 and frequency-weight-5 arms
run on both cipher families. Injective and injective-plus-frequency-weight-1 arms
run on one-to-one only. Baseline position-shuffled controls provide a matched
reference. This totals 100 searches and 6 million mutation evaluations.
Weights and budgets are fixed before these searches; this is a development
comparison, not an independent final evaluation or automatic hyperparameter choice.

All 96 focused tests pass. New tests verify homophonic token aggregation, local
deltas against independent full scoring across 1,200 joint changes, exact resume
across initialization modes, infeasible injective domains, declared-family job
scheduling and an exhaustive injective mutation graph. Integration tests verify
serial/parallel agreement and artifact validation for the new objective options.

## Results

All 100 searches completed their frozen budgets: 6,000,000 evaluations.
Independent validation reconstructed all 100 checkpoints, archives, full objectives,
oracle diagnostics, recovery metrics and paired summaries successfully.
The two public fixture artifacts match the earlier covered experiment exactly, and all
five short-budget one-to-one baseline archives reproduce exactly despite the
new optional implementation paths.

Mean exact token recovery across five seeds:

| Cipher | Arm | 10,000 | 50,000 |
| --- | --- | ---: | ---: |
| One-to-one | Baseline | 4.500% | 2.333% |
| One-to-one | Frequency weight 1 | 4.167% | 5.667% |
| One-to-one | Frequency weight 5 | 5.667% | 5.333% |
| One-to-one | Injective | 3.500% | 2.167% |
| One-to-one | Injective + frequency weight 1 | 3.167% | 3.833% |
| Homophonic | Baseline | 3.500% | 1.167% |
| Homophonic | Frequency weight 1 | 4.833% | 4.500% |
| Homophonic | Frequency weight 5 | 4.500% | 5.500% |

Frequency weighting improved some descriptive recovery means, but did not resolve
objective misranking. Of 80 original-data searches, 68 produced a complete-active-
dictionary counterexample and 12 remained below truth. All 40 larger-budget
original searches found an incorrect dictionary above truth. Every frequency-
weighted original search did so at both budgets. Raw objective magnitudes across
different weights are different scores and must not be treated as directly
comparable fitness gains.

The true plaintext has a frequency penalty of 304.74 and LM likelihood of
-901.87 in both cipher realizations. At the larger budget, the frequency-weight-5
solutions have mean penalties of 156.94 (one-to-one) and 158.10 (homophonic),
and mean LM likelihoods of -597.43 and -587.19. They therefore beat truth in
both objective components. The prior rewards dictionaries whose frequencies
look more like training text than this short screened passage does.

Injectivity removes collapse exactly, but its larger-budget mean LM likelihood
is -705.98, still above truth at -901.87. The constraint excludes many degenerate
dictionaries without identifying the true one. Unconstrained frequency weighting
also increases mean collapse: in one-to-one at the larger budget, baseline has
12 excess assignments, weight 1 has 15.2 and weight 5 has 20.4. Homophonic collapse
can be legitimate, but all these cases still have low recovery.

These options remain experimental and disabled by default. The results do not
support promoting either refinement or spending another large budget on these
scores. Next calibration should increase independent natural-text context and
test whether the scoring model can identify the dictionary there, while accounting
for finite-sample frequency uncertainty. It should retain oracle counterexamples
as regression evidence rather than interpreting improved fitness as recovery.
