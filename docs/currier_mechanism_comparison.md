# Paired mechanisms, separately for Currier A and B

The four proposed mechanisms have now been generated and scored on cached real
Caesar, Aquinas and Middle Bavarian Kottanerin passages. **No mechanism is a
convincing overall match in this grid.** Adding nulls worsens length compatibility;
independent renewal spacing can approach the mean but produces much too much
length variance. These are descriptive compatibility results, not hypothesis
probabilities, plaintext recovery or a fitted manuscript cipher.

## Frozen experiment

[Prepared protocol](../experiments/results/currier-mechanism-comparison/prepared.json),
[report](../experiments/results/currier-mechanism-comparison/report.json),
[all metric comparisons](../experiments/results/currier-mechanism-comparison/comparison.csv),
and [held-out CDF plot](../experiments/results/currier-mechanism-comparison/heldout-length-cdf.png).

Atomic lowercase EVA characters are the glyph proxies throughout. Currier classes
come from the cached ZL transcription's page metadata `$L=A/B`. Paragraph lines
with any uncertain spacing or invalid word are excluded, as are unlabelled pages.
Complete clean lines are accumulated within a folio into packets of at least
32 words. The initial 64-consecutive-word plan had no eligible A packets;
64 words even across clean lines did not support six folios per split. This
feasibility adjustment preceded generation and scoring. Omitted lines never
contribute adjacency pairs. This strict selection is **not a representative
full-transcription estimate**.

Six development and six held-out distinct folios per class are sampled using
fixed seeds and a SHA256 folio split. Natural source passages are nonoverlapping,
with held-out passages in the second half of each source. Each passage supplies
the same word count and line geometry as its paired target. Target geometry is
conditioned on, not independently predicted. Existing source normalization is
retained, including the legacy German normalization; this is one variety, not
all German dialects.

Three keys per passage give **216 paired payloads and 1,728 scored variants**.
Each plaintext character has two randomly chosen prefix-free homophones of
one or two atomic glyphs. The output alphabet is the 25 clean EVA labels;
two labels are reserved for nulls. Code choices are independent and uniform,
with no contractions or language-frequency tuning. Exact one-glyph-only codes
were not tested here, so expansion costs can drive part of the mismatch.

The eight reported profiles cover four mechanisms:

| Mechanism | Frozen variants |
| --- | --- |
| Preserved spaces, no nulls | Shared payload baseline |
| Independent nulls | 10% and 30% of payload glyph count; uniform distinct complete-code gaps |
| Positional nulls | Same exact budgets and null identities; word ends, then starts, then internal gaps backwards |
| Removed spaces, generated boundaries | Per-line renewal cuts at each glyph gap with probability 1/4, 1/6 or 1/8 |

The last arm preserves glyph streams and lines but can split codewords. It is a
statistical generator, **not reversible recovery of original plaintext spaces**.
Nulls never split a codeword, and removing their reserved labels restores the
identical payload. Parameters were frozen before scoring; all variants are
reported rather than choosing a best setting after seeing held-out results.

## Main held-out observations

Means below average packets equally; key seeds are repeated measurements on the
same passages, not independent manuscript samples. Selected A packets average
4.99 atomic glyphs per word; selected B packets average 5.44.

| Source | Preserved mean A / B | Token-length JS A / B | Renewal-6 mean A / B | Renewal-6 variance absolute error A / B |
| --- | --- | --- | --- | --- |
| Caesar | 9.60 / 9.24 | .434 / .428 | 5.12 / 5.30 | 16.06 / 18.88 |
| Aquinas | 8.94 / 8.02 | .352 / .261 | 5.06 / 5.23 | 16.26 / 18.48 |
| Middle Bavarian | 6.95 / 6.62 | .252 / .173 | 4.97 / 5.17 | 15.73 / 18.36 |

Jensen–Shannon divergence uses base-2 logs: zero means identical empirical
length distributions. Mean agreement in renewal-6 therefore hides a substantial
shape mismatch. Renewal-4 reduces variance error but gives means only 3.42–3.52.
German preserved spaces have better length divergence than any renewal variant
for both classes. Latin sometimes improves under renewal, but not uniformly
across sources/classes or other metrics.

Both null mechanisms increase mean length by exactly their matched budget.
Every null variant worsens token-length divergence against its own preserved
baseline on held-out A and B. Positional placement can reduce the discrepancy
in word-position mutual information relative to independent placement; that
isolated improvement does not repair the length mismatch or establish nulls.

Within-line adjacency correlations, repeated-word rates and one-edit near-variant
rates do not nominate a common winner across the grid. A change in boundaries
also changes word count, so raw repeat/type rates are size-sensitive. Independent
homophone choices largely suppress repeated ciphertext words; deterministic
word-level selection is a separate untested variant of this comparison.

## What is measured and checked

Each record includes token and distinct-type length histograms and moments
(population variance and standardized third central moment), within-line adjacent
length correlation, adjacent exact repeats, repeated-token fraction, all-pair
exact repeat rates, and one-edit near-variant rates weighted by tokens and types.
Near variants permit one insertion, deletion or substitution, excluding exact
matches. Undefined correlations remain missing.

Glyph frequencies are recorded in four word-relative glyph bins and four
line-relative word-position bins. Comparisons include mutual information and
frequency-rank profiles rather than equating random cipher labels with EVA
labels. Rank profiles are only a heuristic invariant: ties, missing labels,
small packets and biased empirical mutual information limit interpretation.
Distances remain separate; there is no combined score or posterior ranking.
Type moments are in raw records; the CSV reports type length divergence, token
moment distances and all other scalar distances. CDF plots show lengths 1–25;
full histograms retain the longer tail.

The independent validator checks frozen hashes, disjoint passages/folios,
paired null conservation, resegmented glyph conservation, length histograms,
adjacency boundaries and position count totals. It recomputes every near-variant
statistic using full Levenshtein distance rather than the generation benchmark's
optimized predicate. See [validation](../experiments/results/currier-mechanism-comparison/validation.json).

```sh
.venv/bin/python -m benchmarks.currier_mechanism_comparison
.venv/bin/python -m benchmarks.validate_currier_mechanism_comparison
.venv/bin/python -m pytest -q tests/integration/test_currier_mechanism_comparison.py
```

## Next decision

Do not move these mechanisms into long Z3 runs on these results. The cheapest
informative follow-up is to repeat this paired screen with **one-glyph homophones**
and compare independent versus deterministic homophone selection. That separates
the expansion penalty and repetition penalty from the null/spacing effects.
If boundary generation remains relevant, test an explicitly specified bounded
or state-dependent length rule against renewal, with matched synthetic controls;
do not tune a boundary rule directly to the Voynich length histogram.
