# One longer-budget sparse membership replay

Replay only the frozen default-inventory length-eight, fully hidden positive
from [length-range calibration](latin_layered_lengths.md). No anchor letters,
key constraints or target spelling are supplied. The exact inventory and sparse
encoding remain unchanged. The solver budget increases from 2,000 to **30,000
ms**, and the worker wall limit increases from 15 to **60 seconds**.

A separate worker writes durable checkpoints before loading, construction,
solving and verification, with completed phase durations and elapsed worker
time. A process timeout retains the last checkpoint. This identifies the active
phase but does not measure its final duration when interrupted. Wall limits
include loading and construction; the solver budget does not. No automatic
retry or other length/inventory is added based on the outcome.

```sh
.venv/bin/python -m benchmarks.latin_layered_timeout --run
.venv/bin/python -m benchmarks.latin_layered_timeout --validate
```

Artifacts: `experiments/results/latin-layered-timeout`. Preparation pins the
previous case/protocol, automaton identity, encoding hash and new benchmark code.
SAT witnesses are independently checked against the Python automaton. UNKNOWN
and process timeouts remain unresolved despite the known inventory witness.
A worker test checks saved phase timings and witness verification. No cipher
recovery or manuscript-language inference.

## Result

**SAT, independently verified**, with witness `cutemque`:

| Phase | Seconds |
| --- | --- |
| Automaton loading | 0.009 |
| Formula construction | 2.391 |
| Solving | 2.269 |
| Witness verification | 0.00015 |
| Whole worker | 4.670 |

The original 2-second run remains UNKNOWN in its own artifacts. This replay
resolved shortly beyond that budget: it provides no evidence of a severe search
bottleneck for this particular length-eight query. One run does not establish
stable timing, longer-length performance, broader-inventory performance or
scaling under shared cipher constraints. No further timeout reruns were added.

The next proposed step is a small known-encryption synthetic control coupling
this membership relation to a shared substitution key, with public fixed word
lengths first. It should measure construction and solving separately and verify
both the recovered explanation and a frozen held-out word. This would test the
missing cipher coupling before any new manuscript experiment.
