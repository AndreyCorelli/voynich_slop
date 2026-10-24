# Fixed contraction inventory: distribution-capacity audit

The existing seven-rule Latin inventory cannot bridge the length gap for the tested Latin source-frequency benchmarks, even when every permitted contraction is used maximally and every cipher unit emits only one output unit. This is a limit of this inventory and benchmark, not a rejection of contraction-based encoding or Latin generally.

## Fixed inventory and scope

Rules remain `ae`, `per`, `pro`, initial `con`, whole-word `et`/`est`, and final `rum`, with distinct reversible expansions. Compare letters-only, optional ae-only and optional seven-rule profiles. No rules, corpora, glyph groupings or normalization conventions were added. Historical support and mixed-period limitations are inherited from the [documented inventory](latin_contractions.md) and [configuration](../experiments/configs/latin-contractions.json). This combines existing precedents rather than reconstructing an abbreviation system used in Voynich.

Every word receives its minimum attainable input-unit count under optional non-overlapping rules, retaining a reversible witness. This is an optimistic maximum-compression envelope, not a measured rate of scribal use or a globally consistent cipher fit. An output code emits at least one unit per input unit; homophone alternatives do not bypass that floor. Cipher expansion consumes additional length and cannot rescue an already excessive minimum input length.

Seven Latin sources use the cached historical extraction: Caesar, Aquinas, Vita Caroli, Einhard, Gesta Francorum, Philobiblon and Monarchia. Nine cached German varieties are **uncontracted references only**; Latin abbreviation rules are not asserted to be German conventions. German streams retain the legacy parser and known short-form/bracket-fragment caveats rather than the separately corrected solver vocabularies.

Targets are all 37,608 clean cached manuscript word occurrences under atomic EVA and the single existing grouped convention. Uncertain/excluded records are barriers. The grouped convention combines ch/sh and four benched-gallows sequences; neither representation is established as the encoding's true glyph inventory. Source passages, books, exclusion barriers and manuscript folios are never bridged when constructing 22-word windows.

## Seven stages

1. Freeze sources, seven-rule inventory, representations and diagnostics.
2. Audit Caesar under three profiles.
3. Audit Aquinas and Vita Caroli under three profiles.
4. Audit four additional Latin works under three profiles.
5. Record nine German letters-only references.
6. Compare full word-length distributions and mean emission headroom.
7. Compare complete overlapping 22-word-window distributions and assess capacity.

All stages save plans before scoring, with prepared/preceding-result digests. Results contain full histograms and minimum-unit witnesses/frequencies, not just aggregate means. No Z3 call, dependency install or download occurred.

## Mean capacity

Atomic EVA mean is **4.971**; existing grouped mean is **4.464**. Table percentages for further shortening use the already maximally contracted unit count as denominator. They are necessary mean-level bounds for exact source-frequency matching, not historical contraction-rate estimates.

| Latin source | Original mean letters | Best seven-rule mean units | Maximum letter saving | Further shortening needed: atomic | Further shortening needed: grouped |
|---|---:|---:|---:|---:|---:|
| caesar | 6.007 | 5.741 | 4.42% | 13.41% | 22.24% |
| aquinas | 5.598 | 5.320 | 4.97% | 6.56% | 16.08% |
| caroli | 5.702 | 5.488 | 3.76% | 9.42% | 18.65% |
| einhard | 6.017 | 5.740 | 4.61% | 13.39% | 22.22% |
| gesta | 5.786 | 5.555 | 4.00% | 10.50% | 19.63% |
| bury | 6.593 | 6.295 | 4.52% | 21.03% | 29.08% |
| dante | 5.629 | 5.387 | 4.30% | 7.72% | 17.13% |

All seven-rule Latin means remain above atomic EVA. Mean output/input ratios required to match the atomic target are 0.790–0.934, below the model's minimum ratio of one. The grouped target is stricter. These sample means do not identify the manuscript's language: the plaintext could have different genre, vocabulary, frequency distribution or boundary conventions.

## Full-distribution diagnostics

Mean alone misses where capacity is needed. We compare empirical length-frequency marginals using two optimistic diagnostics:

- At each threshold t, compare the fraction of target words no longer than t with the fraction of minimally contracted source words no longer than t. A positive deficit means the source lacks enough short input-unit words to supply that target short tail when output cannot shorten units.
- Couple source and target quantiles monotonically, allowing arbitrary reordering. Integrate `max(source minimum units − target units, 0)` over quantile mass. This is the minimum additional unit removal under an optimistic arbitrary-shortening coupling. It assumes no real contraction rules, key, text order or repetition constraint; it is a capacity lower bound, not an implementable encoder.

For Latin with the seven rules, maximum atomic short-tail deficits range from **16.3 to 29.2 percentage points**, at source-specific thresholds. Optimistic extra removal is **0.684–1.364 input units per word**. These exceed simple mean gaps because some source words are already shorter than the target and cannot donate unused length to longer words. Existing grouped targets show larger deficits. Full thresholds and histogram quantiles are retained in the stage-6 records.

Window comparisons operate on total units in each contiguous 22-word window. Their word-mean quantiles are saved, and deficit/removal diagnostics compare total-window lengths. Removal units in stage 7 are **per window**, not per word. Overlapping windows are descriptive observations, not independent trials. Even arbitrary matching leaves maximum atomic short-window fraction deficits of **21.5–71.9 percentage points** across the seven Latin sources. This is a distribution comparison, not a new aligned-passage or shared-key search.

The exact-frequency benchmark is deliberately strong: it asks whether these empirical source marginals can map to the manuscript marginal without additional shortening. It does not require that an unknown real plaintext have exactly those source frequencies. A failure limits this benchmark; it does not exclude a language or unseen short-word passage.

## German reference and interpretation

The nine uncontracted German means range from **4.225 to 4.849**, all below atomic EVA's 4.971. Thus the average-length concern does not demand contractions under those source/normalization choices. Some short-tail deficits remain, and five references exceed the grouped target mean. No common codebook, grammatical plaintext, language probability or German contraction convention was tested. Legacy normalization caveats prevent treating these as certified diplomatic distributions.

## Decision and next step

Stop this seven-rule inventory: another solver run would not repair its insufficient capacity for the tested Latin frequency benchmarks. The contraction idea remains open because this inventory is small and combines limited precedents.

A broader contraction hypothesis would need an independently documented, finite inventory, frozen before looking at fits, with unique expansion semantics or explicitly bounded ambiguity. It must clear a distribution-capacity gate before hidden-recovery testing. Do not add frequent digraphs merely until the arithmetic passes. If independent justification does not provide sufficient capacity, report that limit rather than widen rules opportunistically. Only a capacity-positive inventory would justify the previous hidden-boundary synthetic prediction proposal with contractions included.

## Reproduce and validation

```sh
.venv/bin/python -m benchmarks.contraction_distribution_audit --run
.venv/bin/python -m benchmarks.contraction_distribution_validation
.venv/bin/python -m pytest -q tests/integration/test_contraction_distribution_audit.py
```

Artifacts: `experiments/results/contraction-distribution-audit/`, including seven plans/results, frozen preparation, word-level witnesses, full histograms, assessment and validation. Existing artifacts are preserved. Benchmark/source-parser/inventory hashes pin the protocol.

Three tests check rational quantile removal, a short-tail deficit despite a lower mean, and window barriers. Independent validation reconstructs minimum unit counts by reverse dynamic programming, witness expansions, all word/window histograms, manuscript grouping/barriers, rational quantile integrals, means and saved plans. The cached historical parsing is reused; it is not independent palaeographic validation.

Validation passed across **16 sources and 30 source/profile rows**: 120,438 independent minimum-word-type checks and 435,236 token occurrences counted across profiles. All three tests passed; zero solver calls.
