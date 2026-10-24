# Source-trained predicate-pair grouping signal

## Fixed development-first plan

Keep the repaired reference, gold finite positions, iteration 9 marker model/out-of-fold marker evidence and iteration 10 out-of-fold-trained parent models fixed. Fit two binary same-sentence classifiers on all unordered finite-predicate pairs in the original 266 training streams: a distance-only control and a richer token/morphology/marker model. Labels use source sentence membership only during fitting/evaluation. Use the existing logistic fit with regularization 0.01, unweighted pairs, no downsampling or validation calibration.

Distance features are log token distance and log intervening-predicate count. Rich features add ordered endpoint morphology windows, intervening morphology summaries and marker flags/scopes relative to the pair. No punctuation, gold boundaries/roles/heads/complex membership, absolute offsets, number of sentences or target annotations enter feature construction. Training marker evidence is the saved fold-local out-of-fold predictions; evaluation uses frozen predicted markers, with reference-marker evidence as an explicitly labeled diagnostic.

Test each classifier in three fixed ways: (1) add `log P(same sentence)` once to each non-root parent logit, leaving ROOT scores unchanged (strength exactly one); (2) keep non-root parents only when pair probability is at least 0.5; (3) infer an arbitrary-count contiguous partition of the ordered predicate sequence by maximizing the sum of within-block pair log-odds, then retain only same-block parents. ROOT always remains available. The partition has no supplied sentence count or token boundaries. The pair filter need not be transitive and is a compatibility diagnostic, not recovered segmentation. The partition objective is an unnormalized pairwise surrogate, not a calibrated joint probability. Compare with unchanged parents and a gold sentence-boundary upper control; never treat the upper control as learned recovery.

The primary condition is the rich **soft signal**, predicted evaluation markers and the frozen out-of-fold-trained **interaction** parent model, without role or boundary oracles. Keep the marker-only parent model as a replication and distance-only signals as controls. **Predeclared gate:** primary edge F1 must exceed the better unmodified parent control by at least two percentage points; reduce selected cross-sentence parent links by at least 25% relative to the unmodified interaction model; retain ROOT recall at least 80%; and exceed the distance-only soft signal by at least one F1 point. These are diagnostic point-estimate requirements. Do not select another application mode or retune strength/thresholds after development results. If the gate fails, keep confirmation and target evaluation deferred. If it passes, evaluate the frozen specification on the already inspected source confirmation cohort, explicitly labeling reuse.

Report pairwise discrimination/calibration, grouping consistency, true-parent candidate retention for hard restrictions, exact score components and reference feasibility, ROOT and non-root edge metrics, paired stream intervals and parent corrections/regressions. Validate both fits, absence of annotation inputs, feature symmetry, partition optimality, fixed baseline reproduction and independent forest optima. Preserve earlier results; no dictionary search or lexical-restoration claim.

## Result: the grouping signal fails the development screen

Two classifiers fit 3,484 unordered training pairs, including 951 same-sentence pairs (27.30%). Development has 844 pairs, including 233 same-sentence pairs (27.61%), over the unchanged 66 streams / 2,101 tokens / 342 reference finite positions. Thus the observed failure is not accompanied by a large overall same-sentence prevalence shift. The rich model has 137 features; the distance control has two. Parent models, marker models and repaired reference annotations are unchanged.

Primary out-of-fold-trained **interaction** parent model, **predicted** markers, unknown roles and boundaries:

| Applied grouping information | Non-root edge F1 | Selected cross-sentence parents | Reference parents still available |
|---|---:|---:|---:|
| None | 60.67% | 41 | 154/154 |
| Gold boundaries, upper control | 77.14% | 0 | 154/154 |
| Distance-only soft signal | 60.35% | 33 | 154/154 |
| Rich soft signal, **primary** | **55.83%** | **37** | 154/154 |
| Distance-only pair filter | 52.24% | 32 | 93/154 |
| Rich pair filter | 50.55% | 34 | 94/154 |
| Distance-only contiguous partition | 39.83% | 31 | 56/154 |
| Rich contiguous partition | 50.37% | 32 | 87/154 |

The primary fails three of four predeclared checks: it is 6.46 F1 points below the better unmodified parent model (marker-only, 62.30%), reduces cross-sentence parents by only 9.76% rather than 25%, and is 4.52 points worse than the distance-only soft signal. ROOT recall is 89.89%, passing that check, but ROOT precision falls from 84.18% to 79.34%. More ROOT decisions do not amount to improved structure: correct non-root edges fall from 91 to 79, and non-root recall falls from 59.09% to 51.30%.

**Confirmation and target evaluation remain deferred.** Neither thresholds nor score strength were tuned after this result, and another application mode was not selected to override the failed primary gate.

Paired development stream-bootstrap intervals (2,000 draws, seed 1729) for interaction-parent F1 are:

- Rich soft minus unrestricted: **−4.84 points [−9.19, −0.43]**.
- Distance soft minus unrestricted: **−0.32 [−3.59, +2.94]**.
- Rich soft minus distance soft: **−4.52 [−8.86, −0.02]**.

These describe the inspected development passages; they are not independent author-transfer evidence. The marker-only parent replication also loses F1 with either soft signal: 62.30% unmodified, 58.45% with distance and 54.55% with rich features. Supplying reference marker attachments does not rescue the interaction model: F1 is 61.24% unmodified, 60.63% with distance soft scoring and 57.44% with rich soft scoring.

## Why pair accuracy was insufficient

With predicted markers, pairwise AUROC is **81.40% for distance** and **80.71% for rich features**. The rich model does not improve on proximity on these passages. Its threshold-0.5 same-sentence precision is 58.05% and recall 51.07%, compared with 59.68% and 47.64% for distance. Brier score is 0.1581 versus 0.1518, and log loss 0.4828 versus 0.4581 (lower is better). With reference markers the rich AUROC is slightly higher, 82.27%, but this is an oracle-scope diagnostic and does not improve the downstream result.

More decisively, restrict the descriptive comparison to the **154 reference parent pairs** and the **41 cross-sentence parents selected by the unmodified interaction decoder**. AUROC separating those sets is only **48.13%** for rich features and **44.25%** for distance. Rich mean compatibility is 0.563 for reference parents and 0.588 for the selected wrong cross-sentence parents. This is a dependent, error-conditioned sample rather than a new statistical test, but it exposes the mismatch: success on many easy unordered pairs does not separate the decoder's actual confusions.

Adding `log P(same)` can therefore penalize correct edges at least as strongly as the wrong edges we want to remove. It also penalizes every non-root alternative while leaving ROOT unchanged. This compositional bias and the poor error-conditioned separation are observed mechanisms to investigate; this experiment does not isolate their individual causal contributions or show that no grouping model can work.

The hard restrictions make the cost explicit. Rich pair filtering removes **60/154** true parents; rich contiguous grouping removes **67/154**. The complete reference forest is unavailable in 39/66 and 41/66 streams, respectively. Those cases are not scored as reference victories or omitted from recovery denominators. Soft scoring preserves every candidate, so its decline cannot be attributed to retrieval failure.

## Consistency and error changes

The raw compatibility filters are not partitions: among 1,318 development predicate triples, thresholded distance compatibility has 104 nontransitive triples and rich compatibility has 92. The dynamic program enforces contiguous, transitive membership and infers its own block count, but that consistency does not make the groups correct. The rich partition predicts from one to seven predicate groups per stream; it is not told to recover the three source sentences. Predicates without intervening finite predicates do not define full token boundaries, and sentences with no selected predicate cannot be recovered by this representation.

Relative to the unmodified interaction decoder, rich soft scoring corrects **seven parent choices and regresses fifteen**, for eight fewer correct parents overall. Gold boundaries correct 35 and regress none on these development examples. Distance soft scoring corrects nine and regresses eight, but shifts some correct non-root decisions to ROOT, leaving edge F1 essentially unchanged. Saved [review.json](../experiments/results/grammar-restoration/iteration11/review.json) records every changed parent, pair compatibility on the decoder-confusion set and partition consistency counts.

Examples of primary soft-score regressions include `persequentur → fugite` becoming ROOT and `misit → recipit` becoming ROOT. The repaired nested relative edge `sunt → essent` also becomes ROOT. The current grouping evidence does not reliably distinguish long valid dependencies from nearby cross-sentence alternatives.

## Recommendation

Do not integrate this signal or launch dictionary decoding. There is still substantial headroom under gold boundaries, but the tested pair classifier does not supply it. The next inexpensive diagnostic should target the **actual competing parent pairs**, controlling token/predicate distance, rather than optimize aggregate all-pair accuracy. If fitting a revised classifier, construct difficult cross-sentence negatives using end-to-end source cross-fitting of the decoder, preserve reference-positive pairs and ordinary supervised calibration, and require improvement on a separate source error-conditioned discrimination check before composing its score with the parent objective. Do not reuse the failed one-batch forest-contrast objective or silently tune this experiment's weight against development.

This is a recommendation for a new, separately declared experiment; it was not run here. A failure on those harder source contrasts would support revisiting available grammatical evidence or the grouping target itself, rather than adding another penalty.

## Reproduction and validation

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_predicate_grouping_iteration11
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_predicate_grouping_iteration11_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_predicate_grouping.py tests/unit/test_parent_marker_interactions.py tests/unit/test_predicate_projection.py tests/unit/test_boundary_role_oracles.py tests/unit/test_training_alignment.py tests/unit/test_marker_oracle.py tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

Forty-five focused tests pass. The [validator](../experiments/results/grammar-restoration/iteration11/validation.json) refits both pair models, reconstructs frozen parent logits and all 264 pair-prediction sets, reproduces 528 unrestricted/gold-boundary controls, and verifies all **2,112 development forests**. It exhaustively enumerates **13,684 possible contiguous partitions** across all 264 grouping cases and matches every dynamic-program optimum. Independent Z3 optimization matches **104 forest optima** across all application modes on reviewed streams. Source/input/code hashes, pair labels, root/candidate preservation, score components, reference availability, all metrics/intervals and the failed gate are verified. No confirmation conditions were produced. Benchmark runtime was 1.3 seconds. [Report](../experiments/results/grammar-restoration/iteration11/report.json) and [gate](../experiments/results/grammar-restoration/iteration11/development-gate.json) preserve the result; earlier artifacts remain unchanged.
