# Blinded synthetic mechanism discrimination

The new feature vector has **some synthetic discriminating power, but is not yet
calibrated for ranking Voynich hypotheses**. It separates four specified mechanisms
well for Aquinas and two broad mechanisms for German. Caesar's sparse independent
homophony is poorly resolved and produces three accepted errors. High aggregate
accepted accuracy hides that weak class.

This follows the [25-label capacity comparison](currier_alphabet_comparison.md).
No manuscript sample was classified and no Z3 calls were made.

## Frozen experiment and blinding

Fresh real passages come from the same cached Caesar, Aquinas and Middle Bavarian
sources, excluding every passage used in the earlier paired screens. Each source
has eight training, four calibration and eight evaluation passages, each 64 words.
Training/calibration use the first source half; evaluation uses the second.
All intervals are disjoint. Three different key seeds per split provide repeated
measurements, not independent passages. Layout is four lines of 16 original words;
this is conditioned geometry, not generated historical line structure.

The four known mechanisms are:

| Class | Cipher and boundaries |
| --- | --- |
| Mono | One distinct atomic output glyph per plaintext character; preserved spaces |
| Sparse independent | At most 25 labels, spare homophones allocated by training character frequency; uniform independent choices |
| Sparse deterministic | Same allocation, choices determined by seed, whole plaintext word and letter position |
| Renewal-6 | Mono payload with original spaces removed within each line, independent boundary cuts at probability 1/6 |

German has 25 plaintext characters and no spare labels. Its sparse classes are
identical to mono and are therefore omitted, leaving two German classes. Latin
has four classes. All symbols count as atomic glyphs. There are no nulls,
contractions or expansions, and this tests one frozen renewal parameter.
Allocation uses only the new training passages; labels are the original 25 EVA
labels, with fresh seeded assignments. The deterministic hash rule is an instrument
rule, not a proposed historical implementation.

**600 records** were generated: 240 training, 120 calibration and 240 evaluation.
The public feature file has truth labels only for training records. Prediction
reads that file alone, saves 360 calibration/evaluation predictions, and only then
scoring reads the separate truth file. IDs are opaque hashes; filenames and public
metadata do not expose held-out mechanisms. This is programmatic blinding within
the benchmark, not an independently administered challenge. The validator replays
prediction in a temporary directory containing only the public feature file and
verifies identical predictions.

Source identity is public and each source has its own classifier. This does
**not** test language identification, unknown-source generalization or Currier A/B
classification. No thresholds or feature choices were changed after inspecting
calibration or evaluation results. Calibration is an untouched descriptive audit,
not used to optimize rejection thresholds.

## Frozen classifier

Features are the existing token/type length distributions (bins 1–16 plus tail),
token/type length mean/variance/skewness, repeated-token and repeat-pair rates,
one-edit token/type near-pair rates, within-line length correlation and adjacent
repeats, word/line glyph-position mutual information, and the top-three frequency
ranks' mass in each of four positional bins. This is one explicit fixed summary
of the earlier metrics, not a search over feature subsets.

Training means impute missing values and training scales standardize features.
Four groups receive equal distance weight: lengths, repetition/variants,
adjacency and position. Prediction uses the nearest class centroid. It is
**unresolved** if the relative gap to the second-nearest centroid is below 0.2,
or its distance exceeds the class's training support radius. Radii are the
95th percentile of true-class distances from leave-one-passage-out training folds;
all keys and mechanisms from that passage are removed before refitting the fold.
These distances are not likelihoods or calibrated posterior probabilities.

## Held-out evaluation

| Source | Evaluation records | Accepted | Accuracy among accepted | Forced nearest-class accuracy |
| --- | --- | --- | --- | --- |
| Caesar | 96 | 46 (47.9%) | 43/46 (93.5%) | 74.0% |
| Aquinas | 96 | 65 (67.7%) | 65/65 (100%) | 96.9% |
| Middle Bavarian | 48 | 37 (77.1%) | 37/37 (100%) | 100% |

Each class contributes 24 evaluation records from eight passages and three key
seeds. The unresolved cases matter as much as accepted accuracy:

| Source / true class | Correct | Wrong accepted | Unresolved |
| --- | --- | --- | --- |
| Caesar mono | 15 | 0 | 9 |
| Caesar sparse independent | 1 | 3 | 20 |
| Caesar sparse deterministic | 7 | 0 | 17 |
| Caesar renewal-6 | 20 | 0 | 4 |
| Aquinas mono | 21 | 0 | 3 |
| Aquinas sparse independent | 19 | 0 | 5 |
| Aquinas sparse deterministic | 13 | 0 | 11 |
| Aquinas renewal-6 | 12 | 0 | 12 |
| German mono | 21 | 0 | 3 |
| German renewal-6 | 16 | 0 | 8 |

All three Caesar accepted errors are sparse-independent ciphertexts called
sparse-deterministic. Its success rate on sparse-independent cases is not summarized
by the overall 93.5%: among the four accepted decisions on that true class,
only one is correct. The classifier should therefore not be treated as a
reliable discriminator for that branch.

Calibration accepted accuracies were Caesar 81.3%, Aquinas 100% and German 100%,
with coverage 66.7%, 70.8% and 58.3%. No tuning followed this discrepancy. Aggregate
case percentages are descriptive; the eight evaluation passages per source and
shared keys/paired mechanisms do not support treating every row as independent.
The 64-word packets also differ from the earlier 32+word manuscript packets.

## Assessment and next decision

The features can recognize known distinctions under some same-source conditions;
they are not entirely uninformative. They do not consistently separate subtle
homophone-selection mechanisms across sources. Source-conditioned success cannot
be transferred directly to an unknown plaintext language or an unmodelled cipher.
The candidate set omits nulls, mixed widths, contractions, alternative renewal
parameters and out-of-family text generation. None of these results establish
how an out-of-family sample would be classified or rejected.

Do not apply this classifier to Voynich yet. The next informative test is
**source transfer and out-of-family rejection**, with fresh source passages and
frozen decisions. Broad mono-versus-renewal discrimination should be reported
separately from the weak sparse-selection distinction. This checks whether the
instrument recognizes a mechanism rather than a particular source's lexical and
positional statistics. It is preferable to another long solver run or parameter
search on the manuscript.

## Artifacts and validation

[Prepared protocol](../experiments/results/currier-mechanism-discrimination/prepared.json),
[public features](../experiments/results/currier-mechanism-discrimination/public.json),
[saved predictions](../experiments/results/currier-mechanism-discrimination/predictions.json),
[report and confusion tables](../experiments/results/currier-mechanism-discrimination/report.json),
and [validation](../experiments/results/currier-mechanism-discrimination/validation.json).
Generating labels, codebooks, ciphertext and raw metrics are in a separate truth
artifact. Previous frozen experiments remain unchanged.

Validation checks frozen code/source hashes, disjoint passages and source halves,
training-only allocation, held-out label omission, code capacity, inverse decoding
and payload conservation, full metric recomputation, blind prediction replay and
independent confusion/acceptance counts. Ten focused tests across the four
comparison benchmarks pass.

```sh
.venv/bin/python -m benchmarks.currier_mechanism_discrimination
.venv/bin/python -m benchmarks.validate_currier_mechanism_discrimination
.venv/bin/python -m pytest -q tests/integration/test_currier_mechanism_discrimination.py
```
