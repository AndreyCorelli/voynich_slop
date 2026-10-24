# Sparse length-layered Latin membership

This comparison preserves the six queries, inventories, alphabets and budgets
from [the constant-array test](latin_symbolic_membership.md). Each fresh worker
has a 2,000 ms solver budget and a 15-second external wall limit, including
loading, construction, solving and verification. No manuscript or cipher fit.

The new encoding uses explicit sparse transition relations for each position.
Backward reachability keeps states that can reach a terminal in exactly the
remaining number of letters. Forward root reachability removes unreachable
transitions. These filters use only the public five-letter length, not the
anchor, fixed letters, true key or query outcome. Integer path states witness
membership; each edge constrains its source, letter and destination together.
No global nested Store array is used. The represented fixed-length language is
exactly the corresponding subset of the unchanged complete inventory.

| Inventory | Concrete word | One hidden letter | All five letters hidden |
| --- | --- | --- | --- |
| Default, 2.55 million forms | SAT, 0.012 s | SAT, 0.065 s | SAT, 0.420 s |
| Broader, 6.33 million forms | SAT, 0.021 s | SAT, 0.194 s | SAT, 1.249 s |

All six SAT witnesses passed independent Python-automaton membership checks and
checks for any fixed letters. Table/formula construction took 0.59 seconds for
the default inventory and 0.97 seconds for the broader inventory. The five layers
contain 9,862 and 15,837 transition occurrences respectively. Earlier constant
array results remain preserved: two concrete SAT queries and four unresolved
symbolic queries (two external timeouts, two solver UNKNOWN).

Five tests pass, including quantified symbolic equivalence against an explicit
small language at lengths zero through four, impossible lengths, invalid letters,
and all three worker constraint patterns. Artifact validation checks pinned
baseline identity, new encoding/code hashes and saved SAT witnesses. It does not
certify the entire new encoding for every length of the large inventory.

```sh
.venv/bin/python -m benchmarks.latin_layered_membership --run
.venv/bin/python -m benchmarks.latin_layered_membership --validate
```

Artifacts: `experiments/results/latin-layered-membership`.

This is evidence that sparse length layers improve these membership smoke tests,
not that cipher recovery will scale. Only one public length and one anchor were
used. The next useful check is a frozen range of public lengths with positive
and deliberately impossible prefix constraints, before coupling membership to
shared cipher-key variables. Unknown plaintext lengths and OOV allowances still
need separate implementations and calibration.
