# Bounded neural archive reranking

The full-segment Latin RoBERTa scorer changed which dictionary was selected in
13 of 16 development archives, but exact token recovery did not change in any
archive. Mean accuracy stayed at **2.42%**. This bounds what reranking this
shortlist can achieve: every candidate in each five-entry shortlist had the same
exact token accuracy. Even a truth-aware oracle could not improve it.

## Protocol

The frozen parent is `experiments/results/word-mapping/long-context-calibration`.
For each of bundle-1, bundle-2, bundle-3 and pooled, use the injective and trigram
one-to-one searches, seeds 11 and 22, budget 50,000, original development input.
Select the top five archive entries by their existing n-gram ranking. This gives
16 archives and 80 dictionaries. No new optimization occurs.

Score all development segments using full-segment context and the same pinned
local model as [the neural counterexample probe](word_mapping_neural_probe.md).
Select the greatest `word_normalized_log_sum` (mean subword log score per word,
then summed over words), breaking ties by original archive rank. Truth is loaded
only after selection to calculate recovery. Model files, source archives,
rendered candidates, code, package versions and protocol are frozen by hashes.
Resume rejects protocol changes; validation independently recomputes all scores
and reconstructs recovery and the report.

Run and validate offline:

```sh
.venv/bin/python -m benchmarks.word_mapping_neural_rerank
.venv/bin/python -m benchmarks.word_mapping_neural_rerank --validate
```

Outputs are under `experiments/results/word-mapping/neural-rerank/`. The run
recorded about 44.4 seconds in scoring calls and 10,966 actual masked-word
forward examples. Cached identical segments account for much of the savings;
these numbers exclude model loading, archive preparation and validation.
The scorer cache is cleared after each archive to bound memory.

## Findings and limits

| Measure | Result |
| --- | ---: |
| Dictionaries scored | 80 |
| Archives | 16 |
| Changed selected dictionary | 13 |
| Improved / worsened / unchanged recovery | 0 / 0 / 16 |
| Mean exact token accuracy before | 2.4194% |
| Mean exact token accuracy after | 2.4194% |
| Archives with a better five-entry oracle candidate | 0 |

An additional evaluation-only inspection of all 30 entries in each source
archive is saved in `full-archive-oracle.json`. Only pooled/trigram/seed-22 has a
candidate exceeding its original winner: 4.3001% versus 4.2086%. Fifteen of the
sixteen full archives offer no improvement at all. This diagnostic did not
change the frozen shortlist or neural selection.

The next experiment should improve candidate diversity, such as retaining
solutions across separate restarts or using bounded neural-guided proposals.
Simply expanding this shortlist or running the same n-gram search longer is
unlikely to address the poor candidates. The counterexample probe's ability to
rank many near-truth mappings does not establish recovery from these bad
initializations.

These are selected same-author development bundles, and pooled overlaps the
others. Pretrained Caesar exposure remains unknown. The final test is unscored.
All 80 dictionary scores were independently recomputed and validated. All 111
focused tests pass. The neural scoring and reranking checks include metric selection, stable ties,
budget validation, synthetic recovery improvement, resume, protocol rejection
and tamper detection.
