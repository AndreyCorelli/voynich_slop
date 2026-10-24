# Vocabulary robustness of the 19-word German conflict

The four longer retries all returned **independently verified SAT**. The
19-word conflict is therefore vocabulary-dependent within this cipher model:
the source-143 dictionary and two further dictionaries exclude it, while four
other regional dictionaries admit fits with the same ciphertext and rules.
Only vocabulary and its alphabet change; dictionary fits do not establish
grammatical German or identify the manuscript language.

| Source | Regional vocabulary | Longer result | Solver seconds | Mean plaintext word length |
|---|---|---|---:|---:|
| 123 | Swabian | Verified SAT | 952.32 | 2.16 |
| 133 | East Franconian | Verified SAT | 207.03 | 2.63 |
| 153 | Ripuarian | Verified SAT | 425.87 | 2.21 |
| 233 | Alsatian | Verified SAT | 793.77 | 2.58 |

The [long checkpoint](../experiments/results/german-vocabulary-robustness/budget-1800000ms.json)
contains all four results. Its
[independent validation](../experiments/results/german-vocabulary-robustness/long-validation.json)
checks exact ciphertext and fixed settings, source-vocabulary and input
hashes, dictionary membership, key bounds, prefix-freeness and complete
encoding/decoding round trips. Full recovered plaintexts are saved there.
There are no unresolved vocabularies in this comparison after combining the
short and long runs: four SAT, three solver-reported UNSAT including the
source-143 baseline, and two direct minimum-word-length exclusions.
These results use the original vocabularies. The later
[provenance audit](german_regional_audit.md) identifies artificial fragments
and nonlexical/unresolved forms in the other three SAT witnesses, with
separate corrected variants prepared. It does not claim those corrected
variants are SAT.

This comparison tests whether the source-143 exclusion survives changing the
finite vocabulary. It holds the inclusion-minimal 19-word conflict fixed and
tests each of the other eight existing regional German vocabularies separately.
Only the dictionary, its plaintext alphabet and solver budget change.

All requests use free homophone selection, one shared global prefix-free
H2/L3 key, preserved word boundaries, no nulls, no contractions, finite/trie
recovery and observed code domains. Full vocabularies retain their historical
normalization; there is no pooling, modern spelling conversion, frequency
filter or added word. The fixed input is the noncontiguous subsequence
identified by the [word-deletion diagnostic](german_word_deletions.md).

The source-143 19-word UNSAT replay is checked against its input hash and
rebuilt source vocabulary, retained as the baseline, and not rerun. Other
source requests are independently saved with their source manifests,
vocabulary and input hashes, one-letter entries and length certificates.

## Interpreting the comparison

Sources 113 (Kottanerin) and 243 (Hessian) have no one-letter vocabulary entries.
They cannot encode the fixed ciphertext word `s` without compression or
boundary changes. These get `UNSAT_BY_LENGTH`, a necessary emission-length
certificate, with no solver call. They do not count as new exclusions based
on the shared-key structure. The other six sources pass this preflight.

SAT for any other vocabulary would establish that the source-143 conflict is
vocabulary-dependent within this model. UNSAT across the other eligible
vocabularies would provide a broader bounded exclusion, while remaining
finite-dictionary tests. UNKNOWN provides neither conclusion. Neither SAT
nor UNSAT identifies a manuscript language, and dictionary membership does
not demonstrate grammatical prose.

The short checkpoint is
[budget-30000ms.json](../experiments/results/german-vocabulary-robustness/budget-30000ms.json).
The configured budget limits solver checks, with formula construction adding
wall time. Probes are sequential and results are saved after each source.

## Recorded short results

| Source | Regional vocabulary | Result | Solver seconds |
|---|---|---|---:|
| 113 | Kottanerin | UNSAT_BY_LENGTH | No solver call |
| 123 | Swabian | UNKNOWN | 30.10 |
| 133 | East Franconian | UNKNOWN | 30.08 |
| 153 | Ripuarian | UNKNOWN | 30.07 |
| 223 | East Swabian | UNSAT | 8.38 |
| 233 | Alsatian | UNKNOWN | 30.09 |
| 243 | Hessian | UNSAT_BY_LENGTH | No solver call |
| 253 | Thuringian | UNSAT | 2.89 |

At the short-budget stage, together with the original source-143 result, the exclusion held
for three individual dictionaries that pass the length preflight. The two
length-excluded dictionaries and four unresolved dictionaries must be kept
separate. No new SAT fit has been found, but this short comparison does not
establish UNSAT for all eligible German vocabularies.

The [validation](../experiments/results/german-vocabulary-robustness/validation.json)
checks the fixed model, vocabulary and request hashes, length certificates
and checkpoint summary. Solver-reported UNSAT lacks independently checked
proof certificates.

## Reproduction

```sh
.venv/bin/python -m benchmarks.german_vocabulary_robustness --resume
.venv/bin/python -m pytest -q tests/integration/test_german_vocabulary_robustness.py
```

`--sources` selects individual source identifiers; `--prepare-only` prepares
requests without solving. A changed budget creates a separate checkpoint and
input folder. Resume checks budgets, source/code hashes, source identities,
public requests and cached length certificates, and independently verifies
any SAT witnesses. Completed UNKNOWN rows are skipped on resume; use a new
budget to retry them.

Only the four UNKNOWN sources have 30-minute retry inputs prepared. Run
the checkpointed batch locally:

```sh
.venv/bin/python -m benchmarks.german_vocabulary_robustness \
  --sources 123 133 153 233 \
  --timeout-ms 1800000 --resume
```

This command now resumes the completed longer checkpoint without rerunning
solved rows. Its checkpoint and input folder are separate from the short
probes. In a fresh run, four 30-minute budgets plus construction time are
available; the recorded solves finished in the times above.

The focused suite passed 28 tests across robustness, historical German
selection and deletion checks. It covers fixed-model request replacement,
separating length exclusions from UNKNOWN, checkpoint tamper rejection,
budget separation, preparation without solving and invalid source selection.
