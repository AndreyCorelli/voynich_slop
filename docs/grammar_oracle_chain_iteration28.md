# Iteration 28: oracle development transitions versus source mismatch

**Oracle development transitions do not prevent EM from corrupting grammatical classes.** Both word and ending arms lose correct tags on their first improving update over the full development corpus. From the same supervised emission initialization, query token accuracy eventually falls from 98.52% to 52.22% / 56.66%. This rules out source-transition mismatch as a sufficient explanation for the drift in this HMM; it does not prove that all first-order methods must fail.

## Controlled comparison

The experiment reuses iteration27's already inspected development corpus: 200 background sentences plus 40 query sentences, 2,052 tokens total and 473 query tokens. The eight classes, anonymous observations, emission parameterizations, emission priors, five random seeds, 600-update cap, relative stopping tolerance 1e-7, and EM implementation are unchanged. No fresh targets or reserved sentences are scored.

The only model change replaces the source-fitted start/transition/termination probabilities with counts from the **exact development reference tag sequences**, using the same .5 pseudocount for every start, transition, and termination entry. Transitions and termination jointly normalize each state's outgoing probabilities. These oracle chain parameters are fixed throughout EM. All oracle-start and random-start emission matrices match their source-chain counterparts; only inference under the chain changes. Source results are reused unchanged from iteration27.

This is a privileged, in-sample diagnostic: the chain already knows aggregate grammatical transitions from the same sentences it decodes, and oracle emission initialization uses their reference labels as well. It is not a deployable unsupervised method, a held-out result, or a guaranteed mathematical ceiling on class accuracy. The development chain has fewer training sentences than the original source chain; the intended control removes population mismatch using the exact sample, rather than matching estimation variance.

## Oracle-start trajectories

Query-token results; balanced accuracy averages recall across the eight classes:

| Fixed chain | Emissions | Initial token accuracy | Final token accuracy | Initial balanced accuracy | Final balanced accuracy | Updates to convergence |
|---|---|---:|---:|---:|---:|---:|
| Source | Word | 98.52% | 54.55% | 98.24% | 50.89% | 325 |
| Oracle development | Word | 98.52% | 52.22% | 98.23% | 48.14% | 539 |
| Source | Ending | 98.73% | 53.07% | 98.48% | 48.44% | 221 |
| Oracle development | Ending | 98.52% | 56.66% | 98.23% | 50.99% | 270 |

Identical emission initialization does not require identical initial decoding: chain probabilities affect the class posterior. All four oracle-start runs converge under the frozen tolerance. Oracle development transitions change the trajectories but give no general rescue: word accuracy is lower and ending accuracy somewhat higher than with source transitions. These are descriptive development comparisons, not estimates of held-out improvement.

Across all 2,052 development tokens, oracle-chain word correctness falls from 2,038 to 1,108 (99.32→54.00%); ending falls from 2,036 to 1,192 (99.22→58.09%). The regularized objectives rise 580.28 and 533.00 log units along those respective trajectories. Cross-chain objective levels are not used to rank models.

## First improving corruption

The first corruption and first net accuracy loss over **all development tokens** occur at update 1 for both oracle-chain arms. This is not an immediate query loss: the first update gains one correct query tag and loses none. The query subset's first net accuracy decline occurs at update 3 for word and update 2 for ending.

| Oracle-chain arm | Changed tokens | Correct → wrong | Wrong → correct | All-token correct, before → after | Query correct, before → after |
|---|---:|---:|---:|---:|---:|
| Word | 8 | 7 | 1 | 2038 → 2032 | 466 → 467 |
| Ending | 9 | 8 | 1 | 2036 → 2029 | 466 → 467 |

Word losses include `deludendum` verb→adjective, three adposition `cum` tokens→conjunction, two pronoun/determiner `hic` tokens→adverb, and `solum` adverb→adjective. The sole gain is a query `hic` annotated adverb. The ending arm also loses noun `die`→adverb, conjunction `quia`→pronoun/determiner, and verb `occisa`→adjective, while its set of changed `hic` tokens differs. The exact sentence IDs, positions, class posteriors, and emission tables are saved in the audit. Claims concern the fixed reference POS inventory; some words admit genuine lexical ambiguity.

First-update component changes, in natural-log units over the entire development corpus:

| Component | Oracle-chain word Δ | Oracle-chain ending Δ |
|---|---:|---:|
| Expected start log probability | +0.841 | +1.973 |
| Expected transition log probability | +6.291 | +14.743 |
| Expected termination log probability | +1.098 | +2.842 |
| Expected emission log probability | −59.346 | −130.615 |
| Posterior path entropy | +60.763 | +131.904 |
| **Observed-data log likelihood** | **+9.647** | **+20.848** |
| Emission log prior | +3.946 | +16.546 |
| **Regularized objective** | **+13.592** | **+37.394** |

The decomposition independently verifies likelihood = expected log joint + posterior entropy. Entropy is part of this identity, not a separately added bonus; chain terms change through posterior assignments even though parameters stay fixed. As in iteration27, unregularized likelihood rises too, so regularization alone does not explain acceptance of these particular damaging updates. A zero-prior refit would take different updates and has not been tested here.

The fixed reference-path joint probability instead loses 7.962 / 28.903 log units. Including the prior still gives a loss 4.016 / 12.357. The observed-word marginal criterion improves by reallocating mass to alternative class paths, despite damage to reference tags. This behavior survives an oracle estimate of first-order development tag transitions.

## Random-start control

Each oracle-chain arm repeats seeds 2601–2605 with the same initial emission matrices as iteration27. Nine of ten random runs converge; word seed2602 reaches the 600-update cap. Selection uses only the regularized objective within each chain/arm.

| Fixed chain | Emissions | Objective-selected seed | Query token accuracy | Query balanced accuracy |
|---|---|---:|---:|---:|
| Source | Word | 2601 | 17.76% | 14.56% |
| Oracle development | Word | 2604 | 31.29% | 28.62% |
| Source | Ending | 2601 | 17.76% | 14.85% |
| Oracle development | Ending | 2604 | 30.02% | 28.28% |

The oracle chain helps these selected random-start solutions relative to the source-chain control, but they remain poor. Unlike the source-chain runs, none of the five oracle-chain random runs exceeds its corresponding oracle-start final objective. There is still an optimization/basin problem in addition to demonstrated drift away from reference classes. Neither the seed sweep nor oracle initialization proves global optimality.

## What this establishes

Replacing source transitions with the exact corpus's smoothed class-transition counts is insufficient to preserve nearly correct classes. The failure therefore includes the unlabeled latent-class objective and its representation of context, not merely source-domain mismatch. The control does not uniquely blame the first-order assumption: word ambiguity, unconstrained emissions, regularization, and latent identifiability remain possible contributors. It also does not establish dependency restoration; no new parsing claim is evaluated.

Before building a richer contextual chain, a cheap next control is to restrict each word's emission support to its reference-observed POS classes, using the same development material and oracle chain. This explicitly privileged constraint separates corruption through invented word/class assignments from unresolved ambiguity among attested classes. If drift persists there, compare higher-order context on the remaining ambiguous tokens; if it disappears, focus first on learning reliable category support. Both branches still require a usable anonymous class signal before returning to parsing.

## Reproduction and checks

Artifacts: `experiments/results/grammar-restoration/iteration28/` contains frozen chain/configuration inputs, all 12 new trajectories, first-corruption audits, source/oracle comparison, and validation report. Previous artifacts remain unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_oracle_chain_iteration28
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_oracle_chain_iteration28_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_oracle_chain_iteration28_validate
```

Runners preserve outputs. Validation independently counts every oracle-chain start/transition/stop probability, checks identical emission starts against the source control, replays all 12 trajectories, verifies every objective trace entry and initial/final accuracy, reproduces both first corruptions and the likelihood decomposition, recomputes the comparison audit, and checks frozen prior hashes. The existing relevant 295-test suite is rerun; no implementation changes to the HMM or earlier benchmarks are required. The 200 reserved sentences remain unscored.
