# Objective diagnostics and multi-seed ablations

The development runner distinguishes a search that cannot find a better
dictionary from an objective that rewards incorrect dictionaries. Ground truth
is used only in evaluation after each completed search; it never generates
candidates, seeds the optimizer, selects mutations or changes run budgets.

## Reproduce the short pilot

```sh
.venv/bin/python -m benchmarks.word_mapping_foundation \
  --out experiments/results/word-mapping/foundation-calibration \
  --max-words 12000 --prepare-only
.venv/bin/python -m benchmarks.word_mapping_foundation \
  --out experiments/results/word-mapping/foundation-calibration --validate
.venv/bin/python -m benchmarks.word_mapping_ablation \
  --foundation experiments/results/word-mapping/foundation-calibration \
  --out experiments/results/word-mapping/ablation-calibration \
  --seeds 11 22 33 --budgets 500 2500 --kinds one-to-one --controls
.venv/bin/python -m benchmarks.word_mapping_ablation \
  --out experiments/results/word-mapping/ablation-calibration --validate
```

Use a new output directory for changed inputs or settings. `--resume` skips
completed jobs and continues incomplete checkpoints; a changed protocol, code,
split, model, candidate catalog or public input rejects resume. `--plan` displays
the run count and total evaluation budget without starting optimization.

The 12,000-word prefix finishes its last sentence and is split into contiguous
complete-segment train/development/test groups. `--prepare-only` builds the
training model and candidates without scoring either held-out split or creating
test fixtures. The ablation runner uses development passages only. It reads
the final-test split for overlap auditing but does not score or optimize it.

Default runner budgets are 10,000 and 100,000 evaluations **per restart**,
with three search seeds and both one-to-one/homophonic fixtures. The short
pilot overrides those budgets and uses one fixture family. Cipher seed and
control seed remain fixed across arms; search seeds vary independently.

## Experimental comparisons

The baseline uses the 50/50 bigram/trigram mixture, frequency initialization and
zero collapse penalty. Each arm changes one factor:

| Arm | Change from baseline |
| --- | --- |
| `unigram` | Frequency-only language objective |
| `bigram` | Bigram conditional likelihood |
| `trigram` | Trigram conditional likelihood |
| `random-init` | Random initial dictionary |
| `lemma-aware-init` | Lemma-frequency initialization |
| `collapse-1` | Collapse weight 1 |
| `collapse-5` | Collapse weight 5 |

Candidate forms, active ciphertext types, smoothing, mutation mixture and
restart count remain shared. The unigram prior still supports smoothing in
the conditional profiles. This is a one-factor ablation, not a factorial
optimization or an automatic hyperparameter-selection procedure.

All conditions receive the same specified budgets. With `--controls`, each
arm/seed/budget also refits within-segment shuffles, position-conditioned
shuffles and bigram surrogates. The control seed is fixed across budget pairs
and its preserved properties are audited. Original plaintext no longer aligns
with shuffled positions, so controls report fitted likelihood and coverage,
without fabricated recovery or truth-dictionary metrics.

The larger-budget run has a longer cooling schedule, rather than extending an
identical short-run prefix. Paired changes therefore describe independent
annealing runs with scaled schedules. Compare recovery across seeds; fitness
gains alone do not justify a long run.

## Reading the truth diagnostic

`truth_diagnostic` reports:

- Missing true candidate forms and ciphertext types with conflicting plaintext
  owners (lossy encodings).
- Active and comparable token/type coverage and the candidate-constrained
  deterministic token-accuracy ceiling, with inactive words counting as errors.
- The true dictionary's likelihood, collapse penalty and objective, compared
  with archived dictionaries on an identical mask of ciphertext types.
- The best archived score difference from truth, plus a diagnosis:
  `incorrect_mapping_outranks_truth`, `incorrect_mapping_ties_truth`,
  `search_below_truth`, `truth_recovered_in_comparison` or `no_comparable_truth`.

If every active type has an unambiguous true form in the candidate set,
`comparison_scope` is `complete_active_dictionary`. Otherwise, both the oracle
and archived mappings are restricted to the same candidate-covered,
unambiguous types. UNKNOWN barriers and EOS events therefore agree exactly.
That comparison is explicitly labeled `candidate-covered_unambiguous_subset`;
it cannot establish a complete-dictionary search diagnosis.

The best projected archived candidate may differ from the candidate ranked
highest on the optimizer's full active vocabulary. Its archive index is saved.
The true full plaintext LM score, including any OOV words, is also recorded
as **noncomparable** and is never used to subtract a misleading score gap.
No missing evaluation form is added to the candidate vocabulary.

An incorrect archived dictionary scoring above truth is a concrete objective
counterexample for the declared comparison. A best score below truth shows a
search shortfall on that comparison; it does not prove truth is the global
optimum or that the objective has no other counterexamples. Ties reveal that
fitness cannot distinguish those dictionaries.

## Reports and validation

`manifest.json` freezes code/source identities, models, splits and the plan
before any search. `plan.json` enumerates all jobs and their total budget.
Each job retains its checkpoint, public input, candidate archive and a
checksummed result. Evaluation-only artifacts live under `truth/`.

`report.json` groups fitness, exact/lemma recovery, coverage, collapse counts
and candidate ceilings across seeds. It also reports paired budget changes,
including the number of seeds improving, worsening or unchanged. Raw fitness
values must not be compared across different scoring profiles. Control
comparisons retain coverage and prediction-event counts because UNKNOWN
layout changes can change the number of scored EOS events.

Validation regenerates fixtures and truth from the frozen development split,
rebuilds models/candidates, verifies saved archives and checkpoints, fully
recomputes their objectives, and reconstructs all oracle comparisons, recovery
metrics and paired summaries. It does not rerun searches or use final-test
scores. No statistical-significance or manuscript-inference gate is declared
passed by this pilot.

Run the focused tests with:

```sh
.venv/bin/python -m pytest \
  tests/unit/test_word_mapping_diagnostics.py \
  tests/integration/test_word_mapping_ablation.py -q
```

They distinguish objective counterexamples, search shortfalls and ties; verify
mask/domain agreement, lossy ceilings and legacy/default n-gram identities;
and test paired budgets, public/truth separation, untouched final-test inputs,
complete resume and rejection of altered artifacts.

## Short-pilot results

The saved `ablation-calibration/` experiment completed and validated all 192
runs (288,000 mutation evaluations). Eight arms each used three search seeds,
two budgets and the original plus three refitted controls. The test split
remains unscored.

Mean exact token recovery across the three seeds:

| Arm | 500 evaluations | 2,500 evaluations |
| --- | ---: | ---: |
| Baseline mixture | 0.313% | 0.166% |
| Unigram | 0.497% | 0.147% |
| Bigram | 0.129% | 0.000% |
| Trigram | 0.074% | 0.442% |
| Random initialization | 0.258% | 0.000% |
| Lemma-aware initialization | 0.166% | 0.000% |
| Collapse weight 1 | 0.939% | 0.166% |
| Collapse weight 5 | 0.755% | 0.000% |

Mean fitness increased in every arm, but mean recovery decreased in seven of
eight. The trigram mean improvement was concentrated in one improving seed;
one seed worsened and one was unchanged. Three seeds do not establish a
statistical-significance or generalization result.

Of the 48 original-data runs, 45 contained an incorrect archived mapping with
a higher matched-subset score than truth. The remaining three were short-budget
random-initialization runs below truth; their larger-budget counterparts also
produced counterexamples. No penalty or initialization tested here solved the
misranking problem.

The development passage contains 1,811 tokens. The 2,955 training-derived
candidates cover 74.05% of those tokens, but only 100 ciphertext types are active
(723 tokens, 39.92%). Four of those types lack their true candidate forms, so
the oracle comparison covers 96 types and 708 tokens. Its candidate-constrained
exact recovery ceiling is 39.09% of all tokens. These are **partial-dictionary**
objective counterexamples, not evidence that fully observed Latin n-grams
cannot distinguish plaintext.

The next refinement should audit fully covered, disjoint synthetic fixtures
with all their ciphertext types active, reporting coverage exclusions explicitly.
Then compare their oracle gaps with the partial-dictionary gaps before changing
UNKNOWN/context treatment or adding stronger mapping priors. Increasing budgets
on the present objective is not supported by this pilot.

All 84 focused tests (including the existing corpus tests) pass. Validation
reconstructed the saved models, archives, oracle diagnostics and all paired
summaries without rerunning searches.
