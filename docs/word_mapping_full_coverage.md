# Fully covered, large-budget development calibration

Reproduce the saved experiment and independently validate its artifacts:

```sh
.venv/bin/python -m benchmarks.word_mapping_full_coverage
.venv/bin/python -m benchmarks.word_mapping_full_coverage --validate
```

The default output is `experiments/results/word-mapping/full-coverage-large/`.
Use `--resume` to continue checkpoints with identical code and inputs, or
`--out` to start a separate experiment. Four independent worker processes run
searches; their seeded results agree with serial execution in integration tests.

The protocol uses five search seeds, one-to-one and homophonic ciphers, two
restarts, and budgets of 10,000 and 200,000 mutations per restart. Baseline,
trigram-only and collapse-weight-5 arms share the same candidates. Baseline
also refits position-shuffled controls. This totals 80 searches and 16.8 million
mutation evaluations. The larger budget has its own scaled cooling schedule.

Training expands to all cached Caesar source positions except the declared
development and test positions. It contains 16,548 words and supplies 4,987
candidate forms. The language model, morphology and candidates are built before
screening development segments. No evaluation word is inserted into candidates.

The cohort admits a complete scored segment only when it contains at least five
words and every word appears in the frozen candidate catalog. Of 76 development
segments containing 1,811 words, 11 segments containing 120 words qualify.
Rejected segments remain boundaries; the runner never joins them into invented
contexts. These are complete scored segments, not necessarily complete linguistic
sentences, because the tokenizer treats punctuation and abbreviations as boundaries.

Every observed ciphertext type is active. Both cipher families have an exact
recovery ceiling of 100%, and oracle comparisons use the complete active
dictionary. Truth is used only after optimization, in the parent process, to
evaluate archived mappings. Worker search inputs contain public ciphertext,
training resources and configuration. The final test split remains unscored.

This is a coverage-screened, same-author development calibration. Its substantial
screening attrition prevents treating it as an unbiased sample of all development
text or evidence of generalization to another author or the manuscript. A score
above truth establishes a counterexample for this objective; a score below truth
establishes a search shortfall without proving the objective is otherwise sound.
The collapse penalty can also penalize true homophonic mappings.

## Completed results

All 80 searches completed, consuming 16,800,000 mutation evaluations. Independent
validation rebuilt the foundation, models, fixtures, checkpoint identities,
archive scores, recovery metrics, oracle comparisons and paired summaries.
All 87 focused tests passed, including parallel/serial equivalence and resume.

Mean exact token recovery over five seeds (budgets are per restart):

| Cipher | Arm | 10,000 | 200,000 |
| --- | --- | ---: | ---: |
| One-to-one | Baseline mixture | 4.500% | 3.333% |
| One-to-one | Trigram | 3.500% | 1.333% |
| One-to-one | Collapse weight 5 | 1.500% | 1.500% |
| Homophonic | Baseline mixture | 3.500% | 0.167% |
| Homophonic | Trigram | 3.500% | 0.333% |
| Homophonic | Collapse weight 5 | 4.000% | 0.333% |

Mean objective fitness improved in every arm/cipher pair, while mean exact
recovery decreased in five pairs and was unchanged in one. Across the 30 paired
original-data seeds, accuracy improved in five, worsened in twenty and stayed
unchanged in five. Fitness gains therefore did not demonstrate recovery gains.

Of 60 original-data searches, 39 archived an incorrect dictionary above truth
and 21 remained below truth. All 30 larger-budget searches produced a complete-
dictionary counterexample, across both cipher families and all three arms.
The 21 search shortfalls all occurred at the smaller budget. Trigram scoring
and this collapse penalty did not remove objective misranking.

Baseline position-shuffled controls also improved substantially with the larger
budget, with mean fitness changes similar to the original-data baseline
(one-to-one: +362.14 control vs +368.03 original; homophonic: +369.71 vs +368.84).
These descriptive comparisons do not establish statistical significance.

The next algorithm work should target the objective and mapping constraints,
using these frozen development fixtures as regression instruments. For example,
evaluate cipher-family-appropriate multiplicity/frequency priors and report
their true-dictionary gaps before allocating another large search budget.
An injective constraint is appropriate for a declared one-to-one synthetic
cipher, but cannot be assumed for the manuscript or homophonic fixtures.
Any later cross-author or final-test evaluation needs a separately frozen protocol.
