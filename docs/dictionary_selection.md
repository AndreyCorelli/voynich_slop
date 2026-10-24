# Dictionary-entry selection experiment

The optional `dictionary_encoding="entry"` formula gives each observed word a
bounded integer selector over its publicly pruned vocabulary candidates. Balanced
lookup trees derive its plaintext length and every token from that selector,
including sentinel padding after the selected word ends. Constant lookup branches
collapse. The selected entry drives the existing codebook, segmentation and
homophone-cycle constraints; these remain symbolic and retain the H2/L3 model.

This changes the search formula, not the accepted language or cipher. The default
membership formula is unchanged. The entry option supports null-free feasibility;
null and optimization solving continue to use the flat formula. The public input
contains no truth hints or key restrictions.

Tests project the entry selector out and prove exact equivalence to flat
membership, including empty candidate sets, padded positions and out-of-range
selectors. Small hidden recovery instances compare entry and trie SAT/UNSAT
outcomes; every SAT result still passes independent witness verification.

The experiment reuses the exact seed-7 state-cycle public controls saved by the
cycle-performance benchmark: 32, 256 and 5,665 vocabulary entries. The reduced
vocabularies are declared easier controls containing the generated words and
sampled distractors. Full-vocabulary recovery uses the original complete public
request. Every input is hash-checked; the only paired change is membership
encoding. Both use a 30-second solver budget. The entry formula receives an
additional 120-second full-vocabulary retry if its 30-second attempt is UNKNOWN.
Construction time is outside the solver budget and included in total wall time.

The user's saved 30-minute trie/state result is linked by hash only after checking
that its public request matches the full control except for timeout. Its UNKNOWN
result is a known-positive solver diagnostic, not evidence against Latin or the
cipher model. A single run per case does not establish a general speedup.

```sh
.venv/bin/python -m benchmarks.dictionary_selection
.venv/bin/python -m benchmarks.cycle_performance --replay data/generated/dictionary-selection/inputs/seed-7-vocab-32-entry-ms30000.json
```

Configuration: `experiments/configs/dictionary-selection.json`. Report:
`experiments/results/dictionary-selection.json`. Replay wrappers use the existing
cycle-performance runner, including `--timeout-ms` and `--replay-output` for
user-initiated longer runs. This milestone runs positive controls; it does not
launch a 30-minute solve or another manuscript solve.

## Recorded comparison

| Vocabulary | Trie/state baseline | Entry/state | Entry solver time | Entry total time |
|---|---|---|---:|---:|
| 32 | SAT (2.04s solver) | SAT | 2.26s | 3.35s |
| 256 | SAT (24.27s solver) | UNKNOWN | 30.10s | 32.02s |
| 5,665 | UNKNOWN (30.15s solver) | UNKNOWN | 30.38s | 43.31s |
| 5,665 | UNKNOWN (30.15s solver) | UNKNOWN | 120.72s | 133.62s |

Entry selection recovered the 32-word control, but timed out at 256 entries
where trie/state recovered a verified fit within 30 seconds. Both full-vocabulary
entry runs returned UNKNOWN, including the 120-second retry. The saved 1,800-second
trie/state baseline also returned UNKNOWN. These results do not demonstrate an
improvement; the new formula remains optional and the default stays unchanged.
All 358 tests pass. No manuscript or 30-minute solve was launched in this milestone.
