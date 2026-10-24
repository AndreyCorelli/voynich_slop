# Seven-iteration compressed H2 membership comparison

This loop compares exact word-membership encodings after the same frozen
matching-capacity and pairwise candidate-support pruning. Ciphertext, dictionary,
Boolean code-to-letter variables, two-code capacity, first-key scoring and
30-second solver/60-second worker budgets are unchanged. Existing frozen files
were not edited. All six initial comparison inputs were prepared before fitting.

Three encodings accept the same finite candidate language:

- **Integer paths:** minimized word automaton with integer states per position;
  map Booleans are translated to letter indices for the existing layered helper.
- **Boolean graph:** recursively shared suffix expressions over a minimized
  automaton, using the existing map Booleans directly and no auxiliary states.
- **Defined Boolean graph:** the same graph with explicit Boolean node variables
  and equivalence constraints. Node names are unique to each training occurrence.

Repeated codes still share one map assignment. Different codes may share a
letter, subject to the existing global capacity. Empty candidate lists encode
False. Six exhaustive small assignment tests verify existential membership
against the direct relation, including repeated codes and empty lists. An empty-
inventory handling defect found by these tests was fixed before inputs froze.

| Iteration | Encoding, fixture | Forms | Positive | Propagation / construction / solver seconds | Exact training / holdout | Shuffle |
|---:|---|---:|---|---|---|---|
| 1 | Integer paths, 5101 | 16,384 | SAT | 4.197 / 1.134 / 28.336 | 24/24, 3/3 | UNSAT |
| 2 | Integer paths, 5101 | 32,768 | UNKNOWN | 6.717 / 8.353 / 30.043 | Unevaluated | UNSAT |
| 3 | Boolean graph, 5101 | 16,384 | SAT | 4.318 / 0.403 / 0.143 | 24/24, 3/3 | UNSAT |
| 4 | Boolean graph, 5101 | 32,768 | SAT | 6.826 / 3.015 / 14.252 | 20/24, 2/3 | UNSAT |
| 5 | Defined Boolean graph, 5101 | 16,384 | SAT | 4.257 / 0.494 / 0.069 | 24/24, 3/3 | UNSAT |
| 6 | Defined Boolean graph, 5101 | 32,768 | SAT | 6.835 / 3.465 / 16.531 | 20/24, 2/3 | UNSAT |
| 7 | Selected Boolean graph, 5102 | 16,384 | SAT | 3.361 / 1.499 / 0.698 | 24/24, 3/3 | UNSAT |

The earlier direct encoding took 0.72 seconds to construct and 0.14 seconds to
solve at 16,384, and remained UNKNOWN at 32,768 (10.04 seconds construction plus
30.06 seconds search). Integer paths regress on the resolved case. Boolean
graphs reduce large-case construction and resolve a previously unresolved fit.
These are single-run timings, not repeated performance estimates.

Iteration 7 selects an encoding without holdout accuracy: require SAT on the
16,384-form positive; prefer SAT on the 32,768-form positive with least total
worker elapsed; otherwise choose least construction time on the completed large
case, breaking ties by mode name. Two tests cover the selection rule. This
selects the Boolean graph. The unchanged independent seed-5102 16,384-form input
from the prior loop is replayed as a representation regression. It is an already
inspected synthetic fixture, not a new blind holdout or independent replication
of the large-case result. Its input and selection provenance are frozen before
this fit. It recovers all training and holdout words. Search is slower than the
prior direct fit (0.70 versus 0.46 seconds), while construction is faster (1.50
versus 2.82 seconds); compression is not a universal search-speed improvement.

## The larger fit exposes ambiguity

Both Boolean variants' first returned keys differ from the generating key on
three observed codes: `qr` maps generating `o` to fitted `r`, `sq` maps `r` to
`s`, and `ts` maps `s` to `o`. Each key satisfies the global two-code capacity,
and every decoded training word belongs to the frozen dictionary. Fitted
`adluor` replaces generating `adluso`, and `aptos` replaces `aptor`, each in two
training occurrences. On holdout, `abites` replaces `abiter`; `abig` and `abitam`
remain exact. Scores are retained without selecting a different key.

The generating key and first fitted key are therefore two verified valid
training explanations. This directly demonstrates non-identifiability at this
vocabulary size and training sample; a second exclusion fit is unnecessary to
establish their existence. `ambiguity-analysis.json` records both comparisons,
input/result hashes, code changes and predictions. It is reproduced and checked
by `benchmarks.latin_h2_compressed_analysis` without additional solver runs.

This is an assisted synthetic fixed-boundary H2 experiment. Each dictionary
retains the whole original generating pool; no individual target forms or
true-key constraints were added. The experiment does not establish natural
Latin, manuscript-language inference, contractions or unknown boundary recovery.
All shuffles are already contradictory under common matching propagation, so
their immediate UNSAT checks do not supply independent evidence favoring one
membership encoding. UNKNOWN remains unresolved, with accuracy unevaluated.
UNSAT has no separately checked proof certificate.

## Validation and continuation

Eleven targeted tests pass (six relation-equivalence cases, two selection-rule
cases and three existing H2 solver/capacity checks). Artifact validators check
all fourteen arms, regenerate the unchanged pruning, verify recovered mappings
and training membership, and recompute each first-key score. The two verified
training explanations are separately checked without new solver calls.

Artifacts and reproduction:

```sh
.venv/bin/python -m benchmarks.latin_h2_compressed --run
.venv/bin/python -m benchmarks.latin_h2_compressed --validate
.venv/bin/python -m benchmarks.latin_h2_compressed_replication --run
.venv/bin/python -m benchmarks.latin_h2_compressed_replication --validate
.venv/bin/python -m benchmarks.latin_h2_compressed_analysis
```

Prepared inputs, per-arm results/phases and per-comparison reports are under
`experiments/results/latin-h2-compressed`; selection provenance and the seventh
pair are under `experiments/results/latin-h2-compressed-replication`. Existing
results are reused rather than overwritten or selected by holdout performance.

All seven iterations are complete. The next priority is **identifiability
calibration at the larger vocabulary**, rather than more timeout increases:
freeze independent synthetic fixtures with more distinct training word types,
fresh novel holdouts and unchanged 32,768-form dictionaries; score the first key
and check whether a second observed-code key remains admissible. This can test
whether broader training recovers the generating explanation uniquely. The
present ambiguity is already proven; any additional training chosen after
inspecting it must be labeled adaptive, with fresh fixtures used for replication.
Natural-text H2 calibration still precedes manuscript-language conclusions.
