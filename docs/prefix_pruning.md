# Indexed public dictionary prefix pruning

Candidate-graph arc consistency now uses indexed support lookups instead of
nested scans of every pair of dictionary candidates. The graph retains the same
candidate ordering, ciphertext relations, fixed-point pruning order and total
pruned count. This changes preparation cost, not the cipher model or evidence.

Equal-word relations use set membership. Shared-token relations index candidate
prefix slices. Strict-prefix relations index proper prefixes, and test longer
words against the shorter-word set. Strict-prefix support must also meet the
shared-token requirement: a shorter word of fewer than that many tokens cannot
have an equal shared slice. Empty support sets eliminate candidates as before.
Each relation still prunes its left side first, then its right side using the
updated left side; fixed-point iteration order is unchanged.

The original implementation is preserved at
`experiments/results/prefix-pruning/reference_dictionary.py`. Differential tests
compare indexed results with its pairwise behavior: 400 randomized relation
prunings cover equality, strict prefixes in either direction, shared slices,
empty domains, short words and input order. Another 100 randomized complete
candidate graphs compare every dataclass field, including pruning counts.

`benchmarks.prefix_pruning` compares the two preserved 36-type requests against
the original implementation on the same machine, timing one graph construction
per implementation and case. It asserts complete graph equality before saving a
result and records source/code hashes, request hashes and graph digests. Completed
cases checkpoint. This benchmark performs no SMT recovery and changes no existing
language or cipher conclusions.

```sh
.venv/bin/python -m benchmarks.prefix_pruning
```

Artifacts: `experiments/results/prefix-pruning/`.

Single-run graph timings measure this preparation function only. They do not
measure a Z3 speedup or total recovery speedup. Solver construction includes other
work, so its earlier 90–156-second timings cannot simply be divided by the graph
speedup. Old experimental results remain preserved; new timings belong to the
indexed implementation.

## Measured results

| Preserved 36-type key | Pairwise reference | Indexed | Speedup | Complete graph |
|---|---:|---:|---:|---|
| fixed-two-seed-3101-types-36 | 86.28 s | 0.103 s | 834× | Exact match |
| mixed-one-two-three-seed-3101-types-36 | 93.54 s | 0.140 s | 667× | Exact match |

All 103 tests passed across focused differential tests, dictionary tests,
known-word/known-length diagnostics, dictionary encodings, hidden recovery and
observed-domain recovery. Both full-size graph comparisons are exact. Saved
artifact validation regenerates the indexed graph digests and checks source/code
hashes and timing arithmetic without repeating the slow reference or any SMT fit.

```sh
PYTHONPATH=src:. .venv/bin/python experiments/results/prefix-pruning/validate.py
```

Next measure complete recovery construction on these inputs under a new output
protocol, preserving the old UNKNOWN records. Previously completed experiment
commands skip their saved fits; rerunning those commands is not a fresh timing
experiment. No new Z3 result is produced by this optimization benchmark.
