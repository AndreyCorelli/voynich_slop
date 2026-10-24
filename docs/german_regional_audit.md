# Audit of the other three surviving German vocabularies

The corrected full-block tests have completed. **Swabian and Alsatian are
independently verified SAT on all 30 words; Ripuarian is UNSAT.** The surviving
fits no longer use the rejected fragments or letter-mention entries.

| Corrected source | Result | Solver seconds | Mean plaintext word length | One-letter uses |
|---|---|---:|---:|---|
| 123, Swabian | Verified SAT | 1,374.32 | 2.43 | `a` at positions 20 and 23 |
| 153, Ripuarian | UNSAT | 165.94 | — | — |
| 233, Alsatian | Verified SAT | 1,546.90 | 2.23 | `e` at positions 20 and 23 |

The [long validation](../experiments/results/german-regional-audit/long-validation.json)
checks exact ciphertext, fixed cipher settings, corrected vocabulary and input
hashes, dictionary membership, key bounds, prefix-freeness and exact encoding
and decoding for both SAT witnesses. Full recovered plaintexts are saved there.
Ripuarian UNSAT remains solver-reported without independent proof checking.
These results show that compatibility survives the corrections for two
vocabularies, but do not establish grammatical prose or manuscript language.

All three original 19-word SAT witnesses use short entries rejected by the
corrected variants. Two sources contain definite delimiter-handling errors;
the third relies on letter mentions and an unresolved marked form. This
does not invalidate the old mathematical SAT certificates for the old
dictionaries. It limits their interpretation as ordinary German word fits.

| Source | Evidence in old witness | Corrected vocabulary | Retained one-letter forms |
|---|---|---:|---|
| 123, Swabian | `t/u` came from one source form `[T]U`, annotated as an imperative of `tun` | 3,181 | `a`, `o` |
| 153, Ripuarian | `h` names an alphabet letter; `u` comes only from marked `ú`, expansion unresolved | 2,616 | `a`, `o` |
| 233, Alsatian | `r` came from uncertain `a[?]r`; isolated `d` has unresolved lexical interpretation | 3,133 | `e`, `o` |

Witness positions in the machine-readable audit refer to the recovered
19-word subset, not the full manuscript block or the restored 30-word text.

## Corrections and sensitivity decisions

The original normalizer treated brackets as word delimiters. `[T]U` became
two artificial dictionary entries, `t` and `u`, rather than `tu`. Similarly,
`a[?]r` became `a` and `r`, despite the source annotating the whole form as a
noun with lemma `ohr`. These are concrete normalization errors.

The separately versioned policy rejoins clearly marked initial letters to
the following word (`[T]U` → `tu`, `[D]As` → `das`). It quarantines entire
uncertain/question-marked, asterisk-marked or other unresolved bracketed
forms. It does not guess missing letters or expand unknown abbreviations.
In these sources the reconstructed complete initial-marked words already
exist in the original vocabularies, so no dictionary words are added.

Additional explicit lexical sensitivity exclusions are evidence-based but
not transcription-error claims:

- Source 153: `b` is a folio-side designation; `h/k/q/x/y/z` occur as alphabet
  letter mentions. Isolated `u` comes from `ú` with unestablished expansion.
  The uncertain `v[?]` occurrence is quarantined by the general rule.
- Source 233: `d` is an isolated unresolved form, `q` follows a quantity and
  appears to be unit notation, and `V/v` have unresolved standalone meanings.
  These are excluded without inventing expansions.
- Source 123: no additional lexical exclusions are imposed; its rejected
  one-letter fragments disappear through the bracket correction.

Context-supported forms remain: Swabian `a/o` occur in interjection-like
contexts; Ripuarian `a` includes a Latin phrase and `o` interjections;
Alsatian `e` appears repeatedly in temporal contexts and `o` interjections.
This is a conservative sensitivity vocabulary, not a complete certified
inventory of ordinary German words. Latin material, rare spellings and
unresolved forms elsewhere may still require linguistic review.

The old length-analysis tokenizer also separates brackets. Earlier German
length-distribution artifacts retain that legacy handling and have not been
recomputed as part of this audit. The quantitative effect has not been measured.

## Prepared full-block tests

The audit traces every witness form of at most three letters and every
one-letter vocabulary entry to raw XML, including occurrence counts, word
numbers, line contexts, annotations and grouped morphs. Its traversal
reproduces the original complete vocabulary frequencies before correction.
Source XML hashes are checked against their manifests.

Corrected vocabularies and inputs have their own paths and version metadata;
original raw data, requests and results remain intact. All three variants
use the full original 30-word contiguous block. Original per-source plaintext
alphabets and every cipher setting remain fixed. No key or plaintext hints
are supplied. The subsequent user-run solves produced the results above;
rejecting an old witness alone did not establish that replacement fits were
impossible.

Artifacts:

- [Audit/preparation report](../experiments/results/german-regional-audit/budget-30000ms.json).
- [30-minute input preparation](../experiments/results/german-regional-audit/budget-1800000ms.json).
- [Validation](../experiments/results/german-regional-audit/validation.json).
- Separate v2 vocabularies under `data/generated/german-regional-audit/vocabularies/`.

Run the prepared three-source batch locally:

```sh
.venv/bin/python -m benchmarks.german_regional_audit \
  --timeout-ms 1800000 --solve --resume
```

Each source gets up to 30 minutes plus formula construction. Results are
saved after each solve, SAT witnesses independently verified, and UNKNOWN
remains unresolved. The batch continues across sources and skips completed
rows on resume. The longer batch has completed; its resume command now
returns without rerunning solved rows.

Default execution audits and prepares without Z3. The focused suite passed
29 tests covering marked initials, whole-form uncertainty quarantine,
editorial exclusion, genuine short forms, real source evidence, original
alphabet/cipher preservation and preparation without solving.
