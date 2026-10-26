# Iteration 188 — entropy repair helps double omissions, but worst-case floor fails

**Preserve a partial improvement, qualify its robustness:** the unchanged entropy-range rule improves applicable-pair count in103/1,378 double-endpoint omissions and worsens none. It gives9/10 applicable pairs in1,305 cases, but one still gives3/10; the8/10 minimum from single omissions does not generalize. This is a targeted optional repair, not a universal confidence guarantee.

## Frozen exhaustive challenge

Enumerate all1,378 unordered pairs of the53 supervised source endpoints, remove the union of their incident labeled training pairs, and freeze every retained-index mask before labels. Keep180 rich/control columns, ridge.1, full-source scales, anonymous feature projection, optimizer, threshold and tie policies unchanged. Deleted examples' unlabeled features remain admitted to fixed source preprocessing; this is a labeled-training perturbation, not corpus deletion.

Repeat187's none, all19-coordinate and two-left-entropy-coordinate range policies, using retained-source raw min/max and tolerance1e-12. Freeze masks, models, probabilities and trimmed/refilled selections before target scoring. Retain original baseline and every low-data/one-class outcome, cache identical fits without pretending repeated masks are independent. Primary: rich entropy-only refilled top10 versus no abstention, with all coverage/useful-evidence costs reported.

All1,378 omissions are trainable: retained source sets have38–51 pairs and8–18 positives. They produce1,078 distinct retained-training masks; adding the original baseline gives1,079 fits per model arm. No coordinate, endpoint, probability threshold or ranking cutoff is chosen from outcomes.

## Main rich-model comparison

| Outcome across1,378 omissions | No abstention | Entropy-only refill | All-coordinate refill |
|---|---:|---:|---:|
| Top10 applicable pairs, range | 3–9 | 3–9 | 5–9 |
| Top10 applicability, mean | 86.59% | 89.23% | 76.97% |
| Top10 joint yield, mean | 72.09% | 73.93% | 58.93% |
| Top10 joint yield, range | 20.00–88.47% | 20.00–88.47% | 37.50–79.58% |
| Accepted candidates (of126) | 126 | 112–122 | 63–88 |
| Useful case-comparable pairs rejected (of36) | 0 | 0–4 | 10–15 |

Entropy-only acceptance is88.89–96.83%, retaining at least32/36 useful candidates. Its applicability count improves in103 omissions (61 by4,38 by3,2 by2,2 by1), is unchanged in1,275 and never decreases. All-coordinate rejection usually worsens lists:1,138 worse,91 better,149 unchanged, with large useful-evidence loss. It is not promoted based on its higher worst-case minimum.

### Full applicability histogram

| Applicable pairs in refilled top10 | No abstention | Entropy-only |
|---:|---:|---:|
| 3 | 1 | 1 |
| 5 | 68 | 3 |
| 6 | 40 | 2 |
| 7 | 13 | 15 |
| 8 | 46 | 52 |
| 9 | 1,210 | 1,305 |

Entropy-only still has21 omission cases below8/10, corresponding to17 distinct training masks. Its single worst fit is unchanged by abstention. The1,305/1,378 rate is a conditional robustness statistic on correlated perturbations of one development source/target pair, not an estimated probability of future decipherment success.

## Residual failure and broad classifier behavior

Worst case `omit1160` retains40 source pairs, only8 positive. Both no-abstention and entropy-only lists have3/10 applicability and20% joint yield. Entropy screening rejects4 non-case targets and0 useful targets, but the wrong top-ranked candidates remain inside its source bounds. Thus the earlier out-of-range mechanism is not the only ranking failure.

Across all double omissions, rich full-targetNLL ranges.4229–.6098 and AUC.7256–.8611. Rich NLL beats its matched frequency/support control in all1,378 cases, and beats the original control NLL.5958 in1,375 (three exceptions). The control's AUC range.5074–.7062 remains below the rich range, while NLL ranges overlap. This preserves the broader contextual-feature transfer signal while rejecting a universal9/10 shortlist claim.

The original full-model baseline remains unchanged:9/10 applicability, with entropy-only rejection of4 non-case candidates and no useful ones. All per-fit accepted probability metrics, threshold/top10/top20 trimmed and refilled lists, pair/type coverage, joint yields, masks and comparisons remain in the artifacts. Conditional accuracy-like quantities must not replace coverage or useful-evidence loss; abstentions are not correct predictions.

## Interpretation and next audit

The entropy check survives a larger perturbation family as a no-harm improvement in applicable-pair count, but it solves a specific extrapolation mechanism. It does not detect every failure of source evidence coverage. Both model settings and screening rules were held fixed; no failed cases were dropped.

Next audit the residual weak masks' retained positive training evidence and feature coverage, comparing every mask rather than selecting a new confidence threshold from target outcomes. Determine whether low shortlist applicability reflects loss of positive neighborhoods, source class-prevalence shifts, or errors inside otherwise admitted source ranges. Freeze the diagnostic grouping before labels/target metrics; do not adopt reweighting or a new filter from this explanation alone.

All results are on previously used Cicero passages with strong vocabulary overlap and correlated endpoints. No new-author validation, named cases, general POS, syntactic links or lexical nuclei are established. Preserve the source-trained grammatical interface and entropy screening as an experimental option with explicit coverage limits.

## Verification

Independent reconstruction verified all1,378 double-endpoint masks and retained-source bounds. Separate Newton solves checked2,158 unique models (1,079 per arm), duplicate-mask reuse, fixed scales, gradients, all target probabilities,41,370 shortlist metric groups, all coverage/accepted calibration, ranges and paired comparisons. Exact180 original baselines passed; source-mask/policy baselines remain consistent with187's rule. Frozen input/omission/mask/model/prediction/selection hashes passed. The broader test suite was not rerun for this reference-only perturbation diagnostic; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_double_omission_iteration188.py`; reviewer: `benchmarks/grammar_case_double_omission_iteration188_review.py`. Frozen design, omissions, complete models/probabilities/masks/selections/summaries, skipped-fit inventory, ranges, paired changes, audit and verification manifest: `experiments/results/grammar-restoration/iteration188/`.
