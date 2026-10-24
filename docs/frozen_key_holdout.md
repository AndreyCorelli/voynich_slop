# Frozen-key next-block prediction

The saved letters-only Latin key and corrected Swabian (123) and Alsatian (233)
keys were frozen without repairs. Their fitted SAT witnesses were independently
verified first. Each key was tested on the **immediate next 22 contiguous
records after its own fitting block**, on folio f3r. No excluded record was
skipped and no better-scoring window was substituted.

The Latin training block occupies records 473–495 inclusive; its holdout is
496–517. Both German training blocks occupy 474–503; their holdout is 504–525.
These are zero-based processed-corpus indices, saved together with full raw
record metadata and loci. The Latin holdout partly overlaps German training:
results are per-key extensions, not independent identical-window comparisons.
This is retrospective analysis of existing data, not a prospectively blind test.

## Results

| Frozen key | Fully decoded / 22 | Dictionary words / 22 | New ciphertext words | Fully decoded new words | Dictionary words among new words |
| --- | --- | --- | --- | --- | --- |
| Latin letters | 12 | 7 | 17 | 7 | 2 |
| Swabian 123 | 9 | 3 | 20 | 7 | 1 |
| Alsatian 233 | 8 | 2 | 20 | 6 | 0 |

Every complete decode was re-encoded to check exact round trips. A dictionary
hit requires complete word decoding and exact membership in the fitted model's
original dictionary. Partial decoded prefixes never count as dictionary hits.
All keys leave many holdout words undecodable, so none explains the entire next
block under its existing mappings.

Repeated training ciphertext words account for five of the Latin dictionary
hits and two hits for each German key. The novel Latin hits are `cthom → ubi`
and `chom → ei`; the Swabian novel hit is `shol → ain`. The Alsatian key has
no novel dictionary hits. Repeated words are legitimate predictions but weaker
evidence of extension than novel word forms. Neither these isolated hits nor
the overall decoded outputs establish grammatical plaintext.

## Matched controls

Each holdout has 20 typewise within-word shuffles and 20 global frequency
shuffles, using fixed seeds 0–19. Both preserve word lengths and total glyph
counts. Typewise shuffles additionally preserve every word's glyph multiset
and exact repeated-word relationships. Shuffling is performed after the held-out
block is fixed; the key and dictionary are identical for real and control text.

| Key | Real dictionary words | Typewise min / mean / max | Global min / mean / max |
| --- | --- | --- | --- |
| Latin | 7 | 0 / 0.95 / 4 | 0 / 0.10 / 1 |
| Swabian | 3 | 0 / 0.00 / 0 | 0 / 0.15 / 1 |
| Alsatian | 2 | 0 / 0.05 / 1 | 0 / 0.05 / 1 |

Real total dictionary hits exceed all 40 controls for each key. However, once
training word repeats are removed, four typewise Latin controls reach at least
its two novel hits; three global Swabian controls reach its one novel hit. The
Alsatian novel score is zero. Novel-word denominators can differ in controls;
all denominators and individual word results are retained. These raw counts
are descriptive and are not a significance test or language likelihood.

The aggregate total-score advantage partly reflects recurring local Voynich
word forms whose mappings were already fitted. It does not establish that the
keys explain new natural-language text. Shared glyph structure can persist
without the fitted plaintext being correct.

## Validation and scope

The decoder stops at the first impossible prefix or unfinished final code in
each word. The optional glyph-prefix coverage metric counts only glyphs consumed
by complete codes before that failure; it is not whole-word decoding coverage.
It is approximately 54–56% for these real holdouts. No skipped-glyph recovery,
unknown mapping insertion, transcription repair or new key search is allowed.

For each frozen key, a decoder calibration re-encodes the first 22 fitted
plaintext words with new free choices. All 22 decode back into dictionary words.
This checks the implementation, not independent language generalization.
Full codebook hashes and source report hashes bind the frozen keys.

The experiment rejects complete next-block coverage by these **particular
keys**. It does not exclude another key in the family, require every plaintext
word to occur in the finite dictionary, or rank Latin versus German: training
sizes, holdouts and dictionaries differ. There were no solver calls or new
Voynich windows selected in response to the results.

This bounded prediction test is complete. It supplies little reason to keep
extending the same fitted keys. A further experiment should pose a different
question or use a predefined broader validation protocol rather than repair
these keys to their holdouts.

## Reproduction

```sh
.venv/bin/python -m benchmarks.frozen_key_holdout
.venv/bin/python -m pytest -q \
  tests/integration/test_frozen_key_holdout.py \
  tests/integration/test_german_shuffle_controls.py
```

All **10 focused tests pass**. Reports, exact selections, 120 shuffled controls,
word-level decode failures, novelty counts, and calibration results are saved
under `experiments/results/frozen-key-holdout/`. Validation rechecks frozen key
identity, matched shuffle invariants and complete-decode round trips.
