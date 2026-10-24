# Full-vocabulary synthetic prefix calibration

This experiment localizes recovery difficulty by solving increasing prefixes of
one fixed saved seed-7 synthetic text. It tests 1, 2, 4, 6, 8 and 11 words with
the complete 5,665-entry vocabulary, full plaintext/ciphertext alphabets, H2/L3,
prefix-free encoding, text-wide cycles, trie membership and Boolean phase updates.
Only ciphertext prefix length varies. Each solve starts fresh and gets 30 seconds;
no earlier recovered key or plaintext is supplied as a hint.

Prefixes begin at the first word, so the original cycle starts at phase zero.
The saved generation witness is independently checked for the full text and
for every truncated prefix. Its choices are truncated by plaintext token count,
not ciphertext size. Public replay inputs contain only the request and cycle
formula. Ground truth is saved separately and never passed into hidden recovery.
A recovered fit may differ from the generation witness; this is an existence
experiment, not a requirement to recover the original key uniquely.

All lengths are attempted even after a timeout. Longer inputs can constrain the
search more strongly, so solver runtime and UNKNOWN outcomes need not be
monotonic. A sampled first timeout is not a minimal UNSAT prefix or a proof of
impossibility. Every instance is known positive; UNSAT would be recorded and
raise an error. Every returned SAT fit must pass independent verification.

```sh
.venv/bin/python -m benchmarks.synthetic_prefix
.venv/bin/python -m benchmarks.synthetic_prefix --resume
.venv/bin/python -m benchmarks.cycle_performance --replay data/generated/synthetic-prefix/inputs/seed-7-words-04.json
```

The configuration is `experiments/configs/synthetic-prefix.json`. Results are in
`experiments/results/synthetic-prefix.json`; wrapped public inputs and separate
truth snapshots are in `data/generated/synthetic-prefix/`. The report records
ciphertext size, solver statistics, construction and total elapsed time, witness
verification, source hashes and implementation/environment identity. Resume
requires these identities to match and rechecks saved public inputs and SAT fits.
There is no manuscript solve or 30-minute attempt in this experiment.

## Recorded results

| Prefix words | Ciphertext tokens | Result | Solver time | Total time |
|---:|---:|---|---:|---:|
| 1 | 26 | SAT | 1.13s | 1.82s |
| 2 | 41 | SAT | 2.19s | 3.65s |
| 3 | 58 | SAT | 13.93s | 16.26s |
| 4 | 79 | UNKNOWN | 30.08s | 33.00s |
| 6 | 133 | UNKNOWN | 30.08s | 34.33s |
| 8 | 175 | UNKNOWN | 30.09s | 35.89s |
| 11 | 252 | UNKNOWN | 30.14s | 37.68s |

Every SAT fit was independently verified. The three-word follow-up fills
the gap between two-word SAT and four-word UNKNOWN; it is saved separately in
`experiments/results/synthetic-prefix-gap.json`, with replay inputs and truth in
`data/generated/synthetic-prefix-gap/`. Its configuration is
`experiments/configs/synthetic-prefix-gap.json`.

For this seed, formula and 30-second budget, verified recovery succeeds through
three words. Four words is the first tested timeout; the tested longer prefixes
also timed out. This is a runtime observation, not an UNSAT or manuscript-language
conclusion. Known valid witnesses exist for all prefixes. Single-run timings
do not establish a general length threshold or exclude later SAT fits.

All 362 tests pass, and checked resume of the completed main run succeeded
without rerunning the solver. The next targeted diagnostic is the four-word
control: compare hidden recovery with separately revealed segmentation, plaintext
or partial mappings to identify which uncertainty creates the difficulty.

To reproduce the three-word follow-up:

```sh
.venv/bin/python -m benchmarks.synthetic_prefix \
  --config experiments/configs/synthetic-prefix-gap.json \
  --output experiments/results/synthetic-prefix-gap.json \
  --artifacts data/generated/synthetic-prefix-gap
```
