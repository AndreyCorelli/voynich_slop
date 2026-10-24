# Full-vocabulary mixed contraction pilot

This fixed pilot retains all 5,655 corrected Caesar spellings and the original
23-word ciphertext. Complete optional tokenizations produce:

| Profile | Expanded spellings | Unit dictionary entries | 5-word positive, 10 seconds |
| --- | --- | --- | --- |
| Letters | 5,655 | 5,655 | UNKNOWN |
| Optional ae | 5,655 | 5,937 | UNKNOWN |
| Optional seven units | 5,655 | 6,804 | Verified SAT, 7.14 seconds |

The three positives share expanded spellings `quae per est contra quorum` and
seed 7, but have different ciphertexts because their input unitizations and
alphabets differ. Each uses the full vocabulary, not the seven-word gate
dictionary. Generating keys have two length-two homophones; recovery permits
H2/L1–3. The original ciphertext alphabet is retained, and all generating
witnesses are independently checked. Public inputs contain no plaintext/key.

Original letter alphabets remain intact; active contraction units are added
per profile. All profiles use free selection, globally prefix-free codewords,
observed-code domains and no nulls. The earlier 23-word Latin UNSAT used
text-wide cycles, so it is not the free-selection baseline for this comparison.
More units also require more codebook entries; these are different bounded
models, not an assertion that every old key extends to the richer alphabet.

Only the seven-unit profile passed calibration at this short budget. Its
23-word Voynich probe returned UNKNOWN at 10.13 seconds. Letters and ae were
skipped by the calibration gate. No negative inference follows from these
timeouts. One short five-word positive does not establish reliable recovery
on a 23-word sample; it is a limited functional/performance checkpoint.

## Fixed next run and stopping rule

### Recorded long result

The capped seven-unit run returned **independently verified SAT in 591.84
seconds**. Expanding the recovered units gives:

```text
dc ut eo xv uno hae ex una ulla ea hae una eo uni xv dc ex eo ei ea e ut eos
```

Only `<ae>` is used, twice in `hae`; the other six contraction units are absent
from the recovered plaintext. Removing their unused codebook entries yields
an independently verified SAT certificate for the prepared **ae-only** model,
without another solver call. The transfer is saved in
`experiments/results/latin-mixed-comparison/ae-only-transferred-witness.json`.
Unused ordinary letter mappings remain, as required by that model's alphabet.

All expanded words belong to the corrected vocabulary, including `dc` and `xv`.
The sequence is a dictionary fit, not readable Latin. The result establishes
compatibility of both bounded models for this block; it does not establish
that contractions are necessary. Letters-only **free-selection** feasibility
remains unresolved; the older cyclic UNSAT cannot answer that comparison.
Long witness validation and expanded spellings are saved in `long-validation.json`.

The prescribed long attempt is complete. Do not repeat it or expand the
inventory. The next informative comparison is the existing letters-only
free-selection input, using the same block and vocabulary, rather than a
long ae-only run whose SAT witness is already available.

The matching letters-only input has been validated against the ae-only request:
only the active plaintext alphabet and dictionary tokenizations differ. Run:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/latin-mixed-comparison/budget-1800000ms/inputs/letters-voynich.json \
  --replay-output experiments/results/latin-mixed-comparison/letters-voynich-30min.json
```

This is one capped comparison, not a new sweep. SAT would show that contractions
are unnecessary for compatibility of this block. UNSAT would establish their
necessity within these matched bounded models, provided the verified ae-only
certificate remains valid; it would not establish historical usage. UNKNOWN
leaves necessity unresolved. The letters-only synthetic probe was UNKNOWN at
10 seconds, so timeouts provide no negative evidence. No long run was started
while preparing this command.

### Letters-only comparison completed

The matching letters-only run returned **independently verified SAT in 343.35
seconds**, with expanded/plain letter sequence:

```text
apr soli ei ubi xv sed et xi soli di ad sed ei xl ut res et di dc di e sc eius
```

The public request hash, source input and encoder round trip were checked;
validation is saved in `letters-long-validation.json`. No contraction units
occur. Thus contractions are **not necessary for compatibility of this
23-word block** under the free-selection H2/L1–3 dictionary model. The
seven-unit SAT did not establish a contraction advantage. Runtime differences
between single runs do not establish a performance advantage either.

Both sequences include short entries and numeral-like forms from the actual
Caesar vocabulary; neither is a grammatical passage. This closes the fixed
contraction pilot. Earlier Latin cyclic UNSAT and current free-selection SAT
refer to different selection assumptions and are consistent. Any future
selection-policy comparison must explicitly keep all other model inputs fixed.
Do not expand the inventory or start prefix/deletion analysis from this result.

Six full-budget inputs (three positives and three Voynich variants) are
prepared, but do not run the whole matrix yet. The next bounded run is **one**
30-minute seven-unit Voynich attempt:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/latin-mixed-comparison/budget-1800000ms/inputs/bounded-seven-voynich.json \
  --replay-output experiments/results/latin-mixed-comparison/bounded-seven-voynich-30min.json
```

Stop this branch after that attempt and review the result; do not widen the
contraction inventory or launch a prefix/deletion search. UNKNOWN is unresolved.
UNSAT excludes only this precise bounded dictionary model. SAT must be expanded
back to the source spellings, verified and evaluated as dictionary compatibility,
not grammatical Latin or decipherment. A matched letters/ae comparison still
requires further calibration of those two profiles.

## Reproduction

```sh
.venv/bin/python -m benchmarks.latin_mixed_comparison
.venv/bin/python -m benchmarks.latin_mixed_comparison --probe --timeout-ms 10000
.venv/bin/python -m benchmarks.latin_mixed_comparison --voynich-probe --timeout-ms 10000
```

Preparation calls no solver. Probe reports checkpoint per completed case;
these small probes overwrite their own report when explicitly rerun. Long
individual replays save separately. Artifacts live under
`data/generated/latin-mixed-comparison/` and `experiments/results/latin-mixed-comparison/`.
All unit words expand back to exactly the corrected vocabulary. Full alphabet,
model, calibration and gating checks are covered by **26 passing focused tests**.
