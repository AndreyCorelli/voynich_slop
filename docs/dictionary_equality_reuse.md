# Reusing equalities in flat dictionary formulas

Flat dictionary membership now caches each word-size/length equality and each
symbol-slot/value equality within a single membership call. Candidate
conjunctions and their ordering remain unchanged, as does the outer disjunction.
Sentinel padding remains explicit. Token-to-alphabet indices are also reused
locally. Caches do not cross word-variable sets or Z3 contexts; no constraints,
word candidates, cipher freedom or oracle information are added or removed.

The original encoding is preserved at
`experiments/results/equality-reuse/reference_dictionary_encoding.py`. Its hash
matches the encoding recorded by the earlier construction profile. Differential
tests compare 50 randomized formulas, including empty candidate sets, contracted
tokens and extra inactive padding. All produce the exact same Z3 AST as the
original, and XOR equivalence checks are UNSAT. Separate tests cover local caches
in distinct contexts and invalid tokens retaining their ValueError behavior.

All 94 tests passed across these equivalence cases, dictionary encodings, hidden
recovery, observed-code recovery and the fresh timing runner. Runner tests verify
request-only solver inputs, unchanged budgets, dictionary/encoding provenance,
old baseline hashes, unscored UNKNOWN and checkpoint reuse.

The two preserved 36-type ordinary hidden requests are measured under a new
protocol, retaining the configured five-second solver timeout and full dictionary.
No training word identities, lengths, generating key or continuation are supplied
to recovery. Construction, solver and full fit times are recorded separately.
The prior indexed-prefix measurements (53.64/62.80 construction seconds) remain
preserved and are hashed in the new protocol. The encoding snapshot, current
encoding and dictionary/model code are explicitly hashed. Python, platform and
Z3 versions are recorded. Each completed fit checkpoints and is skipped on resume.

Artifacts: `experiments/results/equality-reuse/`.

```sh
.venv/bin/python -m benchmarks.dictionary_equality_reuse --validate
```

The earlier profile identified about 93% of model-building time inside flat
membership and 2.93/3.38 million equality occurrences, versus only 13,986/15,774
distinct comparisons within membership calls. This optimization removes redundant
construction of those comparisons. It still builds every candidate conjunction
and uses the same flat membership formula; the comparison-count ratio is not an
expected runtime speedup. Timing comparisons are single-run historical comparisons,
not replicated controlled measurements. Z3 timeouts are configured limits and
may exceed five measured seconds.

## Measured results

| Input | Previous construction | Equality reuse construction | Construction speedup | Solver seconds | Status |
|---|---:|---:|---:|---:|---|
| fixed-two-seed-3101-types-36 | 53.64 s | 22.93 s | 2.34× | 8.19 s | UNKNOWN |
| mixed-one-two-three-seed-3101-types-36 | 62.80 s | 26.72 s | 2.35× | 9.54 s | UNKNOWN |

Both new solver checks report `timeout`; neither is scored. Construction falls
from 53.64/62.80 to 22.93/26.72 seconds, about 2.34×/2.35×. Against the original
pre-indexing construction of 140.76/156.18 seconds, the two implemented
optimizations together reduce construction by about sixfold. These reductions
concern model building, not solver search or predictive identification.

Measured solver checks remain 8.19/9.54 seconds under configured five-second
limits. Historical reports remain unchanged, including the known-length controls
that establish correct predictive solutions. Artifact validation passed for both
new records, checking source/code/snapshot hashes, matched requests/baselines,
no oracle-length metadata, construction accounting and unscored UNKNOWN.
