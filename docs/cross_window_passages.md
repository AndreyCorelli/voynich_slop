# Preselected cross-section passage screen

Ten non-overlapping 22-word Voynich windows were selected **before** comparing
any language corpus. Every one of the eight recorded section codes contributes
one window. The two sections with the most eligible candidate windows, B and
S, contribute a second. Selection uses candidate midpoint/third ranks with a
deterministic nearest nonoverlap fallback; length, repetition and language
scores do not affect selection. Each window stays within one folio and cannot
bridge excluded words. Existing processed transcription normalization is used.

`selection.json` stores all 220 record indices, words, folios and start/end
loci, together with corpus and normalization hashes. Section codes are source
metadata, not eight independent genres; no genre interpretation is inferred.
This is a stratified deterministic pilot, not a random manuscript estimate.

## Every selected window

The screen compares the cached Caesar, six medieval Latin works, nine German
varieties, medieval Italian and diplomatic Old Czech samples. Latin also gets
the fixed seven reversible contractions. No inventories were widened. Each
of 25 source/profile combinations is screened under atomic EVA and the one
recorded six-sequence grouped inventory: 250 paired rows, 500 screens.

| Window | Folio | Atomic / grouped units | Equal-word pairs | Any passage survivor, atomic | Any passage survivor, grouped |
| --- | --- | --- | --- | --- | --- |
| A-1 | f67v1 | 131 / 114 | 0 | Yes | Yes |
| B-1 | f78v | 105 / 102 | 9 | No | No |
| B-2 | f81v | 96 / 88 | 5 | No | No |
| C-1 | fRos | 103 / 97 | 1 | No | No |
| H-1 | f34r | 89 / 79 | 3 | No | No |
| P-1 | f99r | 111 / 93 | 1 | No | No |
| S-1 | f106v | 122 / 112 | 0 | Yes | Yes |
| S-2 | f112r | 100 / 96 | 2 | No | No |
| T-1 | f85r1 | 118 / 105 | 1 | No | No |
| Z-1 | f72r1 | 113 / 104 | 2 | No | No |

Survival means satisfying necessary L1–3 word-length bounds and every equal
ciphertext-word implication. It does not mean a common key exists. Both
surviving windows have no repeated ciphertext words, making their repetition
filter vacuous. They also have larger unit totals than most excluded windows.
This pilot does not isolate the causal effect of repetitions from lengths.

Grouped survivors for A-1 occur in legacy German samples 113 and 123 (one
passage each). For S-1, there is one in Dante with the seven Latin contractions,
and one each in legacy German 123 and 133. Atomic A-1 additionally has Dante
and other German candidates; atomic S-1 additionally has German 113 candidates.
Counts across Latin profiles can overlap and are not distinct passage totals.
Caesar, Italian and Czech have no combined survivors in this pilot.

German source streams retain the historical-length parser's legacy normalization,
including known bracket-fragment and short-form limitations. These counts are
paired sensitivity results, not corrected lexical claims; any follow-up on a
German survivor must audit its actual source forms first. Every affected JSON
row records this caveat. Source gaps and normalization choices in the other
corpora remain unchanged.

## What this changes

The opening block's all-zero passage screen is **not universal across these
ten windows**. Eight remain excluded by necessary filters; two admit candidates.
This does not support a language identification or estimate the probability
of encryption. Attested-passage matching searches a finite source collection,
which need not contain the manuscript's plaintext, and exact repeated-word
placement is a demanding constraint even within natural-language samples.

The agreed cross-window screen is complete. The next useful read-only check
would inspect the few surviving passages and their source normalization,
rather than launch another solver sweep or select additional favorable windows.
All ten selected windows remain in the record.

The [exact survivor audit](passage_survivor_audit.md) is complete. All 25 match
entries were recovered; six source-123 entries are flagged for apparent
speaker labels or unexpanded `etc`, while three grouped matches remain
without those flags. No shared-key fit has been established.

## Reproduction

```sh
.venv/bin/python -m benchmarks.cross_window_passages
.venv/bin/python -m pytest -q \
  tests/integration/test_cross_window_passages.py \
  tests/integration/test_eva_tokenization.py \
  tests/integration/test_historical_word_lengths.py
```

Outputs: `experiments/results/cross-window-passages/{selection,report,validation}.json`.
The report checkpoints after each window. Selection reproducibility, exclusions,
folio boundaries, nonoverlap, unchanged repetition pairs and paired counts were
validated; **23 focused tests pass**. No solver calls, downloads or long runs.
