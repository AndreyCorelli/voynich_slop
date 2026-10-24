# Matched shuffle controls for corrected German fits

The corrected Swabian (123) and Alsatian (233) dictionaries both admit verified
fits to the original 30-word block. Their solver times were 1374.32 and 1546.90
seconds respectively. This pilot asks whether compatibility also survives
destroying within-word glyph order under the same dictionaries and model.

Whole-word reordering leaves the free-selection model invariant: it imposes
dictionary membership without grammar or word-order constraints. Such a control
cannot discriminate here. Instead, the batch uses two glyph-shuffle families:

| Family | Length sequence | Global glyph counts | Each word's glyph counts | Exact repeated-word relationships |
| --- | --- | --- | --- | --- |
| Typewise within-word | Preserved | Preserved | Preserved | Preserved |
| Global frequency shuffle | Preserved | Preserved | Not constrained | Not constrained |

Typewise shuffling draws one permutation per distinct word and reuses it at
every occurrence. Draws merging distinct word types or leaving the whole text
unchanged are rejected. The global shuffle permutes the flattened glyph stream
and cuts it at the original boundaries. Seeds 7, 17 and 1729 produce six texts,
each tested against both corrected vocabularies: 12 shuffle inputs in total.
The alphabets, global prefix-free H2/L3 bounds, free selection, dictionary,
absence of nulls, and observed-code domains remain fixed per source.

Four known-positive controls resample homophone choices from the fitted
plaintext and encoder, conditioned on the original length of every word.
Their generating witnesses are independently verified and saved separately;
the solver inputs contain no key or plaintext hints. They calibrate recovery
of known solutions, but are not independent language samples and do not match
global glyph counts or repetition relationships.

The first seed-7 probe in each family and vocabulary returned UNKNOWN at
30 seconds (four probes). The remaining twelve inputs were not run at that
budget. This cannot establish a difference from originals that needed about
23–26 minutes. Three seeds per family constitute a small exploratory pilot,
not a significance test or an estimate of language likelihood.

## Recorded 30-minute follow-up and pause

The source-123 typewise seed-7 batch test returned UNKNOWN after 1800.18
seconds. Source-233 typewise seed-7 was interrupted after approximately 41
seconds and saved as UNKNOWN; it is not an equal-budget comparison.
Separate source-123 seed-7 replays returned:

| Control | Result | Solver seconds |
| --- | --- | --- |
| Global frequency shuffle | UNKNOWN | 1800.15 |
| Length-conditioned known positive | Independently verified SAT | 1489.82 |

The positive establishes successful recovery of this known-solvable instance.
Neither shuffle timeout establishes incompatibility or an advantage for the
original text. The German expansion branch is paused rather than scheduling
the remaining controls. All checkpoints, inputs and replay reports are retained.
The next bounded branch is documented in
[the Latin dictionary contraction screen](latin_dictionary_contractions.md).

The 30-minute batch is prepared without launching any long solves. Run:

```sh
.venv/bin/python -m benchmarks.german_shuffle_controls \
  --timeout-ms 1800000 --solve --resume
```

Sixteen sequential tests can use up to eight hours of solver time, plus model
construction. Results checkpoint after every test; rerun the same command to
resume. Completed UNKNOWN results remain unresolved and are skipped on resume.

For a narrower follow-up after the first typewise shuffle timed out, replay
only the Swabian seed-7 global shuffle and its known-positive control:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-shuffle-controls/budget-1800000ms/inputs/123-frequency-seed-7.json \
  --replay-output experiments/results/german-shuffle-controls/123-frequency-seed-7-30min.json
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-shuffle-controls/budget-1800000ms/inputs/123-positive-seed-7.json \
  --replay-output experiments/results/german-shuffle-controls/123-positive-seed-7-30min.json
```

These separate replay reports do not update the batch checkpoint. The pair has
a combined solver budget of one hour, plus construction time.

SAT witnesses are verified independently. A known-positive UNSAT aborts the
batch because it contradicts its checked generating witness.

Reports are saved under `experiments/results/german-shuffle-controls/` and
inputs and separate truth files under `data/generated/german-shuffle-controls/`.
Configuration hashes bind the code, sources, inputs and budget. Artifact
validation checked both prepared batches, paired shuffle invariants and all
positive witnesses. The shuffle-control and regional-audit integration suites
passed 17 tests.
