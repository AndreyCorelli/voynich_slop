# Word-length-only full-vocabulary H1 diagnostic

This diagnostic supplies only the eighteen training words' **plaintext token
counts** for the preserved full-vocabulary Latin H1 positive. Word identities,
key, individual code lengths, segmentation and novel continuation remain hidden.
The corrected 5,655-word dictionary, full 24-symbol plaintext alphabet, six-glyph
cipher alphabet, observed domains, free H1/L1–3 and five-second budget are unchanged.

The existing internal `known_word_lengths` feature filters each word's dictionary
candidates to the supplied length. It does not give ciphertext code boundaries
or plaintext symbols. These lengths are oracle information from synthetic truth,
not something established for Voynich. No solver or dataset changes are required.

## Matched results

| Training information | Status | Solver time | Exact novel words |
| --- | --- | --- | --- |
| Fully hidden (saved) | UNKNOWN | 5.03 s | Not evaluated |
| Only plaintext word lengths | Verified SAT | 2.19 s | 3/3 |
| Full plaintext (saved) | Verified SAT | 0.04 s | 3/3 |

All three stages share the same public request and five-second budget. The length
run constructs its formula in 0.82 seconds, separate from solver time. There is
one fit, no seed/budget/encoding tuning, and no selection by continuation score.
The frozen returned key recovers `in`, `a`, `eo` exactly; their ciphertexts and
plaintext types are absent from training, and all generating continuation codes
have already appeared in training.

The recovered training text is:

```text
et et ac ac sub sub re re non non qui qui ut ut ex ex ad ad
```

Only **10 of 18** training words match generating truth. The remaining words
are dictionary-compatible alternatives reproducing the same ciphertext under
a different key. Correct prediction on these three held words therefore does
not establish true-key identification. The held words involve a small subset
of the alphabet and do not expose every wrong assignment.

Supplying lengths resolves this fixed-budget timeout on the fixture without
revealing word identities. It identifies length uncertainty and its associated
candidate proliferation as a useful performance target. Word identity search
still matters and ambiguity persists; this is not a general claim that lengths
are always the dominant bottleneck. Solver encoding/filtering changes when
oracle lengths are provided, so the timing comparison does not isolate a
single implementation cost.

This is oracle-assisted calibration, not successful fully hidden recovery or
evidence for Latin in Voynich. The real manuscript screen remains unchanged
and unresolved where it timed out. No oracle lengths are transferred to it.

## Provenance and validation

Implementation: `benchmarks/full_vocabulary_h1_lengths.py`.
Protocol, code/source hashes, revealed counts, complete key, recovered plaintext,
frozen predictions and independent validation:
`experiments/results/full-vocabulary-h1-lengths/`.
Existing protocol protects the completed experiment from overwrite.

Ten focused tests pass, including exact solver inputs (None plaintext, full
dictionary, only known lengths), invalid-length rejection, no-score UNKNOWN,
output protection and known-plaintext/frozen-scoring regressions. Independent
validation checks the common request identities, oracle lengths, training
reconstruction, 10/18 training matches and all three novel predictions without
new solves.

```sh
.venv/bin/python -m benchmarks.full_vocabulary_h1_lengths
.venv/bin/python -m pytest -q tests/integration/test_full_vocabulary_h1_lengths.py \
  tests/integration/test_full_vocabulary_h1_known.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/full-vocabulary-h1-lengths/validate.py
```

## Next implication

A future performance change should address unknown plaintext lengths while
retaining the complete model and avoiding synthetic truth. Benchmark it on this
preserved fully hidden positive before another manuscript run. Length-restricted
branches must not be reported as global UNSAT unless all admissible branches
are exhausted. Oracle-assisted success alone is not a reason to enlarge cipher
freedoms or solver budgets.
