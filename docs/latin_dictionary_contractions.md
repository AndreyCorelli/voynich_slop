# Latin dictionary contraction capacity

This branch compares ordinary letters, optional `ae`, and the existing seven
distinct reversible units, followed by expansion into 1–3 ciphertext glyphs.
It adds no inventory rules and calls no solver. Historical evidence and scope
limits remain those in [the original contraction pilot](latin_contractions.md).

Earlier work already screened six medieval Latin texts (80,024 attested
22-word windows), with no positionwise length survivors. The new question is
dictionary capacity: which words in the corrected 5,655-entry Caesar vocabulary
become length-feasible for the saved 23-word ciphertext? Arbitrary combinations
of dictionary words are a weaker language constraint than attested passages.

| Cipher word length | Letters | Optional ae | Optional seven units | Newly feasible with seven |
| --- | --- | --- | --- | --- |
| 3 | 135 | 142 | 157 | 22 |
| 4 | 362 | 379 | 423 | 61 |
| 5 | 824 | 858 | 958 | 134 |
| 6 | 1492 | 1534 | 1750 | 258 |
| 7 | 2301 | 2336 | 2634 | 333 |

Counts are distinct expanded words, not tokenizations. Every attainable unit
count is considered, including uncontracted spelling and non-overlapping
optional applications. Saved examples include expansion-verified witnesses.
These gains establish additional capacity, not a shared encoder fit or Latin
plaintext. Homophone bounds, prefix-free codes and selection policies are not
tested by this necessary length filter. Reversible units retain the requirement
that identical ciphertext words expand to identical plaintext words.

The screen retains one tokenization per attainable count. That is sufficient
for counting length-feasible words but **not** for a complete solver search:
different tokenizations of the same count may fit different shared keys.

Reproduce with:

```sh
.venv/bin/python -m benchmarks.latin_dictionary_contractions
.venv/bin/python -m pytest -q tests/integration/test_latin_dictionary_contractions.py tests/integration/test_latin_contractions.py
```

The focused tests pass 20 cases. Results and newly feasible words are stored in
`experiments/results/latin-dictionary-contractions.json`, with input, inventory
and analysis hashes. No new dependencies, downloads or long runs are needed.

Next gate: build complete tokenization support for this fixed inventory and
validate it on small synthetic contracted-and-expanded ciphertext. Only after
that gate passes should a predefined, bounded Latin comparison be attempted.
Do not widen the inventory in response to failures within this pilot.

This functional gate is now complete: [mixed contraction recovery](mixed_contraction_gate.md)
records three independently verified synthetic SAT results and complete
tokenization support. Full-vocabulary performance remains untested.
