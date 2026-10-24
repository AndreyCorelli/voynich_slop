# Repeated unknown word type calibration

All six positives are verified SAT with one unknown type, while all six are UNSAT
with one unknown occurrence. All six paired shuffles are UNSAT under both arms.
No fits time out. Three integration tests and 24-arm artifact validation pass.

| Profile / seed | Type arm training exact | Held-out exact | Occurrence arm | Type shuffle |
|---|---:|---:|---|---|
| Fixed two / 4301 | 18/18 | 3/3 | UNSAT | UNSAT |
| Fixed two / 4302 | 10/18 | 2/3 | UNSAT | UNSAT |
| Mixed 1/2 / 4301 | 6/18 | 1/3 | UNSAT | UNSAT |
| Mixed 1/2 / 4302 | 10/18 | 2/3 | UNSAT | UNSAT |
| Mixed 1/2/3 / 4301 | 18/18 | 3/3 | UNSAT | UNSAT |
| Mixed 1/2/3 / 4302 | 18/18 | 3/3 | UNSAT | UNSAT |

The type arm predicts 14/18 held-out occurrences exactly, compared with 17/18 in
the existing strict 64-word calibration with complete training vocabulary. Three
of six keys recover every training word; the others find alternative explanations.
All six SAT witnesses have one actual unknown type occurring twice. Positives
solve in 0.743–2.067 seconds; type shuffles in 1.095–2.204 seconds. SAT compatibility
is restored, but it does not guarantee key identity or correct prediction.

## Frozen paired experiment

The six existing synthetic fixtures cover fixed-two, mixed-one-two and
mixed-one-two-three generating keys under seeds 4301/4302. Each has 18 training
words (nine distinct types repeated twice) and three novel held-out words. The
existing 64-word dictionaries are used; delete the first true training type,
`et`, without replacement, leaving 63 entries. Existing paired typewise shuffles
with seed 4401 are reused unchanged. Both arms receive identical requests and
five-second timeouts. All twelve cases were frozen before the 24 fits, without
retries, score-based additions or budget extensions. Construction time is extra.

One arm allows at most one actual unknown occurrence. The other allows at most
one actual unknown type, regardless of repetition count. No exempt spelling,
position, plaintext length, key or holdout constraint enters recovery. Generating
witnesses verify under the type arm; the occurrence arm excludes the generating
explanation because `et` occurs twice. Its UNSAT results exclude alternative
explanations only within that bounded model.

The type solver is explicitly restricted to free deterministic H1 coding. With
one prefix-free code per symbol, encoding and decoding are injective: distinct
ciphertext words correspond to distinct plaintext words. Thus charging membership
failure once per ciphertext spelling implements the plaintext-type budget.
Repeated occurrences still share plaintext and membership constraints. The
independent verifier counts distinct recovered unknown plaintext spellings; it
does not trust exemption flags. A homophonic H2 model would require a different
encoding because different ciphertext spellings could represent one plaintext type.

The isolated experimental `oov_type_recovery.py` preserves prior solver hashes
and artifacts. Like the occurrence prototype, it removes dictionary-only pairwise
pruning and permits all alphabet letters at unknown symbolic slots. This copied
builder should be consolidated before broader use; default strict request/replay
semantics remain unchanged.

## Validation and limits

```sh
.venv/bin/python -m benchmarks.oov_type_calibration --run
.venv/bin/python -m benchmarks.oov_type_calibration --validate
```

Artifacts: `experiments/results/oov-type-calibration/` contains hashes, frozen
requests/deletions, protocol, checkpointed witnesses/scores and validation.
Completed arms skip on resume. Validation reconstructs matched source cases,
checks actual occurrence/type budgets, independently verifies SAT witnesses and
recomputes frozen scores. Tests exercise repeated versus distinct unknown words,
H1 restriction, identical public requests, resume and unscored non-SAT handling.

These are engineered repeated-word fixtures with an assisted vocabulary, not
natural prose or blind language identification. The same text is reused across
profiles, so occurrence totals are not independent trials. Controls cover one
shuffle family. UNSAT is solver-reported without independently checked proof
certificates. The useful result is that type-level tolerance fixes one vocabulary
failure while introducing additional ambiguous keys. It does not rank Latin or
German or provide evidence about the manuscript.
