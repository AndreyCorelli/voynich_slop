# Broader attested medieval Latin sample

Four additional edited works add **58,211 eligible 22-word windows** to the
existing Aquinas/Charles IV sample, bringing the medieval total to **80,024**.
The seven-unit inventory and fixed Voynich block are unchanged. No new window
meets all positionwise length bounds, and only two additional windows match
the exact repeated-word pattern. No Z3 calls or cipher changes are made.

## Sources and results

| Added work | Genre | Normalized tokens | Eligible windows | Fewest length failures with seven units | Repetition-compatible windows |
|---|---|---:|---:|---:|---:|
| [Einhard, Vita Karoli Magni](https://www.thelatinlibrary.com/ein.html), 9th c. | Biography | 7,571 | 6,857 | 5 | 0 |
| [Gesta Francorum](https://www.thelatinlibrary.com/gestafrancorum.html), c. 1100, books I–X | Crusade narrative | 20,078 | 19,259 | 4 | 0 |
| [Richard de Bury, Philobiblon](https://www.thelatinlibrary.com/debury.html), 14th c. | Books and learning | 14,522 | 14,001 | 5 | 0 |
| [Dante, Monarchia](https://www.thelatinlibrary.com/dante.html), early 14th c., books I–III | Political philosophy | 19,165 | 18,094 | 1 | 2 |

The minimum failed-position counts are the same with ordinary letters and
with seven units. The best new length-only window, from Dante, needs `patet`
at position 19 shortened from five units to at most four. It nevertheless
conflicts at all three repeated ciphertext pairs: `aut`/`non`, `enim`/`ut`,
and `est`/`patet`. A new reversible contraction for `patet` would not repair
those contradictions.

The two new repetition-compatible Dante windows overlap and come from a
Biblical quotation. They fail at **8** and **10** positions under seven units.
The better-ranked one has total minimum unit-count distance **26**, improving
on the best repetition-compatible Aquinas window's 13 failures and distance
53. These distances sum independent word-length gaps, not numbers of new
abbreviation rules or cipher exceptions.

Across the six medieval works, only **four of 80,024** windows satisfy the
three exact repeated-word equalities, and none satisfies all word lengths.
These are overlapping windows, not independent samples or language
probabilities. Caesar remains a separate control and is not included in the
expanded medieval denominator.

## Extraction and review

Fifteen accepted HTML pages are cached with download manifests and SHA-256
checksums. Einhard's own preface and text are included; Walahfrid's prefatory
material and a separate letter before Einhard's preface are excluded. All
ten Gesta books and all three Monarchia books are scanned separately.

Historical source spellings, including existing u/v and j/i choices, are
retained. Diacritics and typographic ligatures follow the previous analysis's
normalization. Book/chapter boundaries, number-bearing tokens, bracketed
editorial text, and excluded headings interrupt windows. Ordinary paragraphs
may be crossed. Source titles, chapter titles, navigation, explicit/incipit
labels and editorial proposition numbers in Dante are excluded.

A paragraph-stream parser handles missing closing tags without duplicating
body text or letting a later footer truncate the text. A regression check
confirms Philobiblon reaches the last chapter, despite malformed markup near
chapter VII. Inline formatting preserves existing word whitespace instead
of splitting words. Pages that are not valid UTF-8 are decoded strictly as
Windows-1252, with the encoding choice recorded; no replacement characters
are introduced.

Albertano's initially downloaded De amore page is rejected because many words
are merged, such as `patreluminum` and `moribusconformare`. The inspected
Abelard Historia calamitatum page is also excluded because words are fragmented
around folio markers and stray editorial characters. No spacing repairs are
guessed. Accepted texts are edited web transcriptions, not diplomatic
manuscript transcriptions; occasional edition/transcription errors remain a
limitation. Raw source material remains local research data.

## Reproduction and artifacts

```sh
.venv/bin/python -m benchmarks.expanded_medieval_latin
```

For a fresh checkout without the cached texts, add `--download`; existing
checksum-verified files are reused.

Outputs are `experiments/results/expanded-medieval-latin/report.json`,
`summary.csv` and `validation.json`. The JSON includes every source manifest,
extraction audit, failed-position histogram, closest passages, repetition
conflicts, the unchanged inventory hash and the source/code hashes.

```sh
.venv/bin/python -m pytest -q \
  tests/integration/test_expanded_medieval_latin.py \
  tests/integration/test_latin_length_failures.py \
  tests/integration/test_latin_contractions.py \
  tests/integration/test_historical_word_lengths.py
```

**51 focused analysis tests pass**, including complete-source extraction,
malformed paragraph recovery, inline word continuity, proposition-number
removal, chapter/gap handling, strict encoding fallback and the existing
contraction/length diagnostics.

Broader coverage improves the closest repetition-compatible example but does
not establish a passage fit. These finite source-passage exclusions do not
exclude Latin generally, other historical abbreviation systems, revised
word-boundary assumptions or arbitrary dictionary combinations.
