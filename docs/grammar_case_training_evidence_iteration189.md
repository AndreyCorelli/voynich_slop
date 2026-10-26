# Iteration 189 — residual failures concentrate where positive source evidence is depleted

**Diagnostic finding:** all21 double-omission lists below8/10 applicability retain only8–11 positive source pairs, versus18 originally. Every omission retaining13 or more positives has8–9/10 applicability. This is a source-evidence association, not a validated minimum-sample threshold or proof that class imbalance causes the failure.

## Frozen audit

No model or selection changes. For all1,378 double omissions plus original, freeze retained positive/negative counts, prevalence, positive endpoint diversity/incidence and per-class/all-source min/max on all19 features. Using frozen188 entropy-refilled top10 lists, freeze positive/negative coordinate-box membership and nearest standardized Euclidean class distances for every selected target row before consulting target truth.

Prespecify source-positive-count bins<=9,10–12,13–15,>=16 and target-applicability groups<=7,8,9. Report all masks and empty bins, distinct retained-training counts and error geometry. Source labels define training evidence, never target feature inputs. Distances use original180 feature scales; no distance threshold, confidence filter or class reweighting is applied.

## Positive evidence by prespecified source bins

| Retained positive source pairs | Omissions | Distinct training masks | Mean top10 applicable pairs | Range | Mean positive source prevalence |
|---|---:|---:|---:|---:|---:|
| <=9 | 3 | 3 | 5.33 | 3–7 | 21.88% |
| 10–12 | 53 | 45 | 7.58 | 5–9 | 25.86% |
| 13–15 | 136 | 117 | 8.90 | 8–9 | 30.56% |
| >=16 | 1,186 | 913 | 8.99 | 8–9 | 35.48% |

The original source has18 positives among52 pairs (34.62%). The21 weak omissions contain8–11 positives among38–42 retained pairs (20.00–26.83% prevalence), spanning15–18 positive endpoint types versus21 originally. They correspond to17 distinct training masks. This is selective loss of labeled positive neighborhoods, while the candidate features remain projected from the full anonymous corpus.

All21 weak masks belong to the56 omissions retaining<=12 positives, but35 of those56 still achieve8 or9 applicable pairs. Thus low positive count is not sufficient to identify a bad model, and13 must not be adopted as a target-derived training threshold. Counts, class proportions and specific lost feature neighborhoods vary together.

## Residual selected errors are not all range violations

Among the21 weak lists, each has1–5 non-case pairs inside the **all-source19-coordinate box**, averaging1.95 per list. They already passed the fixed two-entropy range rule. Each also has1–5 non-case pairs nearer to a retained positive than a negative source example in fixed-scale Euclidean distance (mean2.19). Raw proximity to positives therefore is not a safe confidence measure.

The positive-class coordinate box contains no selected non-case pair across the audit, but contains only0–1 applicable selected pair per omission:492 lists have none,886 have one; the original list has one. Treating that box as a filter would discard most of the selected useful evidence. This is a descriptive coverage limit, not a new perfect-precision result or a lexical nucleus.

In weak lists,2–5 non-case pairs still receive probability>=.5 (mean3.29), showing imperfect confidence after source evidence loss. Every coordinate, class bound, distance and selected row is retained; no favorable feature or subgroup was chosen as a repair.

## Interpretation and next diagnostic

The entropy abstention candidate addresses missing negative-example support, but depletion of positive training evidence exposes a second failure mode that includes in-range errors. This explains why188's average improvement does not give a universal shortlist floor. The association cannot separate changing class mass from the loss of specific positive contexts; neither adding examples nor reweighting is validated by it alone.

Next freeze a training-contribution control that preserves the **original source class proportions18/52 and34/52** in every omitted fit. Within each retained class, divide its fixed total contribution equally among its examples; retain full-source feature scales, ridge, columns, target inputs and existing masks. Refit all omissions and compare list robustness and full-population probability losses, retaining unfavorable coverage/calibration tradeoffs. This is a diagnostic of training mass versus missing information, not a target-tuned choice of weights or a default class-balancing recommendation.

All observations remain on correlated perturbations of reused same-author Cicero data with extensive vocabulary overlap. No minimum-source-count confidence rule, named cases, POS assignments, syntactic links or lexical nuclei are established. Preserve the original source-trained applicability signal and optional entropy repair with this second evidence limitation explicit.

## Verification

Independent replay checked1,379 source-evidence records, every class-bound/incidence calculation,13,790 selected target geometry records,96 cohort-field summaries, every target-outcome row and all partitions. The original scaling input hash was additionally verified through the frozen188 parent. Frozen input/source/geometry hashes passed. The broader test suite was not rerun for this reference-only diagnostic; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_training_evidence_iteration189.py`; reviewer: `benchmarks/grammar_case_training_evidence_iteration189_review.py`. Frozen design, complete evidence/bounds/geometry/rows, cohorts, summaries, audit and verification manifest: `experiments/results/grammar-restoration/iteration189/`.
