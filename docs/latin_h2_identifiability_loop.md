# Seven fresh-fixture H2 identifiability iterations

Seven cases were frozen before fitting: seeds 7101 and 7102 each at 12, 18 and
24 distinct training forms, followed by an independent 24-form seed-7103 case.
Each form appears twice consecutively. Every family has six new novel holdouts,
a new key and matched shuffle, and its own unchanged 32,768-form dictionary.

Selection reconstructs a whole 512-form sampling pool from the complete default
inventory of 32,846 length-3–6 forms. Twelve initial training types maximize
letter coverage greedily; six covered holdouts are sampled with a separate seed;
additional training types are independently shuffled from remaining pool forms,
excluding holdouts. The dictionary retains the entire generating pool and adds
forms in the existing extension-seed-6201 order. No individual truth forms are
added, no fixtures are replaced, and no fit or holdout score affects selection.
These are generated Latin forms, not natural prose or manuscript windows.

Within each family, adjacent duplicate blocks make the shorter training
ciphertext an exact prefix of the longer one. Key, dictionary and held-out
ciphertext are identical across its three levels. The generating per-letter
alternation is not constrained in the fitted model: fitting still permits free
choice among up to two two-glyph codes per plaintext letter, with public word
boundaries and fixed code width. Membership uses the unchanged Boolean graph,
matching-capacity filtering and joint candidate semijoins.

Each first fit and matched-control fit gets 30 seconds of Z3 search and a
60-second worker cap including construction. First returned keys are scored.
A separate worker then excludes that entire observed-code key and searches for
another admissible key, with its own identical budget. SAT verifies an
alternative, UNSAT establishes observed-key uniqueness in this bounded model,
and UNKNOWN leaves uniqueness unresolved. If a first key differs from the
known generating key, that known key is independently verified as a distinct
training witness instead of performing a redundant search; this shortcut was
not needed in the actual seven cases. Alternatives never replace first scores.

| Iteration | Seed | Distinct training types | First fit / exact train | Novel holdout | Propagation seconds | Z3 seconds | Shuffle | Exclude first observed key |
|---:|---:|---:|---|---|---:|---:|---|---|
| 1 | 7101 | 12 | SAT, 24/24 | 6/6 | 2.018 | 0.0022 | UNSAT | UNSAT |
| 2 | 7101 | 18 | SAT, 36/36 | 6/6 | 2.416 | 0.0021 | UNSAT | UNSAT |
| 3 | 7101 | 24 | SAT, 48/48 | 6/6 | 2.541 | 0.0019 | UNSAT | UNSAT |
| 4 | 7102 | 12 | SAT, 24/24 | 6/6 | 2.170 | 0.0019 | UNSAT | UNSAT |
| 5 | 7102 | 18 | SAT, 36/36 | 6/6 | 2.390 | 0.0020 | UNSAT | UNSAT |
| 6 | 7102 | 24 | SAT, 48/48 | 6/6 | 2.656 | 0.0019 | UNSAT | UNSAT |
| 7 | 7103 | 24 | SAT, 48/48 | 6/6 | 2.189 | 0.0020 | UNSAT | UNSAT |

Propagation reduces every positive training occurrence to one candidate;
construction takes 0.030–0.035 seconds. Exclusion searches take about 0.001
seconds after rebuilding the same filtered relations. All seven shuffles are
contradictory under propagation; their construction still costs 0.68–5.27
seconds even though Z3 checks are effectively immediate. Timings are single runs.

At the common 24-type setting, three independent families recover **144/144
training occurrences and 18/18 novel holdouts**, with unique observed mappings.
Repeated scores of the same six holdouts at multiple levels are not independent
new samples. Seed 7101 observes 42 codes (21 letters); seeds 7102 and 7103
observe 44 (22 letters). Unused generating letters are `k,z` for seed 7101 and
`k` for the other two. Uniqueness concerns observed codes; unobserved full-key
assignments remain unspecified.

## What the result establishes and leaves open

The fresh seed-7101 and seed-7102 cases are already unique with twelve types.
Increasing diversity preserves their success, but this loop does **not** show
that broader training was needed, establish a universal threshold, or eliminate
the prior seed-5101 ambiguity. That earlier case remains stored with its two
valid training explanations and original 20/24, 2/3 first-key scores.

The new adjacent duplication layout differs from the earlier two-pass layout
(`types + types`). Both expose two homophones, but arranging the generating
alternation differently changes which cipher codes co-occur across words. The
nested design was chosen before fitting to hold earlier ciphertext fixed; it
may also make these fixtures easier. Fresh sampling pools, keys and letter
coverage differ as well. These differences prevent attributing the observed
improvement solely to additional training types or generalizing it to arbitrary
H2 encryptions. The solver is not told that adjacent words have equal plaintext.

The next most useful check is therefore a **matched duplication-layout
comparison**: hold fresh families' types, keys, dictionaries and holdouts fixed,
generate adjacent-block and two-pass encryptions, and compare first-key recovery
and observed-key uniqueness under the same budgets. The holdouts have now been
inspected, so this would be an adaptive diagnostic; independent fresh families
are needed for replication. No eighth iteration was run here.

A remaining vocabulary gap also matters: 32,768 forms omit 78 of the complete
32,846 length-compatible default forms. Closing this gap is required before
claiming complete default-inventory H2 calibration for these public-length
cases. Historical vocabulary coverage, natural-text H2, variable boundaries and
manuscript inference remain uncalibrated. UNSAT results have no separately
checked proof certificate; they apply only to the implemented bounded model.

## Validation and reproduction

Eleven targeted tests pass: nested training/held ciphertext and novel selection,
unique/ambiguous key exclusion, six compressed-relation equivalence cases and
three existing H2 solver/capacity checks. Artifact validation regenerates frozen
inputs and candidate pruning, verifies first fitted keys and training membership,
recomputes first-key holdout scores, and checks all seven exclusion records and
provenance. Fourteen fit arms and seven ambiguity records validate successfully.

```sh
.venv/bin/python -m benchmarks.latin_h2_identifiability --run
.venv/bin/python -m benchmarks.latin_h2_identifiability --validate
```

`experiments/results/latin-h2-identifiability/prepared.json` pins inputs, seeds,
source and code hashes. Each case directory contains per-arm results and phase
checkpoints, a report and validation; ambiguity results/checkpoints are separate
from first fits. Root `validation.json` records all seven completed iterations.
Existing results are reused without refitting or changing first-key scores.
