# Known-passage shared-key gate

The three retained grouped matches were tested with exact per-position spellings,
free selection, at most two homophones and code lengths 1–3 grouped units.
All codes are globally prefix-free; word boundaries are preserved and nulls
are absent. Dante includes **every** allowed optional contraction tokenization
at every position, not just the length witness retained by the passage screen.

| Source / selected window | Result | Time |
| --- | --- | --- |
| Kottanner 113 / A-1 | UNSAT | Under 0.1 seconds |
| Dante / S-1 | UNSAT | Under 0.1 seconds |
| East Franconian 133 / S-1 | UNSAT | Under 0.1 seconds |

The positional adapter uses the existing symbolic cipher solver. Its dictionary
graph restricts each position to tokenizations of the specified source word;
words cannot be rearranged or replaced by other words in the union vocabulary.
The codebook covers symbols appearing in candidate tokenizations and the cipher
alphabet consists of observed grouped units. This gate does not test extension
to a full language alphabet or a different glyph inventory.

## Independently checkable obstructions

Prefix-free encoding gives two necessary facts. First, if ciphertext words
share at least three initial units, their first decoded input unit must agree
under L≤3. Second, if one complete ciphertext word is a proper prefix of another,
its decoded input sequence must be a proper prefix of the other sequence.

Each case violates one of these facts independently of homophone selection:

- Kottanner: words 7 and 8 must share their first input unit, but the proposed
  plaintext is `hart` and `vnd`.
- Dante: words 2 and 20 must share their first input unit, but `iam` and `mente`
  have incompatible initial units under every permitted contraction path.
  There is also a proper-prefix obstruction at words 6 and 22 (`cum` / `est`).
- East Franconian: ciphertext word 22 is a proper prefix of word 6, but proposed
  plaintext `zw` is not a prefix of `es`.

The validation artifact retains exact ciphertext token arrays, relation type,
all length-feasible plaintext unit paths at the two positions and the
independently checked absence of a compatible pair. These small structural
certificates supplement solver UNSAT; no general-purpose solver proof object
is claimed.

## Scope and stopping point

All three necessary-length survivors fail shared-key consistency. This closes
the fixed three-case gate without long runs, prefix searches or new inventory
rules. It excludes **these aligned passages under this model**, not German,
Latin, encryption in general, or dictionary combinations. The fact that A-1
and S-1 have no equal ciphertext words did not eliminate prefix constraints.

Seven focused tests pass: hidden positional constraints, a known-valid
contraction case, a letters-only impossibility and complete equal-length
alternative paths. Synthetic cases explicitly declare adequate ciphertext
alphabets so unused plaintext alternatives can receive legal prefix-free codes.

```sh
.venv/bin/python -m benchmarks.known_passage_keys
.venv/bin/python -m pytest -q \
  tests/integration/test_known_passage_keys.py \
  tests/integration/test_complete_contractions.py
```

The report and structural certificates are under
`experiments/results/known-passage-keys/`. The solver budget was ten seconds
per case; no long run is needed.
