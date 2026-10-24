# Footer-free Caesar vocabulary retry

Latin parser version 2 stops at an older Gutenberg prose footer when present,
or otherwise at the formal END marker. Tests cover LF/CRLF input, source offsets,
and both separate-word and concatenated normalization. The preserved source
checksum is verified before rebuilding; no download is needed.

The original parser-v1 corpus, public requests and solver reports remain intact.
The corrected corpus is `data/processed/caesar-latin-v2.json`. The preparation
report is `experiments/results/clean-latin-preparation.json` and records source,
corpus and request hashes, vocabulary changes and the old witness membership test.
Every pre-footer record retains its original tokens and offsets.

The vocabulary shrinks from **5,665 to 5,655 entries**. The removed entries are:

```text
books by commentaries end gutenberg i iulius iv of proiect
```

Some are plausible Latin entries but occurred only in the English footer of this
particular source. The whitelist still permits `a/e/i/o`; only `a/e` occur as
single-letter words in the corrected corpus. The previous 23-word witness fails
membership on `by`, `iv`, and `of`.

This is footer cleanup, not a Latin lexicon or grammar classifier. Roman numerals
and names occurring in the actual Caesar body remain. SAT would establish a
word-vocabulary fit, not automatically a grammatical or meaningful Latin passage.

The new public request uses the same 23 ciphertext words, alphabets, H2/L3 bounds,
text-wide cycles, word-boundary assumptions and observed codeword domains. It
changes only the vocabulary and solver budget. It contains no key or length hints.

Prepare the new corpus and request:

```sh
.venv/bin/python -m benchmarks.clean_latin_retry
```

Short retry:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/clean-latin-voynich/inputs/words-23.json \
  --timeout-ms 30000 \
  --replay-output experiments/results/voynich-clean-latin-23-30sec.json
```

The short retry returned **UNKNOWN in 30.08 solver seconds**. It neither
recovers a corrected witness nor rejects the corrected model. All 420 tests pass.

For a user-run 30-minute retry:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/clean-latin-voynich/inputs/words-23.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/voynich-clean-latin-23-30min.json
```

The user-run long retry returned **UNSAT in 210.32 solver seconds**. Saved
request and input checksums match the prepared corrected request, changing only
the timeout. The provenance audit is
`experiments/results/clean-latin-unsat-validation.json`. No independent UNSAT
proof certificate was checked. `verified=False` refers to the absence of a SAT
witness; it does not turn the solver's UNSAT result into UNKNOWN.

This rules out this 23-word prefix in the fixed 5,655-entry Caesar vocabulary
under globally prefix-free codes of length 1–3, at most two homophones per
letter, text-wide phase-zero cycles, no nulls and preserved word boundaries.
It does not rule out Latin outside this vocabulary or broader cipher families.
The old SAT result remains valid for its frozen, broader vocabulary.

Next, isolate which removed vocabulary entries restore feasibility, and find
a shorter UNSAT prefix under the corrected vocabulary. These can distinguish
the effect of deleting a legitimate Latin entry such as `i` from deleting
English footer words.


The [vocabulary restoration diagnostic](vocabulary_restoration.md) separates
restoring `i/iv/iulius` from restoring English `by/of`, and revalidates the old
witness with just its three missing words restored.
