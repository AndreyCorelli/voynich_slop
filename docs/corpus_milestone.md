# Corpus ingestion and bounded real-text pilot

This milestone acquires two original sources, preserves their bytes, implements
explicit normalization and exact sampling, and measures matched controls before
running a small bounded real-text pilot. No new dependency is required.

## Sources and provenance

| Source | Provider/version | Original bytes | SHA-256 |
| --- | --- | --- | --- |
| [ZL EVA](https://www.voynich.nu/data/ZL3b-n.txt) | Zandbergen–Landini 3b, 13 May 2025; IVTFF Eva- 2.0 | 411,671 | `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc` |
| [Caesar, books I–IV](https://www.gutenberg.org/ebooks/218) | Project Gutenberg 218; header updated 15 March 2009 | 169,899 | `84ac8411841a4d8f5f4a49b6a2cd1f466917c6a5af72916d5e0b2b1ecb2f659c` |

The [transliteration overview](https://www.voynich.nu/transcr.html) describes the
ZL source. [IVTFF documentation](https://www.voynich.nu/software/ivtt/IVTFF_format.pdf)
defines its annotation syntax. Gutenberg's downloaded original retains its terms.
No explicit redistribution license was established for ZL. Both downloaded files,
processed corpora, and generated results remain local and excluded from version
control. Corpus-derived vocabularies and samples remain generated artifacts too.

Raw manifests contain the declared URL, provider, version, UTC acquisition time,
byte length, encoding, rights note, and checksum. Direct fetching records the
resolved URL; local import cannot establish the redirect chain. Existing raw
artifacts are reused only after checksum verification. Imports never overwrite
originals. Processed artifacts record their source manifest and normalization.

## Explicit normalization

EVA defaults to individual EVA character units, with spaces outside the token
alphabet. This is a transliteration convention, not an assertion about manuscript
glyphs. No digraph or gallows grouping is inferred. Folio, complete locus ID,
physical line, page variables, section code `$I`, transcriber ID, source locus text,
word position, and annotations are retained.

Periods and drawing interruptions create word boundaries. Uncertain comma spaces
can be split (default), joined, or cause the complete locus to be excluded.
Uncertain readings, illegible units, rare-character escapes, and ligatures are
retained in records but their whole words are excluded from default solver
samples. `--annotated-words preserve` retains each bracketed reading, ligature,
escape, or illegible run as an atomic annotation token. It never chooses an
alternative reading. Preserved annotation tokens are a different model and should
not be interpreted as resolved glyphs. Inline comments do not become text tokens;
text tags update page metadata. Wrapped loci are joined without inventing spaces.
The parser targets IVTFF EVA 2.0, not every historic transcription format.

Latin processing removes Gutenberg boilerplate before the Caesar incipit and after
the END marker, and excludes internal book headings. Defaults lowercase, remove
combining diacritics, map j to i, preserve u/v, retain spaces, and use the configured
24-symbol alphabet `abcdefghiklmnopqrstuvxyz`. Punctuation separates words.
Words outside the alphabet are excluded whole rather than truncated. Records
retain decoded Unicode character offsets into the source. u/v folding, j retention,
alphabet restriction, and space removal are explicit options. j retention requires
an alphabet containing j. Book headings and exclusions remain auditable.

Default processed measurements:

| Corpus | Eligible words | Tokens | Vocabulary | Observed units | Excluded word records |
| --- | --- | --- | --- | --- | --- |
| ZL EVA | 37,608 | 186,959 | 7,457 | 25 | 1,418 |
| Caesar Latin | 20,496 | 123,094 | 5,675 | 23 | 26 |

These counts describe these normalization settings. In particular, splitting
uncertain spaces and excluding annotated words changes counts from source totals.
Statistics include word and token counts, frequencies, word lengths, within-word
bigrams, unigram entropy, and within-word conditional entropy. Word identities use
atomic token tuples, preserving distinctions between multi-character units.

## Commands

```sh
uv run voynich-smt corpus fetch zl-eva
uv run voynich-smt corpus fetch caesar-latin
uv run voynich-smt corpus normalize data/raw/ZL3b-n.txt.manifest.json \
  --output data/processed/zl-eva.json
uv run voynich-smt corpus normalize data/raw/pg218.txt.manifest.json \
  --output data/processed/caesar-latin.json
uv run voynich-smt corpus sample data/processed/zl-eva.json \
  --words 5 --folio f1r --output data/generated/f1r-first5.json
uv run voynich-smt corpus sample data/processed/caesar-latin.json \
  --words 5 --seed 7 --output data/generated/latin-seed7-first5.json
uv run voynich-smt corpus info data/processed/zl-eva.json
uv run python benchmarks/corpus_comparison.py
uv run pytest -q
```

`fetch --local PATH` imports previously downloaded original bytes with catalogued
source metadata. `normalize` accepts `--uncertain-spaces`, `--annotated-words`,
`--uv`, `--keep-j`, `--alphabet`, and `--remove-spaces`; switches for the wrong
corpus are rejected. `corpus info` also retains its earlier public-request mode.

Sampling supports `--folio`, `--section`, `--line` (complete locus ID), `--offset`,
`--seed`, and `--max-tokens`. Selection operates on eligible records. Random samples
are drawn without replacement in seeded selection order. A token budget retains
complete words only, stopping before the next word would exceed it. Exact record
indices, source locations, settings, corpus identity, and sample checksum are saved.
A sample is an artifact, not itself a solver request: the pilot builds and saves
public requests explicitly.

## Controls and pilot

Seeded controls implement word shuffling, within-word shuffling, global
frequency-preserving shuffling, uniform units, and a simple prefix/stem/suffix
pseudo-language. The latter samples source first/last-unit distributions and
uniform interior units at source word lengths; it is a transparent local generator,
not a reproduction of a published theory. Shuffling preserves the stated
frequencies. All five controls preserve EVA sample word count and total token
count; all except word shuffling also retain the length at each word position.

The pilot uses the first five eligible words of f1r:
`fachys ykal ar ataiin shol`. Its language constraint is **only the first 32 distinct
eligible Caesar words of length at most 12**, not unrestricted Latin. All runs share
the 24-symbol plaintext alphabet, full eligible 25-unit EVA alphabet, prefix-free
verbose codes of length 1–2, at most one homophone, preserved spaces, disabled
nulls/context, feasibility objective, and a ten-second timeout.

| Dataset | Words | Tokens | Result | Solver seconds |
| --- | --- | --- | --- | --- |
| Synthetic Latin ciphertext | 5 | 44 | SAT, independently verified | 0.340 |
| Voynich f1r sample | 5 | 22 | UNSAT | 0.240 |
| Word shuffle | 5 | 22 | UNSAT | 0.057 |
| Within-word shuffle | 5 | 22 | UNSAT | 0.054 |
| Frequency shuffle | 5 | 22 | UNSAT | 0.211 |
| Uniform units | 5 | 22 | UNSAT | 0.234 |
| Prefix/stem/suffix generator | 5 | 22 | UNSAT | 0.221 |

The synthetic gate uses the same dictionary, alphabets, code bounds, and word
count; its ciphertext token lengths differ. Private truth is stored separately,
and solving reloads public inputs only. `synthetic_gate_passed` records verified
SAT; a failed gate makes real-text failure unsuitable for interpretation. One
successful synthetic fixture does not establish reliability across corpus samples.

Results, settings, exact requests, statistics, and metadata are checkpointed to
`experiments/results/corpus-pilot.json`. Public requests are in
`data/generated/corpus-pilot/inputs/`; private truth is in
`data/generated/corpus-pilot/ground_truth.json`. The runner accepts source paths, output,
word count, seed, timeout, vocabulary size, and artifact directory as CLI options.

All six real/control inputs are excluded by this narrow bounded model. Their
shared UNSAT outcome gives no discrimination between these categories and supports
no manuscript-language conclusion. No minimum complexity was measured in this
feasibility pilot. The suite passes **262 tests**, covering normalization,
annotation policies, offsets, sampling, provenance checks, controls, and CLI safety.

The next milestone should widen the corpus-derived vocabulary, validate multiple
synthetic seeds and samples at each setting, and sweep one cipher bound at a time
on matched samples. UNKNOWN must remain distinct from UNSAT. N-gram constraints and
held-out corpus splits can follow once the wider synthetic gate is reliable.


The counts above describe the preserved parser-v1 corpus. Parser version 2
also removes the prose footer before the formal Gutenberg END marker. See
[the footer correction and new vocabulary](clean_latin_retry.md).
