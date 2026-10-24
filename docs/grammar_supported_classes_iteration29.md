# Iteration 29: restrict words to their oracle-observed grammatical classes

**Oracle word/class support prevents the large EM collapse, but does not eliminate mistakes among attested classes.** Both emission arms converge to 98.52% query token accuracy, versus 52.22% / 56.66% without the support constraint. This is a strongly privileged result: 438/473 query tokens have only one allowed class and must be tagged correctly. On the 35 genuinely ambiguous query tokens, accuracy is 28/35 (80%), just two tokens above an oracle word-majority baseline. The remaining problem is not initialization instability in these runs: all 12 oracle/random-start trajectories finish with identical token predictions.

## Controlled diagnostic

The same previously inspected corpus supplies 200 background sentences and 40 query sentences: 2,052 tokens, of which 473 are queries. The oracle development start/transition/termination probabilities from iteration28 remain fixed. The eight POS classes, anonymous word/ending IDs, two emission parameterizations, seeds 2601–2605, maximum 600 updates, and relative objective stopping tolerance 1e-7 are unchanged. No new target sentences, dependency scoring, or reserved-sentence scoring occurs.

For each anonymous word type, the support mask contains every POS class assigned to that word anywhere in these 240 reference sentences. All other emission probabilities are fixed to **exact zero** throughout inference and EM. The mask is computed once; labels do not enter subsequent EM updates. This is an in-sample oracle candidate inventory, not learned category support, a dictionary usable on an unknown language, or evidence of grammatical restoration.

The original priors assign positive mass to forbidden classes, so they cannot be retained literally under exact zeros. The corpus-frequency word prior is conditioned on each state's allowed words and normalized. For ending sharing it is then factored into supported ending and within-ending distributions, with zero mass on inactive groups. Prior strengths remain 1 per state and .2 per active ending group. The constrained M-step optimizes this explicitly defined supported objective; it is not “fit unrestricted probabilities and mask afterward.” Objective values are compared only within a fixed arm/support, never against the unrestricted objective.

Oracle initialization uses supervised word/class counts with the support-conditioned prior: the constrained complete-label MAP estimate. This changes initial emission probabilities from iteration28; identical probabilities are not claimed. Random starts use the original Gamma(2) × corpus-frequency draws, masked and row-normalized with the same seeds. All12 fits converge. Oracle runs take 18 updates; random runs take 22–25.

## How much information the oracle supplies

There are 863 word types, of which 856 have one allowed class and only 7 have multiple classes. The support contains 871 allowed word/class pairs out of 6,904 possible pairs. Ambiguous types cover 194/2,052 development tokens (9.45%) and 35/473 query tokens (7.40%).

| Ambiguous word | Reference class counts over all development tokens |
|---|---|
| et | adverb 7, conjunction 152 |
| cum | adposition 5, conjunction 9 |
| quod | pronoun/determiner 5, adverb 1, conjunction 2 |
| hic | pronoun/determiner 4, adverb 1 |
| nisi | adverb 1, conjunction 1 |
| solum | adjective 1, adverb 1 |
| ne | adverb 3, conjunction 1 |

These are reference annotation categories; some distinctions involve genuine lexical ambiguity or annotation conventions. Support for singleton and rare words is unusually informative because labels from the same query tokens are included. The high aggregate accuracy therefore mostly measures the constraint working as specified.

## Outcomes

Both supported arms finish with exactly the same predictions, including across all five random starts. Rows below describe the oracle-start runs; the objective-selected random start is seed2602 in each arm and has the same final tags.

| Model | Query correct /473 | Query token accuracy | Query balanced accuracy | Ambiguous query correct /35 |
|---|---:|---:|---:|---:|
| Unrestricted word, iteration28 oracle start | 247 | 52.22% | 48.14% | 24 |
| Unrestricted ending, iteration28 oracle start | 268 | 56.66% | 50.99% | 24 |
| Supported word, initial | 466 | 98.52% | 98.23% | 28 |
| Supported ending, initial | 466 | 98.52% | 98.23% | 28 |
| Supported word, converged | 466 | 98.52% | 98.21% | 28 |
| Supported ending, converged | 466 | 98.52% | 98.21% | 28 |
| Oracle word-majority reference | 464 | 98.10% | 97.72% | 26 |

The word-majority reference uses counts from **the same labeled development corpus**, with fixed class-index tie-breaking; it is another privileged comparator, not an independently trained baseline. On ambiguous query tokens its accuracy is 74.29%, versus 80% for the supported HMM. Ambiguous-only balanced accuracy is 58.46% versus 63.23%, over the five classes present in that subset. This tiny, reused 35-token sample does not establish a reliable contextual advantage.

Across all 2,052 development tokens, supported word oracle initialization starts at 2,038 correct (99.32%) and ending at 2,036 (99.22%); both finish at 2,031 (98.98%). On ambiguous tokens alone, both finish at 173/194 (89.18%), compared with the word-majority reference's 175/194 (90.21%). The HMM does not beat word majority uniformly across subsets. Its query accuracy first rises to 467/473, then returns to 466; equal initial/final totals hide a corrected `hic` and a spoiled `cum`.

In the unrestricted iteration28 final predictions, 932/944 word-arm errors and 848/860 ending-arm errors assign a word to a class absent from its development reference support. Query figures are 221/226 and 200/205 errors. These are descriptive error audits, not a claim that each error could be removed by a deployable classifier. The supported experiment changes the feasible emissions and conditions their priors; the oracle mask provides substantial answer information.

## Residual objective corruption

The first strictly improving supported EM update still loses correct tags within the permitted classes. All losses at that update are in the background sentences; one query `hic` improves in each arm.

| Supported arm | First-update changed tokens | Correct → wrong | Wrong → correct | All-token correct, before → after | Query correct, before → after |
|---|---:|---:|---:|---:|---:|
| Word | 7 | 6 | 1 | 2038 → 2033 | 466 → 467 |
| Ending | 5 | 4 | 1 | 2036 → 2033 | 466 → 467 |

Word losses involve adposition `cum`→conjunction, pronoun/determiner `hic`→adverb, and adverb `solum`→adjective. The ending arm loses fewer background `hic` tokens immediately but reaches the same final assignments. Every changed word has multiple oracle-attested classes; no forbidden pair is ever used.

| First-update score change | Word | Ending |
|---|---:|---:|
| Observed-data log likelihood | +2.127 | +2.127 |
| Emission log prior | −0.062 | −0.044 |
| **Regularized objective** | **+2.065** | **+2.082** |
| Fixed reference-path log joint | −1.359 | −1.394 |
| Reference-path joint plus prior | −1.422 | −1.438 |

Here the prior actually worsens while likelihood improves, again exposing a residual mismatch between the unlabeled objective and reference tagging. The posterior identity checks likelihood gain = old-posterior expected emission-log change + KL(old posterior ∥ new posterior): 1.387+0.740 for each arm, approximately. Over the full oracle-start trajectory, objective gains are 4.031 and 3.921 units, much smaller than the unrestricted drifts; objective scales differ under the changed priors, so this is not a cross-model fit comparison.

## Interpretation and next step

Under this strong oracle constraint, the large failure is avoidable without a richer contextual model. Useful word/category candidate support is therefore a concrete prerequisite worth testing before expanding parse complexity. The experiment does **not** show how to obtain that support from anonymous ciphertext; it also leaves modest likelihood-driven errors among attested categories.

The next inexpensive diagnostic is a support-noise stress test on the same development data: retain all reference-supported classes, then add false candidate classes to increasing fractions of word types using several frozen random seeds. Report ambiguous/affected-token performance separately from still-forced singleton tokens and compare against a candidate-only baseline. This measures how precise a learned candidate inventory would need to be. A near-perfect result that vanishes after a few extra candidates would not justify building a candidate learner or claiming progress on actual cipher grammar. Higher-order context can then be tested on the residual genuinely ambiguous words.

## Reproduction and verification

New files: `src/voynich_smt/supported_emissions.py`, the iteration29 runner/evaluator/validator, and four mechanism tests. Existing HMM code and frozen prior artifacts are unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_supported_classes_iteration29
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_supported_classes_iteration29_evaluate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_supported_classes_iteration29_validate
```

Artifacts are under `experiments/results/grammar-restoration/iteration29/`; runners preserve existing outputs. Tests verify that unrestricted support reproduces the old priors/update, compare constrained M-steps with an independent numerical optimizer, enumerate all HMM paths with exact-zero emissions, and check monotonic supported EM including inactive ending groups. Validation independently counts the gold support, replays all 12 full trajectories and their objective/accuracy rows, checks every iterate's normalization/forbidden zeros/singleton correctness, reproduces the first-corruption updates, confirms identical final predictions across all 12 runs, and checks frozen prior hashes. The combined relevant suite passes 299 tests. The 200 reserved sentences remain unscored.
