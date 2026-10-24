# Historical 22-word-window mean lengths

The Voynich block has 22 words and 104 EVA characters. Under the current
noncompressive, word-preserving model, its exact ceiling is **104/22 = 4.72727…
plaintext letter units per word**. We compare integer window totals with 104;
we do not round to 4.73 before classifying a passage. No Z3 imports, calls or
model changes occur in this analysis.

These are distributions for selected historical text editions, not population
estimates for whole languages. Each row below reports all overlapping 22-word
windows within uninterrupted runs. Windows never cross text boundaries,
excluded headings, editorial insertions, unknown abbreviations in the German
primary profile, or gaps. Ordinary paragraph, verse-line and page boundaries
can be crossed. Punctuation contributes no letters.

## Primary distributions

| Historical sample | Eligible windows | P05 | Median | P95 | At or below 4.72727… |
|---|---:|---:|---:|---:|---:|
| Caesar, *De bello Gallico* I–IV | 20,400 | 5.09 | 6.00 | 6.95 | 1.19% |
| Medieval Latin, two prose works | 21,813 | 4.68 | 5.64 | 6.73 | 6.67% |
| 15th-century German, nine varieties | 66,638 | 3.73 | 4.45 | 5.41 | 70.48% |
| Medieval Italian, *Decameron*, first ten stories | 13,895 | 3.82 | 4.64 | 5.55 | 58.49% |
| Old Czech, *Dalimil*, manuscript-style column | 1,403 | 4.00 | 4.86 | 5.91 | 43.26% |

![Cumulative window-length distributions](../experiments/results/historical-word-lengths/window-length-cdf.png)

The ceiling is deep in Caesar's lower tail and in medieval Latin's lower tail,
but it intersects common window lengths in these vernacular samples. In
particular, Caesar's fifth-percentile cutoff of 5.09 cannot be transferred to
all medieval Latin: the pooled medieval Latin fifth percentile is 4.68.
Passing this total-length check is necessary, not sufficient, for cipher
feasibility. No language likelihood or manuscript-language conclusion is
computed.

## Sources and orthographic conventions

**Caesar.** The immutable Gutenberg source and corrected parser-v2 corpus
already present in this project are used. Lowercase, j→i, u/v preserved;
quantity/diacritic marks do not add letters. Book headings break runs.

**Medieval Latin.** [Aquinas, *De ente et essentia*](https://www.thelatinlibrary.com/aquinas/ente.shtml)
(13th-century scholastic prose; 7,129 windows) and
[*Vita Caroli IV*](https://www.thelatinlibrary.com/vitacaroli.html)
(14th-century historical prose; 14,684 windows). Historical spellings such as
`nichil` and `que` are retained, without classicizing them to `nihil` or `quae`.
Typographic æ/œ and presentation ligatures are expanded to their letters;
editorial chapter labels and web navigation are removed. Number-bearing tokens
break runs. These are edited full-word texts, not abbreviation-faithful
manuscript transcriptions. Aquinas has 10.32% of windows below the ceiling;
*Vita Caroli* has 4.90%. An initially retrieved *Disciplina clericalis* page
was rejected because it visibly merges adjacent words, making lengths unreliable.

**German.** The [Bonner Frühneuhochdeutschkorpus](https://korpora.org/FnhdC/),
XML release 2017, with period-III witnesses selected from its
[source bibliography](https://korpora.org/FnhdC/FnhdC-Bibliographie.html).
Period III contains fifteenth-century witnesses; original compositions and
modern editions can have different dates. The mixed genres include chronicles,
religious discourse, medical writing and drama. The Edlibach text 213 is
excluded because its listed additions extend to 1530.

The [provider's normalization documentation](https://korpora.org/FnhdC/Dokumentation.html)
is followed: actual separate `morph` elements remain separate written words,
rather than being silently collapsed into the larger annotated `wortform`.
Spelling is not modernized: `vnd`, for example, remains `vnd`. Long s becomes s;
ß is treated as the two-letter ligature ss (sz would have the same length).
a/o/u with superscript e is unified with graphical umlaut variants and counts
as one base letter. Other explicit superscript letters are retained as letters,
so `buͦch` has the normalized letter sequence `buoch`. Documented grave and
apostrophe abbreviations expand to er/us; the documented superscript ri/s
symbols expand accordingly. Ordinary accent and umlaut marks add no letters.
Unresolved overbar/macron and uncertain-sign forms break primary runs;
no n/m or longer lexical expansion is guessed. Editorial insertions and
headings also break runs. This complete-letter-window selection can be biased;
the two as-written sensitivity profiles below show its effect. The raw archive
is retained only as a local research copy; provider terms prohibit redistribution.

**Italian.** [Boccaccio's *Decameron*](https://it.wikisource.org/wiki/Decameron),
all ten stories of the first day, in the Massera 1927 edition transcribed on
Wikisource. This preserves medieval language, but is not a diplomatic manuscript
edition. Narration/dialogue is extracted separately for each story; rubrics,
page-navigation labels and notes are excluded. Source forms, elisions and word
spacing are retained, with no restoration of lost vowels. Internal apostrophes
remain within one written word: `l’uomo` counts as one five-letter token.
Accents count as one base letter. Apostrophe splitting is reported separately
because it changes the number of words and lowers means.

**Czech.** Oxford's [parallel *Dalimilova kronika* excerpts](https://czech.mml.ox.ac.uk/dalimilova-kronika)
and [editorial guidelines](https://czech.mml.ox.ac.uk/chrestomatie-editorial-guidelines).
The primary profile uses the manuscript-style column drawn from the Cambridge
manuscript via Porák's chrestomathy. The parallel H&D 1958 critical transcription
is a sensitivity profile, retaining Old Czech language rather than translating
it into modern Czech. These columns differ in readings and content as well as
orthography, so their difference is not a pure orthographic intervention.
Long s is unified with s; diacritics/quantity marks count as one base letter;
actual written digraphs such as ch/cz/ss retain two letters. Folio labels are
removed without breaking the words they interrupt. Chapter headings and gaps
break runs. Explicit scribal expansions are retained in the primary column and
suppressed in a separate conservative as-written profile. Modern reference
paragraphs and gloss attributes are excluded. The main sample is small and
in verse, so dated prose excerpts are also reported below.

## German varieties

| Corpus ID; witness | Variety | P05 | Median | P95 | ≤ ceiling |
|---|---|---:|---:|---:|---:|
| 113; Kottanerin, 1445–1452 | Middle Bavarian, Vienna | 3.59 | 4.18 | 4.91 | 90.36% |
| 123; Neidhart, 1486 | Swabian, Ulm | 3.68 | 4.41 | 5.32 | 75.25% |
| 133; Pillenreuth, 1463 | East Franconian, Nuremberg | 3.77 | 4.50 | 5.45 | 68.07% |
| 143; Tauler edition, 1498 | Upper Saxon, Leipzig | 3.86 | 4.45 | 5.27 | 73.70% |
| 153; Koelhoff, 1499 | Ripuarian, Cologne | 3.95 | 4.73 | 5.68 | 52.69% |
| 223; Burlaeus edition, 1490 | East Swabian, Augsburg | 4.09 | 4.86 | 5.82 | 40.64% |
| 233; Brunschwig, 1497 | Alsatian, Strasbourg | 3.64 | 4.36 | 5.27 | 76.03% |
| 243; Wonnecke, 1485 | Hessian, Mainz | 4.00 | 4.73 | 5.50 | 50.78% |
| 253; Rothe witness, later 15th c. | Thuringian, Eisenach | 3.95 | 4.55 | 5.32 | 66.45% |

Pooling weights sources by eligible window count. It does not establish that
regional differences are independent of genre or editor. Metadata, window
counts and each source's full distribution are included in the report.

## Sensitivity and genre checks

| Alternative profile | Windows | P05 | Median | P95 | ≤ ceiling |
|---|---:|---:|---:|---:|---:|
| German: unresolved abbreviation forms included as written | 111,541 | 3.77 | 4.50 | 5.45 | 67.25% |
| German: conservative base-grapheme count, including abbreviations | 111,541 | 3.73 | 4.45 | 5.41 | 70.33% |
| Italian: internal apostrophes split | 14,207 | 3.77 | 4.55 | 5.45 | 65.86% |
| Czech: scholarly transcription of Old Czech | 1,469 | 3.59 | 4.36 | 5.27 | 76.45% |
| Czech: manuscript-style, explicit expansions suppressed | 1,403 | 3.96 | 4.82 | 5.91 | 45.47% |

Oxford's [dated Bible excerpts](https://czech.mml.ox.ac.uk/vyvoj-jazyka-prekladu-bible)
provide a small fifteenth-century prose check. These are four versions of the
same Genesis 22:1–14 passage, not four independent texts or a broad Czech corpus.
Each version is kept separate. Verse numbers and manuscript references are
removed; historical orthography and explicit expansions are retained. The
sixteenth-century Kralice version is excluded.

| Czech prose witness | Windows | P05 | Median | P95 | ≤ ceiling |
|---|---:|---:|---:|---:|---:|
| Olomouc Bible, 1417 | 273 | 3.35 | 4.27 | 4.82 | 91.58% |
| Boskovice Bible, c.1420 | 269 | 3.56 | 4.32 | 4.86 | 89.59% |
| Nymburk Bible, mid-15th c. | 254 | 3.80 | 4.41 | 5.00 | 84.25% |
| Prague Bible, 1488 | 274 | 3.68 | 4.59 | 5.09 | 66.42% |

Nonoverlapping-window checks give ceiling fractions of 0.86%, 6.37%, 69.27%,
59.34% and 45.45% for the five primary rows, respectively. This reduces overlap
but does not make the corpus samples statistically representative or independent.

## Reproduce and export

```sh
uv sync
.venv/bin/python -m benchmarks.historical_length_sources
MPLCONFIGDIR=/tmp/voynich-historical-matplotlib \
  XDG_CACHE_HOME=/tmp/voynich-historical-cache \
  .venv/bin/python -m benchmarks.historical_word_lengths
.venv/bin/python -m pytest -q tests/integration/test_historical_word_lengths.py
```

Fetching needs network access; cached immutable copies are checksum-checked.
The analysis itself is offline. Beautiful Soup and Matplotlib are development
analysis dependencies, locked in `uv.lock`; runtime cipher dependencies are
unchanged. The source-specific extractor/normalizer is versioned and tested.
All 17 new analysis tests pass; the solver test suite was not run for this task.

Artifacts under `experiments/results/historical-word-lengths/`:

- `report.json`: complete distributions, quantiles, exact ceiling counts,
  normalization rules, source URLs/checksums, individual texts, sensitivities,
  nonoverlapping checks and analysis-code hash.
- `summary.csv`: comparison rows.
- `distributions.csv`: full histograms and cumulative fractions, with exact
  integer totals and mean values.
- `window-length-cdf.svg`, `.pdf`, `.png`: standalone distribution figure.

These letter-unit comparisons depend on normalization, word boundaries and
whether abbreviations are expanded. EVA transcription characters also need
not equal manuscript glyphs. The hard 4.727 ceiling belongs to this particular
22-word ciphertext block, not every window or the whole manuscript.
