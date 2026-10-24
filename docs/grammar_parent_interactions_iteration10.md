# Parent-dependent marker interactions on the repaired reference

## Fixed development-first plan

Keep `predicate-complex-v1`, the exact iteration 9 sentence groups, gold finite positions, morphology lattice, 0.01 regularization, full parent pools and existing marker predictions fixed. Compare iteration 9's 249-feature marker-only parent models with the existing 282-feature interaction variant (`attachment_features(..., interactions=True)`). Refit two parent rankers using identical groups: reference markers and the saved fold-local out-of-fold marker predictions. Reuse all marker fits; do not fit a new marker model or adjust features/hyperparameters after development results.

The interaction variant adds candidate-parent marker flags, child-marker placement relative to a candidate parent, intervening third-predicate markers, direction cues, shared marker presence and subjunctive compatibility. This is a test of the existing feature package, not an attribution of effects to any one feature or a new span parser. Use the same reference/predicted evaluation marker evidence for each pair of parent models, crossed with unrestricted, boundary-only, relation-only and both-oracle candidate pools. Score every condition exactly with the same integer forest solver. Gold relations supply ROOT identity, so use ambiguous non-root parent accuracy to assess the parent-choice mechanism.

**Predeclared development gate, primary out-of-fold-trained arm:** require at least +5 percentage points in ambiguous non-root parent accuracy under reference markers and both oracles; a positive gain under predicted markers and both oracles; no decrease in unrestricted predicted-marker edge F1; and unrestricted predicted-marker ROOT recall at least 80%. This is a point-estimate diagnostic screen, not a statistical generalization claim. Report gold-trained results as a replication, not as an alternative way to select a winner. If the primary gate fails, do not evaluate the interaction models on confirmation or target authors. If it passes, evaluate the unchanged specification on the already inspected iteration 9 confirmation cohort, explicitly labeling that reuse.

Report paired stream intervals, non-root/typed edge F1, ROOT quality, exact reference-score gaps, marker sensitivity under fixed roles, and paired corrections/regressions of development residual errors. Verify both refits and candidate scores, fixed references/evidence, acyclic typed witnesses and an independent Z3 cross-check on reviewed development streams. Preserve earlier artifacts. No dictionary optimization or lexical recovery claim.

## Development result: gate failed

The primary out-of-fold-trained interaction model improves parent choice with correct grouping, but reduces unrestricted edge F1. It fails two predeclared checks: the reference-marker ambiguous-parent gain is 4.35 points (below five), and unrestricted predicted-marker F1 declines by 1.63 points. Predicted-marker ambiguous-parent gain is positive and ROOT recall remains above 80%. **No interaction model was evaluated on confirmation or target authors.**

The comparison uses the same 66 development streams, 2,101 tokens, 342 gold finite positions, 154 non-root links and `predicate-complex-v1` reference as iteration 9. All models use gold finite positions; predicted markers do not make this a fully detected-predicate restoration run.

| Primary out-of-fold-trained model: evaluation evidence | Marker-only | Parent interactions |
|---|---:|---:|
| Reference markers, hidden boundaries/roles: edge F1 | 66.45% | 61.24% |
| Predicted markers, hidden boundaries/roles: edge F1 | 62.30% | 60.67% |
| Predicted markers, gold boundaries, unknown roles: edge F1 | 73.50% | 77.14% |
| Reference markers, gold boundaries/roles: ambiguous-parent accuracy | 71/92 (77.17%) | 75/92 (81.52%) |
| Predicted markers, gold boundaries/roles: ambiguous-parent accuracy | 71/92 (77.17%) | 78/92 (84.78%) |
| Predicted markers, hidden boundaries/roles: ROOT recall | 86.70% | 87.77% |

With both oracles, 62 non-root predicates have only one possible parent; the 92-child accuracy excludes those forced choices. Gold roles also supply ROOT identity, so their 100% ROOT F1 is not a learned improvement. Overall both-oracle edge F1 moves from 86.36% to 88.96% with reference markers and to 90.91% with predicted markers.

Paired stream-bootstrap intervals (2,000 draws, seed 1729) are:

- Reference-marker ambiguous-parent gain under both oracles: **+4.35 points [−3.57, +11.54]**.
- Predicted-marker ambiguous-parent gain under both oracles: **+7.61 points [+1.10, +13.70]**.
- Unrestricted predicted-marker edge-F1 change: **−1.63 points [−6.54, +3.21]**.

The unrestricted interval does not establish a population-level degradation; the point estimate nevertheless fails the frozen non-degradation screen. The oracle-conditioned positive interval concerns inspected same-author development passages and is not evidence of independent transfer. Features, thresholds and regularization were not retuned to rescue the gate.

The reference-marker-trained replication shows the same broad tradeoff: unrestricted F1 changes from 69.45% to 69.23% with reference markers and 62.95% to 61.24% with predicted markers. Both-oracle ambiguous-parent accuracy increases from 77.17% to 82.61% and 80.43%, respectively. The replication is not used to override the failed primary gate.

## What the interactions changed

The representational defect identified in iteration 9 is removed: under fixed relation labels, changing reference to predicted marker evidence changes **13/66** primary interaction forests without boundaries and **8/66** with boundaries. The marker-only controls change **0/66** in both cases. This verifies that markers now influence parent choice; it does not show that every influence is correct.

Paired primary-model parent outcomes clarify the tradeoff:

| Evidence and restrictions | Corrected parents | Previously correct parents made wrong | Selected cross-sentence parents, before → after |
|---|---:|---:|---:|
| Reference markers, both oracles | 9 | 5 | 0 → 0 |
| Predicted markers, both oracles | 9 | 2 | 0 → 0 |
| Predicted markers, gold roles only | 8 | 10 | 13 → 20 |
| Predicted markers, no boundary/role oracle | 9 | 11 | 36 → 41 |

These counts compare parent identity across every finite predicate, including ROOT decisions; edge F1 also depends on the number of predicted non-root links. More cross-sentence choices accompany the hidden-boundary failure, while supplied boundaries expose a useful parent-ranking gain. This supports grouping as a remaining bottleneck, but does not prove that cross-sentence mistakes explain every regression or that an inferred grouping model will recover the oracle benefit. With both oracles and predicted markers, strictly outscored reference forests fall from 13/66 to 9/66; with no oracles they change only from 45/66 to 44/66.

The saved [paired review](../experiments/results/grammar-restoration/iteration10/review.json) includes every changed parent and normalized sentence context. Examples with both oracles and predicted markers:

- `mansissent` now chooses `descendes` instead of embedded relative `sunt` (13305).
- `feceris` now chooses main `extingues` instead of intervening relative `nocebat` (160166).
- `auertunt` now coordinates with `accipiunt` instead of subordinate `cedat` (160170).
- A regression reverses the recently corrected relative nesting: `sunt` now chooses `mansissent` instead of `fuissent` (13305). Another moves `estis` from `laboratis` to outer `uenite` (13314).

These are annotation-relative corrections/regressions, not independent expert adjudication. Predicted-marker evidence producing a better point estimate than reference-marker evidence under both oracles is model/evidence interaction, not a reason to redefine the reference or claim predictions are more linguistically accurate than it.

## Recommendation

Retain the interaction model as a useful conditional diagnostic, not a promoted restoration scorer. Keep confirmation and target evaluation deferred. The next small experiment should address grouping explicitly: learn a source-only same-sentence compatibility signal between predicate pairs, then compare its effect on candidate selection against the existing hidden/gold-boundary controls. Use only tokens, morphology, markers and relative geometry at inference; do not supply punctuation or gold boundaries. A constrained or latent grouping model would need its own validation before integration.

The existing interaction package also adds direction and subjunctive-compatibility features, so this experiment cannot attribute gains or regressions to marker scope alone. If subsequent grouping succeeds, an interaction-family ablation can identify which evidence is useful. Do not add another unconstrained optimizer-negative refit to compensate for this failed screen.

## Reproduction and verification

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_parent_interactions_iteration10
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_parent_interactions_iteration10_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_parent_marker_interactions.py tests/unit/test_predicate_projection.py tests/unit/test_boundary_role_oracles.py tests/unit/test_training_alignment.py tests/unit/test_marker_oracle.py tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

Forty-two focused tests pass. Independent validation refits both interaction models on the same 1,385 groups, verifies the frozen marker fits and evidence through saved input hashes, reproduces all 1,056 marker-only control conditions from iteration 9, and verifies all **2,112 development conditions**. An independent Z3 cross-check matches **104 interaction optima** across the reviewed development streams, evidence modes and oracle masks. Exact reference scores, candidate pools, evidence equality, acyclicity, nested gap monotonicity, all metrics/intervals and the failed gate reproduce. The validator also verifies that no confirmation conditions or post-gate input artifact were produced. Benchmark runtime was 10.2 seconds. [Report](../experiments/results/grammar-restoration/iteration10/report.json), [gate](../experiments/results/grammar-restoration/iteration10/development-gate.json) and [validation](../experiments/results/grammar-restoration/iteration10/validation.json) retain the negative result. No dictionary search.
