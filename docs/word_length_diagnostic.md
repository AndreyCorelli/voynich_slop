# Four-word length-only diagnostic

This experiment separates word-length knowledge from exact codeword boundaries
on the saved four-word seed-7 control. Three fresh solves use the same full
5,665-entry vocabulary, H2/L3 prefix-free coding, trie membership, text-wide cycles
and 30-second budgets. Each starts with a new solver and no previous recovered
key or plaintext hints.

The length-only wrapper supplies the four plaintext token counts `[9, 5, 6, 8]`.
It supplies no plaintext letters, codeword boundaries, mappings or choices.
Candidate words are filtered by length, and word sizes are fixed accordingly;
all individual codeword lengths and offsets remain symbolic. The boundary case
uses the original complete segmentation. The fully hidden case supplies neither.

Oracle lengths live in an explicit diagnostic wrapper, separate from ordinary
`HiddenRecoveryRequest`. Inputs are validated against observed word sizes and
code-length bounds. SAT verification checks the recovered plaintext lengths as
well as dictionary, cipher, cycle and re-encoding correctness. Tests establish
that a length-restricted model has the same SAT feasibility as the union of all
admissible boundary models with that count. Distinct segmentations remain feasible
at the same supplied lengths. Invalid lengths and mixed oracle wrappers are rejected.

## Recorded result

| Information supplied | Result | Solver time | Total time |
|---|---|---:|---:|
| Word lengths only | Verified SAT | 4.96s | 5.74s |
| Exact boundaries | Verified SAT | 4.03s | 4.79s |
| Neither | UNKNOWN (timeout) | 30.09s | 33.02s |

Both oracle cases pruned 14,023 per-word dictionary candidates in aggregate; the
fully hidden preprocessing pruned none. The length-only fit has different
boundaries from the generated witness, providing a concrete example of successful
recovery without the original segmentation. Every SAT explanation was independently
verified. All 382 tests pass.

For this instance and formula, word-length information alone is sufficient to
make recovery tractable within the budget. This does not establish an exclusive
bottleneck or a general speedup; the timings are single-run observations. The
length-only success is an oracle diagnostic, not full hidden recovery. The model
and manuscript-language hypothesis remain unaffected by the hidden timeout.

Observed ciphertext word lengths are `[26, 15, 17, 21]`. Public L3 bounds alone
therefore give minimum plaintext lengths `[9, 5, 6, 7]`, close to the supplied
oracle lengths. A useful next experiment is to search publicly admissible length
vectors starting with shorter candidates. Such a search must retain all allowed
vectors or label its explored subset explicitly; one rejected vector cannot rule
out the complete hidden model. Oracle lengths must not enter that search.

```sh
.venv/bin/python -m benchmarks.segmentation_diagnostic \
  --config experiments/configs/word-length-diagnostic.json \
  --output experiments/results/word-length-diagnostic.json \
  --artifacts data/generated/word-length-diagnostic

.venv/bin/python -m benchmarks.segmentation_diagnostic \
  --replay data/generated/word-length-diagnostic/inputs/lengths.json
```

The original boundary diagnostic remains available with its default configuration.
The new report preserves source and truth hashes plus all fresh results. Replay
with the dedicated diagnostic runner preserves the length-only restriction.
