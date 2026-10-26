# Iteration 183 — transfer loss survives every source-endpoint omission; shortlist has a leverage point

**Preserve the positive and its limit:** all53 source-endpoint omission fits retain better target NLL than both the original frequency/support model and their matched omission control. Fifty fits preserve9/10 target applicability, one gives8/10 and two give5/10. The latter two delete the same single negative training pair through its two endpoints, identifying a real shortlist sensitivity.

## Frozen omission audit

Enumerate all53 opaque endpoint IDs in the52 supervised source pairs before consulting labels. For each, remove all incident training pairs; keep every omission, including duplicate training masks. Use unchanged180 rich19 and frequency/support3 columns, ordinary ridge logistic strength.1, optimizer and source-only rescaling on the retained rows. Original-label baseline copies exact180 fits.

Feature values remain those of the full anonymous corpus, including outside-query context projection and global frequencies. Therefore this deletes a source word's **labeled neighborhood**, not its tokens or all its influence on feature extraction. Freeze omission indices, source models and then all target probabilities before target evaluation. All fixed.5/top10/top20 policies and exact ties remain; no target tuning or endpoint selection.

Training sets contain43–51 pairs. All contain both classes, so no one-class fits are skipped. The53 endpoint omissions produce47 distinct training masks; they are correlated sensitivity checks, not53 independent replications.

## Target sensitivity ranges

| Target metric | Original rich fit | Rich omission range | Frequency/support omission range |
|---|---:|---:|---:|
| NLL | .4411 | .4314–.5459 | .5796–.6110 |
| Brier loss | .1416 | .1381–.1785 | .1975–.2109 |
| AUC | .8417 | .7762–.8540 | .6000–.6830 |
| Top10 case applicability | 90% | 50–90% | 30–50% |
| Top10 joint yield | 74.58% | 49.58–78.47% | 18.33–37.22% |
| Top10 case-involved types | 11 | 9–12 | 5–9 |
| Overlap with original model's top10 | 10 | 6–10 pairs | 4–10 pairs |

All53 rich omissions beat the original control NLL.5958 and all53 matched-control NLLs. Even the worst rich NLL is below the best control-omission NLL, and the rich/control AUC ranges do not overlap in this audit. These ranges are development sensitivity evidence, not generalization bounds or calibrated confidence intervals.

Joint yield remains a diagnostic agreement sum over all selected pairs, not recovered case/word accuracy. Case-involved type diversity and list overlap refer to each fit's selected target pairs; names and POS labels are not predicted.

## Shortlist leverage: one negative example

| Rich-model omission outcome | Endpoint omissions |
|---|---:|
| Top10 contains9 applicable pairs | 50 |
| Top10 contains8 applicable pairs | 1 |
| Top10 contains5 applicable pairs | 2 |

The two low-applicability cases are `omit12` and `omit33`. Both remove exactly source pair index21 (zero-based), leaving51 training pairs and all18 positive examples. Their models/predictions are identical: targetNLL.5459, AUC.7762 and5/10 applicable top10 pairs. This is one shared negative-example leverage point, not two separate influential training pairs. It does not erase the broader classifier advantage, but it prevents claiming uniformly stable9/10 ranking.

No omission is discarded, and this post-outcome identification is descriptive; it did not change training or target cutoffs. Every fit, prediction, calibration bin, threshold/top10/top20 list, low-data count and summary remains in the artifacts.

## Interpretation and next diagnostic

The source-context relation is not wholly dependent on any one supervised endpoint neighborhood: applicability loss and AUC advantages persist. Nevertheless one negative example materially affects the precise shortlist. Source scaling is recomputed after deletion, so this audit combines loss of that training label/example with changes to means/scales; it does not identify which mechanism drives the shift.

Next freeze an otherwise identical control that keeps180's full-source feature means/scales fixed for all omissions while still deleting incident labeled pairs. This isolates the effect of rescaling from omission of training evidence. Keep all53 omissions, exact models/thresholds and target metrics, and compare to the current restandardized fits without choosing favorable endpoints. Full-source scaling admits only unlabeled source features, so document that distinction rather than describe it as training-subset-only scaling.

Both passages remain reused Cicero development data with largely shared vocabulary. The candidate universe is a restricted primary graph, probabilities remain imperfectly calibrated, and no named cases, general POS, lexical nuclei or syntactic links have been recovered. Preserve the potential supervised grammatical interface; neither a default hard constraint nor Voynich readiness is established.

## Verification

Independent reconstruction checked all53 endpoint omissions and47 distinct retained-training masks. Separate Newton refits verified108 models (106 omissions plus2 original arms), source-only rescaling and gradients below1e-6; every target probability, classification/calibration value,324 shortlist metric groups, all ranges and exact180 original models/predictions/summaries passed. Frozen hashes passed. The broader test suite was not rerun for this reference-only sensitivity audit; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_endpoint_sensitivity_iteration183.py`; reviewer: `benchmarks/grammar_case_endpoint_sensitivity_iteration183_review.py`. Frozen design, omissions, complete models/predictions/selections/summaries, ranges, skipped-fit inventory, audit and verification manifest: `experiments/results/grammar-restoration/iteration183/`.
