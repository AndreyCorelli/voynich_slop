# Public-boundary two-homophone calibration

The extension relaxes one-code-per-letter substitution to **at most two observed
codes per plaintext letter**. Different codes may decode to the same letter;
each code still has one consistent decoding. Code boundaries and two-glyph
lengths remain public, so plaintext word lengths are public too. There are no
nulls. Homophone selection is free in fitting, not constrained to the generating
alternation rule.

## Iteration 1: sound H2 membership and synthetic controls

Reuse three independently selected twelve-type generated-inventory fixtures from
synthetic replication. Each training list is repeated twice (24 occurrences) so
both homophones of every observed letter occur in training. All three novel
holdouts use observed codes. New keys use seeds 6001–6003, with two distinct
codes per alphabet letter, drawn without collision from 64 pairs over eight
glyphs. Generating choices alternate per letter across training and holdout;
fitting does not see that rule, the source words, key or held-out spellings.

The old injective exact-pattern filter is deliberately not used. The new local
filter requires:

- repeated occurrences of a code decode to the same letter;
- at most two distinct codes within a candidate word decode to any one letter.

Distinct codes may now merge into one plaintext letter. This local filter is
sound but not sufficient globally. Shared integer code-decoding variables and
per-letter pseudo-Boolean capacity constraints enforce the global bound of two.
Full default morphology inventory and alphabet remain unchanged. Sparse exact
membership relations represent the surviving candidate subsets.

Shuffle seeds 6101–6103 preserve exact within-word code equality signatures,
lengths and code counts. The H2 model may admit a shuffled fit, so controls are
not stipulated negatives. Both arms have identical nonempty candidate counts.
All six fits are frozen before solving, with unchanged 30-second solver and
60-second worker budgets and durable loading/filtering/construction/solving
checkpoints. First SAT keys alone receive positive training/holdout scores.

```sh
.venv/bin/python -m benchmarks.latin_h2_public --run
.venv/bin/python -m benchmarks.latin_h2_public --validate
```

Artifacts: `experiments/results/latin-h2-public`.

Tests explicitly allow two distinct codes to decode to one letter, reject three,
preserve repeated-code consistency, and exhaustively compare local filtering
against all bounded mappings on small alphabets. No H1 distinctness constraint
is retained by mistake.

## Iteration 2: sound shared-code domain propagation

Freeze exactly the same cases and budgets; change only preprocessing. Each word
supports letter domains for its shared code variables. Intersect those domains
across occurrences/words and drop candidates using unsupported assignments.
When a letter already has two forced code assignments, remove it from other
non-singleton code domains. More than two forced assignments or empty support
is a contradiction. Iterate to a fixed point, then build per-word automata from
the reduced exact candidate subsets and assert the reduced domains in Z3.

This propagation uses neither true plaintext nor key. It removes no valid global
explanation: every removal follows necessary word support or the global capacity
bound. It is not full generalized cardinality propagation or a search algorithm.
Small exhaustive global-solution tests check preservation; dedicated worker tests
check two-code acceptance and three-code rejection after preprocessing.

```sh
.venv/bin/python -m benchmarks.latin_h2_propagation --run
.venv/bin/python -m benchmarks.latin_h2_propagation --validate
```

Artifacts: `experiments/results/latin-h2-propagation`.

Further iterations, if needed, will follow completed results and retain frozen
comparisons. UNKNOWN remains unresolved and holdout accuracy is unevaluated.
No manuscript or hidden-boundary fitting is part of these experiments.

Iteration 1 completed: **all six arms returned UNKNOWN** at the 30-second solver
budget. Filtering took 0.33–0.36 seconds, construction 12.3–14.3 seconds and
solver calls about 30.05 seconds. No positive key was recovered, so accuracy is
unevaluated; no control was accepted or rejected. Full artifact validation passes.
This is a performance limit, not evidence against the generating H2 explanation.

Iteration 2 completed: **all six arms again returned UNKNOWN**. Propagation took
0.66–0.80 seconds; construction 11.7–13.6 seconds. Candidate row reductions on
the first two positives are 412,978→410,536 and 387,806→381,780 (roughly 0.6%
and 1.6%). Necessary local pruning is too weak to resolve this search within
budget. It retains all frozen inputs and previous UNKNOWN records.

## Iteration 3: direct exact candidate relations

Keep the same weak-pattern subsets, propagation, cases and budgets; replace
layered automaton paths with a direct finite disjunction of candidate code-to-
letter assignments. Repeated-code inconsistencies are rejected and shared
letter-equality predicates are cached. Global H2 capacities remain. This removes
auxiliary path-state variables without changing the admissible observed keys.
Small symbolic-equivalence tests and capacity/worker tests pass before full fits.

```sh
.venv/bin/python -m benchmarks.latin_h2_direct --run
.venv/bin/python -m benchmarks.latin_h2_direct --validate
```

Artifacts: `experiments/results/latin-h2-direct`.

## Iteration 4: pure Boolean key representation

If direct integer mappings remain unresolved, isolate the mapping representation
on the first fixed fixture (seed-5101), both positive and shuffled arms. The
selection is the frozen fixture's position, not successful outcomes. Each
code/letter assignment becomes a Boolean selector. Exactly one selector is true
per observed code; at most two are true per plaintext letter. Domains and exact
candidate relations are unchanged. There are no integer key variables or path
states. This represents precisely the same observed-key model as bounded
integer assignments.

```sh
.venv/bin/python -m benchmarks.latin_h2_boolean --run
.venv/bin/python -m benchmarks.latin_h2_boolean --validate
```

Artifacts: `experiments/results/latin-h2-boolean`. Worker tests verify merging
two codes and rejecting three. The smaller two-arm comparison is a representation
smoke test; it is not three-fixture replication or an accuracy estimate.

Iteration 3 completed: **all six arms returned UNKNOWN** at the 30-second solver
budget. Direct relation construction took 16.5–20.1 seconds, slower than layered
membership. It did not resolve any frozen fit. Full artifact validation passes.

Iteration 4 completed: **both first-fixture arms returned UNKNOWN**, construction
17.8–18.2 seconds and solver calls about 30.1 seconds. Removing integer key
variables alone does not solve the large candidate search. Artifact validation
passes. No other fixtures were fitted with this representation.

## Iteration 5: original sampling-pool scale diagnostic

Keep the first fixture's ciphertext, two-code key model, holdout, capacities,
Boolean relations, propagation and budgets. Change the dictionary to the entire
**original 512-word sampling pool** used to generate that fixture, reconstructed
from seed 5101 and the unchanged eligible source list. The pool was sampled
before its twelve training types, holdouts or key were selected. All pool words
are retained; no individual truth words are inserted or selected after outcomes.
Reconstructed pool/automaton artifacts and hashes are frozen before fitting.

This is an assisted controlled-vocabulary diagnostic. Pool membership includes
the held-out forms by construction, though no held-out spellings constrain the
fit. It is not blind language identification or full-inventory H2 calibration.
There are 32,846 complete-inventory forms at public lengths 3–6, so the full
inventory's nominal 2.55-million size overstates the length-compatible search
in these toy fixtures; the useful scale comparison is 512 versus 32,846 forms.

```sh
.venv/bin/python -m benchmarks.latin_h2_pool --run
.venv/bin/python -m benchmarks.latin_h2_pool --validate
```

Artifacts: `experiments/results/latin-h2-pool`.

| Arm | Status | Construction | Solver | Accuracy |
| --- | --- | --- | --- | --- |
| Known H2 encryption | SAT, independently verified | 0.202 s | 0.034 s | 24/24 training, 3/3 novel holdouts |
| Matched shuffle | UNSAT | 0.143 s | 0.00011 s | Not scored against original plaintext |

The positive genuinely uses two codes per observed letter; both are exercised
in training and all holdout codes were previously observed. Candidate occurrences
reduce from 6,374 to 3,908. The shuffle is rejected by a sound shared-domain/
capacity contradiction before substantive Z3 search. Its initial pattern subsets
are nonempty and match the positive counts, so it does not use an empty-pattern
shortcut. This confirms basic H2 recovery at smaller controlled vocabulary scale,
not a general randomized-control rejection rate.

## Five-iteration conclusion

| Iteration | Method | Frozen fits | Outcome |
| --- | --- | --- | --- |
| 1 | Weak-pattern layered membership, integer inverse key | 3 positives + 3 shuffles | 6 UNKNOWN |
| 2 | Add sound support/capacity propagation | Same 6 | 6 UNKNOWN |
| 3 | Direct candidate relations | Same 6 | 6 UNKNOWN |
| 4 | Pure Boolean key mapping | First positive/shuffle pair | 2 UNKNOWN |
| 5 | Original 512-word pool, same Boolean model | Same first pair | Verified SAT positive, UNSAT shuffle |

All five artifact validations pass. Eighteen targeted tests pass: weak-pattern
mapping equivalence, repeated-code consistency, global two-code capacity across
separate words, sound propagation, direct relation equivalence and capacity/
holdout behavior across all four representations and the small-pool variant.

The five-iteration limit is reached. All 20 full-inventory UNKNOWN results remain
stored; none are interpreted as UNSAT or rescored as successes. Holdout accuracy
for those fits remains unevaluated. The small-pool success establishes that the
H2 model/implementation can recover a known two-homophone explanation and
continuation in this assisted setting. It isolates vocabulary/search scale as a
major bottleneck; it does not prove scale is the only bottleneck. Natural full-
inventory H2 recovery, unknown code boundaries and homophone selection rules
remain uncalibrated. The old H1 exact-pattern optimization is unsound under H2
and was never reused here.

Next priority: a frozen **dictionary-size ladder**, retaining the original pool
and adding independently ordered length-compatible forms (e.g. 1,024 and 2,048)
with unchanged ciphertext, budgets, scores and matched control. This should
locate where recovery becomes unresolved and provide smaller reproducible
performance cases before another full-vocabulary or manuscript run. No such
ladder or sixth iteration was implemented here.
