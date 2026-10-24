# Necessary length and exact-repetition constraints

This returns from the parked [transfer classifier](currier_mechanism_transfer.md)
to **properties that a specified model must satisfy**. The main hard result
confirms the earlier width audit separately for Currier A/B: fixed two-glyph
output per plaintext unit cannot cover these word-separated samples. Around half
the words have odd lengths, and no eligible 22-word window passes divisibility.
Mixed widths including one remain arithmetically feasible; that does not establish
a key or language. Exact repeats supply an additional constraint, with precise
conditions below.

## Model contracts

Write U for a plaintext **unit word** after any explicitly specified reversible
contraction/normalization, C for its ciphertext word, and L for its output-unit
length. The following statements assume corresponding preserved word boundaries,
nonempty codewords and unique inverse decoding. They concern the same aligned
sample, not independently chosen natural-language corpora.

| Model | Necessary length property | Necessary exact-repeat property |
| --- | --- | --- |
| One-glyph substitution, no nulls | L = number of plaintext units | Deterministic output preserves every word-frequency count |
| Fixed width k, no nulls | L = k × plaintext-unit count; every L divisible by k | Deterministic selection preserves frequency spectrum; varying selection can split repeated words |
| Mixed widths a…b, no nulls | ceil(L/b) ≤ plaintext-unit count ≤ floor(L/a), plus exact reachability for the allowed widths | Same C must decode to same U; varying selection cannot merge distinct U |
| Deterministic whole-word homophone selection | Width constraints above still apply | Frequency spectrum, type count and equal-word-pair count are exactly preserved |
| Context-dependent or iid selection | Width constraints above still apply | Ciphertext type count ≥ plaintext type count; equal-ciphertext pairs ≤ equal-plaintext pairs |
| Unambiguously removable inserted nulls | L includes payload plus nulls; original divisibility need not survive | Same C still implies same U; deterministic complete word output preserves repeats, random nulls may split them |
| Reversible contractions before encoding | Bounds count contracted units, not raw letters | The invariant concerns contracted unit sequences; raw-word claims require the preprocessing itself to be injective |
| Removed/generated word boundaries | Original token length constraints no longer apply to emitted words | No tokenwise type/repeat invariant without recovering the original boundaries |

For a known width inventory W, the exact admissible input-unit counts are those
n for which L is the sum of n widths from W. The reported minimum/maximum totals
sum only compatible word occurrences. If even one occurrence is incompatible,
that subtotal is **not** a whole-sample explanation.

For exact repeats, let N be the aligned token count, V the number of distinct
words and E = Σ choose(frequency,2). Unique decoding makes each ciphertext type
belong to exactly one plaintext type. Splitting a plaintext word's occurrences
across ciphertext variants gives V_C ≥ V_U and E_C ≤ E_U. A deterministic
injective whole-word map instead gives equality of the entire multiset of
frequencies, not just approximately similar common-word rankings. Thus repeated
ciphertext requires repeated plaintext in the same positions, even when a cipher
uses homophones. Unrelated language corpora need not have identical spectra.

These statements do not hold as written for ambiguous/non-prefix-free decoding,
noninjective preprocessing, word deletion, uncertain reconstructed spaces or
other mechanisms that break the assumed inverse/word alignment. A positional
marker sharing a payload label can still be removable under an explicit known
rule; it is not the same model as a reserved null label.

Contractions can relax raw-letter length ceilings: if each plaintext unit expands
to at most K letters, raw letters ≤ K × floor(L/a) without nulls. The actual
inventory and legal unitizations impose tighter constraints. Output expansion
alone cannot shorten unit words. This report adds no new contraction inventory.

## Corpus census and filtering

Metadata `$L=A/B` identifies Currier classes in the cached ZL transcription;
only paragraph loci are considered. There are 11,337 labelled A paragraph records
and 23,188 B records before these exclusions. Two cohorts make filtering visible:

* **Whole-clean-lines:** exclude a complete line if any word is invalid or spacing
  is uncertain. Retains 4,391 A tokens and 9,108 B tokens, about 39% overall.
* **Clean-words:** retain individually clean words in otherwise damaged lines,
  still excluding records from uncertain-spacing loci. Retains 6,125 A and 11,350 B
  tokens, about 51% overall. Invalid records remain barriers to contiguous windows.

Both cohorts exclude unlabelled and nonparagraph records. Neither is a complete
all-annotations transcription census, and a biased transcription filter can
change the estimated distributions. The sensitivity comparison does not remove
that limitation.

Counts use both atomic EVA characters and the existing greedy reversible grouping
of `cth`, `ckh`, `cph`, `cfh`, `ch`, `sh`. These are counting conventions, not proven
historical glyph identities. Grouping preserves each original word string exactly,
so it changes lengths but cannot change exact equality or word frequencies.

## Word lengths with folio sampling sensitivity

Intervals below are 95% percentile intervals from 1,000 folio-cluster resamples.
Every folio's words stay together. They describe heterogeneity under an
exchangeable-folio sampling model, not uncertainty over glyph interpretation,
transcription errors, scribal selection or the complete historical manuscript.

| Cohort / units | A mean (interval) | B mean (interval) |
| --- | --- | --- |
| Whole clean lines / atomic | 5.051 (4.976–5.123) | 5.347 (5.258–5.432) |
| Clean words / atomic | 5.009 (4.940–5.081) | 5.333 (5.244–5.405) |
| Whole clean lines / grouped | 4.332 (4.251–4.417) | 4.847 (4.769–4.919) |
| Clean words / grouped | 4.302 (4.223–4.381) | 4.835 (4.758–4.904) |

B's higher mean is stable across both filters and conventions. Earlier 4.73
ceilings concerned a particular pilot block; they are not manuscript-wide means
or universal bounds. The atomic/grouped difference is materially larger than
these folio resampling intervals.

For the broader clean-word cohort:

| Currier / units | Odd lengths | One-unit words | Eligible 22-word windows | Fixed-two compatible windows |
| --- | --- | --- | --- | --- |
| A atomic | 51.1% | 2.29% | 416 | 0 |
| B atomic | 50.3% | 0.77% | 1,724 | 0 |
| A grouped | 54.7% | 2.42% | 416 | 0 |
| B grouped | 49.8% | 0.78% | 1,724 | 0 |

Whole-clean-line windows also have zero fixed-two survivors (308 A and 1,481 B).
Windows may cross consecutive included lines within a folio but never excluded
records/loci or folios. Their heavy overlap means they are not independent trials.
Fixed-three likewise fails to explain the whole cohort. Mixed-one-two and
mixed-one-two-three admit every positive output length arithmetically. Mixed-two-three
fails on one-unit words. These are necessary arithmetic checks only; free choices
of widths do not imply a globally consistent codebook.

## Exact repeated words

The broader cohort has 2,108 distinct A words and 2,911 distinct B words. Full
frequency spectra, token/type length histograms, per-folio summaries and
22-word-window repeat-pair histograms are saved in the report.

| Cohort | Global equal-pair rate A / B | Within-folio equal-pair rate A / B | Within-folio bootstrap interval A / B |
| --- | --- | --- | --- |
| Whole clean lines | .00576 / .00448 | .00882 / .00776 | [.00710,.01112] / [.00670,.00884] |
| Clean words | .00555 / .00429 | .00823 / .00740 | [.00692,.00980] / [.00644,.00840] |

An equal-pair rate is the proportion of unordered pairs of observed word tokens
that are identical. The global statistic includes pairs from different folios;
the within-folio statistic sums equal pairs and possible pairs within each
folio, then takes their ratio. It therefore weights larger folios more heavily.
Global spectra and rates are descriptive, without a bootstrap interval.

A has higher observed repeat rates, but within-folio intervals overlap. Do not
promote that difference into a strong source/language conclusion. The bootstrap
resamples **within-folio pair counts**, never concatenating duplicated folios
into a global word stream; concatenation would fabricate cross-copy repeats.
Atomic and grouped exact-repeat counts are identical, as required by reversible
grouping. Slight interval differences across counting conventions are Monte Carlo
variation from separately seeded resamples, not a change in the repeat statistic.

## What this decides

* Exact two-glyph-per-unit models with preserved spaces and no nulls cannot cover
  either filtered class, under either tested counting convention. This confirms
  rather than overturns the earlier width audit.
* One-glyph and mixed widths including one survive these arithmetic checks.
  Necessary feasibility is not successful decryption.
* Deterministic whole-word substitution cannot independently adjust a candidate
  passage's repeated-word spectrum. Stochastic selection can reduce exact repeats,
  but cannot manufacture repeated ciphertext from different uniquely decoded
  plaintext unit words.
* Boundary changes and contractions are genuine structural alternatives, not
  simply more solver time for the excluded fixed-two model. Their specific rules
  must be stated before applying these constraints.

No language is excluded by comparing these observations with an unrelated source
corpus average. No assumption that Voynich's most common word must be `et` or `est`
is introduced. The exact constraints apply to an aligned candidate passage;
frequency priors over possible passages remain statistical assumptions.

## Next recommendation

Use these contracts as a cheap **joint length-and-repeat passage filter** on
predeclared A/B windows and cached natural texts, with known synthetic controls.
Compare letters with the already documented reversible contraction inventory;
retain all legal unitizations and require repeated ciphertext positions to share
plaintext. Freeze window selection rather than choosing a block after observing
survivors. Surviving passages are only candidates for a later common-key test;
zero survivors exclude the finite tested corpus/model, not Latin or German in
general. Do not return to the parked classifier to interpret these filters.

## Artifacts and verification

[Prepared protocol](../experiments/results/currier-structural-constraints/prepared.json),
[full census, histograms and intervals](../experiments/results/currier-structural-constraints/report.json),
and [independent validation with concrete width counterexamples](../experiments/results/currier-structural-constraints/validation.json).
README and structural coverage map link this report. No prior frozen result was
changed and no Z3 calls were made.

The independent validator reconstructs eligibility directly from locus records,
checks frequency spectra and global/within-folio pair totals, calculates reachable
unit counts with an independent dynamic program, verifies window totals and
exact repetition identity across groupings, and saves explicit odd-word witnesses.
Focused tests check exclusion barriers, width constraints and repeat splitting.

```sh
.venv/bin/python -m benchmarks.currier_structural_constraints
.venv/bin/python -m benchmarks.validate_currier_structural_constraints
.venv/bin/python -m pytest -q tests/integration/test_currier_structural_constraints.py
```
