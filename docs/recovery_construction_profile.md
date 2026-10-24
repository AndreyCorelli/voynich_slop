# Profiling remaining recovery construction

Two fresh profiles cover ordinary hidden recovery on the preserved 36-type
length-two and mixed-key inputs. The requests, five-second solver timeouts,
indexed dictionary graph, alphabets, full dictionary and cipher bounds remain
unchanged from the [unprofiled indexed runs](training_diversity_indexed.md).
No word lengths, training identities, key or continuation enter fitting.

A temporary wrapper disables cProfile immediately before the first `Solver.check`
call. The original solver check still runs normally. The wrapper is restored on
success or error; no production solver/model code is edited. Profiling includes
public candidate-graph construction, dictionary formulas and the remaining SMT
constraint construction, but excludes the native solver check, SAT model handling,
independent verification and frozen-key evaluation. Exactly one solver check is
required for each profile.

Each output includes a binary `.prof`, source and code hashes, unchanged request
hashes, solver result, profile-file hash, and JSON tables of the top 30 functions
by cumulative and self time. Cumulative function times overlap and must not be
added; self times partition profiled work. A dedicated row reports dictionary
membership construction. Profiled timings include instrumentation overhead and
must not be interpreted as ordinary construction performance measurements.
Python, platform and Z3 versions are recorded. Completed profiles checkpoint
under a new directory; old experiment results are preserved.

Three focused tests pass, checking that solver-native calls are excluded, the
same input reaches the solver wrapper, instrumentation is restored on errors,
and unexpected solver-check counts are rejected. Artifact validation verifies
hashes, requests, raw-profile summaries and independently checks/scores recovered
witnesses if any. UNKNOWN is unresolved and remains unscored.

Artifacts: `experiments/results/recovery-construction-profile/`.

```sh
.venv/bin/python -m benchmarks.recovery_construction_profile --validate
```

To inspect a raw profile interactively:

```sh
.venv/bin/python -m pstats experiments/results/recovery-construction-profile/fixed-two-seed-3101-types-36.prof
```

Within pstats, `sort cumulative` followed by `stats 30` lists the main call paths;
`sort time` shows functions' exclusive self costs. The saved JSON summaries are
also readable without profile tools.


The optimization to evaluate next is per-membership reuse of the identical
`symbol[i] == letter` and `word_size == length` expressions. The flat encoding
currently recreates these Python/Z3 expressions for each candidate even when the
same slot/value comparison has already appeared. Reusing them can preserve the
same candidate alternatives, AST structure and constraint meaning. Validate
formula equivalence before measuring any improvement; changing dictionaries,
adding cribs or switching languages is not needed to address this cost.

## Findings

| Input | Profiled construction | Dictionary membership cumulative | Membership share | Indexed graph share |
|---|---:|---:|---:|---:|
| fixed-two-seed-3101-types-36 | 178.04 s | 165.71 s | 93.08% | 0.15% |
| mixed-one-two-three-seed-3101-types-36 | 209.12 s | 194.33 s | 92.93% | 0.15% |

Both profiles identify flat dictionary membership construction as about 93% of
profiled work, with 72 membership calls per input. Z3 equality construction,
expression coercion, conjunctions and AST/reference wrappers dominate that path.
Their cumulative times overlap; they are not independent percentages to add.
The indexed public candidate graph now accounts for only about 0.15%.

A separate structural count of membership comparisons finds:

| Input | Flat equality occurrences | Distinct equalities per membership call, summed |
|---|---:|---:|
| fixed-two-seed-3101-types-36 | 2,927,668 | 13,986 |
| mixed-one-two-three-seed-3101-types-36 | 3,376,116 | 15,774 |

Counts include each candidate's size comparison and each slot's letter/sentinel
comparison. The distinct counts assume local reuse within each membership call;
no equality is shared between different word variables. They are potential reuse
counts, not measured optimized performance. The redundant equality occurrences
alone exceed the unique comparisons by more than 200×.

Both ordinary solver checks remained UNKNOWN (`timeout`), taking 8.10/9.79 seconds
outside the profiles. They are unscored. Profiling increases construction from the
unprofiled 53.64/62.80 seconds to 178.05/209.13 seconds; those profiled durations
must not be used as a new performance regression. No native `Z3_solver_check`
entry appears in either raw profile. Both profile files and JSON summaries passed
artifact validation. Historical results remain unchanged.

Next priority: cache the repeated slot/value and size/length equality ASTs inside
the existing flat membership encoding. Retain the exact candidate order and
conjunctions/disjunctions, test formula equivalence, and benchmark fresh unprofiled
construction timings. Leave trie alternatives and model/language changes aside
until that measured source of redundant construction is addressed.
