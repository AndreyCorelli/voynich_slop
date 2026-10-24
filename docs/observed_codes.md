# Observed codeword-domain experiment

Any codeword actually emitted in a null-free observed sample is a contiguous
substring of one ciphertext word, within the public code-length bounds. The
optional observed-domain formula states that consequence explicitly for key
mappings used in the sample. It never joins substrings across word boundaries.
The public pool depends only on ciphertext and bounds, not on plaintext or key.

For unprotected key slots, existing normalization already requires every active
slot to be used, so the domain condition is guarded by slot activity. For protected
pins or learned owners that may retain unvisited alternatives, the guard instead
checks actual appearances of that symbol/choice pair. Unused letters completed
outside SMT and unvisited protected homophones need not belong to the pool.
This preserves the model and avoids treating arbitrary completion codes as observed.
Masked observations are unsupported by this option so unobserved words cannot
accidentally be restricted by the observed pool.

Substrings are grouped by length and padded prefix-tree rank. Finite interval
start variables receive explicit disjunctions of those ranks rather than relying
only on the existing per-token encoding constraints to derive the same domains.
Prefix-freeness, code counts, dictionary membership and cycle rules stay unchanged.
Every SAT explanation independently checks that its actual emitted codes belong
to the pool, in addition to the usual re-encoding, decoding and cycle verification.
The option is separate from the ordinary public request and remains experimental.

The benchmark retries the same saved full-vocabulary seed-7 4/6/8/11-word hidden
controls, using 30-second solver budgets and no fixed lengths or boundary hints.
Matched historical baselines are imported only after checking their public input
hashes and exact budgets. Baseline timings are previous runs, not fresh paired
measurements. No truth files are read by this benchmark.

```sh
.venv/bin/python -m benchmarks.observed_codes
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/observed-codes/inputs/words-04.json
```

Configuration: `experiments/configs/observed-codes.json`. Report:
`experiments/results/observed-codes.json`. Public wrappers carry only a request
and the optional domain strategy. Metadata reports the distinct substring count
by length, constraints, solver statistics and timings. Construction lies outside
the solver timeout and is included in total elapsed time.

Tests compare original/observed SAT/UNSAT outcomes over small hidden texts under
both text- and word-reset cycles, validate substring boundaries, verify that
unused pinned alternatives can stay outside the pool, and check compatibility
with fixed-length branch solving. Those fixed-length tests are separate from the
fully hidden benchmark. This experiment does not run a manuscript solve.

## Recorded result

| Words | Distinct codeword substrings | Baseline | Observed domains | Solver time | Total time |
|---:|---:|---|---|---:|---:|
| 4 | 136 | UNKNOWN | UNKNOWN | 30.07s | 33.17s |
| 6 | 193 | UNKNOWN | UNKNOWN | 30.10s | 34.56s |
| 8 | 231 | UNKNOWN | UNKNOWN | 30.11s | 35.99s |
| 11 | 285 | UNKNOWN | UNKNOWN | 30.13s | 37.87s |

All four explicit-domain retries returned UNKNOWN at the 30-second budget,
matching the baseline feasibility status. No performance improvement was
established; the strategy remains optional and the default is unchanged. All
416 tests pass. These are known-positive controls, so their timeouts do not
reject the cipher model or establish any manuscript-language conclusion.

A next diagnostic could supply only word lengths on the full eleven-word
control, to determine whether its conditional search is tractable when the
length vector is correct. This would be labeled an oracle test, separate from
public length enumeration and hidden recovery.

## User-initiated 30-minute full-control retry

From the repository root:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/observed-codes/inputs/words-11.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/observed-codes-11-30min.json
```

This retries only the full eleven-word control with observed substring domains.
The solver budget is 30 minutes; construction adds elapsed time. The saved report
includes the effective request, result, timing and environment. The long run was
not started as part of the command preparation.

## Verified long-run synthetic witness

The user-initiated full eleven-word run returned **SAT, independently verified**
after 1,300.45 seconds of solver time (21 minutes 40 seconds). The effective public
request matches the original full-vocabulary control except for its timeout.
Validation rechecked the complete legal prefix-free key, all dictionary words,
word bounds, re-encoding/decoding, text-wide cycles, segmentation offsets and
observed used-codeword domains. The validation record is
`experiments/results/observed-codes-validation.json`, with a hash of the saved
`observed-codes-11-30min.json` report.

This establishes one full-vocabulary hidden synthetic recovery without truth
hints under the observed-domain formulation. The earlier formulation timed out
at 1,800 seconds on the same public control. The single-run comparison is evidence
of improvement on this instance, not a general speedup or manuscript-language
conclusion. Other full-vocabulary seeds still require calibration.

## Prepared full 23-word Voynich retry

The original full prefix has been saved with the same observed-domain strategy
and 30-minute budget. It retains H2/L3, the full dictionary, alphabets, word
boundaries and text-wide cycles. No fixed plaintext lengths, segmentation, key
pins, hints or learned exclusions are supplied. Only the solver timeout changes
from the original request; observed-domain clauses are redundant consequences.

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/observed-codes-voynich/inputs/words-23.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/voynich-observed-codes-23-30min.json
```

The user subsequently ran this command: **SAT, verified, 351.30 seconds**.
The saved witness was independently audited and its mappings tested against
word 24. The frozen vocabulary includes English footer contamination; see
[the plaintext, key and scoped extension result](voynich_witness_extension.md).
