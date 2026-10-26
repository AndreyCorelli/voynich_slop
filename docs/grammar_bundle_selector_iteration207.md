# Iteration207: anonymous bundle selector does not yield a reliable head

The fixed source-trained bundle model fails the small-shortlist goal. Full12 top3 selects zero teacher-supported centers in every author; top5 selects one each in Aquinas, Cicero and Jerome, and none in Caesar. Preserve the earlier gold-reference bundle evidence, but do not promote this predictor into a decoder.

## Frozen experiment

Use the conservative205 graph and its edge-or-pivot deletion adjusted detections as teacher labels:7/136 Aquinas,0/23 Caesar,3/34 Cicero,3/112 Jerome. These labels indicate support under the fixed conditional Case/POS-profile null, not ground-truth grammatical classes or word identities. Each target author is excluded from fitting and standardization; all other three receive equal total training weight, including Caesar's zero-positive rows. No new raw annotations, Dante reuse or reserved Seneca labels enter this pilot.

The full12 features are log frequency; log1p degree, shared frames and queried pivots; occurrence reuse; queried/global-frequency fraction; mean log partner frequency and log1p partner degree; normalized left, right and joint context entropies; and joint context unique fraction. Contexts use every occurrence with valid lexical neighbors and respect193 boundaries. Compare the first four features as a learned count control, plus raw frequency and degree ranking. Both learned models minimize source-author-balanced logistic NLL plus .05 times squared slope norm, with free intercept and source-only weighted scaling. No feature, model, threshold or author selection follows target results.

Features are frozen before teacher loading, and all models, predictions and tied top3/top5 lists before evaluation. Raw rankings are not probabilities; logistic outputs estimate teacher support, not grammatical correctness. All ties remain in the lists.

## Results

Cells show supported/selected centers for top3, then top5.

| Held-out author | Full12 | Count4 | Frequency | Degree |
|---|---|---|---|---|
| Aquinas |0/3;1/5|1/3;1/5|0/3;1/5|1/3;1/5|
| Caesar |0/3;0/5|0/3;0/5|0/3;0/5|0/3;0/5|
| Cicero |0/3;1/5|0/3;1/5|0/3;0/5|0/4;1/6|
| Jerome |0/3;1/5|0/3;0/5|0/3;0/5|0/3;1/5|

Full12 AUC is .9313 Aquinas, undefined Caesar, .6452 Cicero and .8440 Jerome. Degree alone yields .9557, undefined, .5645 and .8869 respectively. Broad rank discrimination therefore does not imply useful precision at the head. Caesar's teacher contains no positives, and Cicero/Jerome each only three, so even an oracle cannot give five supported centers in every text. Supported centers are anonymous: no intersection of correctly identified Latin words has been demonstrated.

Machine-readable summary includes per-list coverage/precision/recall/AUC and learned-model NLL, Brier, fixed-.5 confusion and calibration. Caesar recall and AUC are explicitly undefined. The four authors and correlated teacher labels are reused development data; this is not fresh-author confirmation.

## Audit and next diagnostic

Independent code reconstructs all305 feature rows from stream and edge memberships, checks teacher labels, source weights/scales, eight Newton refits, predictions,32 tied lists, scalar ranking metrics and classification metrics, plus11 freeze hashes. All checks pass. Artifacts reside in `experiments/results/grammar-restoration/iteration207/`.

Next examine all13 supported centers' rank intervals and the false positives above them under all four fixed rankings, together with count/topology/context feature contrasts. Separate broad ranking from head precision and identify whether unsupported high-degree hubs dominate. This descriptive development audit must not choose a new confidence threshold or redefine the teacher from target outcomes. A new predictor should follow only a specific transferable explanation; the earlier annotation-based evidence remains useful independently.
