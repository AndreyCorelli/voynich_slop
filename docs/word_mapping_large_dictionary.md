# Large dictionary and independent structural scoring

A 100,000-form candidate inventory and a plaintext-independent morphological sequence scorer are implemented and tested. This completes the preparation and objective-validation step; Caesar has not been cracked and no new blind search was run.

## Dictionary

`benchmarks/latin_large_dictionary.py` generates compatible stem/ending combinations through the pinned Whitaker matcher and includes unique forms. It retains part of speech, grammatical features, enclitics and a generating witness. Rule-generated forms are not necessarily historically attested. Spelling is canonical j→i/v→u.

The generator yields 1,412,284 distinct surfaces including parser-recognized forms attested in the frozen training split. Selection prioritizes training word frequency, then the resource's frequency class, with a SHA-256 tie-breaker. It selects exactly 100,000 unique forms without consulting development text for selection. Training and development are the unchanged widening experiment's disjoint book allocations.

| Inventory | Training token coverage | Development token coverage | Development type coverage |
|---|---:|---:|---:|
| Selected 100,000 | 97.38% | 86.78% | 61.96% |
| All generated in this runner | 97.38% | 96.26% | 90.37% |

The initial resource-frequency-only selection covered just 50.56% of development tokens. Common words were crowded out by generated inflections. Prioritizing disjoint training frequencies improves coverage, but missing proper names and inflections remain. These are exploratory development comparisons, not a final-test result. A deterministic 1,000-form sample of the final inventory round-trips through the parser with no unrecognized forms or missing generated signatures.

The workspace also already contains the broader independent inventory documented in [Latin form inventory](latin_form_inventory.md): 6,327,182 forms including a built-in enclitic layer. That inventory remains available; the new runner deliberately avoids materializing annotated entries for all six million forms. A future solver should keep a larger inventory available for escape proposals rather than treating the 100,000 selection as complete Latin.

Artifacts: `experiments/results/latin-large-dictionary/forms-100000.jsonl`, `all-surfaces.txt`, `report.json`, and `validation.json`.

## Independent scorer

`src/voynich_smt/structural_language.py` learns transitions between morphological signatures from the 39,346-word training split. Closed-class analyses retain word identity. Ambiguous words have uniform emissions over distinct signatures; a forward algorithm sums over consistent state paths. Training transition counts are fractional expected counts under uniform analyses, not a supervised parse or an EM-fitted grammar. Additive smoothing and unigram backoff are fixed before evaluation.

The scorer receives decoded surface sequences, not a plaintext key or oracle dictionary. The benchmark loads truth afterward to construct and evaluate controlled dictionaries. Equal full signature sets yield exactly equal scores regardless of content-word identity. Original segment boundaries remain intact, including local swap evaluations.

| Evaluation words | Broad broken-feature score delta / event | Changed-function-word delta / event | Original preferred over locally broken swaps |
|---:|---:|---:|---:|
| 503 | −0.379 | −0.594 | 82/100 |
| 2,022 | −0.301 | −0.765 | 76/100 |
| 8,024 | −0.303 | −0.816 | 75/100 |
| 16,021 | −0.360 | −0.842 | 77/100 |
| 32,004 | −0.462 | −0.876 | 90/100 |

Compatible dictionaries tie the perfect dictionary exactly at every width. Broad corruption controls score worse at every width. However, some locally incompatible swaps still score better: 10/100 at the largest width. They are retained in the report as explicit objective counterexamples. This is a statistical morphology proxy; it does not establish dependency structure, verb valency, grammaticality, meaning or successful decryption. Missing analyses share an explicit unknown state.

The scorer calibration uses cached training morphology, not the new inventory's analyses. This isolates objective behavior from candidate coverage. Search integration and efficient transactional scoring remain to be implemented; the present forward scorer is intended for calibration.

Artifacts: `experiments/results/word-mapping/structural-language-calibration/report.json` and `validation.json`.

## Validation and reproduction

Both new experiments replay deterministically to identical report hashes. Inventory validation checks exact size, unique canonical spellings, signatures and artifact hashes. The focused suite passes 158 tests, including an exhaustive latent-path calculation that independently checks the forward scorer.

```sh
.venv/bin/python -m benchmarks.latin_large_dictionary
.venv/bin/python -m benchmarks.word_mapping_structural_language
```

During implementation, an existing benchmark filename and report were accidentally reused. The original driver was recovered exactly from session history, and the original report was reconstructed and matched its downstream frozen digest. Its original compressed inventories were retained and fully validated. All new artifacts are isolated in the paths above.

## Implication for a whole-Caesar run

The experiment supports morphology-tolerant scoring and demonstrates that a large annotated inventory is practical. It does not establish a trustworthy optimization target. Before committing a long blind run, address the local misranking counterexamples, integrate the scorer with search, and freeze a whole-work benchmark with training outside that work. The current split trains on some Caesar books, so it cannot be reused unchanged for an experiment targeting all Caesar text. Preserve a held-out evaluation rather than training the language model on the target work.
