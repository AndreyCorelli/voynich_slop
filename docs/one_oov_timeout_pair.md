# One-OOV bounded timeout pair

The fixed Latin passage 2, fixed-two positive recovers all 24 training words and
predicts all six novel held-out words correctly. Its paired shuffle is UNSAT.
Both were UNKNOWN in the previous five-second experiment.

| Case | Five-second result | 60-second result | New solver time |
|---|---|---|---:|
| Latin 2 fixed-two, one deletion | UNKNOWN | Verified SAT; 24/24 training, 6/6 holdout | 4.996 s |
| Paired shuffle | UNKNOWN | UNSAT | 5.498 s |

The positive's new runtime is just below five seconds, so this is a near-cutoff
case, not evidence that it inherently needs a longer timeout. Solver timeout
handling, timing and search variation near that boundary can affect termination.
The result shows the frozen pair can resolve with a modest allowance; it does
not justify assuming all remaining cases will resolve or running 30-minute jobs.

Selection was fixed before solving: the first previously timed-out positive in
the frozen [one-OOV calibration](one_oov_calibration.md) order, and its paired
shuffle. Only `timeout_ms` changes from 5000 to 60000. Dictionary, one unknown
occurrence, ciphertext, holdout, alphabets, bounds, free selection and encoding
remain identical. All generating and recovered witnesses are checked independently.
No retries, replacement cases or outcome-based tuning are added. Construction
remains outside the solver budget; first SAT key is frozen-scored. UNSAT is
solver-reported without independent proof certificates. These two correlated
inputs do not establish population discrimination or a manuscript hypothesis.

One integration test checks fixed selection, budget, checkpoint/resume and
unscored UNKNOWN handling. Two-case artifact validation additionally verifies
timeout-only changes, SAT witness, training identities, OOV count and frozen scores.
Original five-second results are preserved.

```sh
.venv/bin/python -m benchmarks.one_oov_timeout_pair --run
.venv/bin/python -m benchmarks.one_oov_timeout_pair --validate
```

Artifacts: `experiments/results/one-oov-60s-pair/` contains frozen protocol/inputs,
paired old rows, hashes, checkpointed report and validation. Completed cases skip
on resume.
