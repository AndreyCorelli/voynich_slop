# Synthetic recovery calibration and H2 cycle performance

H2 cycles now use a Boolean phase per plaintext letter. It starts false and toggles
only on an active occurrence of that letter. A two-homophone letter chooses the
current phase; a one-homophone letter always chooses zero. Word-reset selection
clears the phase at each word boundary. Inactive dictionary padding never toggles
any phase. The previous formula summed every earlier symbolic letter position and
took that sum modulo the homophone count.

Both formulas express the same cipher. The new formula shares intermediate phases,
reducing repeated construction of symbolic history sums. It becomes the default
for null-free H2 cyclic recovery; other homophone bounds and free selection retain
the history formula. The separate bounded/null/optimization solver is unchanged.
The private `cycle_encoding` option supports explicit paired experiments without
adding hidden-key fields to the public recovery request.

Tests prove the recurrence agrees with the history sum for symbolic counts,
active positions and inactive padding. End-to-end tests compare SAT/UNSAT results
for small hidden instances under both text and word resets. Returned SAT witnesses
still require independent Python verification of key, dictionary, ciphertext,
segmentation and homophone choices.

The benchmark uses the exact saved 11-word positive controls for seeds 7, 17 and
1729. All contain length-three codes, use the full 24-letter alphabet and follow
the same H2/text-wide-cycle model as the manuscript experiment. Truth is used to
validate generation, never to supply key, plaintext order, phases or segmentation
to hidden recovery.

For seed 7, paired history/state runs also use 32- and 256-entry vocabularies.
These are explicitly easier controls: a deterministic sample of distractors plus
the generated words. Their success cannot substitute for full-vocabulary recovery.
Both full-vocabulary seed-7 probes use the same trie request and 30-second budget;
request hashes govern reuse of their saved results. Seeds 17 and 1729 use the new
formula with the unchanged full vocabulary and the same budget.

The final manuscript check uses all original 23 words, H2/L3, all 5,665 vocabulary
entries, trie membership and a 120-second solver budget. No pins, truth hints or
learned exclusions enter that check. Its scope matches the earlier unrestricted
trie result; UNKNOWN cannot reject the cipher or Latin hypothesis.

```sh
.venv/bin/python -m benchmarks.cycle_performance
.venv/bin/python -m benchmarks.cycle_performance --replay data/generated/cycle-performance/inputs/seed-7-vocab-5665-state.json
```

Configuration: `experiments/configs/cycle-performance.json`. Report:
`experiments/results/cycle-performance.json`. Public wrappers contain only a
request and the choice of equivalent cycle formula. Truth remains in the original
synthetic truth files, referenced separately by the report. Solver time is reported
separately from formula construction and total wall time. Timings describe a
single run per case and are not a statistical speedup estimate.

## Recorded calibration

| Vocabulary | Formula | Status | Construction | Solver | Total |
|---|---|---|---:|---:|---:|
| 32 | history | SAT | 3.29s | 2.43s | 5.73s |
| 32 | state | SAT | 1.09s | 2.04s | 3.13s |
| 256 | history | SAT | 7.45s | 22.32s | 29.78s |
| 256 | state | SAT | 1.95s | 24.27s | 26.24s |
| 5,665 | history | UNKNOWN | 17.02s | 30.14s | 47.16s |
| 5,665 | state | UNKNOWN | 7.06s | 30.15s | 37.21s |

The full-vocabulary state controls for seeds 17 and 1729 also returned UNKNOWN
at 30 seconds, with construction times of 6.51 and 7.57 seconds. Smaller controls
returned independently verified SAT fits; their reduced vocabulary is part of
the calibration assumptions. Full-vocabulary hidden recovery remains uncalibrated.

On the matched full-vocabulary seed-7 case, construction fell from 17.02 to
7.06 seconds (about 2.4 times faster). Both solve phases timed out. At 256 words,
state construction was faster but the solver check was slower, so these results
support a construction improvement rather than a general search speedup.

The unchanged 23-word Voynich retry returned **UNKNOWN (timeout)**:
120.09 seconds solving, 2.63 seconds constructing,
and 122.72 seconds total. No full-prefix witness or impossibility
proof was obtained. All 351 tests pass, and a saved 32-word state-control replay
returned verified SAT.

## A single 30-minute positive-control run

From the repository root, run the exact full-vocabulary seed-7 control with only
its timeout increased. This command saves the effective request, result, timing
and environment separately from the original calibration report:

```sh
.venv/bin/python -m benchmarks.cycle_performance \
  --replay data/generated/cycle-performance/inputs/seed-7-vocab-5665-state.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/seed-7-state-30min.json
```

The 30-minute limit covers solving; construction adds some elapsed time. SAT
must be independently verified. UNKNOWN leaves recovery unresolved; UNSAT on
this known positive control indicates an encoding or solver problem. The long
run is user-initiated and has not been performed as part of this update.
