# Shortest UNSAT suffix ending at word 23

This search retains the fixed 5,658-entry footer-free Caesar vocabulary plus
`i/iv/iulius`, globally prefix-free H2/L3 codes, preserved word boundaries,
no nulls, and text-wide cyclic selection. It tests only contiguous suffixes
ending at word 23 (`chololy`). It does not test arbitrary deletions or relax the
cipher bounds.

The original broader-vocabulary witness independently certifies the last eight
words in this vocabulary:

```text
spe ab in is iv a dc ante
```

To restrict a text-wide cyclic witness to a suffix, count each plaintext
letter's occurrences in the removed initial block. Rotate that letter's ordered
homophone list by this count modulo its number of alternatives, and subtract
the same phase from retained choice indices. The emitted ciphertext stays the
same and the retained block obeys phase-zero cycles. Code bounds and global
prefix-freeness are preserved. Unused code lists may rotate too.

New hidden solves infer their own key with phase-zero code order; they receive
no rotation, key, length, phase or segmentation hints. Freely inferred code
ordering makes this the same existential suffix question. In particular, a
legal longer-suffix witness can always be restricted and rotated to certify a
shorter suffix. Adjacent SAT/UNSAT suffix lengths therefore certify minimality.

The 15-word suffix, words `[8:23]` with zero-based endpoints, returned UNKNOWN
in 30.07 solver seconds. Current bounds are **8 words verified SAT / 23 words
UNSAT**. The shortest suffix is not yet established.

Run or resume a short search:

```sh
.venv/bin/python -m benchmarks.clean_latin_suffix --resume
```

Continue with **up to 30 minutes per suffix check**:

```sh
.venv/bin/python -m benchmarks.clean_latin_suffix \
  --timeout-ms 1800000 --resume
```

The longer search has not been launched. It retries the unresolved midpoint and
continues binary search after decisive results. It checkpoints every result,
stops at UNKNOWN, and marks completion only when SAT and UNSAT lengths are
adjacent. Total duration can exceed 30 minutes. Construction time is additional
to each solver budget. UNKNOWN never moves a certified bound.

Report: `experiments/results/clean-latin-suffix.json`.
Prepared public wrappers: `data/generated/clean-latin-suffix/inputs/words-01.json`
through `words-23.json`. Requests contain only the suffix ciphertext and the
fixed model, with the observed-domain option. Resume checks source hashes,
request parameters, exact suffix identity and input checksums, and revalidates
cached SAT witnesses. Cached rows preserve their effective requests even when
prepared files are regenerated with a different budget.

Tests verify rotation and ciphertext/phase preservation for two and three
alternatives at every cut of a small text, absence of source-witness mutation,
and rejection of a prefix presented as a cached suffix. UNSAT reports are not
independently checked proof certificates. A minimal result concerns only
suffixes of this fixed 23-word block under this fixed vocabulary and cipher.

## Completed boundary and contiguous-block minimality

The user-run longer search completed:

| Suffix length | Original words (one-based) | Result | Solver time |
|---:|---|---|---:|
| 15 | 9–23 | SAT | 53.18s |
| 19 | 5–23 | SAT | 190.07s |
| 21 | 3–23 | SAT | 140.02s |
| 22 | 2–23 | UNSAT | 232.50s |

All saved suffix requests and hashes were checked. SAT witnesses were
independently verified, including segmentation offsets. The completed audit is
`experiments/results/clean-latin-suffix-validation.json`.

The **shortest UNSAT suffix is words 2–23, length 22**, beginning `qopal` and
ending `chololy`. Its ciphertext is:

```text
qopal chol cthol daimg ycheor chor dam qotcham cham ochor qocheor
chol daiin cthy schey chor chal chag cham cho qokol chololy
```

The verified 21-word suffix plaintext is:

```text
an eo xl eum ab xv dum iv sc dum an xl et ob ab in is iv a dc ante
```

Combining this with the independently verified 22-word SAT prefix proves that
this is also the **shortest UNSAT contiguous block anywhere in the original
23-word sample**. Any block ending before word 23 is contained in the SAT prefix
(words 1–22). Any shorter block ending at word 23 is contained in the SAT suffix
(words 3–23). Rotating code lists preserves SAT under either contiguous
restriction. Thus every block of length at most 21 is SAT, while words 2–23 are
UNSAT.

Deleting either endpoint of that conflict gives a verified SAT block. The
words 2–22 witness is derived from the prefix witness by dropping word 1 and
rotating cyclic code lists; it was independently checked and saved at
`data/generated/clean-latin-suffix/certificates/drop-last-word.json`. It contains
an explicit public input and derived witness, with no new solver timing claimed.

This does not prove arbitrary deletion minimality: removing an interior word
changes cyclic history. It concerns only this original 23-word sample and fixed
vocabulary/cipher model. UNSAT report provenance was checked; no independent
UNSAT proof certificate was checked.

A next useful experiment is to keep this 22-word block and its vocabulary fixed
and compare free homophone selection and word-reset cycles against the current
text-wide cycle. SAT in a relaxation would help isolate the selection rule's
role; UNSAT would show that that particular relaxation is insufficient.


The [selection-rule comparison](conflict_selection.md) now implements that
experiment. Word-reset cycles returned UNSAT; free choice needs a longer retry.
