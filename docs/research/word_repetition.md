# Equal-window word repetition diagnostics

The ten saved 22-word Voynich windows are unchanged. The earlier 22-word
opening block is included as a separately labeled reference, not an eleventh
member of the preselected sample. All 18 previous source streams and all six
texts in [the frequency note](word_frequencies.md) are compared separately.
No frequencies are pooled across languages, no lemmatization is added, and
no solver is called. Atomic and grouped EVA have identical word-equality
patterns because the recorded grouping is reversible.

## Measurements and definitions

For each window, the analysis counts distinct words, excess occurrences beyond
the first, repeated types, maximum multiplicity, and equal-word pairs. A type
occurring three times contributes three pairs. Distances count intervening
token positions as `j-i`: adjacent occurrences have distance one. Both pooled
all-pair distance histograms and the distribution of nearest-repeat distances
are saved; the latter excludes windows with no repeats, whose count is reported
separately. Multiplicity histograms for all Voynich targets are retained.

| Voynich window | Distinct words | Equal-word pairs | Maximum multiplicity |
| --- | --- | --- | --- |
| A-1 | 22 | 0 | 1 |
| B-1 | 15 | 9 | 3 |
| B-2 | 18 | 5 | 3 |
| C-1 | 21 | 1 | 2 |
| H-1 | 19 | 3 | 2 |
| P-1 | 21 | 1 | 2 |
| S-1 | 22 | 0 | 1 |
| S-2 | 20 | 2 | 2 |
| T-1 | 21 | 1 | 2 |
| Z-1 | 20 | 2 | 2 |
| Opening reference | 19 | 3 | 2 |

The opening block has three repeated types, each occurring twice. All three
equal-word pairs have distance **10**. Its repetition amount and its exact
positions must therefore be distinguished.

## Thematic comparison

**Subsequent audit correction:** the Turba stream below includes English after
the Latin material. Its figures remain reproducible for that mixed stream but
must not be interpreted as Latin statistics. It is quarantined in
[the audited thematic passage screen](thematic_latin_passages.md).

| Text | Sliding windows | Median distinct | Windows with ≥3 equal pairs | Opening equality-implication matches |
| --- | --- | --- | --- | --- |
| Emerald Tablet, Latin | 140 | 20 | 50.00% | 0 |
| Grosseteste, Latin | 5,679 | 20 | 42.58% | 0 |
| Mirror of Alchemy, English | 3,677 | 19 | 57.52% | 0 |
| Turba, mixed Latin/English; quarantined | 33,271 | 20 | 36.52% | 0 |
| Manilius, Latin verse | 27,441 | 22 | 6.58% | 0 |
| Ptolemy, Greek | 38,006 | 20 | 52.81% | 2 |

Thus three repeated pairs are common in several prose comparanda, although
much less common in Manilius's verse. Requiring them at the opening block's
particular positions is far more selective. The two Greek matches satisfy
the required equalities but neither has exactly the same equality partition:
they contain additional equalities. The nonoverlapping Greek subset contains
zero such implication matches. Neither count establishes a Greek advantage.

Earlier corpora reproduce the opening repetition-only matches: Aquinas two,
Dante two, German 113 one and German 143 two; other streams zero. These
counts ignore lengths. They are not the combined passage survivors from the
cross-window screen. Each of the ten windows has its own comparison counts,
plus marginal below/equal/above ranks for every scalar metric, saved in JSON.

## Model interpretation

Two pattern comparisons are explicitly separate:

1. **Equality implications:** equal ciphertext words require equal plaintext
   words under our globally uniquely decodable, boundary-preserving model.
   Other word positions may coincide. This is the necessary filter previously
   used in passage screening.
2. **Exact equality partition:** all same/different relationships match. This
   is a descriptive diagnostic, **not** a necessary cipher constraint: free
   homophone choices can give one plaintext word several ciphertext forms.

The opening block's low passage-match count should not be described as unusual
repetition quantity or language exclusion. It reflects exact positions in a
finite source collection. That collection need not contain the unknown plaintext.
The model does not provide an occurrence-selection distribution, so ciphertext
and plaintext repetition frequencies cannot simply be equated.

## Extraction and statistical limits

The thematic texts reuse their hash-checked extracted snapshots and exactly
the frequency note's tokenization. Their counts are reproduced before analysis.
This retains chapter headings and flattens book/chapter boundaries; numbers
were removed by the frequency extractor, so windows can bridge them. These
streams are exploratory comparanda, not replacements for the earlier
barrier-preserving passage parser. Turba is a recension compilation with
uncertain OCR/provenance; Emerald is very short; the English supplement is
later; Greek retains accents and inflection. Existing historical corpora retain
their prior normalization, including the documented German legacy caveat.

Primary sliding windows overlap. Separate nonoverlapping windows, resetting
at each source segment or exclusion barrier, are reported as a sensitivity
check. Neither set is guaranteed independent. Ranks and proportions are
descriptive, not p-values, manuscript-wide estimates, or language likelihoods.
Pooled pair distances weight windows with more pairs more heavily and count
the same occurrence pair again when it appears in overlapping windows.

## Reproduction

```sh
.venv/bin/python -m benchmarks.word_repetition
.venv/bin/python -m pytest -q \
  tests/integration/test_word_repetition.py \
  tests/integration/test_cross_window_passages.py \
  tests/integration/test_eva_tokenization.py
```

Results checkpoint per source under `experiments/results/word-repetition/`.
The report stores source records, selection and code hashes, full scalar
distributions, pair distances and all per-window comparisons. **11 focused
tests pass**, covering triple-occurrence pairs, distances, gap resets,
nonoverlap, quantiles, and the distinction between implication and exact
partition. No new downloads, no solver calls, no additional Voynich selection.

Next useful step: audit/extract the thematic Latin texts with explicit source
barriers before adding them to the same fixed ten-window length-plus-repetition
screen. This analysis alone does not justify a Greek cipher branch or more
solver runs.
