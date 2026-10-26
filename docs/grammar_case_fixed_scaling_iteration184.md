# Iteration 184 — fixed scaling does not resolve the influential-example shortlist drop

**The sensitivity is not primarily a rescaling artifact:** using original full-source means/scales leaves the rich model's top10 case-applicability count unchanged in all53 source-endpoint omissions. The same two omissions still give5/10 rather than9/10. The broader transfer loss advantage remains, but the exact shortlist genuinely depends on training evidence from one negative pair.

## Frozen control

Copy every183 omission mask, including all duplicate retained-training sets. Keep the same180 anonymous feature values, rich19/control3 columns, ordinary logistic mean NLL plus fixed.1 slope ridge, unpenalized intercept, optimizer, target features and list thresholds/tie policies. Change only standardization: use original180 full-source means/stds for every omission fit rather than recomputing them after deletion.

Deleted examples' **unlabeled features** therefore remain in source preprocessing, but their labels/examples do not enter fitting. No target statistics enter scaling. This is a diagnostic control on labeled-neighborhood omission, not token deletion, a new source-only subset projection, or a proposed preprocessing winner. Freeze omission indices, all fits and target probabilities before evaluation; retain all53 omissions and both arms.

## Rich-model comparison across all omissions

| Target metric | Recomputed scales (183) | Fixed full-source scales (184) |
|---|---:|---:|
| NLL range | .4314–.5459 | .4324–.5286 |
| Mean NLL | .4465 | .4459 |
| Brier range | .1381–.1785 | .1378–.1738 |
| AUC range | .7762–.8540 | .7824–.8543 |
| Top10 applicability range | 50–90% | 50–90% |
| Top10 contains9 applicable pairs | 50/53 | 50/53 |
| Top10 contains8 applicable pairs | 1/53 | 1/53 |
| Top10 contains5 applicable pairs | 2/53 | 2/53 |
| Top10 joint-yield range | 49.58–78.47% | 39.58–78.47% |
| Top10 case-involved types | 9–12 | 8–12 |
| Original-top10 overlap | 6–10 pairs | 6–10 pairs |

Fixed scaling improves rich NLL in33 omissions and worsens it in20. **No rich omission changes its top10 applicable-pair count**, although membership and conditional consistency can change. All53 fixed-scale rich fits still beat original control NLL.5958 and their matched fixed-scale controls; the latter's NLL range is.5789–.6113. These are correlated development sensitivity checks:53 endpoint omissions,47 distinct retained-training masks.

All full control ranges, per-omission deltas and classification/calibration/list outputs remain in the artifacts. Frequency/support top10 counts change in one omission, not enough to alter the principal rich-model conclusion.

## Known leverage example

Both `omit12` and `omit33` remove exactly negative source pair index21, leaving51 training pairs and all18 positives. They are the same training perturbation through two endpoints, not two independent failures.

| Target result after deleting pair21 | Rescaled | Fixed scaling |
|---|---:|---:|
| NLL | .5459 | .5286 |
| AUC | .7762 | .7824 |
| Top10 applicability | 5/10 | 5/10 |
| Top10 joint yield | 49.58% | 39.58% |

The fixed-scale list's conditional case agreement is79.17%, but only half its selected pairs have comparable cases. Neither that percentage nor the joint-yield percentage is named-case accuracy or lexical restoration. Fixing scales slightly helps broad classification while worsening this list's joint yield; do not adopt it as a robustness fix on these results.

## Interpretation and next diagnostic

The earlier result is bounded more precisely: source-trained contextual applicability generalizes beyond exact labeled-pair repetition and retains a broad loss advantage under every single endpoint-label-neighborhood omission, yet one negative example materially affects top-ranked predictions. Recomputing source scales contributes to numeric changes but does not explain the5/10 failure.

Next proposed diagnostic: with full-source scales fixed, give source pair21 a predeclared series of training weights from zero to one, leaving all other labels/examples unchanged. Report coefficient movement, target probability/rank crossings, loss and list applicability for every weight; no weight is selected for deployment or optimized against target labels. This traces the training influence and identifies the affected feature directions before proposing a model change. Preserve source/target development and dependence limits.

No default algorithm change, named cases, POS tags, syntactic links or lexical nuclei result here. The model remains a supervised source-language diagnostic on reused same-author data with highly overlapping passage vocabulary.

## Verification

Independent reconstruction verified identical183 masks, original full-source scales in every fit,108 separate Newton solutions and all gradient checks, every target probability/classification/calibration value,324 list metric groups, all ranges and all paired184-versus183 deltas. Exact180 original models/predictions/summaries passed. Frozen input/omission/model/prediction hashes passed. The broader test suite was not rerun for this reference-only control; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_fixed_scaling_iteration184.py`; reviewer: `benchmarks/grammar_case_fixed_scaling_iteration184_review.py`. Frozen design, omissions, complete models/predictions/selections/summaries, ranges, paired deltas, audit and verification manifest: `experiments/results/grammar-restoration/iteration184/`.
