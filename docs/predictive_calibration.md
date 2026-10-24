# Fixed predictive-calibration benchmark

The protocol is frozen in
`experiments/configs/predictive-calibration.json`: two corrected dictionaries
(5,655-entry Latin and 3,181-entry Swabian), atomic EVA units, free selection,
H2/L1–3, globally prefix-free codes, no contractions or nulls. Each case has
30 fitting words and a 22-word continuation; the full fitting budget is 30
minutes. There is one fixed key seed, homophone-choice seed and shuffle seed.
No retries with new seeds, key repairs or inventory widening are prescribed.

## Six prepared cases

For each dictionary, three training/continuation pairs are prepared:

1. A known source passage encrypted by the tested mechanism.
2. The same preselected Voynich block, shared across dictionaries.
3. One typewise shuffled version of that Voynich block, also shared across
   dictionaries.

Selection uses the first contiguous 52 eligible words, before fitting or
scoring. Synthetic source words must all belong to their corrected dictionary;
an excluded or uncovered record interrupts a candidate run. Caesar uses the
corrected processed corpus. Swabian uses the cached XML with marked-initial
and uncertain-form corrections and the previously corrected dictionary;
its original spelling and source morph boundaries are retained. This is a
source passage, not a hand-picked combination of short dictionary words.
The dramatic source's spelling/genre limitations still apply.

Voynich stays on one folio and uses the saved corpus's original eligibility
rules. All selected records, raw forms and loci are retained in the manifest.
Typewise shuffling operates on the whole 52-word pair, preserving word lengths,
global/per-word glyph counts and word equality across the fitting/continuation
boundary. It is a structural negative control, not another language sample.

Every public fitting input contains only the first 30 ciphertext words,
dictionary, alphabets and model constraints. Continuations are stored separately,
and generating plaintext/key/choices in separate truth files. Recovery never
receives the truth or continuation. The same ciphertext alphabet is used for
all cases. The generating synthetic keys reproduce training ciphertext and
decode **all 22 continuation words into their dictionaries** independently.

## Interpretation gate

The full-budget synthetic gate passes only if the independently verified
recovered key, frozen without repairs, completely decodes all 22 continuation
words and all 22 are dictionary members. Exact generating-key or original
plaintext recovery is not required. Novel ciphertext-form results are recorded
separately to expose repetition-driven success.

This is a strict operational gate, not a statistical significance threshold.
Success on one synthetic case does not establish reliability. A poor prediction
means this recovery procedure has not preserved the known encoder's predictive
ability; it does not falsify that encoder or the cipher family. UNKNOWN remains
unresolved and receives no prediction score. Do not start the remaining matrix
or interpret Voynich failures before reviewing this gate.

The Latin ten-second smoke fit returned **UNKNOWN in 10.25 seconds**, with no
holdout score. The initial smoke protocol is preserved in `smoke-protocol.json`;
the explicit full-continuation threshold was fixed after that unresolved
smoke fit and before any full-budget fit. Its addition changes no fitting input.

## Current next command

**Completed long calibration:** the Latin synthetic run returned UNKNOWN after
1800.38 seconds, with `NOT_EVALUATED_NO_SAT`. No recovered key or continuation
score exists. The generating key remains verified for training and all 22
continuation words. Thus this is unresolved recovery of a known-solvable
instance, not failed prediction or evidence against the cipher family.

The predictive gate remains unresolved. Do not run the other five cases or
repeat this completed attempt at a larger budget. The command below is retained
for provenance and its output file prevents an accidental rerun. The next
distinct step is a small synthetic training-size ladder with this fixed
generating key, to find where recovery becomes practical before revisiting
30-word prediction. This is calibration work, not further Voynich fitting.

The [fixed-key size ladder](synthetic_size_ladder.md) has now completed:
5-, 10- and 15-word fits all returned UNKNOWN at ten seconds. No prediction
scores exist. The full comparative matrix remains deferred; known-plaintext
recovery is the next distinct diagnostic, not another budget escalation.

Run only the Latin synthetic calibration at the fixed long budget:

```sh
.venv/bin/python -m benchmarks.predictive_calibration --case latin-synthetic
```

This performs one capped fitting attempt, then automatically evaluates the
frozen recovered key only on verified SAT. Results are saved to
`experiments/results/predictive-calibration/latin-synthetic-1800000ms.json`.
Existing result files prevent accidental repeats. Preparation defaults to
no solves; no long run was started while implementing this benchmark.

## Important matching limitation

Word counts, alphabets, dictionaries and budgets match; synthetic and Voynich
glyph counts and word-length distributions **do not**. Encrypting natural
source passages by expansion can produce substantially longer ciphertext.
This is a calibration of recovery and prediction, not a length-matched
classification test. A future claim that Voynich resembles shuffled text
requires review of this confound and more samples. Do not silently choose
shorter passages or tune code lengths after results.

The dataset is retrospective and the existing manuscript material has been
inspected previously. One recovered key per case need not represent the full
set of fitting keys. These restrictions prevent interpreting failed prediction
as a universal model exclusion or comparing languages by isolated fit times.

## Validation and reproduction

```sh
.venv/bin/python -m benchmarks.predictive_calibration
.venv/bin/python -m pytest -q \
  tests/integration/test_predictive_calibration.py \
  tests/integration/test_frozen_key_holdout.py
```

All **7 focused tests pass**. Tests check source coverage and gap/folio boundaries,
30/22 splits, hidden public inputs, generating continuation round trips, paired
Voynich/control equality across dictionaries, UNKNOWN handling and repeat-run
protection. Artifact validation checks all input/truth/holdout hashes and both
generating full-passage round trips.

Inputs, continuations and truth files are under
`data/generated/predictive-calibration/`; protocol/selection manifests and fit
reports are under `experiments/results/predictive-calibration/`.
