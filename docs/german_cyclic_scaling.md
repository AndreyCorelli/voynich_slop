# Audited Upper Saxon cyclic extension

Source 143 (Tauler edition, Leipzig, 1498) gives an exact prefix boundary:
22 words independently verified SAT and 23 words solver-reported UNSAT.
The extension keeps the complete 2,261-word vocabulary, alphabets,
globally prefix-free H2/L3 key, preserved spaces and text-wide cycling fixed.
A new key may be inferred for each prefix, but must explain that whole prefix.
The original 22-word witness key is not frozen.

## Audit of the one-letter word

The sole one-letter vocabulary entry `o` occurs twice as a separate `morph`
in `XML/143.xml`, word numbers 1177 and 1181. Both lie in line 5,
running line 221, with the context:

```text
o du edele sele o du edele creatur
```

These entries are source text outside the excluded bibliographical, editorial,
annotation and heading elements. The context supports an interjection.
No entry was added to the vocabulary. The audit records the raw word XML,
line identifiers and XML-member hash, checked against the rebuilt vocabulary.

The baseline request hash and complete 22-word cyclic SAT witness were checked.
All extended prefixes pass the necessary word-length check, including the
single-character Voynich `s` at word 23. Thus the previous source-113
minimum-length contradiction does not explain this result.

## Recorded bounded probe

| Input | Budget | Result | Solver seconds |
|---|---:|---|---:|
| Synthetic 23 words, seed 17 | 5 seconds | UNKNOWN | 5.23 |
| Synthetic 23 words, seed 7 | 5 seconds | UNKNOWN | 5.19 |
| Voynich 23 words | 30 seconds | UNSAT | 15.80 |

Formula construction adds wall time beyond the solver budget. Each control
has an independently verified generating witness, but neither hidden-recovery
run finished. These are not successful recovery calibration gates. UNKNOWN
does not mean UNSAT and does not invalidate a separate solver-reported UNSAT
result. No independent UNSAT proof certificate was checked.

The existing verified 22-word SAT and new 23-word UNSAT establish the smallest
excluded prefix under this fixed model. Prepared 30-, 40- and 51-word prefixes
contain the same 23-word prefix and inherit its contradiction: extending a
SAT witness would restrict to a SAT witness for that prefix. They were not
separately solved. Word 52 begins a line with uncertain spaces, so 51 is the
last clean extension used.

This is a bounded dictionary-and-cipher result, not an exclusion of German,
and neither a grammar test nor identification of the manuscript language.
The result does not isolate cycling as the cause: free selection was not
tested on this extended source-143 request.

## Artifacts and commands

The saved short probe is
[budget-30000-controls-5000ms.json](../experiments/results/german-cyclic-scaling/budget-30000-controls-5000ms.json).
[validation.json](../experiments/results/german-cyclic-scaling/validation.json)
checks baseline SAT, request hashes, unchanged model settings and every
synthetic generating witness. The exact initial script is archived at
`data/generated/german-cyclic-scaling/provenance/initial-run.py` and matches
the short report's code hash. Subsequent script changes fix checkpoint
comparison after JSON serialization and protect existing results.

Four Voynich inputs and eight controls are also prepared with 30-minute
Voynich budgets and 30-second control budgets. Each seed defines a single
51-word synthetic text and key; its smaller controls are prefixes. Controls
match word counts and model settings, not ciphertext word lengths. Public
inputs contain no plaintext or key hints; truth files are separate.

Preparation and tests:

```sh
.venv/bin/python -m benchmarks.german_cyclic_scaling --resume
.venv/bin/python -m pytest -q tests/integration/test_german_cyclic_scaling.py
```

No long Voynich run is needed. To investigate the unresolved positive-control
performance separately, replay a prepared control:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-cyclic-scaling/budget-1800000-controls-30000ms/inputs/control-23-seed-7.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-cyclic-scaling/control-23-seed-7-30min.json
```

For future staged runs the benchmark supports `--solve`, `--sizes`, separate
control and Voynich budgets, and `--resume`. It saves each result immediately,
rechecks cached SAT witnesses, stops on an incorrectly UNSAT positive control,
and skips longer Voynich prefixes after UNSAT. Changing budgets creates a
separate checkpoint. Resume skips completed UNKNOWN rows; replay with a new
budget to retry them. Historical short results use the archived code and
are retained separately from checkpoints for the current script.
