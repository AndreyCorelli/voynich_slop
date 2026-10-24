# Selection-only comparison on the Upper Saxon extension

The audited source-143 cyclic model returned UNSAT on the 23-word prefix in
15.80 seconds. Free selection initially returned UNKNOWN at a 30-second
budget, then independently verified SAT in 35.18 seconds with a 30-minute
budget. Text-wide cycling therefore excludes a fit that free selection admits
within the same fixed dictionary and cipher model.

The user-run result is saved in
[german-free-extension-23-30min.json](../experiments/results/german-free-extension-23-30min.json).
Its [independent validation](../experiments/results/german-free-extension-23-30min-validation.json)
checks the request hash, encoder bounds, global prefix-freeness, dictionary
membership and complete encoding/decoding round trip. Relative to the cyclic
request, only selection and timeout changed. Timeout does not change the
feasible model set. The cyclic UNSAT remains solver-reported, without an
independently checked proof certificate.

The recovered 23-word witness contains 52 plaintext letters (mean 2.26):

```text
hyn on du am end ob am hir im ad hab on aff du one ob in ir im o hyn one o
```

This is dictionary compatibility, not demonstrated grammatical prose or
manuscript-language identification. It distinguishes free selection from
text-wide cycling, not from every possible deterministic selection rule.

The comparison uses the exact same 23 words, complete 2,261-word dictionary,
plaintext and ciphertext alphabets, globally prefix-free H2/L3 bounds,
preserved boundaries, no nulls, trie encoding, observed code domains and
30-second budget. Only `selection.mode` changes from `cycle` to `free`.
The reset remains `text`. The request has no plaintext or key hints.

The two synthetic controls reuse the exact cyclic control ciphertexts and
generating witnesses, rather than regenerating different examples. Their
witnesses are independently valid under free selection. Control requests
retain the original five-second budgets. Matching these controls to their
cyclic versions does not make them length-matched to Voynich: they have the
same word count and model, with different ciphertext word lengths.
Both free-selection controls also returned UNKNOWN: seed 7 in 5.24 seconds
and seed 17 in 5.15 seconds. Hidden-recovery calibration remains unresolved.
Their generating-witness checks establish that valid solutions exist.

Artifacts:

- [Preparation report](../experiments/results/german-free-extension.json)
  records source, code, input and truth hashes.
- [30-second Voynich replay](../experiments/results/german-free-extension-23-30sec.json)
  records the effective request, result, solver statistics and environment.
- [Comparison validation](../experiments/results/german-free-extension-validation.json)
  checks the unchanged request fields and replay hashes.
- Public inputs are under `data/generated/german-free-extension/inputs/`;
  generating keys and plaintext remain in the separate original truth files.

Preparation and focused checks:

```sh
.venv/bin/python -m benchmarks.german_free_extension
.venv/bin/python -m pytest -q tests/integration/test_german_free_extension.py
```

Tests require that replacing selection back to cycling reproduces the entire
original request, for both the target and controls. Invalid public wrappers
and noncyclic source requests are rejected. Seven focused tests passed across
this comparison and the cyclic extension checkpoint suite.

The completed 30-minute attempt changed only the timeout. To reproduce locally:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-free-extension/inputs/voynich-23-free.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-free-extension-23-30min.json
```

## Thirty-word extension

The unchanged free-selection model was extended to 30 clean consecutive words.
The target preserves the verified 23-word ciphertext prefix, full dictionary,
alphabets, H2/L3 bounds and all remaining settings. The 30-word request infers
one shared key for the whole prefix, without freezing the 23-word witness key.
The short run returned UNKNOWN in 30.12 seconds. The subsequent user-run
30-minute retry returned **UNSAT in 52.56 seconds**, saved in
[the longer replay](../experiments/results/german-free-extension-30-30min.json).
The [validation](../experiments/results/german-free-extension-30-30min-validation.json)
checks the request hash, unchanged model, exact nested prefix and existing
23-word SAT witness. UNSAT is solver-reported; no independent proof
certificate was checked.

The free-selection boundary is now SAT at 23 words and UNSAT at 30. Prefixes
24 through 29 remain unresolved, so prefix minimality is not established.
The prepared 40- and 51-word prefixes inherit the 30-word contradiction and
do not require separate solver runs. The next diagnostic is to locate the
first excluded prefix within 24–30, beginning with 26 words.
The [completed prefix search](german_free_prefix.md) establishes the exact
free-selection boundary: 28 words independently verified SAT, 29 words UNSAT.

`benchmarks.german_free_scaling` reproducibly prepares 30-, 40- and 51-word
targets plus two verified generating witnesses per size. The 40- and 51-word
targets and these larger controls have not been solved. Public input hashes,
source provenance and the verified SAT prefix are recorded in
[the preparation report](../experiments/results/german-free-scaling-preparation.json).
The controls match word counts and model settings, not target glyph lengths.

```sh
.venv/bin/python -m benchmarks.german_free_scaling
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-free-extension/inputs/voynich-30-free.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-free-extension-30-30min.json
```

The 30-minute attempt above has completed; its command is retained for
reproduction.
