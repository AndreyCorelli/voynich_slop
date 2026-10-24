# Coverage-first scheduling experiment

Predeclared comparison: 8,000 proposals for each of seeds 3, 5 and 7,
comparing the existing mixed type scheduler with a coverage-first variant.
The latter visits a seeded permutation of every cipher type once, then
returns to the existing mixed scheduler. Its permutation uses an independent
RNG; the existing mixed scheduler keeps its historical random sequence.

There are 6,235 types in this 35,000-token engineering fixture, leaving
1,765 refinement proposals after the first pass. Both schedules retain
the same exponential temperature schedule over all 8,000 proposals,
candidate retrieval, random initial keys, model and inventory. This tests
the complete scheduling policy, including how it spends early hotter steps;
it does not isolate visitation from annealing order.

Each three-seed invocation has a 900-second search budget with a 30-second
reserve divided across seeds. A time-limited run must be reported as such
rather than treated as an equal-proposal comparison. Live public-only
pool/move traces are enabled for both schedules, with identical instrumentation.
The default remains mixed pending results.

Evaluation will report literal token/type accuracy, primary type visitation,
whether true assignments were ever offered (including implied swap rows),
frequency bands, source-model scores and elapsed time. Truth is accessed only
after search. A visit guarantees a proposal opportunity, not a useful candidate
or a correct assignment.

The fixture overlaps LM training, spans 24 documents rather than one work,
and uses 15,574 inventory forms. This is a scheduling experiment, not evidence
of grammatical/semantic recovery or million-form performance.

Implementation details:

- `SearchConfig.scheduler` accepts `mixed` (default) or `coverage_first`.
  The coverage permutation is reproducible from the seed and type count.
  Resumption uses the saved step to continue it; no visited set is needed.
- Budget stops and short proposal horizons can end before coverage completes.
  Injective swaps can alter a type after its primary visit.
- `--trace` streams gzip diagnostics during a fresh search, respecting existing
  time/memory checks and checkpoint boundaries. Live traces currently require
  a fresh run; checkpoint continuation remains supported without live tracing.
- Legacy checkpoints and resume protocols without a scheduler field default to
  the historical mixed policy.

Reproduction (use fresh output directories):

```sh
.venv/bin/python -m benchmarks.scalable_english_run --public experiments/results/scalable-english/retrieval-ewt-v2/public/cipher.json --output experiments/results/scalable-english/search-ewt-mixed-8000-v1 --proposals 8000 --scheduler mixed --budget-seconds 900 --reserve-seconds 30 --trace
.venv/bin/python -m benchmarks.scalable_english_run --public experiments/results/scalable-english/retrieval-ewt-v2/public/cipher.json --output experiments/results/scalable-english/search-ewt-coverage-8000-v1 --proposals 8000 --scheduler coverage_first --budget-seconds 900 --reserve-seconds 30 --trace
```

For each run, use `benchmarks.scalable_english_evaluate`,
`benchmarks.scalable_english_diagnostics` and
`benchmarks.scalable_english_diagnostics_validate`, passing the run's
`traces/` directory and an `analysis/` output directory.
Then `benchmarks.scalable_english_compare_schedules` verifies that the
protocols differ only in scheduling and that every run completed its proposal
horizon before writing the paired comparison. Incomplete bundles fail this check.

## Results

Every chain finished all 8,000 proposals. The existing mixed scheduler remains
the default.

| Seed | Mixed literal token accuracy | Coverage-first literal token accuracy | Mixed correct types | Coverage-first correct types |
| --- | ---: | ---: | ---: | ---: |
| 3 | 17.25% | 10.38% | 27 | 16 |
| 5 | 22.39% | 16.62% | 65 | 19 |
| 7 | 41.74% | 19.79% | 141 | 24 |
| Mean | **27.13%** | **15.60%** | **77.67** | **19.67** |

Both bundles selected seed 7 solely by source-model score. The resulting
score-selected literal token accuracies are 41.74% and 19.79%.
Mean type accuracies are only 1.25% and 0.32%, respectively.

| Mean over three seeds | Mixed | Coverage-first |
| --- | ---: | ---: |
| Primarily visited types, out of 6,235 | 3,757.67 | 6,235 |
| True assignments ever offered, including implied swaps | 328.33 | 224.67 |
| True assignment offer coverage | 5.27% | 3.60% |
| Elapsed search time per seed | 144.41 s | 52.29 s |

Visiting every type did not produce broad candidate support: coverage-first
never offered the true assignment for 6,022 / 6,007 / 6,001 types. Its recovery
was lower on every seed and in every frequency band when averaged across seeds.
Mean literal token accuracy for types appearing 100+ times fell from 61.03%
to 40.03%; for singleton types it fell from 0.24% to 0.05%.

The mixed scheduler's strongest chain recovers 141 types, including rare words,
but its fixed decoding excerpts still contain substantial incoherent wording.
No grammatical or semantic recovery score has been measured.

Coverage-first used about 36% of the mixed scheduler's elapsed search time.
Rare types have fewer occurrences and affected scoring events, so equal
proposal counts do not imply equal work. This experiment establishes a worse
result at the declared horizon; an equal-time result remains unknown.
All runs stayed below 116 MB peak process RSS. Resource loading and subsequent
evaluation are outside the recorded search clocks.

A plausible explanation is that a uniform first pass spends most early,
higher-temperature proposals on rare words before stable frequent-word
contexts develop. The logs demonstrate poorer candidate support and recovery;
they do not isolate that explanation from other effects of proposal order.

## Decision and next candidate

Keep the mixed scheduler. Retain coverage-first as an explicit experimental
option and preserve the failed comparison.

If scheduling is tested further, a reasonable next policy is to interleave
a small guaranteed-coverage quota with the existing mixed proposals, rather
than postponing frequent-type refinement until a complete uniform pass ends.
That policy and an equal-time comparison have not been implemented or evaluated.
Candidate generation from better contexts remains a separate substantial
problem; the current offered pools miss most true assignments.

The earlier 2,000-proposal experiment had 20.22% mean literal token accuracy
and 25.25% for its score-selected seed. The longer mixed runs reached 27.13%
and 41.74%, with substantial variation across seeds. Changing the proposal
horizon also stretches the annealing schedule, so these differences combine
additional proposals and a changed cooling rate. They do not establish
generalization to independent works or larger inventories.

## Artifacts and validation

All paths below are relative to the repository root:

- `experiments/results/scalable-english/search-ewt-mixed-8000-v1/`
- `experiments/results/scalable-english/search-ewt-coverage-8000-v1/`
- `experiments/results/scalable-english/search-ewt-schedule-comparison-v1.json`

Each run directory contains the protocol, public cipher, three checkpoints,
source-score-only inference selection, live gzip traces, separate
`evaluation.json`, and `analysis/{diagnostics.json,inspection.md,validation.json}`.
The comparison file records each seed and paired differences, with protocols
checked to differ only in scheduler. Both bundles pass independent full-score
checks of logged correct-assignment displacements (14 events for mixed and
7 for coverage-first), final-key/trace consistency and failure-category accounting.

103 relevant tests pass. Added coverage includes exact continuation before,
at and after the coverage transition; legacy checkpoints/protocols; bounded
short horizons; identical live/replayed logs; and comparison rejection of
incomplete or confounded bundles.

```sh
.venv/bin/python -m pytest tests/unit/test_scalable_*.py tests/integration/test_scalable_*.py tests/unit/test_ravi_knight_*.py tests/integration/test_ravi_knight_*.py tests/integration/test_word_mapping_pipeline.py -q
.venv/bin/python -m benchmarks.scalable_english_compare_schedules --mixed experiments/results/scalable-english/search-ewt-mixed-8000-v1 --coverage experiments/results/scalable-english/search-ewt-coverage-8000-v1 --output experiments/results/scalable-english/search-ewt-schedule-comparison-v1.json
```

Comparison output is exclusive: use a new filename when reproducing it.
