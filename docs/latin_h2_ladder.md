# Assisted H2 vocabulary-size ladder

Seven frozen rungs retain the original 512-word sampling pool and add forms in
one independently seeded order (6201) from the 32,846 default-inventory forms of
length 3–6. Ciphertext, key, 24 training occurrences, three novel holdouts,
matched pattern/count-preserving shuffle, H2 Boolean encoding and budgets are
unchanged: 30 seconds for Z3, 60 seconds per worker including construction.
All seven inputs were frozen before fitting. Each rung is one experiment
iteration; no intermediate outcome changed the remaining rungs.

This is an assisted dictionary-scale diagnostic on the original seed-5101
synthetic fixture. Retaining its whole generating pool ensures the positive
explanation is available without adding individual target words. It is not
independent fixture replication, natural prose calibration or a manuscript test.
The first returned key is scored without held-out selection.

| Vocabulary | Positive | Solver seconds | Training exact | Novel holdout exact | Shuffle | Solver seconds |
|---:|---|---:|---:|---:|---|---:|
| 512 | SAT | 0.041 | 24/24 | 3/3 | UNSAT | <0.001 |
| 1,024 | SAT | 0.062 | 24/24 | 3/3 | UNSAT | <0.001 |
| 2,048 | SAT | 0.424 | 24/24 | 3/3 | UNSAT | 0.200 |
| 4,096 | SAT | 2.127 | 24/24 | 3/3 | UNSAT | 2.067 |
| 8,192 | SAT | 23.634 | 24/24 | 3/3 | UNSAT | 11.089 |
| 16,384 | UNKNOWN | 30.040 | Unevaluated | Unevaluated | UNKNOWN | 30.042 |
| 32,768 | UNKNOWN | 30.086 | Unevaluated | Unevaluated | UNKNOWN | 30.685 |

All ten SAT/UNSAT outcomes at the first five sizes are resolved within budget;
all four larger outcomes remain unresolved. Construction rises from 0.20 to
18.27 seconds for positives. After propagation, positive candidate rows rise
from 3,908 to 409,558 (training occurrences counted separately). This is an
observed budget transition for this fixture and extension order, not a monotonic
hardness theorem or an exact vocabulary-size threshold. UNSAT applies only to
the matched shuffle under this bounded model; no independent proof certificate
was produced. UNKNOWN is neither evidence against H2 nor an accuracy failure.

Four targeted tests pass. The artifact validator checks each rung with its own
inventory and automaton, reproduces filtering and propagation, verifies frozen
inputs, checks recovered mappings and training membership, and recomputes first-
key holdout scores. Existing frozen benchmark implementations were unchanged.

Artifacts: `experiments/results/latin-h2-ladder/prepared.json`, per-size
`report.json`, per-arm result/phase files, and `validation.json`.

```sh
.venv/bin/python -m benchmarks.latin_h2_ladder --run
.venv/bin/python -m benchmarks.latin_h2_ladder --validate
```

Next recommendation: use the frozen 16,384-word positive/control pair to test
stronger global-capacity propagation (matching-based feasibility/support beyond
singleton saturation), with unchanged budgets and first-key scoring. The 8,192-
word pair is a resolved regression case. Replicate any improvement on independent
fixtures before claiming general H2 calibration or returning to manuscript fits.
The seven-iteration allowance is exhausted by this ladder; that refinement has
not been implemented here.
