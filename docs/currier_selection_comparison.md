# Fixed one-glyph homophones and stable word selection

This follow-up removes the expansion cost from the
[paired Currier mechanism screen](currier_mechanism_comparison.md), then compares
independent homophone choices with deterministic choices for each plaintext
word. **Expansion was a substantial confound. Nulls are no longer uniformly
worse, but no arm establishes an overall manuscript match.** Stable selection
restores repeated words without consistently improving repeat-rate agreement.

## Capacity caveat and frozen protocol

Two distinct one-glyph homophones per character require 46 payload labels for
Caesar, 44 for Aquinas and 50 for the Middle Bavarian source. The previous 25-label
EVA alphabet cannot accommodate these codes, even before reserving nulls.
Consequently this is a **52-symbol diagnostic**, not a feasible 25-label cipher
hypothesis. Each `gNN` symbol counts as one abstract glyph, never three printed
characters. Two of the 52 labels are reserved for nulls; some payload labels are
unused in Latin. Alphabet size, homophone allocation and glyph-position profiles
are therefore confounded in comparisons with the earlier mixed-width experiment.
Length comparisons isolate the expansion cost more directly.

The 24 folio targets, 72 real passages, source normalization, three key seeds,
A/B labels and development/held-out splits are reused exactly. Six held-out
folios per class remain selected clean-line packets, not the whole manuscript.
Word and line geometry, null budgets/placements and renewal rules are unchanged.
No parameters were tuned to the new results.

Each source uses two distinct one-glyph codes per plaintext letter, globally
unambiguous. Independent selection is iid uniform. Deterministic selection uses
SHA256 of the fixed seed, whole plaintext word and letter position, modulo two.
The same plaintext word always produces the same preserved-space payload,
regardless of its context or position. This is a reproducible statistical
selection rule, not a proposed historical hash cipher or a simple historical
cycle. Inserted nulls and renewed boundaries can still break whole-word equality.

There are **432 payload fixtures and 3,456 metric records**: two selection rules
and all eight original profiles. Word-length token distributions are identical
between selection rules for every paired profile. Type distributions, repetition,
near-variants and glyph positions can differ. All metrics remain separate;
there is no combined fit score, posterior probability or fitted key.

## Held-out results

Lower Jensen–Shannon divergence means closer empirical token-length distributions.
It is identical for both selection rules, since codes all have width one.

| Source | Preserved mean A / B | Preserved token-length JS A / B | Positional 10% null JS A / B | Renewal-6 JS A / B |
| --- | --- | --- | --- | --- |
| Caesar | 6.33 / 6.06 | .263 / .202 | .247 / .213 | .333 / .376 |
| Aquinas | 5.85 / 5.26 | .218 / .207 | .219 / .172 | .321 / .397 |
| Middle Bavarian | 4.40 / 4.18 | .255 / .235 | .189 / .194 | .368 / .409 |

Selected Voynich packets average 4.99 for A and 5.44 for B. Removing expansion
improves preserved length divergence for both Latin sources in A/B. Middle
Bavarian becomes too short on average and its preserved divergence worsens
slightly in A and more in B. Positional 10% nulls improve German length divergence
in both classes, and Aquinas in B. Thus **the previous observation that every null
variant worsened length compatibility does not generalize across code widths**.
This does not select a language: Latin and German now trade places on some metrics.

Renewal-6 approaches the mean, yet has mean absolute variance errors of
15.38–16.26 for A and 18.81–20.43 for B. Preserved spaces have smaller variance
errors for every source/class. Renewal token-length divergence is worse than
preserved spaces for all six source/class combinations in this fixed-width grid.

Deterministic preserved-space selection reduces repeat-pair absolute error for
all three A source groups, most strongly Aquinas (.0132 to .0071). In B it helps
Aquinas slightly but worsens Caesar and German. Near-variant pair errors worsen
under deterministic preserved selection in all six held-out groups. Word-position
mutual-information errors improve, but the enlarged alphabet and small empirical
samples make this an instrument diagnostic, not a calibrated significance test.

The restored repeated words do not establish a Voynich-like distribution of
near-variants. A deterministic word mapping preserves the plaintext's word
repetitions exactly; it cannot freely change their frequencies. Independent
selection changes these repeats, particularly for longer words.

## Artifacts and validation

[Prepared protocol](../experiments/results/currier-selection-comparison/prepared.json),
[report](../experiments/results/currier-selection-comparison/report.json),
[comparison CSV](../experiments/results/currier-selection-comparison/comparison.csv),
and [independent validation](../experiments/results/currier-selection-comparison/validation.json).
Per-fixture records contain the encoders, generated words, glyph positions,
token/type length moments and all metric distances. Counting and metric
definitions are inherited from the original screen.

Validation checks source/code provenance, one-glyph code uniqueness, independent
inverse decoding against the original passages, equal payload lengths across
selection rules, deterministic repeats, null identities/budgets and payload
restoration, renewed glyph streams, histograms and adjacency boundaries. Exact
repeat rates and near-variant statistics are independently recomputed for every
record; the latter uses full Levenshtein distance rather than the optimized
one-edit predicate. The original frozen benchmark and results are unchanged.

```sh
.venv/bin/python -m benchmarks.currier_selection_comparison
.venv/bin/python -m benchmarks.validate_currier_selection_comparison
.venv/bin/python -m pytest -q tests/integration/test_currier_selection_comparison.py
```

## Next recommendation

Resolve the alphabet constraint before another Z3 campaign. A small paired screen
with a **25-label monoalphabetic baseline without reserved nulls** and a
**25-label variable-allocation homophonic model without reserved nulls** would
separate label capacity from the length/repetition effects. The latter gives every
plaintext character at least one glyph, allocating only remaining labels as extra
homophones by a frozen source-frequency rule. Caesar has two spare labels,
Aquinas three, and this German alphabet none: full H2 is unavailable. Null variants
need either a larger alphabet, a smaller justified plaintext inventory or an
explicitly ambiguous/reversible null mechanism; simply sharing labels is not
an unambiguous cipher. Keep contractions as a separate dimension rather than
quietly using them to solve the alphabet shortage.
