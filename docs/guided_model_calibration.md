# Guided proposals across Latin/German and expansion/mixed models

This fixed pilot compares language-aware candidate generation with ordinary
solver order. It uses fresh synthetic controls, covered continuation homophones,
paired shuffled negatives and both recovery models on every ciphertext. No
Voynich solve, budget enlargement or seed search is performed.

## Protocol and scope

Reference words and add-one bigram scores come only from the first half of each
cached corpus. Evaluation uses its second half: normalized Caesar for Latin and
corrected Swabian source 123 for German. The twelve most frequent reference words
of at most three letters define each vocabulary. Intervening words are removed:
these are projected same-source sequences, not intact historical prose or
independent-author validation. The German stream follows the existing marked
initial/quarantine normalization; no new spelling conversions are introduced.

Two generation profiles use the same source block per language:

- Letters: ordinary letters encoded by expanding homophones.
- Mixed: shortest reversible tokenization, adding one dedicated contraction
  unit; recovery allows both letters and contracted tokenizations.

Latin uses a whole-word `et` unit, motivated by the Tironian sign documented by
[HMML](https://hmmlschool.org/latin-gothic-transcription/). German uses a whole-word
`in` unit inspired by the nasal mark that supplies omitted n/m, described by
[Ad fontes](https://www.adfontes.uzh.ch/tutorium/schriften-lesen/abkuerzungen).
The German unit is an explicit **modeling inference**, not an attested cipher
unit or a recovered abbreviation in source 123. Neither inventory reconstructs
historical mark shapes, ambiguities or usage rates. A dedicated unit preserves
its expansion unambiguously; this is a narrow compression sensitivity model.

Generation has two length-two homophones per plaintext unit over six glyphs;
both recovery profiles permit free H2/L1–3, globally prefix-free codes and no
nulls. Training choices alternate per unit to expose both alternatives. Held-out
choices are seeded free draws. The earliest prefix of 4–48 projected words
covering each continuation unit twice under both profiles is selected.
Contraction use is required in training. Latin starts at projected offset 64
and German at 0; these offsets were fixed before fitting.

Construction yields 24 training words for Latin and 19 for German, each with
four continuation words. All four positives independently cover every generating
codeword in continuation. Latin's mixed continuation uses `et`; German's does
not use `in`. The German contraction comparison therefore exercises training
compression but not directly contracted continuation words.

An initial preparation required contraction use in continuation as well and
failed for German before any solver calls. That protocol/failure is preserved in
`preflight-v1.json`. Version 2 relaxes only that construction requirement. No
fit or continuation score informed this change; budgets, sources and seeds
remain fixed.

Each of eight ciphertext cases (language × generation profile × positive/shuffle)
is fitted by both recovery profiles and both proposal methods: **32 arms**.
Every arm has a five-second total solver budget and at most three attempts.
Proposal time is measured separately, not included in the solver cap. Budgets
are equal ceilings, not equal CPU consumption; solver overhead can exceed the
remaining timeout slightly. Completed arms are checkpointed and skipped on reuse.

Ordinary recovery enumerates dictionary fits using the existing used-ownership
exclusions. Guided recovery builds a width-16 beam of training plaintexts, using
public dictionary lengths/prefix relations and reference scores, then tests the
top three through known-plaintext encoder recovery. These proposed plaintexts
are generated from training alone, not revealed truth. The known-plaintext
solver checks key feasibility; it does not make the proposals correct.

Both methods select their best returned fit using the same frozen training score
before continuation evaluation. Thus the statistical comparison concerns
**candidate generation**, holding the final selection rule fixed. Guided
proposal UNSAT rejects only that particular sequence; it cannot prove the full
dictionary hypothesis UNSAT. Ordinary UNSAT after a SAT with ownership blocks
likewise does not negate the earlier fit.

## Recorded results

All selected keys below come from ordinary recovery; guided proposals produce
no SAT keys in any arm.

| Positive ciphertext | Letter recovery: exact words | Mixed recovery: exact words | Matching model: novel exact words |
| --- | --- | --- | --- |
| Latin letters | 3/4 | 3/4 | 1 |
| Latin mixed | UNSAT | 4/4 | 2 |
| Swabian letters | 4/4 | 4/4 | 2 |
| Swabian mixed | UNSAT | 4/4 | 3 |

Ten returned fits independently reproduce training and obey their recovery
models. All four generating-model positives are SAT. Both letter-only fits on
mixed-generated positives are UNSAT: the two bounded models can be distinguished
on these constructed examples. This is expected under an active contraction
mechanism, not evidence that historical/Voynich text uses it. Letter and mixed
generation differ in ciphertext lengths and key unit assignments, so their
prediction scores are not a controlled estimate of a contraction advantage.

Every shuffle is UNSAT under its corresponding generation/recovery profile.
Across the wider cross-profile comparison, mixed recovery on the Swabian letter
shuffle is UNKNOWN at five seconds; the other seven ordinary shuffle arms are
UNSAT. No shuffled arm returns SAT. An additional-key search for mixed recovery
on the Latin letter positive is also UNKNOWN after one valid SAT fit; this does
not invalidate that fit or exhaust the candidate pool.

All **48 guided sequence proposals are UNSAT**, including those for positives.
Public prefix/length feasibility plus a high language score is insufficient to
construct a sequence compatible with one shared key. This particular beam
strategy fails the positive-control gate. It does not establish that statistical
information is useless; beam truncation, proposal count and missing shared-key
reasoning are inseparable in this fixed pilot. No candidates or budgets were
added after seeing the failure.

The matrix used 36.06 seconds of solver runtime and 0.50 seconds for guided
proposal generation. Five focused tests pass. Independent validation checks all
32 arms, 72 attempts, ten SAT fits, generating coverage, proposals, budget
allocation, scores, selection, expanded-spelling predictions and exact/novel
matches. The earlier calibration artifacts remain unchanged.

## Artifacts and commands

Configuration: `experiments/configs/guided-model-calibration.json`.
Implementation: `benchmarks/guided_model_calibration.py`.
Protocol, reference counts, complete requests/truth, case reports and independent
validation: `experiments/results/guided-model-calibration/`.

```sh
.venv/bin/python -m benchmarks.guided_model_calibration
.venv/bin/python -m benchmarks.guided_model_calibration --case latin-letters-synthetic
.venv/bin/python -m benchmarks.guided_model_calibration --run-all
.venv/bin/python -m pytest -q tests/integration/test_guided_model_calibration.py \
  tests/integration/test_generating_key_ranking.py
PYTHONPATH=.:src .venv/bin/python experiments/results/guided-model-calibration/validate.py
```

Preparation rejects source/config/code identity changes. Completed arms are
preserved; interrupted arms repeat from their start. Existing UNKNOWN outcomes
are not rerun automatically.

## Decision

Do not scale this free-standing sequence beam or choose Latin/German from these
four positives. Retain ordinary recovery as the calibrated baseline and the
fixed mixed model as a bounded challenger. If statistical proposals are pursued,
they must account for shared-key feasibility during construction, rather than
rank whole plaintext sequences before testing a key. Demonstrate that on a small
covered positive before a larger matrix or renewed Voynich fits. The matrix does
not establish a language preference or justify additional cipher freedoms.
