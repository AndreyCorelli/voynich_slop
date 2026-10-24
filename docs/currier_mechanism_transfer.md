# Cross-source transfer and outside-grid rejection

**Park this classifier for manuscript inference.** The frozen features and
rejection rules do not transfer reliably across sources. Broad spacing decisions
have high accuracy when accepted, but reject nearly every genuine renewal case.
Sparse-selection transfer has accepted errors. Rejecting most outside-grid
controls is not strong evidence when genuine cases are rejected too.

This follows the [same-source synthetic discrimination test](currier_mechanism_discrimination.md).
No Voynich sample was classified and no solver calls were made.

## Frozen protocol

The classifier reuses only the prior experiment's 240 training feature records,
labels and training-derived code allocations. Features, four equally weighted
distance groups, nearest-centroid classification, 0.2 margin and leave-one-passage-out
95th-percentile support radii are unchanged. No calibration or evaluation
passages enter training and no rejection thresholds were tuned.

Each cached source supplies eight fresh 64-word second-half evaluation passages,
excluding all earlier paired-screen and discrimination passages. Three new key
seeds and four original lines of 16 words are used. Generators retain the 25
atomic EVA labels. Source identities route transfer models, but the training
source always differs from the evaluation source; no target-source centroids or
scales are fitted. Thus language identification remains untested.

Two questions are kept separate:

* **Broad spacing:** all six directed source-transfer pairs, trained only on mono
  versus renewal-6. Sparse preserved-space evaluation examples count as preserved,
  testing some breadth beyond the mono training examples. There are three
  preserved Latin classes and one renewal class, so aggregate cases are imbalanced.
* **Fine mechanism:** Caesar to Aquinas and Aquinas to Caesar, with mono, sparse
  independent, sparse deterministic and renewal-6. German is omitted because its
  25-character inventory leaves no distinct sparse class.

Five additional generators are outside the exact candidate grid:

| Generator | Construction and meaning |
| --- | --- |
| Fixed-two expansion | Replace each mono glyph g with (g, fixed glyph); unambiguous fixed-width decoding |
| Word-final marker | Append one fixed glyph to every word; strip the final position to restore payload, even when the label also occurs as payload |
| Glyph shuffle | Shuffle the whole packet's glyph stream, then restore the original word-length/line layout; exact glyph totals and lengths match |
| Renewal-4 | Same mono stream, renewal mean 4 |
| Renewal-8 | Same mono stream, renewal mean 8 |

Renewal-4/8 are **parameter shifts within the renewal family**, not different
mechanisms at the broad spacing level. Accepting them as renewal need not be a
broad family error; their results are therefore shown separately from expansion,
marker and shuffle controls. Rejecting a known case means unresolved or outside
training support; it does not imply a particular alternative mechanism.

**600 fresh ciphertext records** produce **1,632 cross-source predictions**.
The public file contains labelled training features and unlabelled evaluation
features. Prediction reads only that file and writes decisions before scoring
reads generating truth. A replay in a temporary directory containing only the
public file reproduces all decisions. This is programmatic blinding, not an
independently administered challenge. Keys, generators and source identity are
known to the experimental design; the model sees only the specified features.

## Broad transfer results

The table concerns known mechanisms, excluding outside-grid generators.

| Train → evaluate | Known cases | Accepted | Accuracy among accepted | Forced nearest-class accuracy |
| --- | --- | --- | --- | --- |
| Aquinas → Caesar | 96 | 60 | 100% | 100% |
| Aquinas → German | 48 | 24 | 100% | 100% |
| Caesar → Aquinas | 96 | 2 | 100% | 99.0% |
| Caesar → German | 48 | 0 | Undefined | 95.8% |
| German → Aquinas | 96 | 27 | 100% | 89.6% |
| German → Caesar | 96 | 9 | 100% | 80.2% |

Only **122/480 decisions (25.4%)** are accepted, all correct. However, only
**one of the 144 genuine renewal-6 transfer decisions** is accepted. High forced
accuracy suggests the feature geometry retains broad spacing information;
rejection support learned from one source is poorly portable. A system that
mostly accepts preserved spaces and rejects genuine renewed boundaries cannot
reliably rank the two manuscript hypotheses. The asymmetry between transfer
directions is also substantial.

## Fine transfer results

| Train → evaluate | Known cases | Accepted | Correct among accepted | Forced accuracy |
| --- | --- | --- | --- | --- |
| Aquinas → Caesar | 96 | 36 | 27/36 (75%) | 71.9% |
| Caesar → Aquinas | 96 | 4 | 2/4 (50%) | 68.8% |

Overall accepted accuracy is **29/40 (72.5%)**, with only **20.8% coverage**.
Nine Caesar sparse-deterministic cases are called sparse-independent. Two Aquinas
sparse-independent cases are called sparse-deterministic. These accepted mistakes
show that same-source success did not establish transferable selection inference.

## Outside-grid acceptance

Each generator contributes 144 broad transfer decisions and 48 fine transfer
decisions. Counts below are decisions accepted as a trained class, not posterior
support for that mechanism.

| Generator | Broad accepted | Fine accepted |
| --- | --- | --- |
| Fixed-two expansion | 0/144 | 0/48 |
| Word-final marker | 17/144 | 5/48 |
| Glyph shuffle | 8/144 | 4/48 |
| Renewal-4 parameter shift | 19/144 | 2/48 |
| Renewal-8 parameter shift | 5/144 | 0/48 |

The three expansion/marker/shuffle controls are rejected in 94.2% of broad and
93.8% of fine decisions. But genuine-case rejection is 74.6% and 79.2%, respectively.
The rejection rates therefore do not establish a trustworthy outside-family
detector. This small control menu also does not cover historical cipher families
or pseudo-text mechanisms generally. Near-grid parameter shifts are not counted
as proof that all renewal mechanisms are excluded.

## Decision

Stop this sequence of classifier refinements before applying scores to Voynich.
Further radius or margin tuning could improve these particular samples without
providing independent evidence about the manuscript. Keep the raw compatibility
screens as descriptive measurements, with their alphabet, spacing and sample-size
assumptions visible. Earlier null results remain conditional on output width;
these transfer failures do not reverse that observation.

The next productive step is a research reset toward **necessary structural
constraints**, rather than another learned ranking: enumerate what each remaining
model must preserve or change in word lengths and exact repeated-word frequencies,
then check those constraints across Currier A/B with manuscript sampling uncertainty.
That can identify an actual model contradiction without relying on this classifier's
source-dependent scores. No additional classifier or manuscript fit was run here.

## Artifacts and validation

[Prepared protocol](../experiments/results/currier-mechanism-transfer/prepared.json),
[public features](../experiments/results/currier-mechanism-transfer/public.json),
[predictions](../experiments/results/currier-mechanism-transfer/predictions.json),
[report and full confusion counts](../experiments/results/currier-mechanism-transfer/report.json),
and [validation](../experiments/results/currier-mechanism-transfer/validation.json).

Validation checks frozen code/source hashes, exact training-only reuse, disjoint
fresh passages, inverse decoding and control conservation, output glyph budget,
all regenerated metrics, public-only blind replay, cross-source exclusion and
independent confusion/acceptance counts. Eleven focused tests across the five
comparison benchmarks pass. Earlier frozen artifacts remain unchanged.

All percentages describe repeated key/mechanism measurements on eight evaluation
passages per source. Transfer directions reuse those passages, so 1,632 decisions
are not 1,632 independent observations. The sources, fixed layouts and 64-word
packets do not represent unknown Voynich plaintext or the entire manuscript.

```sh
.venv/bin/python -m benchmarks.currier_mechanism_transfer
.venv/bin/python -m benchmarks.validate_currier_mechanism_transfer
.venv/bin/python -m pytest -q tests/integration/test_currier_mechanism_transfer.py
```
