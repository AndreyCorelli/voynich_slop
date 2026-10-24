# Independent Latin morphology coverage

Independent morphology closes much of the exact-form gap. The frozen Latin
passage goes from five uncovered training words to one under the upstream-default
analyzer combined with attested vocabulary, and zero under the broader frozen
setting. Two tests and six-row artifact validation pass; no Z3 runs.

| Recognition inventory | Missing training / 24 | Later blocks with ≤1 missing / 393 | Median missing |
|---|---:|---:|---:|
| Attested external-plus-prefix vocabulary | 5 | 22 (5.6%) | 4 |
| Same vocabulary, j/i and v/u equivalence only | 5 | 22 (5.6%) | 4 |
| Default morphology alone | 2 | 128 (32.6%) | 2 |
| Default morphology plus attested vocabulary | 1 | 268 (68.2%) | 1 |
| Broader morphology alone | 0 | 357 (90.8%) | 0 |
| Broader morphology plus attested vocabulary | 0 | 367 (93.4%) | 0 |

All six frozen held-out words are covered in every row. Default morphology alone
fails on `introrsus` and `hostes`; the existing attested vocabulary supplies
`hostes`, leaving only `introrsus` uncovered in the default combined row.
The broader setting recognizes both. Raw analyses, stems, endings, lexeme IDs,
features, properties and enclitic information are retained per query. Recognition
is not a claim of uniquely correct analysis or historical attestation.

Orthography equivalence alone changes neither frozen passage nor grid coverage,
so the improvement in this particular audit is not explained by u/v merging alone.
The morphology recognizer nevertheless uses that equivalence internally. The
same normalized cipher text and alphabet remain preserved; adopting equivalence
in a future finite dictionary requires an explicit spelling-generation policy.

## Resource and frozen settings

Use the Python implementation of
[Whitaker's Words](https://github.com/blagae/whitakers_words/tree/92eb56f188ec9dadecca01ca34d3c9fd13d746da),
pinned at commit `92eb56f188ec9dadecca01ca34d3c9fd13d746da`. Its unmodified source
archive, checksum manifest, package, MIT license and upstream README are retained.
Upstream data generation ran locally; no global install, extra runtime package,
hand-added target words or upstream code/data modifications were needed.

Two settings were frozen before recognition:

- `upstream-default`: the unmodified Parser defaults (age C, lexical frequency C,
  inflection frequency B).
- `through-medieval-rare`: `age='F', frequency='F'` (also sets inflection frequency
  F in this API). These are library thresholds, not a complete restriction of all
  lexical entries to a medieval date range; lexical age filtering is incomplete.

The resource documents limitations, including incomplete filtering and problematic
pronoun analyses. Built-in enclitic handling is allowed; prefix/suffix logic is
not fully implemented. It merges j/i and v/u. These behaviors are accepted as a
fixed sensitivity audit, not presented as authoritative validation of every
historical spelling. Broad settings can increase false recognition; that has not
yet been calibrated against randomized spellings.

## Coverage only, not a ready solver dictionary

The analyzer code/data is independent of the target corpus. Querying the 3,406
distinct types in the frozen passage/holdout and unchanged later-source grid does
not train it or add rules. Queries were frozen before recognition, with no tuning
or target-word reservation. All accepted and rejected analyses are checkpointed.
The earlier-source vocabulary is combined unchanged where specified.

This audit evaluates membership support. It does not enumerate a complete finite
inflected dictionary or establish its size, frequency ranking, solver construction
cost or public maximum word length. Consequently, the ≤1-missing block counts
are membership-coverage counts, not full model-admission or recovery rates. Adding
only recognized test words to a solver dictionary would reintroduce target-based
assistance. A future dictionary must instead enumerate forms independently from
all resource lemmas/rules before selecting test inputs.

The grid still contains 393 eligible blocks with 34 whole-block exclusions; the
same frozen passage can overlap grid blocks. Totals are correlated, with no
confidence intervals, manuscript inference or comparison against German.

```sh
.venv/bin/python -m benchmarks.latin_morphology_coverage --run
.venv/bin/python -m benchmarks.latin_morphology_coverage --validate
```

Artifacts: `experiments/results/latin-morphology-coverage/` contains pinned
identity/protocol, frozen queries/targets, per-query recognition evidence,
coverage report and validation. Raw archive provenance lives in
`data/raw/latin-morphology/`; source is in `data/vendor/whitakers-words/`.
Validation hashes raw/code/data, regenerates every recognition and reconstructs
orthography-only and membership comparisons. Tests check genuine/negative
recognition and occurrence counting with separate orthography effects.

Next, independently enumerate the morphology-backed spelling inventory and audit
its size/coverage before using it in Z3. Recognition of randomized controls should
also be measured: broader coverage must not be mistaken for stronger specificity.
