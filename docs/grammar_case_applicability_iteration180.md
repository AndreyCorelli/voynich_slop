# Iteration 180 — source-trained applicability transfers to a diverse target shortlist

**Highlight this initial positive result:** a fixed source-trained model ranks9 case-comparable pairs among its target top10, involving11 word types, with82.87% conditional case agreement and74.58% joint yield. The frequency/support-only model finds4/10, and the full target graph has36/126 applicable pairs. This is a supervised source-language component operating on opaque target features, not supplied target POS/case selection or exact lexical restoration.

## Frozen training and inference

Train on52 earlier Cicero primary pairs (18 applicable), then transfer unchanged to126 replication pairs. The binary target is whether a candidate pair has **any** recognized-case occurrence comparison in its existing shared frames; it does not name a case, POS, or individual case-bearing token. At inference all candidate pairs are eligible regardless of reference labels.

For each endpoint, exclude every occurrence belonging to any of the queried pair's shared frames from its context distributions. Keep whole-passage global unigram frequencies. Endpoint features are log global frequency; log(1 + outside-query count); unique-left/outside-count; unique-right/outside-count; left and right entropy divided by log outside-count; left and right mean log neighbor frequency divided by log passage length; and a no-outside-occurrences flag. Empty entropy/fraction/frequency features are zero. Pair features are symmetric means and absolute differences of these9 values, plus log distinct shared-frame support:19 features. No spelling, word identity feature, POS, case, or sentence boundary is used.

Primary model: ordinary unweighted logistic regression, mean NLL plus `.1/2` times squared slope weights, unpenalized intercept, source-only mean/std scaling. No hyperparameter, feature, threshold, or model selection. Controls: the same fixed model on mean log frequency, absolute log-frequency difference and log support; and source positive prevalence as a constant prior. Freeze features, source labels/models, then all source/target predictions before target evaluation. Source scores are in-sample diagnostics, not OOF evidence. Fixed selections are probability>=.5 and top10/top20 including all exact probability ties.

The design's target-label barrier is procedural, not physically isolated storage: the shared172 JSON cache is parsed for source access, but only its earlier labels enter fitting before model/prediction freezes. Target labels are consumed only in the evaluation stage; no target-based tuning occurs. This implementation detail is recorded in the audit rather than claiming the joint cache was not parsed.

## Transfer classification: case applicability, not named morphology

Target contains126 pairs,36 positive (28.57%).

| Fixed model | Target AUC | Brier loss | NLL | >=.5 selected | True positives | Precision | Recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rich anonymous contexts (primary) | .8417 | .1416 | .4411 | 30 | 20 | 66.67% | 55.56% |
| Frequency/support only | .6265 | .2043 | .5958 | 8 | 3 | 37.50% | 8.33% |
| Source prevalence prior | .5000 | .2077 | .6066 | 0 | 0 | — | 0.00% |

Rich model target confusion:20 TP,10 FP,16 FN,80 TN. Its apparent source AUC is.9118 (in-sample), which is not additional transfer evidence. Both loss measures improve over both controls on target; they do not establish fully calibrated confidence.

### Fixed target shortlist behavior

All case agreement retains the original frame-within-pair/pair-macro scoring; selection uses no target labels.

| Model/list | Selected pairs | Case-comparable pairs | Case-involved types | Conditional agreement | Joint yield |
|---|---:|---:|---:|---:|---:|
| Rich >=.5 | 30 | 20 | 19 | 81.74% | 54.49% |
| Rich top10 | 10 | 9 | 11 | 82.87% | 74.58% |
| Rich top20 | 20 | 15 | 16 | 82.31% | 61.74% |
| Frequency/support >=.5 | 8 | 3 | 5 | 90.74% | 34.03% |
| Frequency/support top10 | 10 | 4 | 7 | 68.06% | 27.22% |
| Frequency/support top20 | 20 | 7 | 11 | 81.75% | 28.61% |
| All graph (prior top10/top20 ties) | 126 | 36 | 33 | 70.41% | 20.12% |

The constant prior has no ordering, so its tie-inclusive top lists contain all126 pairs; it must not be described as a ten-pair shortlist. Joint yield is the sum of covered-pair agreements divided by all selected pairs, assigning inapplicable pairs zero contribution solely as a diagnostic; it is not token accuracy or restored-case accuracy. All source/target lists, counts and metrics are preserved.

### Target calibration bins for the rich model

| Predicted range | Pairs | Mean predicted applicability | Observed applicability |
|---|---:|---:|---:|
| [0,.2) | 45 | 10.81% | 6.67% |
| [.2,.4) | 33 | 29.34% | 15.15% |
| [.4,.6) | 30 | 48.94% | 43.33% |
| [.6,.8) | 12 | 70.45% | 83.33% |
| [.8,1] | 6 | 85.06% | 83.33% |

The [.2,.4) bin shows substantial overprediction and the upper bins are small. Raw scores should not yet be treated as calibrated probabilities of grammatical correctness.

## What this contributes toward decipherment

This is an initial label-free-at-inference interface to the case-compatibility relation: candidate pairs can now be prioritized without target POS/case truth, with materially greater diversity than the one-pair shortlists in177. It is explicitly **supervised on source Latin references**, unlike the graph construction itself. It predicts case applicability among a restricted candidate graph, not general POS, every case-bearing position, named case values, syntactic attachments, or lexical nuclei. The source-trained component could in principle be reused on a one-word-per-word opaque target, but neither Voynich applicability nor another-author reliability has been tested.

Both passages are previously investigated Cicero development material; source has only52 training pairs, with shared endpoints and correlated observations. Query-frame exclusion reduces direct reuse of the scored occurrences in context distributions, but global counts, graph support and other occurrences remain admitted features. Target inputs were available in earlier research; this is not a fresh sealed holdout result. No algorithm is adopted as a hard constraint or decipherment confidence rule.

Next proposed diagnostic: freeze the rich and frequency/support pipelines and refit them under a fixed set of source-label permutations preserving the18/52 positive count. Apply each fit unchanged to the same target features; compare transfer loss/AUC/top10 applicability with the actual-label fits, retaining every outcome. This tests the source-label/context relationship behind the gain, not new-author generalization. No target tuning or feature selection from the permutation outcomes; independently verify all fits and labels.

## Verification

Independent reconstruction verified all178 feature rows and every queried-frame exclusion using stream-neighbor identities rather than descriptor position filtering. Two separate Newton solves recover the frozen source fits within1e-5, all fitted gradients are below1e-6, and source-only scales, predictions, confusion matrices, calibration bins, AUC, Brier/NLL and18 fixed-list metric groups passed independent checks. Input/feature/model/prediction hashes passed. The broader test suite was not rerun for this reference-only diagnostic. No new annotations, reserved or sealed data were used.

Runner: `benchmarks/grammar_case_applicability_iteration180.py`; reviewer: `benchmarks/grammar_case_applicability_iteration180_review.py`. Frozen design, features, source labels, models, predictions, selections, complete summaries, audit and verification manifest: `experiments/results/grammar-restoration/iteration180/`.
