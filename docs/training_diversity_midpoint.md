# Public midpoint search on richer training inputs

A resumable runner applies the frozen public midpoint length rule to both
preserved 36-type inputs (72 training words). It retains the full dictionary,
alphabets, H1 prefix-free L1–3 model, free selection and observed code domains.
No generating lengths, training identities, key, segmentation or continuation
enter the proposal function or the solver. Each case shares a configured 5,000 ms
solver budget across up to three scheduled branches. Rejected branches cannot
prove global UNSAT; unsuccessful searches remain UNKNOWN and unscored.

The rule ranks each public candidate length by distance from ciphertext length
divided by the midpoint of the code-length bounds, with shorter ties first.
Vectors are ordered by the sum of per-position preference ranks, then by the full
length vector. Public prefix/equality relations filter admissible vectors.

The implementation groups repeated ciphertext words before enumeration. Their
lengths must agree under the existing equality constraint. Group preferences
retain the sum of the original position ranks, including repeated occurrences,
and retain full-vector lexical tie-breaking. This removes impossible unequal
repeat assignments without changing the surviving vectors or their ordering.
A complete toy comparison checks equivalence with the frozen original enumerator.
The original heuristic module and all historical results remain unchanged.

Schedule generation first computes the public dictionary candidate graph.
An initial preparation attempt was interrupted during that graph's prefix
pruning, before any fits or schedules were saved. This is another substantial
cost outside the solver timeout. Both actual searches have now completed as UNKNOWN and passed artifact validation.
Preparation and fitting can take minutes per case. Both completed schedules
and completed fits checkpoint separately; interruptions within a schedule or fit
require that unfinished case to restart. Source and code hashes prevent resuming
under changed inputs or implementations.

Run the prepared implementation locally:

```sh
.venv/bin/python -m benchmarks.training_diversity_midpoint --run
```

The command freezes both public schedules before fitting. It records schedule,
construction, solver and fit wall times separately. The prior ordinary hidden
fits exceeded their configured five-second timeout (8.51 and 9.55 measured
seconds), so this timeout is not advertised as a strict wall-clock cap. The
branch runner subtracts measured solver time before deciding whether another
branch may run; construction is excluded from that shared budget.

Artifacts are written to `experiments/results/training-diversity-midpoint/`.
After completion:

```sh
.venv/bin/python -m benchmarks.training_diversity_midpoint --validate
```

Eight focused tests pass, covering public request isolation, unscored UNKNOWN,
checkpoint reuse, preparation resume, complete grouped-order equivalence,
complete original rank enumeration, shared solver budgets and no global UNSAT
from branch rejection. Artifact validation regenerates public schedules, checks
budget consumption, full witnesses and fixed branch lengths, then independently
recomputes frozen predictions. It also regenerates the expensive public candidate
graph, so actual validation can take minutes.

The known-length controls predict 3/3 on both inputs; unrestricted hidden fits
returned UNKNOWN. This experiment tests whether the existing public heuristic
obtains that benefit without truth-derived lengths. It uses two selected fixtures,
not blind calibration or manuscript evidence. Public guesses may differ from the
mixed key's true lengths. A successful first witness would not establish that all
valid keys predict the same continuation.


## Recorded results

| Key | Status | Public schedule seconds | Construction seconds | Solver seconds | Branches run |
|---|---|---:|---:|---:|---:|
| Length two / 3101 | UNKNOWN (`timeout`) | 85.98 | 92.56 | 5.07 | 1 |
| Mixed / 3101 | UNKNOWN (`timeout`) | 93.23 | 99.94 | 5.07 | 1 |

Both first checks consumed the complete shared budget, so the other two frozen
vectors were not tried. Neither record has a prediction score. Actual artifact
validation passed and preserves these outcomes.

The length-two first vector equals the truth-derived training lengths supplied
to the previously successful control. The request and fixed-length model are the
same; the earlier check returned SAT in 4.06 seconds, while this one timed out
at 5.07 seconds. This is evidence of sensitivity to a tight configured timeout,
not evidence that the heuristic could not propose a useful vector. We have not
isolated the runtime/environment cause of the different outcome. The mixed first
vector differs from the generating lengths; its timeout does not establish that
those alternative lengths are infeasible.

Across the two searches, public scheduling and model construction consumed about
372 seconds, versus about ten seconds in solver checks. A code inspection finds
that dictionary candidate-graph pruning repeatedly uses nested pairwise scans to
find supporting plaintext prefixes. These graph computations occur during public
scheduling and during solver construction. Timing does not isolate every internal
construction cost, so it is not claimed that prefix pruning accounts for all of it.

Recommended next step: replace those pairwise support searches with indexed
prefix/equality lookups, preserving exactly the same candidate graph and order.
Check output equivalence against the current implementation before running any
new solver experiments. This reduces a measured preparation cost without adding
model freedom, oracle information, new languages, or longer fitting budgets.
