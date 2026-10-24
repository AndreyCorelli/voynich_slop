# Joint ordering constraints

Seven frozen stages tested whether stronger repeat avoidance and suffix-conditioned ordering can coexist. These are stress tests on the same excerpts used in the previous adjacency experiment, not independent replication or manuscript tests.

## Protocol

Four sources (German 113, 133, 253 and Italian), three preset seeds, five arms: original prose, uniform random ordering, greedy avoidance, beam avoidance, and joint beam avoidance/mapped ordering. Each arm uses 89 held-out blocks of 32 words. Training uses a separate 32 blocks to derive the final-letter → initial-letter mapping. Generators receive the held-out word inventories and public layout; they cannot invent words. Every block preserves exact position-bin/length inventories.

The beam retains 16 candidate prefixes per slot. Its objective first minimizes adjacent exact repeats, then (joint arm only) maximizes within-line mapped boundary matches. Random tie breaking uses preset seeds. This is bounded search, not a proof of globally optimal avoidance. All arms receive the same reversible 1/16 context-prefix encoding.

Two frequency-adjusted statistics are reported: encoded adjacent-repeat fraction minus its constrained permutation expectation, and payload mapped within-line match fraction minus its constrained permutation expectation. Both use block-equal means. The second is a new direct boundary statistic, **not the previously used character-predictor gain**. Results cannot be substituted for that predictor's calibration.

## Seven stages

1. Freeze sources, seeds, arms, objectives and metrics before scoring.
2. Test German 113.
3. Test German 133.
4. Test German 253.
5. Test Italian.
6. Compare joint effects across sources.
7. Assess whether these statistics separate ordering mechanisms.

Every stage saves its plan before scoring and links to the preceding result by digest. No arms were selected or tuned after seeing results.

## Results

Mean over three keys/tie-breaking seeds; values are fractions, not bits per character.

| Source | Prose repeat | Beam-avoid repeat | Joint repeat | Prose mapped | Joint mapped |
|---|---:|---:|---:|---:|---:|
| German 113 | −0.006214 | −0.006625 | −0.006025 | 0.009450 | 0.135136 |
| German 133 | −0.006048 | −0.006816 | −0.006808 | 0.005943 | 0.116490 |
| German 253 | −0.007571 | −0.007530 | −0.007359 | 0.011951 | 0.096534 |
| Italian | −0.002831 | −0.002803 | −0.002787 | 0.009576 | 0.084896 |

Stronger avoidance reaches suppression close to or beyond prose in all four excerpts. The joint generator retains suppression while producing a positive mapped signal substantially larger than prose. Thus these two signs can coexist in a deliberately generated ordering. This does not demonstrate an exact two-statistic match, nor a match to earlier predictive gains: the joint mapped effect overshoots by roughly 8–20 times.

The generator's access to complete block inventories makes this an adversarial specificity check, not a historical mechanism reconstruction. Three seeds are not three independent prose samples. German 133 includes four `k` and two `x` held-out tokens previously flagged as unresolved prayer notations. Cached historical parsing is reused, not independently reimplemented. No decryption, language identification, manuscript classification, Z3 run, or historical mechanism posterior follows from these results.

## Verification and reproduction

Two tests check a known small joint optimum and agreement of mapped expectation with exhaustive permutation. Independent validation enumerates labeled source-index pairs for both statistics, verifies inventory preservation, decodes every output word, and checks the saved plan chain. It does not prove beam optimality or independently parse raw sources.

```sh
.venv/bin/python -m benchmarks.joint_order_constraints --run
.venv/bin/python -m benchmarks.joint_order_validation
.venv/bin/python -m pytest -q tests/integration/test_joint_order_constraints.py
```

Records: `experiments/results/joint-order-constraints/`. The benchmark code is hashed in the prepared record; further variants must use a new module/output directory.

## Next priority

Park repeat suppression and mapped boundary excess as standalone mechanism discriminators. A bounded follow-up could test predeclared weaker joint objectives with the **original character predictor** on training-only calibrated generators, followed by untouched evaluation fixtures. That would resolve the remaining magnitude/predictor gap. Beyond that, prioritize an independently specified prediction involving longer-range dependencies rather than extending local-statistic tuning indefinitely.
