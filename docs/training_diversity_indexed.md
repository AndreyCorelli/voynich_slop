# Full recovery after indexed prefix pruning

A fresh timing protocol reruns ordinary hidden recovery on both preserved
36-type synthetic positives. It supplies the same 72-word ciphertext, full
Latin dictionary, alphabets, H1 prefix-free L1–3 bounds, free selection and
observed code domains. Training word identities, lengths, key, segmentation and
continuation remain hidden. No public length branching or statistical guidance
is added. Each fit keeps the configured five-second solver timeout.

The only model-building change is the output-equivalent
[indexed candidate-graph pruning](prefix_pruning.md). That function's candidate
lists, ordering, relations and pruning counts match the preserved original
implementation exactly on these inputs. The previous ordinary hidden fits took
140.76/156.18 construction seconds and returned UNKNOWN after 8.51/9.55 measured
solver seconds. Their reports remain preserved and are hashed in the new protocol.

The new protocol additionally hashes the dictionary implementation and records
Python, platform and Z3 versions. It freezes exact public requests and prior
measurements before fitting. Every completed case checkpoints, and resume skips
completed cases. Construction, solver and fit wall times are reported separately.
The five-second timeout is a configured solver limit, not a strict wall-time
promise. A returned UNKNOWN remains unscored, even though the generating key and
known-length controls independently demonstrate a correct predictive solution.

Nine focused tests pass, covering request-only solver inputs, unchanged requests
and timeouts, absence of truth/holdout fields in solver-ready cases, UNKNOWN
remaining unscored, checkpoint reuse, changed-source rejection, dictionary-code
provenance, preserved baseline hashes and prefix-pruning equivalence. Artifact
validation checks matched requests, baseline comparisons, witnesses if present,
absence of oracle-length metadata and independently recomputed frozen scores.

Artifacts: `experiments/results/training-diversity-indexed/`.

```sh
.venv/bin/python -m benchmarks.training_diversity_indexed --run
.venv/bin/python -m benchmarks.training_diversity_indexed --validate
```

These are single-run historical timing comparisons, not repeated controlled
measurements. Execution conditions may differ across runs, so construction ratios
are descriptive. No claim of Z3 speedup follows solely from the candidate-graph
optimization. New SAT witnesses, if any, require full independent verification
and frozen continuation scoring; correct first predictions do not prove uniqueness.

## Recorded results

| Key | Previous construction | Indexed construction | Previous solver | Indexed solver | Indexed status |
|---|---:|---:|---:|---:|---|
| fixed-two-seed-3101-types-36 | 140.76 s | 53.64 s | 8.51 s | 8.02 s | UNKNOWN |
| mixed-one-two-three-seed-3101-types-36 | 156.18 s | 62.80 s | 9.55 s | 10.04 s | UNKNOWN |

Both cases returned UNKNOWN with reason `timeout`, and neither is scored.
Construction dropped from 140.76/156.18 to 53.64/62.80 seconds (about 2.6×/2.5×).
The measured solver checks took 8.02/10.04 seconds under configured five-second
timeouts. Total fit wall times, including solver/model handling, are saved in the
report. There is no demonstrated solver or predictive improvement in these runs.

Actual artifact validation passed for both records. The earlier known-length
controls still demonstrate correct predictive solutions. Removing graph overhead
makes experiments cheaper, while finding those solutions with lengths hidden
remains unresolved. About a minute of construction per input also remains; profile
that work before attempting further model-building optimizations. Do not increase
language/model flexibility based on these timeout outcomes.
