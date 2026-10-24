# Random natural H2: 48 versus 96 training words

This adaptive check retains all seven random-choice passages from the preceding fresh-prose comparison. Each is audited at 48 training words and with 48 preceding words prepended. Every original training ciphertext word, generating key and all six heldout ciphertext words remain fixed. Added plaintext uses a separately seeded independent uniform random homophone stream; no balancing, word duplication or favorable code-choice search is introduced.

The full broader finite inventory remains unchanged at 6,327,182 forms. Missing training forms or invalid source records prevent fitting that condition. Added vocabulary failures are kept in the report. Holdouts with unseen codes remain individually unevaluated, with first-key exact decoding reported only on covered words. Alternative keys never replace the first key. All fourteen conditions were frozen before fitting.

## Coverage

Only passages 1 and 5 admit the 96-word extension. Passage 4 is admitted at 48 words, but its extension contains `xii`, absent from the inventory. Its earlier ambiguity therefore remains unresolved by this test. Passages 2, 3, 6 and 7 retain their earlier vocabulary failures; longer contexts do not cure them.

Passage 1 covers all six heldouts at either length. Passage 5 covers five at either length: additional random training choices do not guarantee that a rare homophone will be observed. No unseen code is counted as a wrong decoding or supplied from the generating key.

All three admitted 48-word records are reused byte for byte with frozen file digests. Two new 96-word conditions receive positive fitting, a shuffled control and observed-key exclusion: six new records plus nine reused records. Each task retains the 30-second solver and 60-second worker budgets, including preprocessing. All missing-form conditions are NOT_ADMITTED, not solver UNSAT.

## Completed result

| Passage / context | First training score | Covered-holdout score | Observed-key alternative | Shuffled control |
|---|---:|---:|---|---|
| 1 / 48 (reused) | 47/48 | 6/6 | SAT | UNSAT |
| 1 / 96 | 96/96 | 6/6 | UNSAT | UNSAT |
| 4 / 48 (reused) | 47/48 | 6/6 | SAT | UNSAT |
| 4 / 96 | NOT_ADMITTED | unevaluated | unevaluated | unevaluated |
| 5 / 48 (reused) | 48/48 | 5/5, one unseen | UNSAT | UNSAT |
| 5 / 96 | 96/96 | 5/5, one unseen | UNSAT | UNSAT |

The passage-1 extension removes the earlier `ferebantur` → `herebantur` error and makes its observed key unique. Both new extended fits recover the generating mapping exactly on observed codes; both shuffled controls and key exclusions are UNSAT. Passage 5's additional context preserves unique recovery but leaves its sixth holdout uncovered. The passage-4 ambiguity is still unresolved because its extended context fails vocabulary coverage.

All six new records and nine reused records validated. Fourteen tests passed. There were no worker timeouts or solver UNKNOWN results. These outcomes support a bounded context effect, not a claim that longer training always succeeds.

## Scope and next step

The comparison is adaptive, uses overlapping source context and repeats previously scored heldouts. It measures the effect of adding information to those cases; it is not independent replication. The model remains free H<=2, fixed two-glyph expansion and public boundaries. UNSAT exclusion establishes uniqueness only on observed codes within this model, without an independently checked proof certificate.

A successful context extension cannot establish manuscript-language evidence. Remaining limitations include proper-name/numeral dictionary coverage and unseen heldout codes. Before another solver branch, screen manuscript samples for compatibility with these public boundary and fixed-width assumptions, then choose a predeclared feasible discrimination experiment with matched controls. Increasing timeouts cannot distinguish verified alternative valid keys or add absent vocabulary.

## Commands and checks

```sh
.venv/bin/python -m benchmarks.latin_h2_random_context --run
.venv/bin/python -m benchmarks.latin_h2_random_context --validate
.venv/bin/python -m pytest tests/integration/test_latin_h2_random_context.py tests/integration/test_latin_h2_natural_random.py tests/integration/test_latin_h2_natural_context.py tests/integration/test_compressed_candidates.py -q
```

Protocol, per-task records, `report.json`, `comparison.json` and `validation.json` are under `experiments/results/latin-h2-random-context/`. Validation reconstructs coverage and matched inputs, checks first-key scores, membership, capacity, task phase completion, alternative-key provenance and byte-for-byte reused records. Tests independently reproduce added RNG choices and verify fixed original ciphertext and retention of the excluded numeral case.
