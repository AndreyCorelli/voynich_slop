# Independently generated Latin form inventories

The complete finite inventories under the two pinned implementation settings are
generated without consulting target words:

| Settings | Canonical forms | Compressed artifact | Maximum length | Frozen training misses | Grid ≤1 missing, inventory only |
|---|---:|---:|---:|---:|---:|
| Upstream defaults | 2,550,580 | 6.10 MB | 27 | 2/24 | 128/393 |
| Through-medieval/rare sensitivity | 6,327,182 | 15.13 MB | 30 | 0/24 | 357/393 |

Generation and initial checks take approximately 12 and 30 seconds respectively
on this run. These are inventory/check wall times, not solver budgets. No Z3 fits
are performed. Two tests and full-regeneration artifact validation pass.

Combined with the unchanged, canonicalized attested inventory, default coverage
leaves only `introrsus` unknown in the frozen training passage and reaches
268/393 grid blocks with at most one missing occurrence. The broader combination
covers the whole passage and reaches 367/393. Every frozen held-out word is covered.
These agree with the prior recognition audit, but the vocabulary now exists as
an independently enumerated artifact rather than target-query acceptances.

## Enumeration policy

All pinned filtered stems are combined with compatible filtered endings through
the upstream `Matcher`, including its stem-number, declension/conjugation,
gender and special-verb rules. Empty-ending forms follow the upstream word-key
and part-of-speech checks. Unique forms are included. Add one built-in enclitic
layer using the same branch/position rules as the parser, including the upstream
behavior for unique analyses. Stemless words and endings that would consume the
whole query are excluded, matching the recognizer's lookup behavior. No recursive
enclitics, unsupported derivational prefixes/suffixes, target additions, ranking,
size cap or hand-edited spelling variants are introduced.

The output spelling is the resource's canonical j→i and v→u convention. It does
not preserve the original u/v distinction in the cipher experiments. Cipher text
and earlier dictionaries are not altered. A future solver using these forms must
explicitly adopt a normalization model or independently enumerate spelling
variants; adding observed spellings afterward would reintroduce assistance.

Each form is generated entirely from the independent resource. Target types
enter only subsequent equivalence and coverage audits. Generation uses no target
list, corpus frequencies, holdout scores or generating cipher keys. Protocol and
source identity are frozen before generation. Completed mode artifacts checkpoint
and skip on resume. Inventories are lexically sorted newline files, gzip-compressed
with a fixed timestamp; compressed and uncompressed SHA-256 hashes are retained.

## Verification and limits

Validation independently regenerates each entire set and compares it with its
saved inventory, checks hashes, and reconstructs coverage. Membership agrees with
the pinned recognizer for all 3,406 previously frozen query types. A deterministic
lexically spaced sample of 1,024 generated forms per mode is also recognized by
that parser. These checks use the same upstream implementation; they are not an
independent linguistic gold standard or exhaustive recognition of every generated
form. Tests separately exercise compatibility filters, enclitic position rules,
canonical spelling and occurrence-based coverage.

"Complete" refers to this pinned finite enumeration policy, not every historical
Latin spelling. The resource's incomplete filtering and known analysis issues
remain. Its matching rules can license theoretical or overly broad forms;
generated forms are not claimed to be attested words. Millions of accepted forms
may increase accidental fits and destroy the useful constraint of a small
vocabulary. Randomized-spelling recognition has not yet been calibrated. Coverage
alone cannot establish reliable recovery or a manuscript language.

The inventory is much larger than the earlier 256-word models. Feeding millions
of entries into the flat dictionary solver is not an appropriate immediate next
run. A compact morphology/lexicon encoding and performance calibration, or a
separately frozen reduction justified from public inputs, is needed before any
positive/control recovery experiment. Do not retain only recognized test words.

```sh
.venv/bin/python -m benchmarks.latin_form_inventory --run
.venv/bin/python -m benchmarks.latin_form_inventory --validate
```

Artifacts in `experiments/results/latin-form-inventory/` include protocol/source
identity, `upstream-default.txt.gz`, `through-medieval-rare.txt.gz`, counts,
coverage/equivalence audits and validation. The upstream resource, options and
license are described in [Latin morphology coverage](latin_morphology_coverage.md).
