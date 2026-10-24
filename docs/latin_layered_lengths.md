# Length-range calibration of sparse membership

This experiment freezes public word lengths **2, 5, 8 and 12** on both unchanged
Latin inventories. Each length receives an unconstrained word query and an
impossible two-letter prefix query: 16 cases total. Alphabet, automaton and sparse
encoding are unchanged from [the six-query comparison](latin_layered_membership.md).

Expectations are established without Z3 by scanning the exact generated inventory.
The positive anchor is its lexicographically first word at that length, retained
only for expectation checking; no anchor letters are supplied to the solver.
The negative prefix is the lexicographically first alphabet pair absent from all
inventory words of that length. These are intentionally impossible controls,
not realistic shuffled ciphertext or evidence about accidental cipher fits.

Each fresh subprocess receives the same **2,000 ms solver timeout** and
**15-second external wall limit**, including loading, formula construction,
solving and verification. UNKNOWN and WALL_TIMEOUT remain unresolved. SAT words
are checked independently against the Python automaton. UNSAT is a bounded
solver result without an independently checked proof certificate; validation
separately checks that the full generated inventory contains no matching word.

```sh
.venv/bin/python -m benchmarks.latin_layered_lengths --run
.venv/bin/python -m benchmarks.latin_layered_lengths --validate
```

Outputs: `experiments/results/latin-layered-lengths`. Preparation pins the prior
benchmark, new benchmark code, unchanged encoding, automata and deterministic
case selection. Validation rescans full inventories to check all case
expectations and verifies saved SAT witnesses. Four worker tests cover variable
lengths and both SAT/UNSAT outcomes. No cipher recovery or manuscript fitting.

## Results

| Inventory | Length 2 positive | Length 5 positive | Length 8 positive | Length 12 positive |
| --- | --- | --- | --- | --- |
| Default | SAT, 0.006 s | SAT, 0.419 s | UNKNOWN, 2.13 s | UNKNOWN, 2.40 s |
| Broader | SAT, 0.002 s | SAT, 1.240 s | WALL_TIMEOUT, 15.01 s | WALL_TIMEOUT, 15.01 s |

All eight impossible-prefix controls returned UNSAT, with solver times below
0.17 seconds. Completed positive SAT witnesses verify. Overall: **4 SAT, 8 UNSAT,
2 UNKNOWN, 2 external wall timeouts**. No unresolved case is counted as failure
to belong to the inventory: all four have an independently established witness.

Construction for completed longer cases took 2.12–2.56 seconds on the default
inventory and 4.81–6.24 seconds on the broader one. Worker wall timeouts do not
provide phase timings, so they cannot be attributed exclusively to solving.

The short-word gains are real for these cases, but arbitrary-word search is
still limited at longer lengths. Before adding shared cipher constraints, the
next proposed check is a single frozen default-inventory length-eight positive
with a modest longer budget and durable phase timings. This would separate a
too-short search budget from a more serious encoding bottleneck. It has not
been run here. These tests do not estimate realistic cipher false-positive rates.
