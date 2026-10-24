# Predicate-complex reference repair

## Fixed plan

Introduce reference version `predicate-complex-v1` alongside the unchanged nearest-finite-ancestor reference. Preserve every admitted token, sentence ID and finite-predicate position. Collapse a nonfinite lexical verbal head (VERB/AUX) and its single direct finite auxiliary with UD `aux`/`cop` into a clause representative at the finite auxiliary position; support a unique finite copula attached to a nonverbal head as well. Traverse parent and token/relative-marker paths through those representatives. Route `mark`/`cc` attached directly to a supported complex head to its representative. Relation labels follow the outward dependency path, not the internal auxiliary edge.

Do not choose an arbitrary representative for multiple finite auxiliaries, finite-headed auxiliary constructions or unsupported auxiliary attachments. Record such cases explicitly and retain the former projection for uncollapsed components. Longer auxiliary chains are outside this first direct-head repair; flag them rather than silently claiming full normalization. Test acyclicity, reference feasibility, token/predicate invariance, passive and copular projection, coordination, marker scopes and ambiguity handling, including the saved 13305 example.

Use only the same source training/development/previously inspected confirmation cohorts as iteration 7, with exact ID/group checks. Audit parent, relation, marker and token-anchor changes separately by split, and keep both references. No new target-author evaluation, dictionary optimization or fresh-confirmation claim.

Refit the same marker model (including four-fold out-of-fold fitting with fold-local vocabulary) and two parent models on revised training annotations, retaining the 249 features, full pools, regularization and folds. Compare the revised parent models with the frozen legacy parent models **on the same revised reference and same revised evaluation marker evidence**. This is a controlled comparison on a common target; old-reference metrics remain separately labeled. Cross gold/predicted marker evidence with hidden/gold sentence boundaries and unknown/gold relation labels. Gold roles supply ROOT identity; report ambiguous non-root parent accuracy. Use exact integer forest inference throughout. Also rescore unchanged legacy gold-evidence predictions against both references to isolate evaluation-label changes without changing predictions.

Preserve all artifacts; independently reconstruct references and source-only fits, verify unchanged source inputs, projection changes, exact candidate scores/masks, acyclic optima and regression examples. Inspect remaining development errors without tuning on the reused confirmation cohort. A cleaner reference is not itself demonstrated grammatical restoration.

## Implemented reference

The new annotation-only module [predicate_projection.py](../src/voynich_smt/predicate_projection.py) contracts supported direct auxiliary/copula edges before projecting clause dependencies. The representative remains at the original finite auxiliary token. There is no new oracle predicate position, lexical resource, feature or parser output supplied to ordinary inference. Unsupported components keep the former uncontracted projection and carry explicit issue records; other supported components in the same sentence can still be repaired.

The key regression is source sentence **13305**:

| Item | Legacy reference | `predicate-complex-v1` |
|---|---|---|
| Parent of relative-clause `sunt` | `mansissent` | `fuissent` |
| Target of relative marker `quae` | `mansissent` | `sunt` |
| Marker `si` on lexical `factae` | Omitted | Targets `fuissent` |

The repair also supports a unique finite copula on a nominal/adjectival predicate. This goes beyond the verbal-only mechanical audit in iteration 8; its counts therefore differ. Cases with multiple finite auxiliaries or an already finite lexical head are not silently merged. A nonfinite auxiliary chain can be partially contracted at the supported direct edge, but remains explicitly flagged as incomplete.

## Annotation-change audit

Counts below apply to the **admitted** sentence groups actually used for fitting/evaluation. The full saved audit also includes the three selected sentences per split excluded by the unchanged cross-author grouping rule (800/200/200 selected versus 797/197/197 admitted). Nothing is discarded based on projection difficulty.

| Change | Training | Development | Inspected confirmation |
|---|---:|---:|---:|
| Admitted sentences | 797 | 197 | 197 |
| Supported predicate complexes | 246 | 52 | 59 |
| Changed parent labels | 125 | 23 | 32 |
| Changed relation labels | 115 | 20 | 30 |
| Added marker occurrences | 93 | 21 | 14 |
| Retargeted/retyped markers | 35 | 9 | 8 |
| Removed markers | 0 | 0 | 0 |
| Changed token anchors | 1,319 | 254 | 282 |
| Sentences with flagged components | 16 | 4 | 5 |

All sentence IDs, words, finite positions and boundaries remain identical. There are still 266 training streams / 8,117 tokens / 1,385 parent groups, and 66 streams in each evaluation cohort. Revised confirmation has 380 finite positions, **188 non-root edges and 192 ROOTs**, compared with 158 edges / 222 ROOTs under the old reference. This target change is why old-reference and revised-reference F1 must not be presented as a restoration gain. The revised marker vocabulary has 44 forms; it is learned only from training data, and each out-of-fold vocabulary excludes its held streams.

Flagged admitted training components include three partial nonfinite auxiliary chains, eight auxiliary dependency relations outside the supported contraction rule, one multiple-finite-auxiliary head, one finite head with a finite auxiliary and three unsupported auxiliary-head attachments. Development has four flagged sentences and confirmation five; they remain in every denominator. Full case records are saved in `sentence-complexes.json` and `projection-audit.json`.

## Common-reference model comparison

The comparison below evaluates both legacy and refitted parent models on **the same revised reference**, with **the same revised evaluation marker provider**, exact inference, gold finite positions and hidden sentence boundaries. Thus changes within a row do not arise from changing evaluation labels, marker evidence, candidate pools or solver completion. The learned models differ through their training annotations and resulting training marker evidence/weights. This does not isolate which individual annotation repair caused the gain.

| Parent training marker evidence | Evaluation markers | Frozen legacy parent F1 | Refitted parent F1 | Paired change, points [95% interval] |
|---|---|---:|---:|---:|
| Gold | Revised reference | 47.50% | **54.60%** | +7.10 [1.61, 12.92] |
| Gold | Revised predicted | 45.16% | **52.51%** | +7.35 [2.20, 13.03] |
| Out-of-fold predicted | Revised reference | 45.81% | **54.29%** | +8.48 [3.18, 14.45] |
| Out-of-fold predicted | Revised predicted | 46.51% | **55.36%** | +8.85 [3.35, 15.00] |

These paired stream-bootstrap intervals use 2,000 draws and seed 1729. They describe the previously inspected same-author passages; they are not fresh confirmation or new-author transfer. Revised predicted marker attachment F1 is 83.01% against the revised marker reference, and is identical across compared parent models by design. It cannot be directly compared with an old-reference marker F1 as though the labels were unchanged.

For the primary gold-trained refit, confirmation ROOT F1 is 88.28% with reference markers and 84.09% with predicted markers; ROOT recall is 92.19% in both. Reference-marker typed-edge F1 is 52.92%, versus 54.60% when only parent identity is scored. The complete correct reference is still strictly outscored in 48/66 streams (51/66 with predicted markers).

A separate label-only check preserves the *unchanged* old predictions and their original abstentions. For the old gold-trained model, changing only evaluation labels moves F1 from 45.09% to 46.56%; for the old out-of-fold-trained model, from 44.11% to 44.37%. These are relabeling effects, not improved predictions, and use the original abstention accounting rather than the exact-inference comparison above.

### Repeated oracle isolation

Primary refitted model, revised confirmation reference:

| Restriction | F1, reference markers | F1, predicted markers | Reference outscored / 66, reference markers |
|---|---:|---:|---:|
| Unrestricted | 54.60% | 52.51% | 48 |
| Gold boundaries | 64.16% | 60.74% | 36 |
| Gold relations | 63.83% | 63.83% | 33 |
| Both | 71.28% | 71.28% | 27 |

Gold relations supply ROOT identity. With both oracles, 50/188 non-root children have only one possible parent; among the remaining children, **84/138 parents are correct (60.87%)**. The frozen legacy model on this same revised reference gets 83/138 (60.14%). Overall both-oracle F1 improves only 0.53 points [0.00, 1.57]. Thus most of the useful gain is outside the fully oracle-conditioned parent-choice problem. Do not compare 71.28% here with iteration 8's 71.52% as evidence of degradation: the reference edges and denominators differ.

On development, refitted reference-marker F1 is 69.45% unrestricted and 86.36% under both oracles; with predicted markers, 62.95% and 86.36%. The sizable development/confirmation gap remains.

## Remaining problem and next experiment

The qualitative development review tracks all seventeen earlier cases. The one questionable `sunt → fuissent` prediction is now correctly labeled. The other sixteen reviewed errors remain under the refitted model with both oracles. Across the whole revised development cohort there are 21 residual wrong-parent choices, including newly exposed nesting/scope errors under the corrected target. Sentences, candidates and notes are saved in [review.json](../experiments/results/grammar-restoration/iteration9/review.json); these are text/annotation-based assessments, not independent expert adjudication.

A concrete representation limit is now explicit: **the current marker-only feature block is constant across possible parents once the child's relation is fixed**. It uses the child's own marker flags and distances, with relation-specific blocks, but no candidate-parent marker interaction. Consequently its contribution cancels between candidate parents under a fixed role. All 1,056 paired fixed-role conditions produce identical forests with reference versus predicted markers, as the architecture predicts. Better marker scopes can help role decisions without supplying the evidence needed to select among same-role parents.

The next bounded experiment should therefore test parent-dependent marker/scope evidence on this repaired reference: reuse the existing marker-interaction variant as the first ablation, hold the revised target and splits fixed, and inspect whether it separates sibling/nested clauses and coordination levels on development. If it does not, add explicit clause-span/complex evidence rather than another unconstrained contrastive refit. A role classifier may still help, but it cannot by itself resolve the 54/138 ambiguous confirmation parent errors left with both role and boundary oracles. Keep dictionary optimization deferred.

## Reproduction and validation

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_predicate_complex_iteration9
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_predicate_complex_iteration9_review
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_predicate_complex_iteration9_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_predicate_projection.py tests/unit/test_boundary_role_oracles.py tests/unit/test_training_alignment.py tests/unit/test_marker_oracle.py tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

Forty focused tests pass, including the real 13305 regression. Independent validation reconstructs all **1,200 selected sentence projections using a separate quotient-tree implementation**, verifies all seven source fits and out-of-fold attachments, checks all **4,224 forest conditions**, and matches **88 independent Z3 optima** on the reviewed development streams. It also verifies input hashes, identical token/predicate/split/fold identities, exact candidate masks and scores, reference feasibility, gap monotonicity, label-only rescoring and fixed-role marker invariance. The benchmark took 19.8 seconds. [Report](../experiments/results/grammar-restoration/iteration9/report.json) and [validation](../experiments/results/grammar-restoration/iteration9/validation.json) preserve every comparison and the separately versioned reference. Earlier artifacts and implementations remain unchanged.
