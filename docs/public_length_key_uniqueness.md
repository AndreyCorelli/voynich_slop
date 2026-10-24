# Held-out mapping uniqueness with known training words

All four alternative-mapping checks return UNSAT in 0.028–0.036 solver seconds.
Under the known-training-plaintext model, the generating codes for the five
held-out letters (`a`, `e`, `i`, `n`, `o`) are forced. Therefore the earlier 3/3
predictions on each case do not depend on the solver choosing a lucky key among
alternatives that change those mappings.

| Case | Alternative held-out mapping | Solver time |
|---|---|---:|
| Length two / 3101 | UNSAT | 0.036 s |
| Length two / 3102 | UNSAT | 0.028 s |
| Mixed / 3101 | UNSAT | 0.028 s |
| Mixed / 3102 | UNSAT | 0.028 s |

The [known-plaintext baseline](public_length_known_plaintext.md) independently
establishes a SAT witness and 3/3 exact novel predictions for each case. This
new diagnostic keeps its known training words, ciphertext, alphabets, H1 L1–3
prefix-free model, free selection, observed code domains and five-second budget.
It adds one joint exclusion:

```text
NOT (owns(a, true_code_a) AND owns(e, true_code_e)
     AND owns(i, true_code_i) AND owns(n, true_code_n)
     AND owns(o, true_code_o))
```

Thus at least one of those five assignments must differ. H1 permits only one
code per letter, so rejection of this disjunction of alternatives establishes
all five ownership facts. These letters occur in the training plaintext, and
the generating codewords occur in the observed training ciphertext. No held-out
ciphertext or word constraints are supplied to the solver; the held-out letter
set and generating codes enter only through the truth-assisted exclusion.

UNSAT here applies to the model with the added exclusion. The original synthetic
positive remains SAT. The conclusion does not establish uniqueness of unused
letters, the full key, or hidden-word recovery. It is conditional on known training
identities, full alphabets, H1, prefix freedom, L1–3 bounds and the fixed four
outcome-selected fixtures. With the five mappings forced, their encoded novel
words have the generating plaintext as their unique prefix-free decoding.

These checks support the interpretation that training-word ambiguity, including
length choices, causes the bad hidden-fit predictions on these fixtures. They do
not show how to choose those words without an oracle, or establish a manuscript
language. The two length-three UNKNOWN cases were outside this diagnostic.

Seven focused tests pass. A deliberately ambiguous toy training word produces a
verified alternative SAT mapping; adding identifying training words makes the
same exclusion UNSAT. Tests also check the exact solver inputs, preserved budgets,
unscored non-SAT results and resume without repeated fits. Artifact validation
checks hashes, exclusions, baseline witnesses and conclusion interpretation.
The UNSAT statuses are solver-reported; no independent proof certificates were
produced or checked.

Artifacts: `experiments/results/public-length-key-uniqueness/`.

```sh
.venv/bin/python -m benchmarks.public_length_key_uniqueness --validate
```

A next bounded comparison could reveal only the correct training word lengths on
these four cases, keeping identities hidden. That separates length uncertainty
from word-identity ambiguity, especially for the mixed cases where midpoint
proposals used different lengths. It would be another explicitly labeled oracle
diagnostic, with the same budget and preserved hidden results.
