# Iteration 126: source context sensitivity limits simple recalibration

The frozen class model's pooled probabilities depend substantially on available context. Across three fixed 100-sentence source samples, mean absolute shifts relative to full context are **18.4–19.8 percentage points**; at 1,600 sentences they shrink to **3.7–5.2 points**. Both class decisions and score rankings vary, so the evidence does not justify assuming that one volume-dependent intercept will fix transfer. No new calibrator or author-selected cutoff is fitted.

## Source-only diagnostic

Use the existing thirteen noncatalogue training types, with each type predicted exclusively by its iteration-124 held-type fold model. Its own labels and identities are excluded from that model; all sixteen target catalogue types are masked throughout and are never evaluated here. Inputs are word-only projections of the existing 2,471 source-fit sentences, with the usual supplied surrounding anchors and segmentation.

Three SHA256 orderings, fixed by seeds 12600–12602, define nested samples of 100, 200, 400, 800, and 1,600 sentences. The full 2,471-sentence view is scored once. All present training types are retained; missing types and support are reported, not filtered out. The three streams overlap and are not independent replications. Context composition changes alongside size, so this is not a pure causal volume experiment.

All fold models and the scalar offset remain frozen. The offset was fitted on these same thirteen full-context out-of-fold profiles: this is a calibration robustness diagnostic, not independent model validation. Selections and predictions are frozen before reference metrics. No author scoring, new annotations, reserve features, sealed lexical tests, PP inference, or fitting occurs.

## Results by sample size

Ranges below describe the three individual streams, without pooling their overlapping observations. Correct fractions use all present types; their denominators change at small volumes.

| Sentences | Correct types in streams 0 / 1 / 2 | Mean absolute probability shift to full | Cutoff crossings to full |
|---|---|---:|---:|
| 100 | 4/10 · 7/9 · 2/6 | 18.4–19.8 pp | 3–4 |
| 200 | 5/10 · 7/12 · 4/8 | 10.4–20.5 pp | 2–4 |
| 400 | 6/12 · 9/13 · 8/13 | 11.4–16.3 pp | 3–4 |
| 800 | 8/13 · 8/13 · 7/13 | 6.2–11.0 pp | 1–3 |
| 1,600 | 9/13 · 8/13 · 8/13 | 3.7–5.2 pp | 0–3 |
| 2,471 | 9/13, shared full view | 0 | 0 |

Drift and cutoff crossings compare each sample with exactly the same present types in the full view. Full-common metrics, individual type transitions, and class-specific drift are saved, preventing missing types from being counted as successes or conflated with changed decisions.

The full-view result is seven of ten ADPs and two of three CCONJs correct, giving **68.33% balanced accuracy**. Its all-ADP prior gets ten of thirteen types correct but only 50% balanced accuracy; the 9/13 versus 10/13 raw comparison reflects the imbalanced type pool and must not be read alone. The fitted model's full-view NLL is approximately 0.590 versus the balanced prior's 0.693. These calibration-set figures do not establish out-of-sample reliability.

Full-view AUC is 0.70. At 800 sentences it ranges from 0.6333 to 0.9333, and at 1,600 from 0.70 to 0.90. Thus stronger ranking is not monotonic in context size. Sparse types make this particularly unstable: only three training types are CCONJ, and one 100-sentence sample contains only one present CCONJ type. No uncertainty guarantee follows from these small counts.

## What this changes

The earlier transferable ranking gains remain preserved in iterations 124–125. This diagnostic adds evidence that absolute class probabilities and, sometimes, rank ordering are sensitive to context composition; it does not prove that context volume caused the Caesar errors. It provides no validated replacement cutoff and no reason to select different models or thresholds per author.

For the high-level decipherment goal, keep the probabilistic grammatical signal as a candidate input, but avoid asserting its hard classes as certain. The next proposed experiment is uncertainty-aware PP integration, calibrated only on existing source calibration data, with frozen unknown-class and hard-class controls and unchanged precision/coverage guards. This tests whether an imperfect class signal can supply useful structural constraints without requiring exact word recovery first. A model that passes such a test would still need its supplied-anchor assumptions addressed before Voynich use.

## Verification

An independent review verifies 14 frozen hashes, reconstructs all sixteen selections, independently checks 184 type probabilities and 174 metric groups, confirms target-field poison invariance in all 48 fold/view combinations, checks source/reserve separation, and replays drift and common-type comparisons. Full profiles reproduce iteration 124's out-of-fold predictions. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration126/`.
