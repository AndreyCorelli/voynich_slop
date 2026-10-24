# Natural H2: preceding context and partial holdouts

Seven matched comparisons retain every passage from the preceding natural Latin loop. Each compares the original 48 training words with the preceding 48 words prepended, for 96 training words. All comparisons, code seeds, coverage masks and budgets were frozen before new fitting.

## What stays fixed

The six continuation holdouts, generating key and ciphertext of the original 48 training words remain exactly fixed within each pair. The prefix is encrypted with a per-letter starting phase chosen so that its alternating homophone sequence reaches code 0 at the start of the existing passage. An independent backward-phase audit checks this alignment. Original words are neither duplicated nor rearranged.

This is an adaptive context check on already inspected passages. Longer contexts overlap other passages and several holdout words have been scored before. Its results are not independent fresh replications or a manuscript-language conclusion.

The fitted model is still free H<=2 with public boundaries and two-glyph codes. It uses all 6,327,182 forms in the broader finite policy inventory. The default inventory is audited separately. There are no word additions, numerical exceptions, removed training words, or relaxed per-letter capacities.

## Coverage and scoring

Missing training forms or structurally invalid prefix records prevent fitting that condition. A holdout with an unseen code is retained as `UNSEEN_CODE`; it is excluded from the exact-decoding denominator. Covered holdouts are scored using the **first returned key**. UNKNOWN and worker timeouts do not receive accuracy scores. Separate alternative-key checks cannot rescue first-key results.

The engine receives only covered holdouts for scoring, while the frozen protocol and report retain all six original holdouts and their coverage mask. Holdouts do not participate in training constraints. No code is changed to make a heldout word covered.

| Passage | 48-word training coverage | Covered holdouts, 48 words | 96-word training coverage | Covered holdouts, 96 words |
|---|---|---:|---|---:|
| 1 | complete | 6/6 | complete | 6/6 |
| 2 | complete | 6/6 | complete | 6/6 |
| 3 | complete | 5/6 | complete | 6/6 |
| 4 | missing uiiii, x | 6/6 | missing uiiii, x | 6/6 |
| 5 | missing atrebates | 6/6 | missing uiiii, x, atrebates | 6/6 |
| 6 | missing numerals and uiromanduis | 5/6 | additionally missing atrebates | 6/6 |
| 7 | complete | 5/6 | missing uiromanduis, xii, uii, boduognato | 6/6 |

Code coverage in this table is a pre-fit property, even for conditions that fail dictionary coverage. A missing-form condition is `NOT_ADMITTED`, not UNSAT. All fourteen conditions remain in the report. No case is replaced after its audit.

Seven conditions are admitted: four original contexts and three extended contexts. The original passage-1 and passage-2 records are reused byte for byte with frozen provenance; they are not rerun. Five new conditions get a positive fit, shuffled control and observed-key exclusion, for 15 new records plus six reused records. Each worker has a 60-second wall budget, with a 30-second Z3 budget inside it, including no implicit extensions or retries.

## Completed outcomes

| Passage/context | First training score | First covered-holdout score | Observed-key exclusion | Shuffled control |
|---|---:|---:|---|---|
| 1 / 48 (reused) | 48/48 | 6/6 | UNSAT | UNSAT |
| 1 / 96 | 96/96 | 6/6 | UNSAT | UNSAT |
| 2 / 48 (reused) | 48/48 | 6/6 | UNSAT | UNSAT |
| 2 / 96 | 96/96 | 6/6 | UNSAT | UNSAT |
| 3 / 48 | 48/48 | 5/5, one unseen | SAT alternative | UNSAT |
| 3 / 96 | 96/96 | 6/6 | UNSAT | UNSAT |
| 7 / 48 | 48/48 | 5/5, one unseen | SAT alternative | UNSAT |

All seven admitted conditions returned the exact generating key on observed codes. That does **not** imply uniqueness: the two shorter contexts with unseen holdouts also have valid alternatives. Passage 7's alternative maps `xt` from `x` to `g`, decoding `dixeram` as `digeram`. Its 96-word counterpart remains NOT_ADMITTED; no claim about resolving that ambiguity is available.

All 15 new records and six reused records validated. Twelve tests passed. New positive fits took about 10–17 seconds, mostly vocabulary filtering and propagation; Z3 took about 2–4 milliseconds. There were no solver UNKNOWN or worker timeouts. These scores include repeated holdouts and overlapping training contexts, so totals are not an independent accuracy estimate.

## Interpretation

For passage 3, the 48-word first key recovered 48/48 training words and 5/5 covered holdouts, leaving one holdout unevaluated. Its observed key was **not unique**: the returned alternative maps `xr` from `f` to `b`, decoding `defuerit` as `debuerit`, another dictionary form. The 96-word first fit recovered 96/96 training words and all 6/6 fixed holdouts; its observed-key exclusion was UNSAT. Both shuffled controls were UNSAT. More context therefore improves both heldout code coverage and observed-key identifiability in this matched case. Alternative-key diagnostics remain training-only.

Additional text can supply previously unseen homophones, but can also introduce absent vocabulary. Passage 3 is the clean matched test: the longer context covers its sixth holdout without changing the old ciphertext or dictionary. Passage 7 demonstrates the tradeoff: the longer context covers all holdout codes but fails training vocabulary coverage.

Missing names and numerals remain a separate vocabulary limitation. Longer timeouts cannot repair absent dictionary entries. Partial scoring allows us to assess the original passages 3 and 7 without pretending that an unseen code is either correctly or incorrectly decoded.

Next priority: random homophone selection on fresh natural prose, retaining full vocabulary audits and per-word code-coverage reporting. This tests the remaining cyclic generating assumption before returning to manuscript discrimination. It should be a separately frozen protocol, with no favorable key or heldout outcome selected afterwards.

## Artifacts and checks

- `benchmarks/latin_h2_natural_context.py`: frozen pairs, workers, first-key validation, partial scoring.
- `benchmarks/latin_h2_natural_context_analysis.py`: matched ciphertext, backward prefix phase, reused provenance and outcome comparison.
- `experiments/results/latin-h2-natural-context/prepared.json`: all fourteen conditions frozen before fitting.
- `report.json`, `validation.json`, `analysis.json` in the same result directory: results, checks and comparison.

```sh
.venv/bin/python -m benchmarks.latin_h2_natural_context --run
.venv/bin/python -m benchmarks.latin_h2_natural_context --validate
.venv/bin/python -m benchmarks.latin_h2_natural_context_analysis
.venv/bin/python -m pytest tests/integration/test_latin_h2_natural_context.py tests/integration/test_latin_h2_natural.py tests/integration/test_compressed_candidates.py -q
```

Validation regenerates coverage audits and code masks, checks stored first-key decoding, finite-inventory membership, capacity, phase completion and alternative-key provenance. Prefix alignment and absence of truth-based scoring rescue have dedicated tests. UNSAT uniqueness is restricted to observed codes under this bounded model and has no independently checked proof certificate.
