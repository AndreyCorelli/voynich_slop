# Missing training vocabulary calibration

Deleting just one predetermined training type makes all eight real-encryption
fixtures UNSAT. At two deletions, seven return UNSAT and one returns UNKNOWN.
All sixteen ablated shuffles return UNSAT. There are no SAT fits to score.
Two integration tests and 32-case artifact validation pass.

The two-deletion `swabian-1-fixed-two` timeout is preserved as raw UNKNOWN.
Its one-deletion counterpart is UNSAT and admits a strict superset of its
dictionary, with every other request field unchanged. Therefore the two-deletion
model is also excluded by monotonicity, conditional on that solver-reported
UNSAT. This separate implication is saved in `monotonicity.json`; it does not
replace the raw result or supply an independently checked proof certificate.

This is a sharp brittleness result: under these strict dictionary constraints,
one missing word can reject genuine encrypted natural text. UNSAT alone is
therefore unsafe as evidence against a language or cipher when vocabulary
coverage is uncertain. The next useful model change would allow a small,
explicitly bounded number of out-of-dictionary training words, calibrated on
these same cases and controls before returning to Voynich.

This experiment removes the first one and first two distinct true training word
types, in passage occurrence order, from the frozen training-seeded 256-word
dictionaries. It keeps all four passages, both key profiles and paired shuffles.
The deletion sets are nested and dictionaries shrink to 255/254 words without
replacement. No lengths, frequencies, held-out scores or solver outcomes select
the deletions. All 32 requests were frozen before fitting.

| Passage | First deleted type | Second deleted type | Training types |
|---|---|---|---:|
| Latin 1 | praeberent | quo | 22 |
| Latin 2 | nostri | castris | 22 |
| Swabian 1 | tag | lug | 22 |
| Swabian 2 | kennest | den | 21 |

Each removed type occurs once in its training passage. The ablation removes
approximately 4.5–4.8% or 9.1–9.5% of true training types. It is a fixed ordering
check, not a random sample of possible vocabulary omissions. Deleting one/two
entries rather than filling replacements keeps the intervention strictly nested;
it also reduces dictionary size by one/two words.

The generating keys still encode the ciphertext, but their true training words
are no longer all admitted by the dictionary. Thus the original explanation is
excluded by construction. Real-encryption fixtures are not guaranteed SAT under
these changed requests: UNSAT is allowed and means no alternative explanation
exists within the ablated model. A SAT answer must alter the missing word(s), so
full original training recovery is impossible. Any SAT key is frozen-scored on
the unchanged held-out text for exact and novel-exact accuracy, with dictionary
coverage recomputed after deletion. Controls receive compatibility scores only.

All other public fields remain unchanged: alphabets, H1 L1–3, free selection,
flat observed encoding and five-second solver budgets. Construction is extra.
The prior completed 256-word results are retained and hash-matched. No new
known-word solves, retries or timeout extensions are used. UNKNOWN is unresolved;
UNSAT is solver-reported without independently checked proof certificates.
Structural holdout selection, assistance for retained training types, and
same-source/profile correlations remain. No manuscript-language inference follows.

```sh
.venv/bin/python -m benchmarks.training_vocabulary_ablation --run
.venv/bin/python -m benchmarks.training_vocabulary_ablation --validate
```

Artifacts: `experiments/results/training-vocabulary-ablation/` saves the frozen
protocol, inputs, deletion words/counts, baseline rows, checkpointed results and
validation. Completed fits skip on resume. Validation reconstructs deletions,
checks generating-explanation exclusion and dictionary-only changes, verifies
SAT witnesses and recomputes frozen scores. Two tests cover nesting, exact public
input isolation, resume, permitted UNSAT/unscored handling and baseline rejection.
