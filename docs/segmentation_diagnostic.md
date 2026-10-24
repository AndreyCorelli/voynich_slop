# Four-word synthetic boundary diagnostic

The saved seed-7 four-word prefix has a known valid generation witness, but hidden
recovery timed out at 30 seconds. This diagnostic supplies only the witness's
codeword boundary offsets in each ciphertext word. The plaintext tokens, key,
homophone choices and cyclic phases remain unknown. Both paired runs retain the
full 5,665-word vocabulary, full alphabets, H2/L3 prefix-free coding, trie membership
and text-wide Boolean-phase cycles. Each receives a fresh 30-second solve budget.

Boundary offsets necessarily reveal each word's plaintext token count as well as
its individual code lengths. Vocabulary candidates are filtered by that count;
the vocabulary itself is unchanged. The ordinary public hidden-recovery request
has no boundary field. An explicit diagnostic wrapper carries this oracle input,
and a separate entry point validates and imposes it. It is not hidden recovery
or a manuscript witness.

Each boundary list must start at zero, end at the observed word length, and have
strictly increasing integer offsets whose differences satisfy code-length bounds.
SAT extraction independently checks both the full encoding explanation and exact
agreement with the supplied boundaries. Tests compare all admissible segmentations
on small cases: their SAT union agrees with ordinary hidden feasibility. They also
reject malformed boundaries and keep oracle fields out of ordinary requests.

## Recorded result

| Information supplied | Result | Solver time | Total time |
|---|---|---:|---:|
| Codeword boundaries | Verified SAT | 3.02s | 3.78s |
| None; fresh hidden solve | UNKNOWN (timeout) | 30.07s | 33.02s |

The generation witness was checked before either solve. The returned SAT fit was
independently verified and need not reproduce the original plaintext or key.
Boundary-derived lengths pruned 14,023 per-word vocabulary candidates in total;
the hidden run's prefix preprocessing pruned none. These are counts over all
word candidate sets, not distinct vocabulary entries.

The result identifies oracle boundaries, including their implied word lengths,
as useful information for this instance and formula. It does not prove that
segmentation alone is the exclusive bottleneck or that the cipher model is valid
for Voynich. Single-run timings are diagnostic observations. The next isolating
test would reveal only the four plaintext word lengths, allowing boundaries to
remain symbolic, to separate length pruning from exact codeword boundaries.

```sh
.venv/bin/python -m benchmarks.segmentation_diagnostic
.venv/bin/python -m benchmarks.segmentation_diagnostic \
  --replay data/generated/segmentation-diagnostic/inputs/boundaries.json
```

Dedicated diagnostic replay preserves the supplied boundary restrictions. It
accepts `--timeout-ms` for a budget override. The configuration is
`experiments/configs/segmentation-diagnostic.json`; results are in
`experiments/results/segmentation-diagnostic.json`. The two explicit wrappers are
saved in `data/generated/segmentation-diagnostic/inputs/`. The report records
input/truth provenance, the earlier baseline and fresh paired results.
