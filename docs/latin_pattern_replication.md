# Independent exact-pattern synthetic replication

Iteration 1 freezes three new fixtures with training-selection seeds 5101–5103,
key seeds 5201–5203 and pattern-preserving shuffle seeds 5301–5303, before any fit.
Each selection samples 512 forms uniformly without replacement from the complete
32,846-form length-3..6 subset of the unchanged default inventory. Twelve greedy
new-letter-coverage words are selected with lexical tie breaking; the first
three remaining covered forms become novel holdouts. Independent selection can
share forms across fixtures; this is replication across seeds, not independent
historical texts. All selected forms are mechanically generated, not assumed
attested prose.

Both arms keep the full source alphabet and inventory, known two-glyph code
boundaries and public word lengths, and a shared injective H1 substitution key.
Exact equality-pattern filtering uses ciphertext only. Shuffles preserve exact
per-word equality patterns, code-count multisets and lengths. They are randomized
controls, not guaranteed negatives. No true letters, key or holdout constrain
fitting. First SAT keys are scored without rescue or alternative-key selection.

The existing pattern-filter worker is reused unchanged, with its code identity
pinned along with selection, pattern, automaton and shuffle code. Each arm has a
30-second solver budget and 60-second external worker limit with durable phase
checkpoints. All six fits are reported, including UNKNOWN and process timeouts.
A fixture-selection test checks deterministic generation, novelty and letter
coverage; existing worker and pattern tests cover the unchanged solver.

```sh
.venv/bin/python -m benchmarks.latin_pattern_replication --run
.venv/bin/python -m benchmarks.latin_pattern_replication --validate
```

Artifacts: `experiments/results/latin-pattern-replication`. Validation regenerates
selection and verifies source identities, generating explanations, shuffle
invariants, candidate counts, SAT explanations and frozen scores. Accuracy is
unevaluated for non-SAT positives, not counted as zero. UNSAT has no independently
checked proof certificate. No manuscript experiment is part of this replication.

Further iterations, up to the requested maximum of five, will be chosen only if
results reveal a useful specific refinement. Existing results and frozen inputs
will be retained for comparisons; no outcome-based fixture replacement.

## Iteration 1 results

| Fixture | Observed letters | Positive solver | Training exact | Holdout exact | Shuffle solver/status |
| --- | --- | --- | --- | --- | --- |
| seed-5101 | 23/23 | 1.768 s, SAT | 12/12 | 3/3 | 1.429 s, UNSAT |
| seed-5102 | 22/23 | 2.744 s, SAT | 12/12 | 3/3 | 1.270 s, UNSAT |
| seed-5103 | 22/23 | 1.135 s, SAT | 12/12 | 3/3 | 0.770 s, UNSAT |

All three positives independently verify and total **36/36 training words** and
**9/9 held-out word occurrences**. All three shuffled controls return UNSAT.
No UNKNOWN or process timeout occurs. Both arms of each fixture have identical
nonempty per-word candidate counts: none of the rejections uses an empty-pattern
shortcut. Filtering takes 0.255–0.275 seconds and construction 2.000–2.492
seconds. Nine targeted tests pass; full six-arm artifact validation passes.

## Analysis and iteration decision

The prior success reproduces across new word-selection and key seeds within the
same generated-inventory setting. Faster first-key fits correctly predict the
frozen holdouts and reject three more challenging randomized controls. This
resolves the immediate question of whether success depended on the original
fixture, without changing model, budgets or scoring.

**Stop after iteration 1.** The request allows up to five iterations when needed;
no timeout, incorrect prediction or accepted shuffled control identifies a
specific defect to refine here. Additional tuning on these successful fixtures
would provide little evidence. All earlier failures and timeouts remain stored;
no result was overwritten or discarded.

This is not a measured population accuracy or false-fit rate: there are only
three paired controls, coverage is engineered to be high, short word lengths
and atomic boundaries are public, and selected words are drawn from the same
morphology inventory used by the solver. Greedy lexical tie breaking can bias
selected forms and prefixes; different seeds do not remove that bias. The
second-key uniqueness audit from the original fixture has not been repeated on
these three keys. Correct first-key predictions are reported without inferring
uniqueness. No conclusion about Voynich plaintext or language follows.

The next useful external-validity check is a **frozen natural Latin passage
control** with independently generated morphology membership: public fixed
boundaries/lengths first, novel covered holdout, and the same pattern-preserving
shuffle. Before solving, report inventory coverage and apply a predeclared
coverage rule; do not silently inject missing words or select a passage because
it later solves. This is the next recommendation, not implemented in this run.
Hidden boundaries, multiple homophones and manuscript fits remain separate
model extensions requiring calibration.
