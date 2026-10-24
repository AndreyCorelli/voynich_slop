# Contiguous sample-size scaling under a fixed cyclic model

The fixed model returns verified SAT at 5 words, UNKNOWN at 10 words, and UNSAT
at 25 and 50 words. Only observed word count changes across these checks.

## Span and assumptions

The earlier f1r five-word sample cannot be extended to 50 clean contiguous words
without crossing an uncertain reading. Skipping that word would change text-wide
cycle phases. This runner instead selects the earliest 50-word run of paragraph
text on one folio with eligible basic EVA readings and no uncertain comma spaces.
It does not skip excluded words, labels, uncertain spaces, or folio boundaries.

The selected span is on **f3r**, source record indices **473–522**, from locus
`f3r.1,@P0` to `f3r.11,+P0`. It begins:

```text
tsheos qopal chol cthol daimg ycheor chor dam qotcham cham
```

All samples start at record 473. The 5-, 10-, and 25-word samples are exact
prefixes of the 50-word sample. Source locations, normalization, source checksum,
corpus identity, exact record indices, and sample checksums are saved. Paragraph
text may cross line and paragraph divisions; the selector continues across them.
This is a new baseline and should not be conflated with the earlier f1r fit.

Fixed model settings:

- All **5,665** acquired Latin surface vocabulary entries after the existing
  single-letter a/e/i/o whitelist; independent dictionary membership per word.
- The same 24-symbol plaintext alphabet, with u/v distinct, and full 25-unit
  eligible EVA character alphabet at every size.
- Prefix-free verbose homophonic codes, **at most two codes per plaintext letter**,
  each **1–2 EVA character units** long.
- One inferred ordered cycle per letter; counters continue across spaces, lines,
  and paragraph boundaries. First observed occurrences use code 0. Inferred order
  permits per-letter cyclic rotations, absorbing unknown phases before this span.
- Preserved word boundaries; disabled nulls and contextual code mappings;
  feasibility rather than optimization.
- Finite representation and a **30-second Z3 timeout**, unchanged across sizes.

EVA character units are the declared convention, not resolved manuscript glyphs.
The vocabulary retains other surface artifacts, names, numerals, and possible
source errors. It is not an unrestricted Latin lexicon or a grammatical model.

## Results

| Words | EVA units | Last locus | Result | Solver check seconds | Construction seconds | Total wall seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | 25 | f3r.1,@P0 | SAT, independently verified | 1.912 | 0.958 | 2.882 |
| 10 | 49 | f3r.2,+P0 | UNKNOWN, timeout | 30.043 | 2.263 | 32.314 |
| 25 | 115 | f3r.5,+P0 | UNSAT | 3.473 | 6.566 | 10.048 |
| 50 | 240 | f3r.11,+P0 | UNSAT | 16.879 | 21.638 | 38.527 |

The five-word explanation is `pudor eas nos quos rheni`. Its complete recovered
key and cyclic choices independently reproduce and decode the observed prefix.
It is an example of dictionary-constrained feasibility, not a proposed translation.
UNKNOWN exports no plaintext or key. The timeout governs Z3's check, not Python
construction, and is a soft limit in the tactic pipeline.

UNSAT excludes every explanation in this exact model for the corresponding
prefix. In particular, a grammatical sequence using only this vocabulary would
also be excluded: adding grammar constraints cannot restore feasibility. It does
not exclude Latin words outside this vocabulary, other selector rules, larger
code/homophone bounds, or a different glyph-unit model.

The observed transition is verified SAT at 5 words to proved UNSAT at 25 words.
The 10-word result remains undecided; no exact threshold has been located.
A longer contiguous prefix must satisfy all earlier-prefix constraints, so the
25-word exclusion also logically applies to the 50-word prefix. Both cases were
nevertheless checked directly and returned UNSAT.

Solver times need not rise monotonically with sample size. More observed words
add shared-prefix and repeated-word constraints on the same key. The sound public
prefix graph pruned 4,424 candidate entries at 25 words and 13,555 at 50 words;
it recorded 66 and 162 relations respectively. These are ciphertext-derived
consequences of the fixed model, not changes to the public vocabulary or bounds.
The 10-word case left a harder unresolved search at the chosen timeout.

This run addresses sample-size scaling. Prior full-vocabulary synthetic gates
remain incomplete, as documented in [the vocabulary frontier](latin_frontier.md).
These bounded exclusions do not supply a probability for the manuscript's language.

## Reproduction

```sh
uv run python benchmarks/sample_scaling.py
uv run python benchmarks/sample_scaling.py --resume
uv run voynich-smt compare experiments/results/sample-scaling.json
uv run voynich-smt solve data/generated/sample-scaling/inputs/words25.json \
  --output experiments/results/sample-scaling-25-replay.json
uv run pytest -q
```

The versioned runner configuration is
`experiments/configs/sample-scaling.json`. CLI options include `--config`,
`--output`, `--artifact-dir`, and `--resume`. Resume verifies identical configuration,
fixed model, corpora, selected maximum span, and environment before reusing checks.
Changing the maximum requested size may select a different earliest clean span;
treat such a configuration as a new experiment, not an extension of this report.

Checkpointed results are in `experiments/results/sample-scaling.json`.
`data/generated/sample-scaling/inputs/` contains truth-free, standalone public
requests. `samples/` contains exact sample records and the maximum span. Every
request uses the identical serialized dictionary, bounds, alphabets, timeout,
and selector; only `ciphertext` differs. A fixed-model checksum accompanies each
result. All generated datasets/results remain local and excluded from version control.

The suite passes **300 tests**. New tests check uninterrupted selection, exclusion
and folio boundaries, nested prefixes, identical non-ciphertext request fields,
checkpoint resume, UNKNOWN handling, and invalid size progressions.
