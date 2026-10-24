# Sequence scoring inside shared-key feasibility search

The separate language-ranked plaintext beam rejected every proposal, even for
covered positives. This single-case diagnostic keeps the shared-key dictionary
constraints active while searching for a better training score. It tests the
saved weaker positive (`block-2-synthetic`) from coverage calibration: sixteen
training words, four continuation words, twelve-word Latin vocabulary, free
H2/L1–3 and complete generating-code coverage for continuation.

This is retrospective method development on a known synthetic case, not fresh
blind validation. The reference score is unchanged. No continuation score,
generating key, seed search or expanded budget enters recovery.

## Implementation

The internal finite hidden-dictionary solver accepts optional integer language
weights for initial words and adjacent pairs. The benchmark rounds the frozen
add-one log probabilities to thousandths. The sum of these weights is linked
to symbolic dictionary words; all original shared-key constraints remain.

First obtain a feasible SAT model. Then assert that its integer training score
must improve strictly and check again, retaining the latest feasible model.
At most three checks share a five-second timeout allocation. An improvement
UNSAT proves integer-score optimality within the model; UNKNOWN retains the
independently verified SAT incumbent and records unresolved optimality. No
optimality claim is made merely because an incumbent exists.

The comparison arm uses ordinary used-ownership enumeration, the same three
check cap and five-second total allocation. It selects its best returned key by
the unchanged floating-point training score. Guided search uses the rounded
integer objective; rounding is explicit and scores are independently recomputed.
Construction time is separate from the solver budget, and timeout overhead may
slightly exceed the nominal cap. Both candidate sets/selections are frozen
before continuation evaluation. The earlier ordinary score of 1/4 is not reused:
a fresh matched ordinary run is the comparator, and returned witnesses vary.

## Recorded result

| Arm | Feasible fits | Selected exact words | Novel exact words | Dictionary hits |
| --- | --- | --- | --- | --- |
| Ordinary | 2 SAT; third UNKNOWN | 2/4 | 2 | 3/4 |
| Feasible guided | SAT; improvement UNKNOWN | 1/4 | 0 | 1/4 |

Ordinary selected mean training log score is -2.430362 (integer sum -38883).
Guided returns -2.666189 (integer sum -42659). It finds an initial key in 1.14
seconds, then spends 3.96 seconds on an improvement check that times out. No
better feasible incumbent is found. Thus **this method does not clear the
unseen-word improvement gate under the fixed budget**. It does not prove that
its attainable optimum is worse; that search is unresolved.

Ordinary check times total 5.02 seconds; guided checks total 5.11 seconds including
timeout overhead. Construction takes 0.23–0.25 seconds per ordinary call and
0.31 seconds for guided search. Both selected fits obey the complete cipher and
dictionary constraints. Missing true homophones do not explain this case:
continuation's generating codewords are all covered.

## Validation and artifacts

Implementation is split between `src/voynich_smt/solver/language_objective.py`,
the optional internal recovery argument, and
`benchmarks/feasible_sequence_search.py`. Default recovery behavior retains its
ordinary constraint model. Historical calibration reports are preserved with
their original code identities; they should not be overwritten by rerunning
changed solver code.

Protocol, integer weights, source/code identities, complete models, check traces,
frozen predictions and independent validation are in
`experiments/results/feasible-sequence-search/`. Existing protocol prevents a
silent rerun. Eleven focused tests pass, including a tiny proved optimum,
strict score improvement, bounded check count, invalid-table rejection and a
forced UNKNOWN improvement that retains a verified SAT incumbent. Separate
validation reproduces all three fits' scores and predictions without new solves.

```sh
.venv/bin/python -m benchmarks.feasible_sequence_search
.venv/bin/python -m pytest -q tests/integration/test_feasible_sequence_search.py \
  tests/integration/test_tiny_word_sequence.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/feasible-sequence-search/validate.py
```

## Decision

Honor the stopping rule: pause statistical-guidance experiments rather than
increase this case's budget or tune on its continuation. Ordinary recovery
remains the baseline. The next useful calibration branch is harder negative
controls that retain local glyph structure and repetitions. This result does
not decide Latin versus German, contractions versus expansions, or a Voynich
language hypothesis.
