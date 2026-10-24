# Broader external vocabulary coverage

Broader attested vocabulary improves coverage across the eligible later-source
grid but still excludes both frozen generating explanations. No Z3 runs or new
downloads are needed. Two tests and 20-row artifact validation pass.

| Full inventory | Latin types | Latin missing / 24 | Swabian types | Swabian missing / 24 |
|---|---:|---:|---:|---:|
| Earlier test-source portion only (prior audit) | 3,442 | 6 | 1,962 | 4 |
| External sources only | 19,732 | 7 | 15,106 | 5 |
| External plus earlier test-source portion | 21,576 | 5 | 16,129 | 4 |

Neither frozen passage is admitted by the one-unknown-occurrence model, even at
full external-plus-prefix size. The Latin remaining absent spellings are
`silvestris`, `introrsus`, `perspici`, `continebant`, `stationes`; Swabian spellings
are `zebelyben`, `widerkomen`, `ruowet`, `belybt`. These are exact-form inventory
observations, not claims about their historical legitimacy or proposed corrections.

## Grid coverage

The unchanged audit grid has 393 eligible Latin and 207 eligible Swabian
24-word blocks. Its eligibility exclusions remain in place (34 Latin and 169
Swabian blocks rejected), limiting population generalization.

| Full inventory | Latin admitted ≤1 unknown | Swabian admitted ≤1 unknown |
|---|---:|---:|
| Earlier test-source portion only | 5/393 (1.3%) | 11/207 (5.3%) |
| External only | 0/393 | 14/207 (6.8%) |
| External plus earlier portion | 22/393 (5.6%) | 53/207 (25.6%) |

The full combined inventories reduce median missing occurrences from seven to
four for Latin and five to three for Swabian. This is useful improvement, but
most later blocks still cannot admit the true explanation under one unknown
occurrence. External vocabulary alone is not uniformly better than the earlier
same-source vocabulary, despite its larger size.

All rankings are by source frequency with lexical ties. Requested sizes
1,024/2,048/4,096/8,192 and full inventory were fixed before coverage scoring.
For the frozen passages the combined Latin dictionaries miss 11/9/8/8 words at
those finite sizes; combined Swabian misses 7/5/5/5. The 8,192-word combined
inventories admit 1/393 Latin and 28/207 Swabian grid blocks. Larger vocabulary
also increases solver ambiguity and construction costs; no claim about successful
cipher recovery follows from these coverage counts.

## Independent source construction

Use every already-cached work in `expanded_medieval_latin.WORKS`: Einhard,
Gesta Francorum, Bury and Dante, plus cached Aquinas and Caroli prose extraction.
Caesar is excluded from the external inventory. Existing body/footer extraction
and lexical normalization are retained; j maps to i to match the fixed Caesar
alphabet, while u/v remain distinct. Forms outside the alphabet are excluded and
recorded. No morphological generation, target-word additions or new normalization
sensitivity is introduced.

For German, use cached XML sources 113,133,143,153,223,233,243,253, excluding
Swabian test source 123 entirely. Use existing corrected normalization and known
source-specific exclusions. Pooling regional spellings does not claim that all
forms belong to the test dialect. Other editorial contamination may remain;
these are extracted edited-source inventories, not authoritative full lexicons.

External-only and external-plus-earlier-prefix variants are both frozen. The
combined inventory adds only the already-defined first-half vocabulary; no
later test-source records are used. Raw manifest checksums, XML hashes, extraction
quality, normalization events and per-source word counts are retained. Targets,
alphabets and grid blocks remain unchanged from the prior audit. Source selection
uses the cached catalog, not target misses or solver outcomes. Same-source and
profile correlations remain; this is not a matched language comparison.

```sh
.venv/bin/python -m benchmarks.external_vocabulary_coverage --run
.venv/bin/python -m benchmarks.external_vocabulary_coverage --validate
```

Artifacts: `experiments/results/external-vocabulary-coverage/` contains protocol,
source/code identity, word-count provenance, rankings, frozen targets/grid,
coverage reports and validation. Validation rebuilds extraction/rankings, verifies
target-source exclusion, matches unchanged targets and recomputes coverage.
Tests check fixed normalization/frequency ties, unavailable handling and JSON
roundtrip stability.

Coverage is still the practical obstacle. A separately specified morphology or
orthographic-variant inventory would be a different experiment and should be
frozen and audited before solving. Simply adding the observed missing spellings
would restore target assistance. No manuscript-language conclusion follows.
