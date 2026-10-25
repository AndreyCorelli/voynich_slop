# Iteration 145: block-deletion stability does not certify correctness

The frozen joint classifier's stability under removal of text blocks is not a dependable confidence filter. It preserves systematic mistakes and loses correct decisions in several texts. Keep the positive full-text grammatical finding from iterations142/143, but do not add unanimous block-deletion agreement as a validated reliability gate.

Before prediction, five consecutive blocks were fixed at boundaries floor(k*N/5). Each view deletes one block and concatenates the remaining stream; the resulting seam is part of the perturbation. There are five deletion views and one full reference for each of seven already inspected texts. No fitting, calibration, new labels, reserved material or sealed works were used. The primary model is iteration142 joint raw at its unchanged 0.5 cutoff.

A candidate is unanimous only if it remains present in every deletion and all five hard predictions agree with its full-text prediction. Missing candidates are unavailable, never counted as agreement. This rule was declared before evaluation; all agreement-count bins and incomplete cases are retained in the artifacts.

| Text | Full correct/types | Unanimous correct/types | Coverage | Stable wrong types |
|---|---|---|---|---|
| Caesar | 12/15 (80%) | 12/14 (85.7%) | 93.3% | atque, sed |
| Jerome | 12/16 (75%) | 6/9 (66.7%) | 56.3% | c, que, sed |
| Gellius | 12/15 (80%) | 9/11 (81.8%) | 73.3% | per, sed |
| Livy | 10/14 (71.4%) | 7/11 (63.6%) | 78.6% | a, sed, sine, uel |
| Apuleius | 6/13 (46.2%) | 4/8 (50%) | 61.5% | a, ab, ex, sine |
| Curtius | 12/15 (80%) | 8/11 (72.7%) | 73.3% | de, sed, sine |
| Suetonius | 12/16 (75%) | 12/15 (80%) | 93.8% | ac, atque, sed |

In Caesar, the only excluded candidate is an unavailable que, so the apparent precision gain does not demonstrate useful discrimination among fully observed candidates. Jerome has two incomplete candidates (atque, uel); Curtius has one (c). In Livy, every excluded candidate was correctly classified in the full text. Thus stability can select the wrong subset even when the overall classifier is useful.

The intersection of correctly classified unanimous candidates across all seven texts is et and in. This is a descriptive, evaluation-label-selected observation, not a deployable selection rule or exact lexical identification. Catalogue membership is supplied, and references are source-modal ADP/CCONJ classes rather than independent token-level POS annotations. In particular, the c and que normalization caveats remain. Stable errors for sed in six texts show why repeatability alone cannot certify correctness.

Next proposed test: a second spatial scale of the opaque context comparison. Fixed distance-two left/right overlap, corrected by the same pooled-neighbor random-split expectation, could capture parallel structure beyond immediately adjacent words. Train only on the existing 13 non-target training types, retain the frozen joint model as the comparator, and predeclare one augmented model rather than search distances or author-specific arms. This targets missing structural evidence rather than treating stability as correctness; it remains an untested proposal.

Verification: independently reconstructed all 42 views, recomputed overlap by combinatorial counts and roles with dictionary calculations, replayed logits separately, and checked all agreement rows and full-reference equality. The focused suite passed 18 tests. Artifacts are in `experiments/results/grammar-restoration/iteration145/`; the frozen report, runners and artifacts are covered by its verification manifest.
