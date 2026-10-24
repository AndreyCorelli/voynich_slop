# Plaintext-revealed full-alphabet H1 diagnostic

This test reveals only the eighteen training plaintext words in the preserved
full-vocabulary Latin H1 positive. The generating key, code lengths, ciphertext
segmentation and three novel continuation words remain outside the solver input.
Ciphertext, full 24-symbol Latin alphabet, six-glyph cipher alphabet, free
H1/L1–3 model, observed codeword domains and five-second budget are unchanged.

Revealing plaintext necessarily also reveals each word's plaintext token count.
No separate boundary or code-length oracle is supplied. Dictionary word search
is removed from solving; the corrected 5,655-word dictionary remains the same
for independent fit verification and continuation scoring. This is a matched
diagnostic, not successful hidden-plaintext full-vocabulary recovery.

## Recorded outcome

| Training information | Status | Solver time | Exact novel words |
| --- | --- | --- | --- |
| Hidden plaintext, full dictionary (saved) | UNKNOWN | 5.03 s | Not evaluated |
| Revealed plaintext | Verified SAT | 0.04 s | 3/3 |

The returned key independently reproduces exactly the revealed training words
and observed ciphertext. Frozen continuation decoding recovers `in`, `a`, `eo`
exactly; all three ciphertext words are absent from training. Generating code
coverage was already independently verified in the source fixture. No key
repairs, extra choices, budgets or alternative seeds are tried.

On this fixture, key/segmentation recovery is tractable once plaintext and its
token counts are fixed. The hidden word-search problem, including choosing
word lengths, is the immediate bottleneck. This does not isolate word identity
from length/segmentation search, nor guarantee fast key recovery on other texts.
The known-plaintext encoding also removes dictionary-search constraints; the
result is evidence for this matched comparison, not a timing proof about all
full-vocabulary formulations.

The useful key is supplied through revealed plaintext, not discovered from
ciphertext alone. This result cannot be counted as hidden-recovery success,
full-vocabulary predictive calibration, or evidence for Latin in Voynich.
Earlier manuscript UNKNOWN results remain unresolved and unchanged.

## Artifacts and validation

Implementation: `benchmarks/full_vocabulary_h1_known.py`.
Protocol, source/code hashes, revealed training plaintext, complete recovered
key, prediction and independent validation:
`experiments/results/full-vocabulary-h1-known/`.
Existing protocol prevents rerunning/overwriting this fixed diagnostic.

Ten focused tests pass, including exact public solver arguments (no generating
key, dictionary-search input, continuation, length or segmentation oracle), SAT
fit verification, novel-word prediction, output protection and unscored UNKNOWN.
Independent validation checks matched identities, exact revealed plaintext,
training reconstruction and all frozen predictions without new solves.

```sh
.venv/bin/python -m benchmarks.full_vocabulary_h1_known
.venv/bin/python -m pytest -q tests/integration/test_full_vocabulary_h1_known.py \
  tests/integration/test_full_vocabulary_h1.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/full-vocabulary-h1-known/validate.py
```

## Next diagnostic

If this performance branch continues, reveal only plaintext word lengths on
the same hidden full-dictionary request under the same budget. That separates
word-identity search from choosing plaintext lengths. Keep such oracle
information explicitly labeled and do not transfer it to manuscript fits.
No longer manuscript runs or additional cipher freedoms are justified yet.
