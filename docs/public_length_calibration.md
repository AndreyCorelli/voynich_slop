# Frozen public length heuristic: new-key calibration

This comparison fixes the midpoint heuristic before evaluating new keys. Six
synthetic positives use two seeds (3101, 3102) under three generation profiles:
all codes length two, all codes length three, and mixed lengths one/two/three.
Every fit permits H1 prefix-free codes of lengths 1–3; generating profiles are
not supplied to either solver.

The full corrected 5,655-word Latin dictionary, 24-letter plaintext alphabet,
six ciphertext glyphs, engineered 18-word training sequence and three novel
held-out words are preserved from the earlier diagnostic. New generating keys
are independently checked. All held-out plaintext letters occur in training;
the generating key therefore has full held-out code coverage. These are new-key
checks, not new-text or manuscript calibration.

The mixed generator constructs one length-one leaf, ten length-two leaves and
thirteen length-three leaves on disjoint prefix-tree branches. Code assignments
are randomized by the frozen seeds. Uniform profiles sample distinct fixed-length
codes. No cases are rejected or regenerated based on solver outcomes.

Preparation saves all six requests, witnesses, continuations and three public
length vectors per case before any fit. Proposals receive only requests. Each
case compares ordinary observed-domain recovery against midpoint-ranked length
branches with a shared five-second solver budget and a three-branch cap. Branch
rejection cannot establish global UNSAT. A branch may consume the entire budget;
there is no extra budget for the remaining proposals. Scheduling, construction
and solver times are reported separately or recoverable from saved statistics;
the solver budget excludes scheduling and construction for both arms.

Outputs are checkpointed per arm and resume without repeating completed fits.
Source and implementation hashes prevent resuming under changed inputs or code.
Eight focused tests cover prefix-free generation, fixed seeds, public proposals,
complete rank enumeration, budget consumption and non-global UNSAT semantics.
Artifact validation checks synthetic/recovered witnesses, public schedules,
request hashes, shared budgets and frozen-key predictions.

```sh
.venv/bin/python -m benchmarks.public_length_calibration --run
.venv/bin/python -m benchmarks.public_length_calibration --validate
```

Artifacts: `experiments/results/public-length-calibration/`.

## Results

| Generating profile / seed | Ordinary | Public midpoint | Exact novel words |
|---|---|---|---|
| Length two / 3101 | UNKNOWN | SAT, 4.00 s | 0/3 |
| Length two / 3102 | UNKNOWN | SAT, 0.81 s | 0/3 |
| Length three / 3101 | UNKNOWN | UNKNOWN | Unscored |
| Length three / 3102 | UNKNOWN | UNKNOWN | Unscored |
| Mixed / 3101 | UNKNOWN | SAT, 1.35 s | 0/3 |
| Mixed / 3102 | UNKNOWN | SAT, 4.71 s | 1/3 |

All UNKNOWN outcomes consumed approximately five solver seconds. Every SAT
was independently verified against the full model. The four SAT fits all used
the first public vector. The two length-three searches timed out on their first
vector, so the later scheduled alternatives were not tested. Only the uniform
length-two first vectors match the generating plaintext lengths; the mixed
fits use other lengths and word identities.

The heuristic improves feasibility throughput on this small matched suite:
4/6 SAT versus 0/6 ordinary. It does not recover predictive keys reliably:
1/12 held-out occurrences across the four SAT fits is exact. The first fixture's
3/3 result did not generalize to either new length-two key. UNKNOWN cases remain
unscored, so this predictive figure is conditional on the successful fits.
Neither solver's UNKNOWN means a synthetic positive is impossible.

This is enough to retain midpoint ordering as a performance option, but not to
justify a larger manuscript sweep or longer timeouts. The next useful calibration
would expose training plaintext identities on these same four successful cases,
with the key still hidden, to measure how much predictive failure is due to word
ambiguity versus key/code coverage. Preserve the current hidden results unchanged;
this would be a separately labeled oracle diagnostic, not hidden recovery.
