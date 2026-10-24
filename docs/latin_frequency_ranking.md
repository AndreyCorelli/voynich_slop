# External Latin word-frequency ranking

This bounded retrospective pilot ranks 17 existing recovered keys using only
training plaintext and an external Latin unigram prior. It asks whether word
frequency changes candidate selection or improves frozen-key continuation
recovery relative to first returned key and the earlier sequence score.

The reference is the first half of cached Caesar (all nonempty tokens, without
the twelve-word projection); evaluation passages come from the second half.
Each word contributes its add-one smoothed log probability, including unseen
forms. Scores are averaged over every training word, with stable first-key ties.
No top-four requirement, stopword removal, generating-key injection, holdout
selection, additional solver search or score tuning is used. Repeated decoded
words naturally contribute their combined occurrence count. This pilot has no
contraction tokens; it does not validate expansion handling for macro encoders.

## Results

| Saved experiment | Positive candidate keys | First-key exact holdout | Frequency-ranked exact holdout | Earlier sequence-ranked exact holdout |
| --- | ---: | ---: | ---: | ---: |
| Earlier projected Latin | 6 | 0/8 | 0/8 | 0/8 |
| Coverage-controlled projected Latin | 5 | 5/8 | 5/8 | 5/8 |

The six shuffled-control candidate keys likewise select the same indices as the
earlier sequence ranking. Their selected keys yield zero dictionary hits on
both four-word continuations (fully decoded words: zero and two). The two
coverage-control shuffles supplied no SAT candidate, so they are explicitly
not evaluated, rather than counted as successful negative classifications.

All six nonempty candidate pools select the same key as the earlier sequence
score. Frequency ranking changes selection relative to the first returned key
in three earlier pools, but does not improve held-out dictionary or exact-word
recovery. Earlier positives have generating-code coverage gaps, so their zero
recovery is not a clean test of ranking discrimination. Coverage-controlled
positives are more informative, but comprise only two tiny projected passages.
Their three-key pool in block 2 contains no candidate exceeding one exact
continuation word; reranking cannot create an absent useful key.

This shows **no added benefit in these saved pools**, not that word-frequency
priors are ineffective generally. The vocabulary was itself selected for common
short reference words. Same-author projection, short training windows, biased
solver-returned pools and absent fits restrict any inference. It is not a
manuscript, intact-prose, contraction-model or independent-author test.

## Reproduction and next decision

Implementation: `benchmarks/latin_frequency_ranking.py`. Frozen reference counts,
source/input/code hashes, complete scores, selections and continuation outcomes
are under `experiments/results/latin-frequency-ranking/`. Existing output is
protected against overwrite. Two focused tests check unknown-word penalties,
frequency aggregation, tie handling and independence from truth/holdout metadata.
Independent validation recomputes all 17 scores and selections, verifies all
training fits and reproduces positive continuation evaluations. Zero solver calls.

```sh
.venv/bin/python -m pytest -q tests/integration/test_latin_frequency_ranking.py
PYTHONPATH=.:src .venv/bin/python experiments/results/latin-frequency-ranking/validate.py
```

Keep frequency as a soft auxiliary score. Before expanding its role, the useful
next calibration would freeze this rule on fresh coverage-controlled passages
with longer held-out text and a candidate pool containing useful alternatives.
Do not impose hard est/et/in/quod anchors or increase solver time on the strength
of this result.
