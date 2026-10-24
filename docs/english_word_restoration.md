# Separate English-word restoration

The corrected 23-word H2/L3 model with `i/iv/iulius` restored returned UNSAT in
273.64 seconds. These variants retain those three additions and add only `by`,
only `of`, or both. The both-word variant has an independently verified existing
SAT witness. The separate variants are fully hidden fresh searches with no key,
length or segmentation hints.

Scientific parameters and entry ordering are preserved. Each separate variant
has 5,659 vocabulary entries; the both-word variant has 5,660. Each short fresh
search has a 30-second solver budget. UNKNOWN does not establish necessity of
an excluded word, especially given the baseline's longer UNSAT solve.

Run/resume the short diagnostic:

```sh
.venv/bin/python -m benchmarks.vocabulary_restoration --group english --resume
```

Preparation without solving:

```sh
.venv/bin/python -m benchmarks.vocabulary_restoration \
  --group english --prepare-only --resume
```

Report: `experiments/results/english-word-restoration.json`.
Inputs: `data/generated/english-word-restoration/inputs/`.
The earlier restoration report and inputs are retained separately.

Longer retries, to run from the repository root:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/english-word-restoration/inputs/restore-i-iv-iulius-by.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/restore-i-iv-iulius-by-30min.json
```

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/english-word-restoration/inputs/restore-i-iv-iulius-of.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/restore-i-iv-iulius-of-30min.json
```

The 30-minute retries are prepared, not launched. If both return UNSAT while the
both-word variant remains SAT, both words are necessary within this particular
comparison. A SAT result for one variant instead establishes that its one English
addition suffices. These conclusions do not generalize to a broader Latin
vocabulary or a different cipher model. Saved UNSAT results require provenance
checks; no independent proof certificate is claimed.

## Recorded short-run results

| English additions | Status | Fresh solver time |
|---|---|---:|
| by | UNKNOWN | 30.09s |
| of | UNKNOWN | 30.08s |
| by, of | SAT | Existing witness; no new solve |

Both one-word variants remain inconclusive. The both-word variant is SAT by
independent witness validation. Neither word has yet been proved necessary.
All 424 tests pass.

## Completed long-run comparison

Both user-run one-word retries returned UNSAT. The saved requests match their
prepared inputs except for the 1,800,000 ms timeout. Each retains `i/iv/iulius`
and adds exactly its named English word. The both-word witness was independently
verified again. The audit with report and input hashes is
`experiments/results/english-word-restoration-validation.json`.

| English additions to the fixed i/iv/iulius base | Result | Solver time |
|---|---|---:|
| None | UNSAT | 273.64s |
| by | UNSAT | 334.41s |
| of | UNSAT | 306.72s |
| by, of | SAT | Existing independently verified witness |

Both `by` and `of` are necessary and jointly sufficient within this two-word
add-back comparison. Every legal SAT explanation in the both-word vocabulary
must use both words: omitting either would give a witness for a one-word model
that returned UNSAT. This does not prescribe which positions use those words,
prove the recovered text is meaningful, or establish necessity under other
vocabulary extensions or different cipher assumptions.

UNSAT report provenance and request consistency were checked; no independent
UNSAT proof certificate was checked. Historical short-run UNKNOWN records remain
unchanged.

The next diagnostic is the shortest UNSAT prefix under the fixed i/iv/iulius
base. It can isolate the obstruction before adding another corpus or relaxing
the cipher assumptions.


The [prefix-search runner](clean_latin_prefix.md) now implements this diagnostic
with independent SAT checks and a checkpointed longer-run command.
