# Public shortest-first word-length search

The search derives candidate lengths solely from the standard public recovery
request. For each observed word, vocabulary candidates are pruned by ciphertext
size, code-length bounds and the existing sound prefix relations. Their distinct
lengths form a finite domain. A heap enumerates the Cartesian product in increasing
total plaintext length, with lexicographic tie-breaking. Necessary length relations
for identical words and complete ciphertext prefixes remove incompatible vectors.
All allowed vectors remain in the enumeration; the search never uses truth files.

Each vector defines a fresh conditional solve with lengths fixed and plaintext,
key, segmentation and homophone choices unknown. The ordinary H2/L3 prefix-free
model and full vocabulary remain unchanged. SAT requires independent witness
verification and establishes a fit for the full public instance. An UNSAT branch
rejects that length vector only. UNKNOWN is preserved as unresolved and does not
prevent later vectors being tried. Global UNSAT requires exhaustion of the entire
admissible enumeration with every branch proved UNSAT. Hitting the branch budget
returns UNKNOWN unless a verified SAT fit was found.

The initial experiment uses the saved seed-7 four-word control and full eleven-word
control. Each branch gets ten seconds; each case permits up to twelve solves.
Construction adds to elapsed time. These limits define an exploratory search,
not a complete exclusion experiment. No codebook, plaintext, original word-length
vector, segmentation or synthetic truth is loaded by the runner. The full dictionary
remains 5,665 entries. Cases start independently and do not share recovered keys.

```sh
.venv/bin/python -m benchmarks.length_search
.venv/bin/python -m benchmarks.segmentation_diagnostic \
  --replay data/generated/length-search/inputs/case-00-branch-000.json
```

Replay fixes the recorded publicly chosen branch; it does not repeat enumeration.
Configuration: `experiments/configs/length-search.json`. Results:
`experiments/results/length-search.json`. Each branch has a saved wrapper and input
hash. Reports preserve all statuses, length domains, the raw Cartesian-product
size, exhaustion status and overall scope. The raw product includes vectors removed
by necessary prefix/equality relations.

Tests prove enumeration order, completeness and uniqueness on small products.
They exercise all-UNSAT exhaustion, UNKNOWN retention, budget exhaustion, subsequent
SAT after an unresolved branch, and public equality/prefix length filtering.
Single-run timings are observations, not a statistical speedup estimate.

## Recorded result

| Control | Branches tried | Overall result | Total time |
|---|---:|---|---:|
| 4 words | 1 | SAT | 3.28s |
| 11 words | 12 | UNKNOWN | 146.46s |

The four-word control succeeded on its first public vector `[9, 5, 6, 7]`
in 2.55 seconds of solver time. Its lengths differ from the original generation
vector `[9, 5, 6, 8]`; that vector was not consulted by this search. The verified
fit therefore demonstrates full-vocabulary hidden recovery for this four-word
instance without an oracle, despite the ordinary monolithic solve timing out.

All twelve eleven-word branches returned UNKNOWN at ten seconds; none was
rejected, and the enumeration was not exhausted. The full eleven-word positive
control remains unresolved. The trial budget limits what this experiment can
show; it does not rule out these vectors or the complete model. All 392 tests
pass, including classification of exhausted and unresolved searches.

## Intermediate controls

A separate calibration applies the same public length search to saved six- and
eight-word seed-7 prefixes. Each branch receives 30 seconds, with at most four
shortest-first branches per case. The full vocabulary, cipher and cycle formula
remain unchanged. These budgets sample an initial part of the search rather than
exhausting its admissible vectors. Branch UNSAT and UNKNOWN retain their distinct
meanings; no generation truth is read.

```sh
.venv/bin/python -m benchmarks.length_search \
  --config experiments/configs/length-search-intermediate.json \
  --output experiments/results/length-search-intermediate.json \
  --artifacts data/generated/length-search-intermediate
```

The separate configuration, result and input directory preserve the earlier
four/eleven-word run. Existing unit tests cover enumeration and branch-result
classification; the intermediate run changes only configuration and public inputs.

| Intermediate control | Branch outcomes | Total time |
|---|---|---:|
| 6 words | UNSAT, UNKNOWN, UNKNOWN, UNSAT | 100.40s |
| 8 words | UNSAT, UNKNOWN, UNKNOWN, UNSAT | 111.18s |

Neither intermediate control yielded a verified fit in four branches. Each
had two conditional UNSAT results and two unresolved branches; neither enumeration
was exhausted. The full six/eight-word models remain UNKNOWN. A separate
[engine comparison](solver_engines.md) rechecks the first stalled six-word vector
using identical constraints and budgets. All 394 tests pass.

Optional [diverse orderings](length_orderings.md) now interleave diagonal length
sweeps or favor lengths with greater public candidate support. They preserve the
allowed vectors and result-classification rules; shortest-first remains the default.
