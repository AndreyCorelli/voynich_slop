# Currier length differences after section and line-position matching

**The pooled atomic-EVA A/B length gap is not a robust within-section result.**
On comparable herbal pages, matching paragraph-line role and original word
position reduces the point estimate from +.324 to +.128; its folio-resampling
interval includes zero. Under the existing reversible EVA grouping, however,
the matched gap remains +.386 with an interval above zero. Counting convention
is therefore central to the interpretation.

This qualifies the [shared-parameter prediction audit](currier_shared_parameters.md):
its full-cohort mismatch remains a result under its stated assumptions, but should
not be read as proof that comparable A/B pages require different cipher parameters.
This analysis does not fit a cipher or classify manuscript plaintext.

## Metadata and frozen matching design

The cached ZL transcription retains section `$I`, Currier `$L`, locus text and
original parsed word positions. The raw source explicitly describes `$I=H` pages
as herbal. Other section codes are kept literal rather than inventing a new
historical classification.

The broader clean-word paragraph cohort is primary; whole-clean-lines and the
existing greedy reversible EVA grouping are prespecified sensitivities. Filters
are the same as the structural census. Original line positions are assigned
**before** excluding invalid words:

* Word position: first, interior, last or single-word line.
* Paragraph-line role: explicit `<%>` marker means initial, `<$>` means final,
  both mean single, neither means unmarked. Unmarked is not assumed to prove an
  interior paragraph line.
* Section: the cached `$I` code.

A section needs at least five distinct A and five B folios. A supported matched
stratum additionally needs at least ten tokens and five folios in each class.
These thresholds are fixed before scoring. Matching uses the same pooled A+B
token weights for both classes. Weights and common support stay fixed during
1,000 independent-by-class folio cluster resamples; draws missing a fixed
stratum would be skipped and attempts reported. All actual analyses needed
exactly 1,000 attempts. Intervals describe an exchangeable-folio resampling model,
not causal identification or all transcription/glyph uncertainty.

This is descriptive standardization on the same manuscript census, not another
held-out predictive classifier or an independent experiment. It controls these
coarse categories, not every page layout, illustration, scribe, paragraph order,
line length, vertical coordinate or topic.

## Section overlap is limited

Primary clean-word counts:

| Section code | A tokens / folios | B tokens / folios |
| --- | --- | --- |
| H (herbal) | 4,637 / 95 | 1,722 / 32 |
| T | 122 / 1 | 878 / 5 |
| S | 327 / 2 | 5,068 / 23 |
| P | 1,039 / 16 | 0 / 0 |
| B | 0 / 0 | 3,410 / 19 |
| C | 0 / 0 | 272 / 4 |

Only H meets the common-section threshold. There is no supported manuscript-wide
adjusted A/B estimate covering all these sections. T/S are not extrapolated from
one or two A folios, and B-only/P-only sections do not supply within-section A/B
comparisons. This lack of overlap is a substantive limitation, not a missing value
to be filled by a regression.

The full position-matched primary comparison retains 4,634 A words from 95 folios
and 1,722 B words from 32 folios: **75.7% of A but only 15.2% of B ** clean-word tokens.
Three A single-position records lack sufficient common support. Nine strata
(initial/final/unmarked × first/interior/last) remain. Strict-line sensitivity
retains 3,401 A and 1,120 B words on the same folio counts, covering 77.5% and 12.3%
of that cohort. Thus results chiefly concern herbal pages, not every Currier B page.

## Atomic-EVA results

B-minus-A mean output-unit length:

| Adjustment | Clean-word estimate (95% interval) | Whole-clean-line estimate (95% interval) |
| --- | --- | --- |
| None, full cohort | +.324 | +.296 |
| Common section H | +.117 (−.035 to +.301) | +.070 (−.094 to +.254) |
| H + original word position | +.138 (−.013 to +.317) | +.099 (−.053 to +.278) |
| H + paragraph-line role + word position | **+.128 (−.022 to +.305)** | **+.083 (−.082 to +.258)** |

The fully matched clean-word means are A **4.957** and B **5.086**. Most of the change
from the pooled point estimate occurs when restricting to comparable sections;
line-role/word-position adjustment changes the herbal point estimate relatively
little. Because population support and weighting change, this reduction is **not**
a causal claim that section explains a particular percentage of the original gap.

Zero is compatible with the atomic matched intervals. That is neither proof of
identical A/B distributions nor evidence that a shared stationary cipher succeeds.
These intervals also allow a moderate positive residual difference. Exact repeat
rates, full length shapes and actual deciphering predictions are not tested by
this mean adjustment.

## Grouped sensitivity

The existing grouping merges `cth, ckh, cph, cfh, ch, sh` reversibly within words.
The matched records, strata and weights remain identical.

| Adjustment | Clean-word estimate (95% interval) | Whole-clean-line estimate (95% interval) |
| --- | --- | --- |
| None, full cohort | +.532 | +.516 |
| Common section H | +.359 (+.223 to +.522) | +.303 (+.155 to +.472) |
| H + original word position | +.392 (+.259 to +.552) | +.341 (+.202 to +.500) |
| H + paragraph-line role + word position | **+.386 (+.253 to +.548)** | **+.331 (+.181 to +.474)** |

The fully matched primary grouped means are A **4.194** and B **4.580**. A genuine
positive residual in this counting convention survives both filtering cohorts.
It is a descriptive structural difference, not a language/cipher identification.

The discrepancy between conventions has an exact explanation:

* Grouping saves .764 units per matched A word and .505 per B word.
* Therefore grouped contrast = atomic contrast + (.764 − .505).
* The extra **.258** mainly comes from A's greater savings in `cth` (+.107 A−B)
  and `ch` (+.105 A−B), with smaller contributions from the other groups.

Strict-line data give the same pattern, with an additional .249. These savings
are actual measured substring-composition effects under the fixed grouping, not
estimated plaintext contractions. Grouped tokens have not been established as the
historical cipher's atomic symbols. Choosing atomic or grouped counting solely to
obtain a desired A/B result would be inappropriate.

## What this means for shared-parameter hypotheses

The full-cohort atomic length gap alone is weak evidence that A/B require different
cipher parameters: section composition and lack of overlap materially change it.
Conversely, the grouped within-herbal gap remains a constraint a model using
those output units should predict. One shared cipher can still produce differing
glyph composition from different plaintext composition; this analysis supplies
no source distribution or recovered key to demonstrate that explanation.

Keep both conventions visible. The next useful measurement is the **within-herbal
A/B difference in these specific grouped sequences and word-length distributions**,
with page/line effects retained, rather than fitting a Currier-specific scalar
length parameter. This would characterize what a shared model must reproduce:
not merely a mean gap, but which output structures differ on comparable pages.
No new cipher model or historical interpretation is inferred here.

## Artifacts and validation

[Prepared protocol](../experiments/results/currier-section-position/prepared.json),
[full section census, strata and intervals](../experiments/results/currier-section-position/report.json),
and [validation and grouping decomposition](../experiments/results/currier-section-position/validation.json).

Independent validation reconstructs locus eligibility and original positions,
checks unadjusted/matched means, common support, pooled weights and coverage, and
verifies the grouping decomposition algebraically. Tests check explicit markers,
filtering boundaries and removal of a pure composition difference by fixed-stratum
standardization, including its bootstrap. Earlier frozen experiments are unchanged;
README and structural coverage map are updated. No Z3 calls were made.

```sh
.venv/bin/python -m benchmarks.currier_section_position
.venv/bin/python -m benchmarks.validate_currier_section_position
.venv/bin/python -m pytest -q tests/integration/test_currier_section_position.py
```
