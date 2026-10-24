# Preserved-space comparison within 25 output labels

The follow-up to the [52-symbol diagnostic](currier_selection_comparison.md)
now respects the 25 atomic EVA output-label limit. **Sparse homophony provides
no consistent advantage over monoalphabetic substitution in these samples.**
Word-length discrepancies persist because all codes have width one and preserve
spaces. This rules out neither language nor homophonic mechanisms generally.

## Frozen design

The original 24 Currier A/B folio packets, 72 natural passages, source
normalization, development/held-out split and three key seeds are reused.
There are four arms: monoalphabetic or frequency-allocated homophonic codes,
each with independent or deterministic word selection. All preserve spaces;
there are no nulls, contractions, expansions or renewed boundaries. **864 records**
were generated and scored; no Z3 calls or parameter tuning were made.

Every source character gets one distinct output glyph. The homophonic arm
allocates spare glyphs to the most frequent characters in the development
passages only, breaking ties lexically. The full source alphabet remains public,
but held-out character frequencies do not determine allocation. Glyph assignment
uses seeded permutations of the same 25 EVA labels. Codes are globally unique
and one glyph long, so decoding is unambiguous.

| Source | Plaintext alphabet | Spare labels | Characters receiving a second homophone |
| --- | --- | --- | --- |
| Caesar | 23 | 2 | e, i |
| Aquinas | 22 | 3 | e, i, t |
| Middle Bavarian | 25 | 0 | None |

Monoalphabetic codes use fewer than 25 labels where appropriate. The allocated
codes use all 25 in their inventory, although short passages need not emit every
label. Independent choice is uniform among the available homophones. Stable
word selection uses the previous SHA256(seed, whole word, letter position) rule,
modulo the character's homophone count. This is an instrument rule, not a claimed
historical implementation. The same word always yields the same payload.

The deterministic/independent mono arms coincide exactly, as do all four German
arms. These intentional degeneracies are checks, not independent confirmations
or four different German hypotheses. There are 216 source/target/key fixtures,
with four records per fixture, not 864 independent manuscript observations.

## Held-out findings

All four arms have identical token-length distributions for each fixture.
Preserved mean lengths remain Caesar 6.33 / 6.06, Aquinas 5.85 / 5.26 and German
4.40 / 4.18 for A / B, compared with selected Voynich packet means 4.99 / 5.44.
No allocation or selection rule can repair these length differences without
changing character units, code widths or word boundaries.

The following table gives mean absolute repeat-pair rate error. Smaller means
closer to the paired Voynich sample; it is not a likelihood or significance test.

| Source and class | Mono | Allocated independent | Allocated deterministic |
| --- | --- | --- | --- |
| Caesar A | .0116 | .0122 | .0116 |
| Caesar B | .0074 | .0067 | .0074 |
| Aquinas A | .0071 | .0105 | .0071 |
| Aquinas B | .0068 | .0050 | .0068 |
| German A | .0098 | .0098 | .0098 |
| German B | .0074 | .0074 | .0074 |

Independent sparse homophony worsens repeat agreement in A and improves it in B
for both Latin sources. Deterministic homophony preserves exactly the plaintext
word-frequency spectrum, just as monoalphabetic substitution does: unique glyph
codes prevent two different plaintext words from becoming identical ciphertext.
Its unchanged repeat rate is a structural result, not a recovery success.

Near-variant results also trade off. Independent sparse homophony slightly
improves Caesar near-pair agreement in both classes and Aquinas in A, but worsens
Aquinas in B. Deterministic sparse homophony worsens this near-pair measure
relative to mono in all four Latin held-out groups.

Both allocated Latin selection rules reduce word-position mutual-information
error relative to mono. However, frequency-rank position divergence worsens in
all four Latin held-out groups. Agreement on one positional statistic therefore
does not identify a mechanism. Small clean-line packets, rank ties and biased
empirical mutual information remain limitations. No composite score is used.

This tests one sparse allocation rule, one German variety and the retained
normalizations. A larger output alphabet, contractions, expansion, alternative
normalization or ambiguous/non-prefix-free models change the tested hypothesis.
The 25-symbol source inventory is not evidence that a historical scribe used
exactly that inventory. Null mechanisms were omitted because this comparison
allocates the full budget to payload in the homophonic arms; sharing null labels
with payload would require a different decoding rule.

## Artifacts and checks

[Prepared protocol](../experiments/results/currier-alphabet-comparison/prepared.json),
[report](../experiments/results/currier-alphabet-comparison/report.json),
[all metric distances](../experiments/results/currier-alphabet-comparison/comparison.csv),
and [independent validation](../experiments/results/currier-alphabet-comparison/validation.json).

Independent validation verifies frozen source/code hashes, development-only
allocation, alphabet capacity and code uniqueness, inverse decoding against the
original real passages, deterministic word-frequency preservation, identical
mono/German arms, identical token lengths, type histograms, within-line adjacency
and position count totals. It independently recomputes exact repeats and every
near-pair statistic using full Levenshtein distance. Eight focused tests across
the three comparison benchmarks pass. Earlier frozen records are unchanged.

```sh
.venv/bin/python -m benchmarks.currier_alphabet_comparison
.venv/bin/python -m benchmarks.validate_currier_alphabet_comparison
.venv/bin/python -m pytest -q tests/integration/test_currier_alphabet_comparison.py
```

## Next recommendation

Park further allocation/selection variants for now. These paired screens are
not calibrated to distinguish mechanisms: a closer single metric is not a
reliable hypothesis ranking. The next useful check is a **blinded synthetic
classification test** for this existing frozen grid, using fresh passages and
keys: can the measured features distinguish known preserved-space mono,
sparse homophonic and renewal-generated mechanisms on held-out source passages?
Keep equivalent mono/German arms merged, and allow an unresolved outcome rather
than choosing a winner. If known mechanisms cannot be distinguished, stop using
these distances to prioritize manuscript mechanisms. This calibrates the new
feature vector, not the earlier solver-recovery experiments.
