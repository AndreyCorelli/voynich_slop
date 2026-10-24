# Fixed reduced-vocabulary recovery diagnostic

The saved Latin synthetic key, ciphertext, full plaintext/ciphertext alphabets,
free H2/L1–3 prefix-free model and original continuation remain unchanged.
Only dictionary size varies. The predefined protocol is
`experiments/configs/reduced-vocabulary-calibration.json`: 64, 128 and 256
entries, tested on the same 5-, 10- and 15-word training prefixes, with ten
seconds per fit and no seed/budget retries.

All **49 distinct words from the complete 52-word generating passage** are
included in every dictionary. Remaining entries are nested distractors sampled
from the corrected full dictionary with seed 1729, yielding 15, 79 and 207
distractors. The inclusion of continuation spellings is deliberately
**truth-assisted vocabulary construction**. It makes this an easier diagnostic,
not blind or full-vocabulary calibration, and cannot support language evidence.
The solver still receives no word order, key, choices or continuation ciphertext.

## Complete fixed matrix

| Training words | 64 entries | 128 entries | 256 entries |
| --- | --- | --- | --- |
| 5 | Verified SAT, 6.69 s | UNKNOWN, 10.05 s | UNKNOWN, 10.05 s |
| 10 | UNKNOWN, 10.06 s | UNKNOWN, 10.09 s | UNKNOWN, 10.19 s |
| 15 | UNKNOWN, 10.10 s | UNKNOWN, 10.16 s | UNKNOWN, 10.12 s |

Every training case has an independently checked generating witness. UNKNOWN
therefore remains unresolved recovery, not incompatibility or failed prediction.
The SAT key was independently verified and frozen before scoring source words
31–52. It fully decodes **0/22**, produces **0 dictionary hits** under either
the reduced or full vocabulary, and recovers **0 exact generating words**.

Its five recovered training words are:

```text
omnium quod partes differunt ab
```

They constitute a legal dictionary/cipher fit, not recovery of the source
passage. Word-order or grammatical validity was not constrained by this model.
The verified generating encoder still decodes all 22 continuation words.

## Coverage and interpretation

Post-fit generating-codeword coverage is unchanged from the previous diagnostic:
3, 10 and 10 continuation words use only generating homophones seen in the
5-, 10- and 15-word training prefixes respectively. With the five-word plaintext
revealed, all three covered continuation words were recovered correctly. The
hidden-word 64-entry fit recovers none of them, showing an additional ambiguity
failure beyond simply encountering unobserved homophones.

Narrowing vocabulary made one fitting problem solvable within the budget, but
did not preserve predictive ability for that fit. Eight UNKNOWNs do not establish
a monotone vocabulary-size/runtime relationship, and one SAT does not establish
typical recovery behavior. No discarded seeds, successful-key selection or
post-result dictionary adjustments are involved.

This fixed matrix is complete. The main comparative benchmark remains deferred:
we still lack a successful hidden-word predictive calibration. Further budget
escalation or cipher-family expansion is not justified by this diagnostic alone.
Before more Voynich fitting, a distinct approach would need to constrain word
sequences or assess multiple compatible keys rather than treating one arbitrary
dictionary SAT witness as a predictive explanation.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.reduced_vocabulary_calibration --resume
.venv/bin/python -m pytest -q \
  tests/integration/test_reduced_vocabulary_calibration.py \
  tests/integration/test_known_plaintext_ladder.py \
  tests/integration/test_synthetic_size_ladder.py
```

`--resume` preserves completed results, including UNKNOWN, and skips them;
changed inputs/configuration/code or tampered request hashes are rejected.
All **7 focused tests pass**, covering nested seeded vocabularies, required-word
coverage, homophone versus letter coverage, unchanged prefixes/alphabets,
UNKNOWN handling, checkpointing and frozen continuation scoring.

Reports, complete dictionary arrays and validation are saved under
`experiments/results/predictive-calibration/` as
`reduced-vocabulary-10000ms.json` and `reduced-vocabulary-validation.json`.
All nine generating witnesses, nested dictionaries, effective request hashes,
the recovered SAT witness and both continuation scores were independently
checked. Nine short fits were made; no long or Voynich runs.
