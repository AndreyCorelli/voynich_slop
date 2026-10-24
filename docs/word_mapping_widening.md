# Controlled widening experiment

**Result:** widening helps the frequency-based starting dictionary, but the
optimizer does not improve on it. At 32,004 words, the full-coverage arm starts
at 6.94% token recovery and finishes at 6.74% with scaled compute. Only 9–11 of
8,220 assignments are correct; `in`, `et` and `ad` account for about 89% of correct
tokens. No broad decoding was demonstrated.

Test whether short inputs permit accidental high-scoring mappings, and whether
more recurring contexts improve recovery. This experiment preserves whole scored
segments and does not screen out passages for vocabulary coverage.

## Data and controls

Rebuild training from Gallic V–VII and Civil III: 39,346 words. Development uses
Gallic I–IV, excluding the original reserved final-test positions, followed by
Civil I–II: 35,659 words. Civil I–II are removed from training before rebuilding
all counts. Physical split overlap and duplicated long passages are checked.
Cached external dictionary analyses are reused; previous corpus counts are not.

A fixed final 2,048-word development holdout is excluded from every search.
Nested prefixes retain whole punctuation/paragraph scoring segments, so requested
sizes are approximate. The original reserved final test remains unscored. Its
excluded positions remain boundaries; the retained Gallic text has gaps there.

| Requested fit words | Actual words | Types | Words/type | Holdout tokens with a mapped type |
| ---: | ---: | ---: | ---: | ---: |
| 500 | 503 | 336 | 1.50 | 547 / 2,048 |
| 2,000 | 2,022 | 1,040 | 1.94 | 905 / 2,048 |
| 8,000 | 8,024 | 2,928 | 2.74 | 1,270 / 2,048 |
| 16,000 | 16,021 | 4,869 | 3.29 | 1,420 / 2,048 |
| 32,000 | 32,004 | 8,220 | 3.89 | 1,645 / 2,048 |

One synthetic injective word cipher supplies the shared dictionary for all fits
and the holdout. Search workers receive public ciphertext, the fixed model and
candidate catalogs. Evaluation loads decoding keys after all main searches finish.

The 32,000-word case adds Civil War prose; length and domain mix therefore change
together. The smaller four cases stay within the retained Gallic text. The
holdout is Civil II, so larger fits also approach its domain more closely. There
are two seeds, not independent replications across authors or texts.

## Candidate coverage and objective

Compare two fixed catalogs at every size:

- **Training:** 9,835 training-attested surface forms. Roughly 82–84% of fit
  tokens have their true form in this pool; others cannot recover exactly.
- **Oracle vocabulary:** 14,287 forms, adding every development form, including
  holdout vocabulary, without its count or decoding key. This is an explicitly
  favorable vocabulary diagnostic, not a deployable candidate-generation method.

Both arms use one fixed smoothed word bigram/trigram model. Extra surfaces get
separate zero-count IDs rather than collapsing to one OOV ID. Adding them changes
smoothing normalization, consistently across every arm and size. No development
sequence contributes training events. The 4,452 zero-count forms remain
statistically exchangeable under this scorer: full candidate coverage does not
supply linguistic evidence for these words. Report training-attested recovery
separately to expose that limitation. No neural or agreement scores are added.

## Search budgets

Three starts per run: frequency, lemma-aware and random. Seeds 101 and 202.
Compare 20,000 mutations per start at every size with budgets proportional to the
number of mapping variables: 20,000; 61,905; 174,286; 289,822; 489,286 per start.
Budgets at 500 words coincide and share runs. In total: 36 unique searches,
108 starts, and 13,383,588 mutation evaluations.

All arms maximize the same objective with the same temperatures and mutation
families. Longer budgets stretch the cooling schedule; they are not continuations
of identical short trajectories. An inverse owner cache makes injective replacement
O(1), and swaps select a uniform ordered pair without scanning the active list.
Checkpoints, monotonic best-score/time traces and independent full scoring remain.
Only the best dictionary is retained; this is not an archive-diversity experiment.

## Evaluation

Report fit token/type recovery, repeated-word recovery, common words (at least
five occurrences), and training-attested recovery. Freeze the selected dictionary
and evaluate holdout tokens whose types occurred in the fit; report unseen tokens
separately. Coverage growth is not itself recovery improvement.

Compare optimized scores with the true mapping on the same fit. Positive gaps
show wrong dictionaries outscoring truth. Negative gaps establish that the current
search did not reach truth's score, without proving the objective sound. For the
training-only pool, some true forms are unreachable, so its gold score is an
external reference rather than a feasible target.

Holdout score comparisons use only original prediction events whose target and
context types are mapped, with the same mask for prediction and truth. They never
introduce new BOS/EOS events around unknown words. Masks differ across fit sizes;
raw heldout scores are not directly comparable without their event counts.

After main searches finish, a separate oracle diagnostic samples up to 256 types
and up to 32 alternative forms each, including displaced-owner swaps, around truth
at every size. Its best score change is checked with the independent full scorer.
This is a sampled local audit, not exhaustive optimization or a realistic start.

## Completed results

Full oracle-vocabulary pool, mean over two seeds, scaled search budgets:

| Requested fit words | Frequency initialization | After optimization | Holdout recurring-token recovery after optimization |
| ---: | ---: | ---: | ---: |
| 500 | 3.18% | 3.38% | 10.51% |
| 2,000 | 2.42% | 1.95% | 3.43% |
| 8,000 | 0.05% | 0.04% | 0.16% |
| 16,000 | 6.14% | 6.09% | 8.80% |
| 32,000 | 6.94% | 6.74% | 8.48% |

Holdout denominators grow with mapped vocabulary, as shown in the data table;
those percentages are not evaluations on a constant eligible-token set across
sizes. Within the 32,000-word case, the same 1,645 recurring tokens give 8.75%
initial versus 8.48% optimized recovery. Training-attested fit recovery is 8.10%
and common-word recovery is 10.07% after scaled optimization.

Compare equal and scaled budgets, with one fixed model:

| Fit target | Training pool, equal | Training pool, scaled | Oracle pool, equal | Oracle pool, scaled |
| ---: | ---: | ---: | ---: | ---: |
| 500 | 2.98% | 2.98% | 3.38% | 3.38% |
| 2,000 | 2.27% | 1.95% | 1.95% | 1.95% |
| 8,000 | 0.00% | 0.19% | 0.00% | 0.04% |
| 16,000 | 6.16% | 6.10% | 6.17% | 6.09% |
| 32,000 | 6.84% | 6.77% | 6.86% | 6.74% |

At every size, both seeds in both coverage arms outscore truth with scaled
budgets. Equal-budget searches at 8,000 words and above stay below truth's score;
more compute closes that score deficit without recovering a useful dictionary.
The full-pool mean fit score advantage over truth at 32,000 words is +0.108 log
units per prediction event. On the 1,224 eligible original holdout events, both
selected dictionaries score worse than truth (gaps −1.37 and −1.31 per event).
This separates in-sample score optimization from generalization.

The sampled oracle audit finds improving neighbors at every size: 1,218; 572;
669; 587; and 559 improvements among roughly 8,174 proposals per case. At 32,000
words the largest local score improvement is +193.68. These audits include
training-unseen forms, so their failures must be interpreted alongside the
zero-count vocabulary limitation rather than as a clean test of a fully informed
Latin model.

Total recorded search time is 1,216 worker-seconds (about 20 CPU-process minutes),
with four parallel workers; this excludes preparation, checkpoint I/O and
validation. All 36 searches, best dictionaries, traces, split identities and
evaluations independently validate. The posthoc frequency baseline is checked
against the actual first-start objectives and separately recomputes identically.

Widening therefore remains potentially useful, but these results do not support
adding still more compute to this configuration. They show better initialization
on large inputs, persistent objective misranking, poor mapping recovery and poor
heldout scores. Rare-word language evidence and stronger structured search remain
unresolved; this is not a proof that every broader word-mapping method fails.

## Reproduction

```sh
.venv/bin/python -m benchmarks.word_mapping_widening --prepare-only
.venv/bin/python -m benchmarks.word_mapping_widening --resume
.venv/bin/python -m benchmarks.word_mapping_widening --validate
.venv/bin/python -m benchmarks.word_mapping_widening_initialization
.venv/bin/python -m benchmarks.word_mapping_widening_initialization --validate
```

Artifacts: `experiments/results/word-mapping/widening-calibration/`. Validation
reconstructs splits, fixtures, candidate pools and the model; restores completed
checkpoints; independently scores every best mapping; checks traces and exports;
and recomputes recovery, holdout metrics and local truth diagnostics.

Implementation: `src/voynich_smt/widening_mapping.py` and
`benchmarks/word_mapping_widening.py`, isolated from frozen earlier experiments.
146 focused unit and integration tests pass, including whole-segment nesting,
zero-count IDs, inverse owner consistency, full scores, exact checkpoint replay,
paired initialization, holdout event masks, scaled budgets, serial/parallel
agreement, truth access after all searches, protocol changes and tamper rejection.
