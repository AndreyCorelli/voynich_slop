# Alternative suffix keys with proved exclusions

This milestone searches the same 11-word suffix of the same 23-word prefix,
using the full 5,665-entry Caesar surface vocabulary, H2/L3, globally
prefix-free EVA character codes, preserved word boundaries and text-wide cycles.
It does not relax the language or cipher assumptions.

The initial exclusions are independently checked against the full prefix:

- No letter can have exactly the two homophones `qo` and `y`: mandatory
  word-start occurrences violate both cyclic rotations.
- A key owning `r → cth` and `t → ol` forces `cthol → rt`, outside the vocabulary.
- A key owning `f → d`, `u → a`, `v → m` forces `dam → fuv`, outside the vocabulary.

Each suffix candidate is independently verified and its observed letter mappings
are tested against all 23 words. Unobserved letters remain free; each pinned
letter permits cyclic rotation of its complete code list. An UNSAT core is
retained only after a separate guided solve proves it UNSAT without any learned
clauses. Replay repeats that proof; stored status labels are not certificates.
Core exclusions concern complete mappings, not individual code ownership.

Named owners in word and core exclusions retain real code lists in suffix
solving, even when absent from its plaintext. Removing unvisited alternatives or
completing these owners outside SMT could otherwise change the exclusion's
meaning. Every returned SAT key is checked against the exclusions in Python.

UNKNOWN creates no exclusion. The runner stops on an unresolved extension,
an unresolved suffix solve, no new proved exclusion, or its candidate budget.
There are no temporary candidate blocks that could be mistaken for proofs.
A conditional extension UNSAT rejects the candidate's pinned mappings;
it does not establish full-prefix UNSAT or a probability for Latin plaintext.
The suffix's initial cycle phases may differ from the prefix's, so every retained
mapping exclusion permits cyclic rotations.

```sh
.venv/bin/python -m benchmarks.learned_search
.venv/bin/python -m benchmarks.learned_search --replay data/generated/learned-search-certified/inputs/candidate-01.json
.venv/bin/python -m benchmarks.guided_extension --replay data/generated/learned-search-certified/inputs/extension-00.json
```

The configuration is `experiments/configs/learned-search.json`. The report is
`experiments/results/learned-search.json`; wrappers carry the suffix, full context,
slice offset and self-contained proof inputs. Core replay uses the full context's
recorded timeout, so a later UNKNOWN rejects that replay rather than accepting an
unverified exclusion. Configuration and source hashes accompany the report.

## Recorded result

The configured five-candidate run completed. All five alternative suffix fits
were SAT and independently verified (solver checks 2.89–4.74 seconds). Every
full-prefix extension was conditional UNSAT (0.81–2.07 seconds). Separate core
replays succeeded, and the final report retains 19 proved clauses: seven cycle
pair clauses, seven word clauses and five complete-mapping core clauses.
A saved candidate replay also returned verified SAT.

The candidate budget was exhausted; the full 23-word model remains unresolved.
These results show that alternative local fits can also fail extension, without
providing a statistical likelihood for the manuscript-language hypothesis.

## Full-prefix solve with learned exclusions

The next check applies all 19 retained clauses directly to all 23 words, with
no pinned mappings or plaintext hints. The cipher and vocabulary remain unchanged;
only independently proved consequences are added to the solver formula. Analytic
certificates are rechecked and all five core proofs are separately replayed
against the full context before the unrestricted solve.

The full-prefix solver receives 120 seconds. Proof replay and formula construction
are outside that solver budget and are included in reported wall time. The proof
context retains its original 30-second budget. An inconclusive core replay causes
validation to fail, rather than silently treating a stored UNSAT label as a proof.

```sh
.venv/bin/python -m benchmarks.learned_prefix
.venv/bin/python -m benchmarks.learned_search --replay data/generated/learned-prefix/inputs/full-prefix.json
```

Configuration: `experiments/configs/learned-prefix.json`. Report:
`experiments/results/learned-prefix.json`. The wrapper contains both the complete
request and the proof context. SAT requires independent full-witness verification;
UNSAT would exclude this fixed model for these words; UNKNOWN leaves feasibility
unresolved. None of these outcomes supplies a manuscript-language probability.

The full-prefix run returned **UNKNOWN (timeout)**: 120.09 seconds in the
solver and 160.51 seconds total, including proof replay and construction. All
19 exclusions were validated; no mappings were pinned. The earlier unrestricted
trie solve without these clauses also returned UNKNOWN at 120 seconds. Thus the
learned clauses did not resolve feasibility within this budget. All 347 tests pass.
The next useful milestone is solver performance and full-vocabulary synthetic
recovery calibration, rather than expanding the cipher or collecting more suffix fits.
