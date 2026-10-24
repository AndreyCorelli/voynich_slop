# Generating-key ranking capacity diagnostic

This retrospective diagnostic asks whether the frozen corpus-derived score can
recognize a useful key if recovery supplies it. Each saved coverage-controlled
positive's candidate pool contains all its returned SAT keys, followed by the
known generating key. No additional keys are recovered and no score is tuned.

Ranking uses only each candidate's recovered training plaintext and the unchanged
reference model. Labels, codebooks, continuation ciphertext and generating
continuation plaintext do not enter ranking. Ties retain the original order.
The ranking is frozen before evaluation. Injecting truth makes this a
**truth-assisted capacity check, not hidden-key recovery or blind validation**.

## Recorded result

| Positive | Candidate pool | Generating key rank | Generating score minus best recovered | Earlier selected exact words | Augmented selected exact words |
| --- | --- | --- | --- | --- | --- |
| Block 1, 20 training words | 2 recovered + truth | 2/3 | -0.028272 | 4/4 | 4/4 |
| Block 2, 16 training words | 3 recovered + truth | 1/4 | +0.287401 | 1/4 | 4/4 |

Both generating keys decode all four continuation words exactly. In block 1,
the best-scoring recovered key beats the generating score slightly, but both
returned keys already predict every continuation word correctly. Selecting a
predictively useful key is different from identifying the exact generating key.

In block 2, supplying the generating key changes the training-selected key and
raises exact continuation recovery from 1/4 to 4/4. The earlier capped candidate
set omitted an explanation the unchanged score would prefer. Thus **candidate
availability is the immediate bottleneck in this particular block**. This does
not show that longer recovery would find it or that sequence scores reliably
rank useful keys over all wrong alternatives. More wrong keys could outrank it.

The score fails to rank the true generating key first in block 1, so it is not
a consistent true-key identifier even across these two examples. The diagnostic
supports keeping training-only scoring as a possible selection aid; it does
not justify scaling solver budgets or claiming independent discrimination.
No scores, seeds or candidate counts were adjusted in response to the result.
The preceding block-1 third-key UNKNOWN remains unresolved; no rerun was made.

## Provenance and checks

Implementation: `benchmarks/generating_key_ranking.py`. Frozen protocol, source
and scoring-code hashes, complete seven-candidate pools, scores, ranks and
predictions are under `experiments/results/generating-key-ranking/`. Earlier
coverage and corpus-ranking artifacts remain unchanged. Existing output
prevents overwriting or rerunning this fixed diagnostic.

Seven focused tests pass, including independence of ranking from truth labels
and evaluation metadata, stable tie handling, unchanged candidate pools and
score reproduction. Separate validation independently verifies all seven
training fits and reproduces candidate selection and continuation predictions.
Zero solver calls; execution is under a second.

```sh
.venv/bin/python -m benchmarks.generating_key_ranking
.venv/bin/python -m pytest -q tests/integration/test_generating_key_ranking.py \
  tests/integration/test_corpus_sequence_selection.py \
  tests/integration/test_coverage_sequence_selection.py
PYTHONPATH=.:src .venv/bin/python experiments/results/generating-key-ranking/validate.py
```

## Implication for the next decision

Do not interpret this as a reason for an open-ended larger key search. If this
branch continues, test a fixed training-only proposal strategy against ordinary
solver order on fresh coverage-controlled positives and shuffles, with identical
total budgets. A reference score could guide proposals before fitting, rather
than only rerank whichever witnesses appear. This is a new experiment, and its
candidate generation must not use the generating key or continuation scores.
The broader cipher-model comparison remains open; no Voynich hypothesis has
been strengthened by this toy-scale calibration alone.
