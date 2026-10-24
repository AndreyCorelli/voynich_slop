# Solver-engine comparison on a stalled public branch

This experiment follows the six/eight-word public length calibration. It selects
the first six-word branch that remained UNKNOWN at 30 seconds, with lengths
`[9, 5, 6, 7, 7, 12]`. Those lengths were selected from ciphertext/vocabulary bounds,
without generation truth. Each comparison solve starts fresh.

Both engines receive the same finite integer representation, explicit variable
bounds, trie vocabulary membership, prefix-free H2/L3 key constraints, fixed word
lengths, symbolic boundaries and Boolean text-wide cycle phases. The engine alone
changes: Z3's `qffd` tactic versus ordinary `z3.Solver()`. Both receive 30 seconds;
construction is included separately in total wall time. No plaintext or key is
supplied, and all SAT explanations require independent Python verification.

The default solver selection is unchanged. A private explicit backend option
supports this comparison and adds backend identity to result metadata. Ordinary
public requests remain free of backend and fixed-length diagnostic fields.
Tests compare engines' SAT/UNSAT outcomes, pre-check constraint counts and
formula fingerprints on small fixed-length instances. A SAT/UNSAT disagreement in a benchmark is recorded and raises an error.

```sh
.venv/bin/python -m benchmarks.solver_engines
.venv/bin/python -m benchmarks.solver_engines \
  --replay data/generated/solver-engines-certified/inputs/smt.json
```

Configuration: `experiments/configs/solver-engines.json`. Report:
`experiments/results/solver-engines.json`. The two dedicated wrappers carry the
same request and length vector plus an explicit engine choice. Dedicated replay
preserves the chosen engine. Results concern this conditional length branch; an
UNSAT result on it would not reject the full hidden model. UNKNOWN is unresolved.
A single comparison is not a general engine-performance estimate.

Constraint counts and formula fingerprints are captured before `check()`, so
solver preprocessing cannot change the comparison metadata. The runner requires
identical pre-check SHA-256 fingerprints before accepting a completed comparison.
The initial exploratory report is preserved in `solver-engines-initial.json`; its
constraint counts were read after solving and are not comparable across engines.

## Recorded result

| Engine | Result | Solver time | Total time |
|---|---|---:|---:|
| qffd | UNKNOWN (timeout) | 30.05s | 31.62s |
| smt | UNKNOWN (timeout) | 30.02s | 31.71s |

Both engines timed out at 30 seconds. Their pre-check formula fingerprints
and constraint counts match, confirming identical inputs to the engines. This
comparison found no improvement for the tested branch. The branch and full model
remain unresolved. The default backend remains unchanged. All 394 tests pass.
A useful next search experiment is to diversify public length-vector order instead
of concentrating every attempt on minimum total plaintext length.
