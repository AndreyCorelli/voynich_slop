# Matched full-vocabulary Latin H1 positive

This diagnostic checks whether short-budget full-vocabulary recovery works even
for a simpler known cipher. It reuses the Latin letter-only H1 fixture from
`novel-word-holdout`, with eighteen training words and three distinct novel
continuation words (`in`, `a`, `eo`). Every generating continuation codeword has
appeared in training. No H2, contractions, guidance, new corpus or seed search.

## Matched requests

The reduced arm contains the original twelve-word dictionary; the full arm
contains the corrected 5,655-word Latin dictionary. Both use the same **full
24-symbol Latin alphabet** from the existing full-dictionary template, the same
six-glyph cipher alphabet, identical training observations, free H1/L1–3,
prefix-free codes, observed codeword domains and a five-second solver budget.
The serialized requests differ only in dictionary membership. Word-length bounds
are derived from each complete dictionary; no oracle length/segmentation is used.

The generating key's observed assignments are unchanged. Unused Latin alphabet
labels receive unused length-two codes in fixed lexicographic order, without
altering training or continuation ciphertext. This supplies a complete known
positive under both requests. It also prevents alphabet expansion from being
confounded with dictionary growth in the comparison.

Continuation plaintext and ciphertext words are all absent from training.
The true key independently decodes all three exactly and meets both requests.
Held words remain available in both dictionaries. This is an engineered
short-word vocabulary fixture, not a natural Latin passage, and does not match
the fresh Voynich screen's 22-word training size or 25-glyph cipher alphabet.
It tests dictionary scale while holding this fixture fixed.

## Recorded result

| Dictionary | Status | Solver time | Construction time | Exact novel words |
| --- | --- | --- | --- | --- |
| 12 words | Verified SAT | 0.23 s | 0.23 s | 3/3 |
| 5,655 words | UNKNOWN (timeout) | 5.03 s | 2.37 s | Not evaluated |

The reduced control succeeds even with the full alphabet and recovers every
novel word. The full dictionary does not produce a key within the fixed budget.
No prediction score is assigned to UNKNOWN; it is not a failed prediction,
UNSAT or evidence against Latin/H1. A compatible useful generating key is
already independently verified.

This identifies a dictionary-scale recovery obstacle in this matched control.
It cannot distinguish performance from ambiguity after successful full recovery,
because no full-vocabulary SAT key was returned. The reduced result does not
establish full-vocabulary calibration or justify interpreting manuscript
UNKNOWNs as negative language evidence. No longer budget or alternative seed
was tried after the timeout.

## Artifacts and verification

Implementation: `benchmarks/full_vocabulary_h1.py`.
Protocol, source/code identities, complete matched requests, completed generating
key, truth/continuation, results and independent validation:
`experiments/results/full-vocabulary-h1/`.
Completed arms are checkpointed and skipped on rerun; changed inputs/code are
rejected. Earlier fixtures and manuscript results remain unchanged.

Ten focused tests pass, including request equivalence apart from dictionary,
full-alphabet positive verification, type/ciphertext novelty, true-code coverage,
and explicit no-score/no-rerun behavior for UNKNOWN. Independent validation
reproduces generating encoding/decoding, verifies the SAT witness and recomputes
frozen predictions without new solves.

```sh
.venv/bin/python -m benchmarks.full_vocabulary_h1 --run
.venv/bin/python -m pytest -q tests/integration/test_full_vocabulary_h1.py \
  tests/integration/test_novel_word_holdout.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/full-vocabulary-h1/validate.py
```

## Next implication

Pause further manuscript runs and model freedoms. A cheap matched
plaintext-revealed check on this exact full-alphabet/full-dictionary fixture can
separate key/segmentation feasibility from hidden word search. Keep it labeled
as a diagnostic rather than hidden-recovery success. Any performance change
should be evaluated on this preserved positive before another Voynich timeout.
