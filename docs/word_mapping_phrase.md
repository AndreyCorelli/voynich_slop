# Training phrase proposals and exact optimization audit

This experiment separates an optimizer's ability to maximize its objective from
that objective's ability to select the correct decoding. It also tests replacing
independent joint word draws with actual training-attested word pairs.

## Implementation

`src/voynich_smt/phrase_mapping.py` adds `PhraseSearch` without changing frozen
search modules or earlier experiments. A joint proposal draws a distinct adjacent
ciphertext pair, weighted by occurrences, and a distinct Latin pair, weighted by
its training bigram count. Boundary symbols are excluded. Displaced owners receive
vacated forms, preserving the globally consistent injective dictionary. Every
occurrence affected by the proposal contributes to its score.

Single-word replacement, swaps, inflection and lemma proposals remain available;
no candidate forms are permanently excluded. This is heuristic annealing, not
posterior sampling: asymmetric proposal probabilities are not corrected with a
Metropolis-Hastings ratio. Checkpoints include the proposal implementation hash.
No packages or models beyond the existing environment are required.

## Matched search protocol

Three separate development bundles, two seeds (101, 202), and three starts
(frequency, lemma-aware, random) per run. All arms use the same n-gram objective,
full 12,327-form vocabulary, temperatures and archive policy, with paired initial
mappings. There is no morphological or neural score in this experiment.

- Baseline: existing single-word operators.
- Independent joint: 25% joint proposals drawing Latin words independently.
- Phrase: 25% joint proposals drawing training-attested Latin pairs.

The initial experiment uses 20,000 evaluations per start; the larger experiment
uses 100,000. Each has 18 runs and 54 starts, respectively 1.08 million and
5.4 million evaluations. The longer schedule cools more slowly; its trajectory
is not an extension of the shorter schedule. Budget comparisons therefore assess
the whole schedule, not continuation of an identical prefix. Completed restarts
are checkpointed. Truth is loaded only after every search in an experiment finishes.
All resources come from the validated long-context parent; the final test is unscored.

## Matched search results

Mean exact token recovery across six runs per arm:

| Proposals | 20,000 evaluations/start | 100,000 evaluations/start |
| --- | ---: | ---: |
| Baseline | 2.31% | 1.72% |
| Independent joint | 2.09% | 1.97% |
| Training phrase | 1.79% | 1.10% |

All 18 paired best scores improve with the larger budget, while average recovery
falls in every arm. Individual recovery improves in 1/6 baseline, 2/6 independent
joint, and 1/6 phrase runs; respectively 2/6, 3/6 and 2/6 worsen, with the remainder
tied. At the larger budget, phrase beats its paired baseline in 2/6 runs and loses
in 3/6. The aggregate result does not justify promoting this phrase sampler.

These experiments comprise 36 runs, 108 starts and 6.48 million mutations.
Recorded search time totals about 247 seconds, excluding resource preparation,
validation and the separate exhaustive diagnostic. Extra compute clearly helps
maximize the current objective; it does not improve aggregate plaintext recovery
here. Frequent training pairs may encourage generic locally plausible text;
this sampler does not condition proposals on surrounding decoded context.

This is evidence for revising the objective and contextual proposal construction,
not proof that long searches or all phrase proposals are ineffective. The three
bundles share an author and the six paired runs per arm are a limited development
sample. Exact recovery also does not measure semantic coherence directly; no
coherent interpretation has been demonstrated by these results.

## Exhaustive diagnostic protocol

Eighteen deterministic five-token windows, six per development bundle. Each
restricted vocabulary contains the correct forms plus the most frequent training
forms until it has eight candidates. This explicitly uses oracle information and
is a diagnostic, not a realistic candidate-generation or recovery benchmark.

Enumerate every injective assignment using the independent full objective scorer,
including boundaries and repeated-type consistency. Compare with two annealing
runs, each three starts of 2,000 evaluations. Exhaustive certification applies
only to the restricted window and vocabulary; neither the full vocabulary nor
longer texts are certified. Five-token windows provide little linguistic context.

Results: 120,960 enumerated mappings across 18 cases; the true mapping is optimal
in none. The deterministically selected optimum averages 6.67% exact token
recovery. Annealing reaches an optimum in 34 of 36 runs (216,000 evaluations).
This isolates an objective limitation on these small ambiguous cases, while
leaving two search failures. It does not establish impossibility of longer-text
recovery or reject a manuscript language hypothesis.

## Commands and artifacts

```sh
.venv/bin/python -m benchmarks.word_mapping_exact_audit
.venv/bin/python -m benchmarks.word_mapping_exact_audit --validate
.venv/bin/python -m benchmarks.word_mapping_phrase --steps 20000
.venv/bin/python -m benchmarks.word_mapping_phrase --steps 20000 --validate
.venv/bin/python -m benchmarks.word_mapping_phrase --steps 100000 \
  --out experiments/results/word-mapping/phrase-long-calibration
.venv/bin/python -m benchmarks.word_mapping_phrase --steps 100000 \
  --out experiments/results/word-mapping/phrase-long-calibration --validate
```

Use `--resume` with the same output and budget to restore checkpoints and regenerate
exports. Existing outputs reject changed protocols. Validation restores checkpoints,
independently recomputes every archived score, verifies exports, and recomputes
evaluation. The exact audit's validation repeats enumeration and annealing.

Artifacts are under `experiments/results/word-mapping/` in
`exact-mapping-audit`, `phrase-calibration`, and `phrase-long-calibration`.

## Verification

140 focused unit and integration tests pass, including phrase attestation,
injective multi-owner changes, full versus incremental scores, exact enumeration
and budget rejection, deterministic checkpoint replay, truth access after search,
protocol changes, export tampering and regeneration. Both search experiments
validate independently, covering all 1,080 archived dictionaries. The exhaustive
audit also validates by full recomputation. Original frozen implementation files
and their experiment artifacts were preserved.
