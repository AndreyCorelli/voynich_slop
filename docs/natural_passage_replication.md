# Natural passage replication

All eight new hidden-word positive fits are verified SAT, recover 24/24 training
words and predict 6/6 immediate held-out words correctly. All eight known-word
fits also succeed; all eight paired shuffles return UNSAT. No fits time out.
Hidden positive solver times are 0.889–1.123 seconds; shuffle times are
0.301–1.143 seconds under the unchanged five-second timeout.

| Passage | Source records, inclusive | Novel held-out words | Hidden exact, each profile |
|---|---|---:|---:|
| Caesar 1 | 10294–10323 | 6 | 6/6 |
| Caesar 2 | 10324–10353 | 6 | 6/6 |
| Swabian 123, 1 | 9134–9163 | 4 | 6/6 |
| Swabian 123, 2 | 9164–9193 | 3 | 6/6 |

Across both profiles, hidden keys predict 48/48 held-out occurrences and 38/38
novel occurrences correctly. Repeated training words are counted separately
from novel predictions. These are four additional texts reused across two key
profiles, not 48 independent observations.

Selection first reconstructs and excludes the original midpoint passage from
[natural-passage calibration](natural_passage_calibration.md). It then takes the
first eligible contiguous 24+6 block starting at or after that block's end, twice
per language, advancing to the end of each selected block. Every record must be
eligible and in the corrected source dictionary; barriers are not skipped within
a block. At least three distinct held-out types must be novel and every held-out
letter must appear in training. No solver result influences selection.
All sixteen inputs were frozen before the twenty-four fits.

The existing historical normalization, fixed-two and mixed-one-two-three profiles,
key seed 4501, typewise shuffle seed 4502, H1 L1–3 bounds, six ciphertext glyphs,
64-word dictionary and five-second budgets remain unchanged. Each dictionary
explicitly retains all true training and held-out words, then fills from original
corpus order under the passage alphabet. This is oracle-assisted calibration,
not blind language identification. Hidden recovery receives only the training
request, with no plaintext, lengths, key, profile constraint or continuation.
Known-word arms receive training plaintext only. Shuffles preserve word lengths,
per-word glyph counts and the full repetition partition; they are not assumed
impossible. Their UNSAT results are solver-reported without proof certificates.

Three integration tests pass, including selection barriers/nonoverlap and solver
input/resume isolation. Artifact validation reconstructs source blocks,
dictionaries and shuffles, independently checks SAT witnesses, and recomputes
frozen scores. Sources, code and request hashes are saved. Original results and
implementation remain unchanged.

```sh
.venv/bin/python -m benchmarks.natural_passage_replication --run
.venv/bin/python -m benchmarks.natural_passage_replication --validate
```

Artifacts: `experiments/results/natural-passage-replication/` contains the protocol,
prepared inputs, checkpointed report and validation. Completed arms skip on resume.

This replicates successful small-dictionary discrimination on additional natural
passages. Same-source passages and profiles remain correlated. The next useful
stress test is a frozen dictionary expansion on these unchanged inputs: prior
synthetic controls showed that larger dictionaries admit accidental fits and
incorrect first-key predictions. These results justify that calibration step,
not a Voynich language conclusion.
