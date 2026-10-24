# Fixed German vocabulary: extension boundary

The original free-selection German model has an exact prefix boundary:
**22 words verified SAT, 23 words excluded by a necessary length condition**.
No new solver calls were needed.

The baseline is `experiments/results/german-selection-free-30min.json`, using
the unchanged 2,160-word vocabulary from German source 113. Its request hash
and full SAT witness are checked before accepting the lower boundary.
The vocabulary, alphabets, H2/L3 bounds, free homophone selection, null-free
feasibility model and word boundaries remain fixed. Each longer request permits
one newly inferred key shared by all its words; it does not freeze the particular
key returned by the 22-word solve.

## Decisive obstruction

The baseline starts at normalized corpus record 474 on f3r. Word 23 is `s`,
at record 496, locus f3r.5,+P0. The vocabulary has no one-letter entries;
its shortest entries contain two letters. Each plaintext letter emits at least
one ciphertext character. Consequently every dictionary word emits at least
two characters, so none can emit this one-character word.

This is a direct impossibility proof within the fixed model, independent of
key choice, prefix-freeness and homophone selection. `UNSAT_BY_LENGTH` in the
report identifies this ordinary-Python certificate, not a claimed Z3 result.
Together with the independently checked 22-word witness it proves prefix
minimality. Longer nested prefixes inherit the contradiction.

The requested 30- and 40-word extensions have unambiguous boundaries. The
60-word extension reaches lines marked with uncertain spaces beginning at
word 52. Preparation therefore uses 51 words as the final clean extension,
without skipping words or joining across uncertain lines.

| Prefix words | Result | Evidence |
|---|---|---|
| 22 | SAT | Rechecked existing encoder, dictionary and round trip |
| 23 | UNSAT_BY_LENGTH | One-character word, minimum dictionary length two |
| 30 | UNSAT_BY_LENGTH | Contains the same word 23 |
| 40 | UNSAT_BY_LENGTH | Contains the same word 23 |
| 51 | UNSAT_BY_LENGTH | Contains the same word 23 |

This excludes the fixed source-113 dictionary model, not German generally.
It diagnoses a vocabulary/word-length obstruction, not failure to maintain a
shared key after extending the block. Adding one-letter forms would be a new
vocabulary experiment and has not been done here.

## Controls and reproduction

Six synthetic controls (30, 40 and 51 words; seeds 7 and 17) are prepared using
the same model and full dictionary. For each seed the shorter controls are
prefixes of a single generated 51-word text with one shared key. The generating
witnesses are checked independently by encoding, decoding, bounds, vocabulary
membership and selection. Recovery is **not run**: a solver timeout cannot
affect the direct length proof above.

Controls match word counts and model parameters, not ciphertext word lengths.
Exact length matching is impossible under this dictionary at target word 23.
They therefore must not be used as matched statistical evidence about Voynich.
Public requests exclude truth, which is saved in separate files.

```sh
.venv/bin/python -m benchmarks.german_scaling
.venv/bin/python -m pytest -q tests/integration/test_german_scaling.py
```

The report is [german-scaling.json](../experiments/results/german-scaling.json).
Prepared requests and truth files are under `data/generated/german-scaling/`.
Source, request, corpus, analysis-code and truth hashes are recorded.
The configured 30-minute budget is only saved in replay requests; preparation
does not invoke Z3.

An optional hidden-recovery run for a control uses the existing replay command:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-scaling/inputs/control-30-seed-7.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-scaling-control-30-seed-7-30min.json
```

No long run is necessary for the excluded Voynich prefixes.
