# Bounded symbolic Latin membership

This standalone benchmark tests the frozen complete automata before cipher
integration. Both inventories receive three queries of fixed public length five:
fully specified `amare`, `amare` with only its middle letter hidden, and all five
letters hidden. Every query has a known witness; this is a performance smoke test,
not an accuracy or language discrimination experiment.

Each fresh subprocess gets a 2,000 ms Z3 timeout and a 15-second external wall
limit. The external limit includes automaton loading, shared table construction,
formula construction, solving and witness verification. A wall timeout cannot
identify which phase consumed the budget and does not mean UNSAT. Construction
and solver timings are available only for completed workers. No retries, larger
budgets or alternative query selection follow the results.

Run and validate:

```sh
.venv/bin/python -m benchmarks.latin_symbolic_membership --run
.venv/bin/python -m benchmarks.latin_symbolic_membership --validate
```

Artifacts live in `experiments/results/latin-symbolic-membership`. Source report,
code and compressed automaton identities are frozen. SAT witnesses are checked
against the independent Python automaton, with fixed letters checked separately.
Three small-automaton worker tests cover the three constraint patterns.

The initial worker invocation had an incorrect module name; it failed before any
solver measurement. Its preparation was preserved in the `-prevalidation`
directory; the corrected benchmark regenerated the same scientific cases.

Results:

| Inventory | Concrete word | One hidden letter | Five hidden letters |
| --- | --- | --- | --- |
| Default, 2.55 million forms | SAT, verified; solver 0.028 s | WALL_TIMEOUT, 15.02 s | WALL_TIMEOUT, 15.02 s |
| Broader, 6.33 million forms | SAT, verified; solver 0.085 s | UNKNOWN, solver 2.73 s | UNKNOWN, solver 2.58 s |

Completed table/formula construction took 1.43 seconds for the default concrete
case and 4.37–4.45 seconds for the broader cases. The smaller inventory timing
out externally while the larger returns UNKNOWN is not evidence of a monotonic
size relationship: preprocessing and timeout responsiveness can differ.

All four symbolic cases remain unresolved within their budgets, despite known
witnesses. Fast concrete lookup and compact construction therefore do not justify
integrating this nested constant-array encoding into cipher recovery yet. The
next useful experiment is a sparse, length-layered transition relation on the
same queries and budgets, reducing symbolic lookup over a global Store chain.
That encoding is a proposal, not implemented here. No manuscript text was fitted.
