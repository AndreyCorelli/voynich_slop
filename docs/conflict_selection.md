# Selection-rule comparison on the 22-word conflict

The baseline is the certified UNSAT block at original words 2–23, from `qopal`
to `chololy`, under the 5,658-entry corrected Caesar vocabulary plus
`i/iv/iulius`. It uses globally prefix-free H2/L3 codes, preserved word boundaries,
no nulls and text-wide cyclic selection. The baseline returned UNSAT in 232.50
solver seconds. Its request and source hashes are checked before preparing
variants.

Two variants keep the block, dictionary, alphabets, bounds and observed-codeword
domains fixed:

| Variant | Selection rule | Interpretation |
|---|---|---|
| free | Any available homophone at each occurrence | A relaxation of text-wide cycles |
| word-reset | Each letter's ordered cycle restarts at each word | A different selection policy |

Word-reset cycles are not a superset of text-wide cycles; SAT there would show
that this alternative can fit the block, while UNSAT excludes that alternative.
Free-choice SAT would show that a fit exists when cyclic choice constraints are
removed. All SAT explanations require independent key, language, encoding,
decoding and selection verification. No key, lengths, boundaries or plaintext
hints are supplied.

Run/resume the two short checks:

```sh
.venv/bin/python -m benchmarks.conflict_selection --resume
```

Prepare inputs without solving:

```sh
.venv/bin/python -m benchmarks.conflict_selection --prepare-only --resume
```

The runner checkpoints each outcome and validates cached requests on resume.
The report is `experiments/results/conflict-selection.json`. Public requests
are under `data/generated/conflict-selection/inputs/`. Each short check gets
30 seconds; construction is additional. UNKNOWN leaves feasibility unresolved.

Longer individual retries:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/conflict-selection/inputs/free.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/conflict-selection-free-30min.json
```

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/conflict-selection/inputs/word-reset.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/conflict-selection-word-reset-30min.json
```

The longer runs are prepared, not launched. None of these finite-vocabulary
results establish the manuscript's language. UNSAT proof certificates are not
independently checked by the report audit.

## Recorded short-run results

| Selection rule | Result | Solver time |
|---|---|---:|
| free | UNKNOWN | 30.07s |
| word-reset | UNSAT | 18.00s |

Word-reset cycles do not resolve the conflict in this fixed model. Free choice
remains unresolved, so only its longer retry is currently needed. Request and
report checks are recorded in `experiments/results/conflict-selection-validation.json`.
All 442 tests pass.

## Independently verified free-selection SAT witness

The user-run longer free-selection retry returned **SAT in 321.07 solver
seconds**. Its request matches the prepared free variant except for the timeout.
Independent validation rechecked input/report hashes, prefix-free key legality,
vocabulary membership, word and code bounds, re-encoding/decoding, segmentation,
and membership of actual emitted codes in the observed substring pool. The
complete plaintext, ordered key and cycle comparison are saved in
`experiments/results/conflict-selection-free-validation.json`.

The plaintext is:

```text
eo id ob at mdc in ac hac ac xl sin id apr ob lx in ad an ac i se idem
```

This is a vocabulary fit, including numeral-like corpus entries, not a
recovered meaningful Latin passage.

| Selection policy | Result on the same fixed block/vocabulary |
|---|---|
| Text-wide cycle | UNSAT, 232.50s |
| Word-reset cycle | UNSAT, 18.00s |
| Free choice | Independently verified SAT, 321.07s |

Removing the cyclic-choice constraint makes this block feasible without changing
the code bounds or vocabulary. Both tested cycle policies are obstructions for
this fixed model, while bounded verbose homophonic coding with free choices can
fit it. This does not identify the manuscript's actual generation rule.

With the witness's saved code order, its choices differ from text-wide cycles
at 24 occurrences and word-reset cycles at 19 occurrences. These are descriptive
counts for this particular witness, not minimum exception counts across keys,
code-list orders or plaintexts. They must not be interpreted as a necessary
number of violations.

The next diagnostic could minimize how many occurrences must depart from
text-wide cycling while keeping the block and vocabulary fixed. It would measure
how much selection flexibility is needed, rather than only comparing exact
cycling with entirely free choice.


Before adding cycle exceptions, the [word-length comparison](word_length_plausibility.md)
identifies a separate structural capacity limit and an unusually short witness.
