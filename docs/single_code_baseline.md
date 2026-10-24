# One-code substitution baseline versus homophonic expansion

This comparison removes homophone choice while keeping variable-length
expansion. H1 permits exactly one prefix-free codeword per plaintext unit;
H2 permits one or two. Both use code lengths 1–3, the same alphabet, dictionary,
word observations, selection mode and contraction profile for each ciphertext.
H1 is deterministic variable-length substitution, not length-one monoalphabetic
substitution. A length-one baseline over the six-glyph fixtures would have an
unhelpful alphabet-capacity obstruction.

H1 is nested inside H2: every H1 key is admissible under H2. No new contractions,
vocabularies, statistical objective or cipher freedoms are introduced.

## Fixed suite

The eleven existing local-structure cases comprise four H2-generated positives
and seven constructible pair-chunk/bigram controls. Fit them under H1; reuse
existing H2 outcomes only after verifying unchanged solver/source/request
identities and SAT certificates. The unavailable eighth original control remains
unavailable and is not counted as UNSAT.

Add four H1-generated positives using the **same training and continuation
plaintext unit sequences** from the original Latin/Swabian letter/mixed fixtures.
Each generating unit has one length-two codeword, assigned with fixed seed
1919. Choice indices are zero. Each continuation codeword appears in training.
A fixed pair-chunk control per new positive uses seed 2020, preserving word
lengths, per-word glyph counts, aligned pairs and exact repetition partitions.
These controls are not selected by solver or prediction outcomes. Both models
receive these eight new cases.

This yields nineteen ciphertext cases and 38 model outcomes: 27 new fits and
11 reused fits. Each new fit has one ordinary recovery attempt with a five-second
budget. Keys are frozen before continuation scoring; no search for a better
witness, extra seeds or changed budgets. Completion is checkpointed per arm.

## Fitting results

| Case group | Cases | H1 results | H2 results |
| --- | --- | --- | --- |
| Original H2-generated positives | 4 | 4 UNSAT | 4 verified SAT |
| Original structural controls | 7 | 7 UNSAT | 7 UNSAT |
| New H1-generated positives | 4 | 4 verified SAT | 4 verified SAT |
| New H1 pair-chunk controls | 4 | 4 UNSAT | 1 verified SAT, 3 UNSAT |

All own-model positives fit. The H1 restriction distinguishes these H2-generated
fixtures from H1-generated fixtures. The broader model's added capacity also
admits a corrupted Latin mixed H1 control rejected by H1. Its full SAT witness
independently reproduces the training ciphertext within dictionary/cipher bounds.
This is not a solver error: the control is compatible with the broader bounded
model, despite being constructed by corrupting a known ciphertext.

The outcome shows a concrete **flexibility trade-off** on these fixtures. H2 is
needed to fit the H2 positives, yet permits an additional structural-control
fit. Counts are descriptive, not estimated false-positive or language probabilities.
The test does not establish that H1 is universally preferable or H2 implausible.
There are no UNKNOWN outcomes. New fits take 11.65 solver seconds combined,
individually 0.18–1.28 seconds. Reused solver time is not newly spent.

## Frozen predictions on the new H1 positives

| Positive | H1 exact words | H2 exact words | Novel ciphertext words |
| --- | --- | --- | --- |
| Latin letters | 4/4 | 4/4 | 0 |
| Latin mixed | 4/4 | 0/4 | 0 |
| Swabian letters | 4/4 | 4/4 | 1 |
| Swabian mixed | 4/4 | 4/4 | 1 |

All four H2 predictions on the Latin mixed positive are dictionary words but
none is the true generating word. Thus dictionary membership alone can conceal
incorrect recovery even for an uncorrupted, fully covered positive. First SAT
witnesses are not unique or uniformly sampled; a different H2 witness could
predict correctly. This diagnostic does not prove every H2 explanation is wrong.

All Latin continuation ciphertext words have already appeared in training, so
these scores measure consistency with generating truth on repeats, not novel
word generalization. Each German continuation has one novel ciphertext word,
recovered exactly by both models. H1's deterministic generation also changes
repetitions relative to the original H2 fixtures. Those generations are matched
in plaintext sequence and lengths, not all ciphertext statistics.

The H2-compatible corrupted Latin control gives four dictionary continuation
hits, all on previously seen ciphertext words. No exact-original-message score
is assigned to corrupted controls. Its hits do not demonstrate predictive
language recovery.

## Artifacts and validation

Implementation: `benchmarks/single_code_baseline.py`.
Protocol, identities, complete requests/keys, cached-result provenance and
independent validation: `experiments/results/single-code-baseline/`.
Earlier reports are preserved. Preparation rejects source/code changes; completed
arms are skipped on reuse. Model-nesting contradictions are checked explicitly.

Ten focused tests pass, covering nested request equality except for H, own-model
positive certificates, complete continuation code coverage, cached witnesses,
structural controls and frozen-key scoring. Independent validation checks all
38 outcomes' identities, all SAT certificates, cache equality, control generation,
coverage and predictions without new solves. UNSAT outcomes remain recorded
solver proofs rather than independently rerun solves.

```sh
.venv/bin/python -m benchmarks.single_code_baseline --run
.venv/bin/python -m pytest -q tests/integration/test_single_code_baseline.py \
  tests/integration/test_structured_negative_controls.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/single-code-baseline/validate.py
```

## Decision

Keep H1 as the simpler baseline and H2 as the broader challenger. Require
positive-control recovery and structural-negative separation before escalating
model capacity. SAT/dictionary hits alone are insufficient, particularly when
continuation repeats training words. A future comparison needs genuinely novel
held-out words under both generation models before choosing a preferred model.
These projected tiny-vocabulary controls do not decide Latin versus German,
contractions versus letters, or a manuscript-language hypothesis.
