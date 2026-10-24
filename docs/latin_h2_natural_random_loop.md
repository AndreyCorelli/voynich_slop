# Natural Latin with random homophone selection

This loop freezes seven fresh Caesar 48-word training passages and six-word continuations after all prior tested passages. Each passage has a cyclic training arm and an independent uniform random training arm. The seven pairs are frozen before dictionary audits and fitting; failures are retained without replacement.

## Model and comparison

Both arms have identical plaintext, generating key, full finite dictionary and heldout ciphertext. The cyclic arm alternates the two codes of each letter in training. The random arm independently chooses between them at each occurrence with probability one half, without forced balance or requiring both homophones to appear. Holdout choices are independently random under **both** arms, using a separate fixed seed. This isolates training choice while also testing random selection end to end in the random arm; it is not a fully cyclic training-plus-holdout baseline.

Code counts may differ across arms. This is intentional: unlike the earlier balanced-random synthetic check, the random process is not conditioned on equal frequencies. The fitted model assumes neither balance nor cyclic selection. It has at most two observed codes per letter, public word boundaries, and fixed two-glyph codes. This tests expansion from one Latin letter to two ciphertext glyphs; it does not add contractions or variable-length codes.

The broader `through-medieval-rare` inventory retains all 6,327,182 generated forms and all word lengths. Both existing policies are audited after source selection. No target forms, names or numerals are added. Missing training forms gate the whole case; a heldout word with unseen codes is individually unevaluated. Scored holdouts use the first returned key, with no alternative-key rescoring.

Each admitted condition receives a positive fit, a pattern-preserving shuffled control, and a separate observed-key exclusion. Each worker is capped at 60 seconds, including construction, with a 30-second Z3 budget. UNKNOWN and worker timeouts remain unresolved. No prior result is reused.

## Frozen coverage audit

All blocks are contiguous; record ends below are exclusive. Selection requires structural eligibility, heldout letter coverage and at least three novel heldout types, not inventory membership.

| Passage | Source records | Broader missing training forms | Covered holdouts: cyclic / random | Fitted? |
|---|---|---|---:|---|
| 1 | 11025–11079 | none | 6 / 6 | both |
| 2 | 11079–11133 | tunditores, numidas | 4 / 4 | neither |
| 3 | 11133–11187 | prolectus, xii | 6 / 6 | neither |
| 4 | 11187–11241 | none | 6 / 6 | both |
| 5 | 11241–11295 | none | 6 / 5 | both |
| 6 | 11295–11349 | uii | 6 / 5 | neither |
| 7 | 11349–11403 | labienus, x | 6 / 6 | neither |

Four of seven passages fail training vocabulary coverage. These are NOT_ADMITTED, not cipher-model UNSAT. The six admitted conditions produce 18 new fit/exclusion records. Coverage counts for excluded conditions are descriptive properties of their generated ciphertext, not accuracy scores.

## Completed outcomes

| Passage / training choice | First training score | First covered-holdout score | First observed key exact? | Observed-key alternative |
|---|---:|---:|---|---|
| 1 / cyclic | 48/48 | 6/6 | yes | UNSAT |
| 1 / random | 47/48 | 6/6 | no | SAT |
| 4 / cyclic | 45/48 | 5/6 | no | SAT |
| 4 / random | 47/48 | 6/6 | no | SAT |
| 5 / cyclic | 48/48 | 6/6 | yes | UNSAT |
| 5 / random | 48/48 | 5/5, one unseen | yes | UNSAT |

All six fits were verified SAT, and all six shuffled controls were UNSAT. No worker timeout or solver UNKNOWN occurred. All 18 new records and independent source/RNG audits validated; twelve tests passed.

Random training recovers 17/17 covered holdout occurrences, with one other holdout unevaluated. These are conditional scores, not 18/18 recovery and not full-key recovery. Only one of the three random first keys is exact and unique on observed codes. Cyclic training recovers 17/18 holdouts, with two of three first observed keys exact and unique. This small paired batch does not establish that either choice policy is superior.

The random first key in passage 1 maps one `f` code to `h`, yielding `herebantur` instead of `ferebantur`. In passage 4 it maps one `h` code to `p`, yielding `postes` instead of `hostes`. The cyclic passage-4 first key exchanges two code assignments, producing `nexue` for `neque` twice and `eq` for `ex`. All these wrong training explanations satisfy the full finite dictionary and H2 constraints. The known generating key verifies a different valid explanation in these three cases; it does **not** replace the scored first key. Alternative-key diagnostics use training words only.

## Interpretation and next priority

This check removes forced balance and the alternating generating rule from one arm on actual prose. It preserves sparse-letter and unused-homophone effects rather than hiding them through duplicate words or favorable code choices. Any successful results remain conditional on dictionary admission, code coverage, public boundaries and fixed-width expansion. Paired holdout scores repeat the same words; the two arms are not independent new samples.

The immediate limitation is observed-key identifiability, rather than solver timeout. Next, measure whether a predeclared longer training context resolves the random-arm ambiguities, preserving the six heldout ciphertext words and reporting added vocabulary failures. Earlier cyclic-context results motivate this check, but do not establish it for random choices. Keep every failed admission and do not add known target forms. Increasing solve budgets cannot distinguish already verified valid explanations. Finite policy vocabulary is not all historical Latin, and this batch does not support a manuscript-language conclusion.

## Artifacts and validation

- `benchmarks/latin_h2_natural_random.py`: frozen protocol, independent RNG streams, workers and paired validation.
- `benchmarks/latin_h2_natural_random_analysis.py`: independent source and RNG audit, outcome comparison, training-only ambiguity diagnostics.
- `experiments/results/latin-h2-natural-random/prepared.json`: seven fresh pairs and both complete coverage audits.
- `report.json`, `comparison.json`, `validation.json`, `analysis.json` in the result directory: outcomes and provenance.

```sh
.venv/bin/python -m benchmarks.latin_h2_natural_random --run
.venv/bin/python -m benchmarks.latin_h2_natural_random --validate
.venv/bin/python -m benchmarks.latin_h2_natural_random_analysis
.venv/bin/python -m pytest tests/integration/test_latin_h2_natural_random.py tests/integration/test_latin_h2_natural_context.py tests/integration/test_compressed_candidates.py -q
```

Validation checks candidate membership, capacity, first-key decoding, individual holdout coverage, result provenance and phase completion. Source selection, missing forms, RNG streams and paired inputs are independently reconstructed. Tests distinguish independent random choice from forced balancing and verify that unseen codes receive no accuracy score. Observed-key UNSAT exclusion is a bounded solver result without an independently checked proof certificate.
