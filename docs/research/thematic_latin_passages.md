# Audited thematic Latin passage screen

The ten preselected Voynich windows and both recorded EVA tokenizations remain
fixed. Each accepted Latin stream is screened with letters alone and with the
existing seven reversible contractions. No solver, new inventory or new
Voynich selection is involved.

## Source audit

| Source | Decision | Normalized tokens | Explicit segments | Internal barriers | Eligible 22-word windows |
| --- | --- | --- | --- | --- | --- |
| Emerald Tablet | Exploratory small control | 161 | 15 statements | 0 | 5 |
| Grosseteste, De sphaera | Exploratory edited-text control | 5,648 | 5 chapter segments | 90 | 4,588 |
| Manilius, five books | Classical verse sensitivity | 27,142 | 6 book/gap segments | 804 | 11,730 |
| Turba compilation | Quarantined | — | — | — | — |

Emerald extraction uses the fifteen ordered-list statements inside the text
container, excluding Wikisource navigation and editorial framing. The first
and last statements are checked. Each statement is a separate segment;
cross-statement windows are not counted. Its five windows provide very limited
coverage, and the edition provenance remains uncertain.

Grosseteste extraction begins at `Intentio nostra` in body paragraphs. Chapter
headings create breaks and do not become words. Bracketed editorial content,
page numbers and isolated uppercase diagram labels interrupt windows. Ordinary
paragraphs within a chapter may be crossed. Historical spelling and u/v remain
as supplied; no geometric label is invented as a lexical word.

Manilius extraction checks the five book incipits and excludes titles and the
Latin Library footer. Books and asterisk-marked gaps remain separate; numeric
line references and brackets interrupt windows. Ordinary verse lines may be
crossed. Apparent transcription anomalies such as `hoe` and `quls` are left
as supplied, without guessed corrections. This is an edited-web-text sensitivity
control, not a diplomatic manuscript transcription or a medieval prose sample.

All sources retain the existing letter normalization for accents/ligatures and
historical spellings. Inline formatting preserves word boundaries. Unknown
editorial spans are barriers rather than silently removed words. Raw snapshots
are unchanged; their SHA-256 hashes, extraction decisions and normalized segment
arrays are saved separately. Raw hashes bind these cached inputs, but do not
authenticate the underlying historical edition.

### Turba correction

The previous frequency extractor starts at the Latin title but stops at a
later `FINISH.` after English prose, including discussion of “two parts of
Elixir.” Thus the purported Latin frequency and repetition streams are
mixed-language. The Latin part also contains unresolved forms such as
`sententiasq;` and `eamq;`, and belongs to a recension compilation with uncertain
transcription quality. No endpoint or expansion is guessed here.

Turba is excluded from this passage screen. The original snapshots and generated
frequency/repetition JSON remain intact for provenance, while the frequency
note and repetition report documentation now label its statistics as mixed
and quarantined. They must not support Latin-only comparisons.

## Results and scope

**All 60 source/window/profile rows have zero positionwise length survivors
under both EVA tokenizations**, hence zero combined length/repetition survivors.
This covers 120 necessary-filter screens. Repetition alone is recorded separately
and need not fail: these sources are already excluded by length at this stage.

The thematic addition therefore adds no passage candidate for the selected
windows. It does not remove the German/Dante survivors from the previous screen,
exclude Latin as a language, or establish the manuscript's subject. Searches
over these finite edited texts need not include the unknown plaintext, and
explicit barriers substantially reduce the eligible windows compared with the
flattened frequency streams. Do not pool the old and new denominators.

The audit and bounded screen are complete. No solver run is justified by these
all-zero passage results. A distinct next question would be an audit of the
previously surviving German/Dante passages, retaining their exact positions.

## Reproduction

```sh
.venv/bin/python -m benchmarks.thematic_latin_passages
.venv/bin/python -m pytest -q \
  tests/integration/test_thematic_latin_passages.py \
  tests/integration/test_word_repetition.py \
  tests/integration/test_eva_tokenization.py
```

All **13 focused tests pass**, including incipits, footers, chapter/statement/gap
boundaries, numeric/editorial barriers, diagram labels and historical spelling.
Outputs live under `experiments/results/thematic-latin-passages/`, including
the report, three segment artifacts and independent validation. No downloads,
raw modifications or solver calls.
