# Parent-score training alignment and marker-exposure controls

## Frozen source-only experiment

Keep iteration 5's marker-only parent features, full parent pools, finite-skeleton target, regularization 0.01 and source fitting cohort fixed. All primary comparisons use gold predicate positions and hidden sentence boundaries, isolating parent scoring and marker quality. No target-author evaluation or dictionary optimization in this iteration.

Fit two parent rankers on identical source groups: complete gold marker occurrences/classes/scopes, and four-fold out-of-fold predicted markers. Fold-local marker vocabulary and marker-model fitting exclude every held-out stream; folds are contiguous blocks within each source author. Fit a full source marker model for validation predictions, retaining the existing source-only specification. Evaluate each parent ranker with both gold and predicted validation markers (the complete two-by-two comparison).

Keep inspected source sentence positions 400–499 as development/error-analysis material. Reserve previously unused positions 600–699 per source author as fresh confirmation; do not reuse positions 500–599 for a new confirmation claim. Record exact IDs and source-relative freshness limitations. Do not tune thresholds, features, regularization or fold assignment on fresh results.

Before validation scoring, collect actual optimized wrong forests on a fixed fitting-only budget: first forty admitted training streams per source author, gold predicates and gold markers, one forest per stream under the gold-trained conditional ranker. If distinguishable wrong forests exist, fit an explicitly exploratory contrastive ranker on reference-minus-wrong feature differences. Retain the original feature scaling and anchor regularization to the gold-trained model; normalize each difference by its predicate count. This has extra training/optimizer budget and is not a matched-budget comparison with the main two arms.

Report exact candidate-feature collisions, correct-reference score gaps, local parent margins, non-root link precision/recall/F1, ROOT precision/recall/F1 and marker attachment quality. Non-collision of real-valued position features does not establish linguistic sufficiency or linear separability. Use a fitting-only bounded linear-separability diagnostic on collected wrong-forest differences to distinguish achievable contrast constraints from current learned scores. A contrastive improvement on training examples alone is not successful restoration.

Interpretation is predeclared: matched gold/gold success versus cross-quality degradation supports exposure mismatch; persistent gold/gold failures demonstrate deficiencies beyond marker uncertainty; exact feature collisions show a concrete representational limit, while no collisions cannot exclude missing relevant information. Validate on separate passages, preserve abstentions and compute paired stream-cluster intervals. This is a diagnostic matrix, not a new promotion gate; do not choose a winner on fresh confirmation or claim lexical recovery.

## Results

The confirmation cohort contains 66 three-sentence streams, 2,123 tokens and 380 finite predicates (222 ROOT, 158 non-root reference links). Fitting uses 266 streams / 8,117 tokens / 1,385 conditional parent groups; development contains 66 streams / 2,101 tokens. Confirmation uses new passages from the same two source authors, not new authors, and is therefore evidence about source generalization only. All conditions supply gold predicate positions, hide sentence boundaries, and use the unchanged 249 marker-only parent features and full parent pools.

| Parent training markers | Confirmation markers | Non-root edge F1 | ROOT F1 | ROOT recall | Reference strictly outscored / completed | Abstentions / 66 |
|---|---|---:|---:|---:|---:|---:|
| Gold | Gold | 45.09% | 81.88% | 86.49% | 49/65 | 1 |
| Gold | Predicted | 44.11% | 80.25% | 86.94% | 47/65 | 1 |
| Out-of-fold predicted | Gold | 44.11% | 81.50% | 88.29% | 50/65 | 1 |
| Out-of-fold predicted | Predicted | 46.56% | 81.93% | 91.89% | 47/66 | 0 |
| Gold plus graph contrast (exploratory) | Gold | 1.41% | 15.86% | 10.36% | 63/63 | 3 |
| Gold plus graph contrast (exploratory) | Predicted | 1.82% | 15.22% | 9.91% | 64/64 | 2 |

Edge F1 measures parent identity without the relation label; ROOT is reported separately. Abstentions retain all gold denominators and contribute no predicted edges or roots. The scored-reference fractions exclude abstentions only because those have no certified optimum; they are not successful restorations. Oracle markers recover all 199 reference marker attachments; predicted marker attachment F1 is 76.16% (precision 83.73%, recall 69.85%).

Matched gold training/evaluation does not solve parent scoring: its correct reference is strictly beaten in 49/65 completed confirmation streams. Out-of-fold training gives a modest 2.46-point edge-F1 increase with predicted evaluation markers, but reverses on development (45.96% versus 49.38%). With gold evaluation markers it slightly degrades confirmation (44.11% versus 45.09%) and more substantially degrades development (45.89% versus 54.62%). These results do not support marker exposure mismatch as a sufficient explanation.

### Representation and training contrasts

There are **zero exact feature collisions** between a correct typed parent candidate and a wrong candidate in any evaluated condition, including zero feature-aliased selected errors. This rules out that narrow equality mechanism on this cohort. It does not show that distance/position features encode the relevant linguistic distinction, that one linear score can satisfy all examples, or that the missing evidence is available. Under gold/gold, 122/380 predicates locally rank some wrong parent strictly above the best candidate with the correct parent; 124/380 misrank the complete typed reference choice. These local comparisons remain available for abstained forests because all candidate scores were computed.

The fixed fitting-only optimizer budget yields 47 wrong completed forests from 80 streams. Their reference-minus-wrong feature differences are numerically linearly feasible with unit margins and unrestricted coefficients. This audit concerns only those 47 collected comparisons; it is not a proof about all source parent choices or held-out passages. The anchored pairwise contrast fit changes all 47 fixed comparisons from negative to positive margin: minimum per-predicate margin goes from −2.051 to +0.364 and mean from −0.474 to +2.812. Nevertheless, new optimized forests fail severely: with gold confirmation markers, all 269 predicted non-root relations in completed forests become subordination, only three parent edges are correct, and ROOT recall falls to 10.36%. Median optimum-minus-reference score rises from 1.103 to 93.394 score units.

This demonstrates failure of the tested **one-round pairwise objective**, despite correcting every collected training comparison. A likely mechanism is that the new objective constrains only an old set of wrong forests while merely anchoring weights to the conditional model; it does not retain the original conditional likelihood or constrain newly preferred forests. That interpretation is a hypothesis supported by the observed collapse, not an identification of the only cause. Do not promote this contrast model or treat fitting-margin gains as restoration.

### Recommendation

Keep dictionary optimization deferred. The next small experiment should retain the original conditional objective while adding structured constraints, collect new wrong forests iteratively on fitting streams, and monitor ROOT/coordination/subordination behavior on development before another fresh confirmation. First test whether one linear score can satisfy the complete source parent-choice constraints, rather than only the 47 forest contrasts; if it cannot, inspect a small contradictory subset to identify which feature distinctions or relation assumptions are missing. Do not tune these changes against the confirmation cohort used here.

### Reproduction and artifacts

Run from the repository root (the benchmark deliberately refuses to overwrite an existing output directory):

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_training_alignment_iteration7
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_training_alignment_iteration7_validate
.venv/bin/python -m pytest -q tests/unit/test_training_alignment.py tests/unit/test_marker_oracle.py tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

[Saved artifacts](../experiments/results/grammar-restoration/iteration7/report.json) include exact sentence IDs, fold membership, fold-local vocabularies and weights, cached out-of-fold predictions, fitting negatives, reference score audits, feature collision audits and all validation forests. The benchmark took 120.5 seconds. Editorial correction: the implementation tests unit-margin feasibility with unrestricted real coefficients; the initial plan’s word “bounded” was inaccurate.

Paired stream-cluster bootstrap intervals (2,000 draws, seed 1729) for out-of-fold minus gold training are +2.46 edge-F1 points [−2.19, +8.11] with predicted evaluation markers and −0.98 [−6.63, +4.73] with gold evaluation markers. Neither excludes zero. The exploratory contrast fit loses 43.69 points [−51.65, −35.97] with gold markers and 42.29 [−50.67, −34.29] with predicted markers. These descriptive intervals apply to these source passages, not author transfer; the same-author text sequence can retain dependencies beyond the resampled three-sentence unit.

**Validation:** 31 focused tests pass. The [independent validator](../experiments/results/grammar-restoration/iteration7/validation.json) refits all eight models (five marker, two conditional parent, one contrastive), reconstructs every out-of-fold prediction with fold-local fitting/vocabulary, verifies raw-source split IDs and prior-confirmation exclusion, and reconstructs 872 forest conditions (80 fitting plus 792 development/confirmation). It retains all eleven original abstentions. For completed forests, a separate Edmonds maximum-spanning-arborescence calculation on independently recomputed candidate scores agrees with every saved optimum, and reference scores, metrics and collision counts reproduce. A super-root represents the ROOT option; parent-to-child arcs represent non-root options, so the spanning tree corresponds exactly to a legal predicate forest. This verifier requires NetworkX, now declared in development dependencies.

A Z3 replay encountered a certification timeout at confirmation stream 19 under contrast/gold even with a ten-second replay budget. It did not expose a score disagreement. Using the independent polynomial forest algorithm avoids treating a nondeterministic timeout as evidence against a previously certified optimum; original benchmark abstentions remain unchanged in every reported metric. No target-author scoring or dictionary search was performed.
