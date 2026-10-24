# Natural passage dictionary expansion

All eight positives are verified SAT, recover 24/24 training words and predict
6/6 held-out words each: 48/48 total occurrences, including 38/38 novel
occurrences. Seven paired shuffles are UNSAT; one is UNKNOWN. At 64 words,
the same eight positives succeeded and all eight shuffles were UNSAT. No SAT
shuffle appears at 256 words, but the timed-out case prevents a claim that all
controls remain excluded.

| Case | Positive solver | Held-out exact | Shuffle |
|---|---:|---:|---|
| latin-1-fixed-two | 1.777 s | 6/6 | UNSAT, 1.255 s |
| latin-1-mixed-one-two-three | 1.630 s | 6/6 | UNSAT, 1.841 s |
| latin-2-fixed-two | 1.886 s | 6/6 | UNSAT, 1.814 s |
| latin-2-mixed-one-two-three | 1.870 s | 6/6 | UNSAT, 2.285 s |
| swabian-1-fixed-two | 4.943 s | 6/6 | UNKNOWN, 5.029 s |
| swabian-1-mixed-one-two-three | 2.468 s | 6/6 | UNSAT, 3.751 s |
| swabian-2-fixed-two | 2.400 s | 6/6 | UNSAT, 1.238 s |
| swabian-2-mixed-one-two-three | 1.577 s | 6/6 | UNSAT, 1.260 s |

Construction takes 0.943–1.532 seconds per fit. The unresolved case is
`swabian-1-fixed-two-shuffle`; its timeout is retained without extending the
budget. These natural assisted cases remain easier than earlier synthetic
256-word tests where accidental fits and wrong predictions appeared. This
does not establish performance on unrestricted vocabularies or Voynich.


This experiment enlarges the dictionaries of the four frozen
[natural replication passages](natural_passage_replication.md) from 64 to 256
words. Each original dictionary is retained in order, then extended with the
first distinct eligible words from its normalized corpus under the unchanged
passage alphabet. It uses all eight hidden positives and eight paired shuffles;
no new text, keys or controls are selected.

Only the dictionary field changes in each request. Training and held-out
ciphertexts, alphabets, H1 L1–3 bounds, free selection, flat observed encoding and
five-second solver timeout remain unchanged. Construction time is extra.
The existing 64-word hidden results are matched and preserved. Known-word fits
are not repeated because their solver inputs do not depend on the dictionary.
All sixteen expanded inputs were frozen before fitting, with no retries or
outcome-based additions. Completed fits checkpoint and skip on resume.

The vocabularies remain assisted: all true training and held-out words are
retained. Passage selection originally saw held-out plaintext to check novelty
and letter coverage. Positive SAT keys are scored once, frozen, for exact and
novel-exact continuation prediction. Shuffle keys receive dictionary-compatibility
scores only. UNKNOWN is unscored and unresolved; SAT compatibility does not prove
key identity; UNSAT is solver-reported without independent proof certificates.
Same-source passages and profiles remain correlated.

```sh
.venv/bin/python -m benchmarks.natural_vocabulary_expansion --run
.venv/bin/python -m benchmarks.natural_vocabulary_expansion --validate
```

Artifacts in `experiments/results/natural-vocabulary-expansion/` retain source/code
hashes, dictionaries and added-word provenance, paired baseline rows, public
requests, recovered witnesses and frozen scores. Validation reconstructs the
nested dictionaries, checks dictionary-only changes and baseline matching,
independently verifies generating/recovered witnesses and recomputes scoring.
Two integration tests check input isolation, nesting, resume, unscored UNKNOWN
handling and rejection of mismatched baseline results.
