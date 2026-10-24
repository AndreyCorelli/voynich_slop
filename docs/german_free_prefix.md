# Minimal free-selection German prefix

The completed user-run search establishes an exact boundary: **28 words
independently verified SAT, 29 words solver-reported UNSAT**. Adding word 29,
`otaldam`, makes the contiguous prefix impossible within the fixed model.
This is a minimal prefix, not necessarily a minimal conflicting subset.

| Prefix | Result | Solver seconds |
|---|---|---:|
| 26 | Verified SAT | 36.83 |
| 28 | Verified SAT | 45.11 |
| 29 | UNSAT | 42.46 |

The [validation](../experiments/results/german-free-prefix-validation.json)
checks every saved request hash, unchanged scientific parameters and exact
prefix, and independently rechecks all SAT witnesses. The reported boundary
agrees with the saved results. UNSAT remains solver-reported, without an
independently checked proof certificate. There are no unresolved prefix sizes.

The fixed source-143 free-selection H2/L3 model is independently verified SAT
at 23 words and solver-reported UNSAT at 30. The first excluded prefix lies
between 24 and 30 words. This search varies only the length of the same
contiguous clean Voynich block; dictionary, alphabets, coding bounds, word
boundaries and free selection remain fixed. Each request infers one shared
key for its whole prefix. It does not freeze a previously recovered key.

The first probe, at 26 words, returned UNKNOWN in 30.10 seconds with a
30-second budget. Neither boundary moved at that stage. The subsequent
30-minute-budget search completed with the results above.

The checkpoint is
[german-free-prefix.json](../experiments/results/german-free-prefix.json).
It includes source hashes, requests, input hashes, results and SAT/UNSAT bounds.
Prepared inputs are separated by timeout under `data/generated/german-free-prefix/`.

## Reproduce or inspect locally

```sh
.venv/bin/python -m benchmarks.german_free_prefix \
  --timeout-ms 1800000 --resume
```

The completed checkpoint returns without rerunning solved inputs. In a fresh
search, the larger budget retries 26 words first. A decisive result moves one bound
and selects the next midpoint. At most three decisive midpoint solves are
needed from the initial bracket. Each solver receives up to 30 minutes,
with formula construction adding wall time. Results are saved after each
solve. The script stops on UNKNOWN and leaves its request available, without
calling a timeout UNSAT or claiming minimality.

Resume checks unchanged source reports and analysis code, exact nested
prefixes, request hashes and scientific settings. Cached SAT witnesses are
independently re-encoded and decoded. Imported UNSAT and newly solved UNSAT
are solver-reported; independent proof certificates are not checked.

Preparation alone can use `--prepare-only --resume`. Tests cover fixed
parameters, the initial midpoint, UNKNOWN preserving bounds, retrying an
unresolved prefix with a larger budget, rejecting tampered checkpoints and
shrinking an UNSAT bound without premature minimality. Nine focused tests
passed across prefix search and free-selection preparation.

The result concerns this finite dictionary and bounded cipher model, not
German generally or grammatical plaintext.
The completed [suffix reduction](german_free_suffix.md) reduces the conflict
to original words 5–29. Deleting either endpoint gives independently verified
SAT, establishing minimality under contiguous trimming.
