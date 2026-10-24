# Mixed contraction and expansion recovery gate

The fixed seven-unit inventory now has complete optional tokenization support
in `src/voynich_smt/language/contractions.py`. Unlike the length-capacity screen,
this retains all distinct paths of equal length. Applications remain optional,
non-overlapping, and scoped to the documented initial/final/whole-word positions.
Each unit expands uniquely to its original spelling. An explicit variant cap
raises an error instead of silently truncating the model.

The existing solver already accepts multi-character atomic plaintext symbols.
The adapter supplies its dictionary with letter and contraction-unit paths;
no change to cipher constraints or solver internals was needed. Cipher codes
remain globally prefix-free, with free homophone choices and no nulls.

## Synthetic gate results

Each case exercises all seven contraction units as well as spelled-out `ae`
and `per`. Generation uses two two-glyph homophones per input unit; recovery
allows up to two homophones of length 1–3. The nine-word fixture is deliberately
small, and not a grammatical Latin passage. Only the ciphertext, complete unit
dictionary, alphabets and cipher bounds are supplied to recovery. Plaintext,
key and choices are saved separately as truth artifacts.

| Seed | Result | Solver seconds |
| --- | --- | --- |
| 7 | Independently verified SAT | 0.58 |
| 17 | Independently verified SAT | 0.56 |
| 1729 | Independently verified SAT | 0.50 |

Every recovered encoder reproduces the ciphertext and uniquely decodes it;
every expanded recovered word belongs to the original spelling vocabulary.
The recovered explanation need not reproduce the generating key or its choice
of contractions. These small successes establish functional support, not
performance at the full Latin vocabulary scale or evidence about Voynich.

Focused tests also retain overlapping alternative paths of equal length,
check rule scopes and expansion round trips, reject unknown units and duplicate
IDs, and prove a controlled distinction: encoding the sole dictionary spelling
`ae` as one ciphertext glyph is UNSAT with letters alone, but verified SAT with
the optional `<ae>` unit. All **24 focused tests pass**.

```sh
.venv/bin/python -m benchmarks.mixed_contraction_gate
.venv/bin/python -m pytest -q \
  tests/integration/test_complete_contractions.py \
  tests/integration/test_latin_dictionary_contractions.py \
  tests/integration/test_latin_contractions.py
```

The checkpointed report is `experiments/results/mixed-contraction-gate.json`;
separate public and truth inputs are under `data/generated/mixed-contraction-gate/`.
Hashes bind inputs, inventory, tokenizer and gate code.

The next experiment should compare letters, ae-only and seven-unit models on
the same corrected Latin vocabulary and ciphertext, with a fixed budget and
selection policy across the three variants. Before a long run, calibrate on
larger synthetic inputs using that vocabulary. Keep the inventory fixed and
stop this branch at its agreed budget; an UNKNOWN remains unresolved.

The [full-vocabulary pilot](latin_mixed_comparison.md) is now prepared and
short-probed. Its seven-unit positive passes, while the seven-unit Voynich
probe is unresolved at 10 seconds. The next run is capped at one 30-minute
attempt, followed by review rather than further model expansion.
