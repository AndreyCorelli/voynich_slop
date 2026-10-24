# Can shared parameters predict Currier A/B differences?

**None of the 63 tested candidates matches both the absolute A/B mean word
lengths and their difference.** A stationary shared-source/shared-cipher model
predicts zero systematic length difference, inconsistent with this held-out
cohort's folio-resampling interval. A conditional source-half model sometimes
matches the difference while getting the absolute lengths badly wrong.

This is a test of a finite generator shortlist, **not a test of every shared-key
cipher hypothesis**. No manuscript key has been established. The shortlist
contains feasible one-glyph, sparse homophonic and mixed-width generators, then
an explicit extension using the documented seven Latin contractions. These are
survivors of necessary checks, not validated historical models or grammatical
Voynich decryptions. The broader contraction inventory and alternative boundary
models are not tested here.

The [section/position follow-up](currier_section_position.md) now qualifies the
pooled contrast: the matched atomic gap includes zero on herbal pages, while the
grouped gap remains positive. The candidate predictions here concern the original
full cohort and should not be extrapolated to those adjusted populations.

## What shared parameters do—and do not—predict

If the plaintext-word distribution, preprocessing, encoder, selection rule and
boundary/null mechanism all stay the same, the population A/B distributions are
the same. Homophony, expansion and contractions do not spontaneously create
Currier classes. This statement requires a stationary generative process; shared
parameters in a position-dependent or stateful process need not imply stationary
outputs. Such processes are outside this shortlist.

The same cipher can produce different ciphertext distributions from different
plaintext topics, vocabulary or spelling. Therefore rejecting the stationary
null does **not** reject the possibility of one cipher shared across A/B. It says
that a tested model needs a reason for different input distributions or states,
with predictive content specified independently of the target difference.

Two scenarios keep that distinction visible:

1. **Stationary:** shared parameters and the same latent plaintext distribution;
   expected B-minus-A length and repeat-rate differences are zero.
2. **Conditional source halves:** A draws words from the first half of one cached
   natural text, B from its second half. The key and selection rule are shared,
   but the plaintext distributions differ. This assignment is a diagnostic
   assumption, not historical evidence linking those source halves to Currier.

## Held-out manuscript target

Atomic EVA, paragraph loci and the broader clean-word cohort from the
[structural census](currier_structural_constraints.md) are used. Invalid records
and uncertain-spacing loci remain excluded. Folios are divided by the existing
SHA256 modulo-three rule; development and evaluation share no folios.
Only A development mean length ranks candidates. B never changes a key,
contraction rule, homophone allocation or selection parameter.

| Observable | A development | A evaluation | B evaluation | Evaluation B−A |
| --- | --- | --- | --- | --- |
| Mean word length | 4.967 | 5.048 | 5.362 | +.314 |
| Within-folio equal-word-pair rate | .008215 | .008240 | .007477 | −.000763 |

Evaluation includes 54 A folios/3,183 tokens and 30 B folios/4,276 tokens. Development
includes 60 A folios/2,942 tokens and 53 B folios/7,074 tokens. The contrast's
1,000-folio-resample percentile intervals are:

* Mean word-length difference: **+.160 to +.471**.
* Within-folio equal-pair rate difference: **−.004001 to +.002011**.

Thus zero misses the length interval but remains compatible with the repetition
interval. These intervals describe an exchangeable-folio resampling assumption,
not all transcription, filtering or glyph-unit uncertainty. This is one counting
convention; the previous census documents grouped sensitivity.

Within-folio repeat rates use sums of equal/possible pairs, preserving folio
weights. Bootstrap repeats resample within-folio pair totals rather than merging
copies of a folio and creating artificial global repeats.

## Candidate grid and prediction assumptions

The first stage has 45 configurations: Caesar, Aquinas or Middle Bavarian; mono,
sparse-independent, sparse-deterministic, mixed-H2-independent or mixed-H2-deterministic;
three fixed key seeds. Sparse allocation uses only the source's A half frequencies
with a public full-source alphabet. German's 25-letter alphabet gives no sparse
extras, so several configurations are equivalent rather than independent models.

Mixed H2 uses the previous globally prefix-free one/two-glyph generator with two
unused reserved output labels. One key is shared across both source halves.
All output labels fit the original 25 atomic EVA labels. Deterministic selection
uses the frozen seed/whole-word/letter-position hash rule; iid choices are uniform.
No nulls or generated boundaries are added.

The contraction extension has 18 configurations: Caesar/Aquinas with the
`bounded-seven` inventory (`ae, per, pro, con, et, est, rum`), minimum-unit
reversible witness for each word, and H1 mixed-width, H2 independent or H2
deterministic output. The same contraction policy applies to both halves.
The H1 key assigns frequent A-half units short codes and rare units two-glyph
codes, remaining prefix-free within 25 output labels. All configurations are
reported; no contraction rates or key choices are tuned on B.

The extension was specified **after inspecting the letter-stage results**. It is
therefore not a fresh independently blinded replication. It uses a fixed existing
inventory and fixed rules, and does not tune to B. This limitation must remain
visible rather than treating all 63 candidates as a single initial preregistration.

Expected moments are calculated analytically for iid word draws from each half's
empirical frequency distribution. For unit word w with probability p(w),
independent homophone choice gives expected word length equal to the sum of mean
code lengths. Its equal-output-pair contribution is
`p(w)^2 × product(1 / homophone_count(unit))`.
Deterministic selection gives repeat probability `sum(p(w)^2)` and exact emitted
word lengths. Unique inverse decoding prevents cross-word collisions.

These are **with-replacement iid population predictions**, not finite-text pair
counts. They do not model topic clustering, line dependencies, manuscript layouts
or natural ordering. Repeat predictions are consequently conditional on an
additional strong plaintext process assumption. Candidate selection uses the
smallest absolute A-development mean error, not a calibrated overall model score
or a probability of language/cipher correctness.

## Results

The stationary scenario predicts zero for both contrasts. It fails the observed
length contrast, while repetition supplies no strong contradiction.

The closest candidate to A development across both stages is
**Aquinas, bounded-seven contractions, shared H1 mixed-width key**:

| Quantity | Prediction | Observed evaluation |
| --- | --- | --- |
| A mean | 5.433 | 5.048 |
| B mean | 5.321 | 5.362 |
| B−A mean | −.113 | +.314 |
| A equal-pair rate | .009418 | .008240 |
| B equal-pair rate | .010338 | .007477 |

It already misses A-development mean by .466. Its B mean is close, but its A mean
is too large and the contrast has the wrong sign. The repetition contrast is
opposite in sign too, but falls inside the wide observed contrast interval; it
should not be described as decisively excluded by repetition.

Twelve Caesar mixed-H2 configurations put both contrast predictions inside the
observed intervals. Their predicted A means are **8.87–9.63**, however, compared
with 5.05 observed. Matching a difference between two badly wrong levels is not
successful prediction. These configurations also provide no recovered plaintext.

A separate absolute-level folio resampling check gives A mean interval
**4.957–5.134** and B **5.216–5.481**. **Zero configurations** match both mean levels
and both contrast intervals. This is a descriptive interval screen, not a
multiple-testing-adjusted hypothesis probability. The repetition interval is
broad and passing it alone provides little support.

## Assessment

The current feasible generators do not explain the Currier difference with shared
parameters under these specified plaintext assumptions. This reinforces the
absence of a demonstrated predictive manuscript model. It does not establish
that A/B must use different keys or languages: changing plaintext composition or
introducing a specified nonstationary shared process could change the prediction.
Those explanations need independent evidence and should not be fitted solely to
reproduce the observed gap.

A useful next check is whether the length difference persists after matching
manuscript section and line position. That can distinguish a broad Currier
contrast from corpus-composition or layout effects before inventing class-specific
cipher parameters. Another long solver run is not justified by these results.

## Artifacts and verification

[Letter-stage protocol](../experiments/results/currier-shared-parameters/prepared.json),
[letter-stage report](../experiments/results/currier-shared-parameters/report.json),
[contraction-stage protocol](../experiments/results/currier-shared-contractions/prepared.json),
[contraction-stage report](../experiments/results/currier-shared-contractions/report.json),
and [joint validation and absolute-level screen](../experiments/results/currier-shared-parameters/validation.json).

Validation checks both frozen stages, source provenance, contraction expansions,
unique prefix-free keys and output budget, independently calculated analytic
length/collision predictions, contrast/error calculations, A-only candidate
ranking and disjoint manuscript splits. Focused tests check analytic collision
probabilities and prefix-free contraction keys. No Z3 or old-result mutation.

```sh
.venv/bin/python -m benchmarks.currier_shared_parameters
.venv/bin/python -m benchmarks.currier_shared_contractions
.venv/bin/python -m benchmarks.validate_currier_shared_parameters
.venv/bin/python -m pytest -q tests/integration/test_currier_shared_parameters.py
```
