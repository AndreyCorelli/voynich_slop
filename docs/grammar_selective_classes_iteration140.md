# Iteration 140: confidence does not yield a reliable four-text class seed

The source-selected confidence policy selects **zero target types in all four texts**. The predeclared top-five confidence control gives **Caesar 5/5 correct classes, Jerome 1/5, Gellius 4/5, and Livy 3/5** against supplied references. Thus neither a common absolute confidence threshold nor this fixed ranking rule provides the desired dependable cross-text grammatical subset. These are class labels, not recovered exact word mappings.

## Source-only selection

Keep the iteration-135 corrected-overlap predictor, calibration, and 0.5 class boundary unchanged. Eligibility requires at least five occurrences. Class confidence is max(P(CCONJ), 1 − P(CCONJ)). Enumerate all attained confidences among the thirteen source training types' held-type out-of-fold predictions, plus 0.5 and 1, using inclusive comparison and retaining ties.

Require at least three selected types and at least 90% selected-reference accuracy on source. Select maximum correct coverage, then fewer errors, then the higher threshold. The calibrated probabilities already use an offset fitted on these same thirteen out-of-fold profiles; reusing them for selection is disclosed calibration-set reuse, not independent validation. Three correct source types do not establish a statistical reliability guarantee.

The selected confidence threshold is **0.9487595396752573**, retaining exactly `erga`, `ob`, and `siue`, all correctly classified (two ADP, one CCONJ). Freeze that policy before loading four target prediction sets. The test requires every text to retain at least three types with at least 90% agreement; averaging good and bad texts cannot pass it.

Apply it to the same full sentence-free Caesar, Jerome, Gellius, and Livy predictions from iterations 137–138. No class probabilities are refitted. All four primary selections are empty, so the cross-text criterion fails through lack of coverage; empty outputs are not reported as 100% accuracy.

## Fixed rank controls

Top-three and top-five controls are specified before target loading, with all confidence ties at the boundary retained. They are diagnostics, not fallback policies selected after the absolute cutoff fails. No text-specific threshold or arm is chosen.

| Text | Eligible types, correct / available | Source-selected cutoff | Top three, correct / selected | Top five, correct / selected |
|---|---:|---:|---:|---:|
| Caesar | 13/15 | 0 selected | **3/3** | **5/5** |
| Jerome | 7/13 | 0 selected | **1/3** | **1/5** |
| Gellius | 10/15 | 0 selected | 3/3* | 4/5* |
| Livy | 6/14 | 0 selected | **1/3** | **3/5** |

*Gellius selections include raw `c`, whose conjunction reference comes from treebank component segmentation and may not apply to these raw initials. These are supplied-reference agreement counts, not validated token POS accuracy. The primary retains it as predeclared; it is not silently removed or relabeled.

Jerome eligibility excludes three low-count types, leaving thirteen; the old full-context 10/16 result must not be substituted for this eligible subset. Minimum occurrence support does not automatically improve correctness.

For auditability, top-five selections are:

- Caesar: `ab`, `ad`, `aut`, `ex`, `uel`; all five class labels correct.
- Jerome: `aut`, `c`, `per`, `que`, `sine`; only `aut`'s class is correct.
- Gellius: `aut`, `c`, `et`, `per`, `uel`; `per` is wrong, and `c` has the reference caveat above.
- Livy: `a`, `ac`, `atque`, `aut`, `sine`; `a` and `sine` are wrong.

These plaintext names are attached for private benchmark assessment; the algorithm predicts only ADP/CCONJ labels for opaque IDs and does not infer these word identities.

The fixed common-fourteen secondary view also fails to rescue the result: top-five selections give Caesar 5/5, Jerome 1/3, Gellius 3/4, and Livy 3/5. Missing excluded types are not replaced with more favorable candidates. Full eligible, top-three, and common-set metrics are saved.

## Implication and next hypothesis

The long-Caesar class-ordering result remains preserved. It does not support treating this model's confidence as a universal indicator of reliable grammatical recovery. More threshold refinement on these target answers would not be a justified next step. No trustworthy four-text class seed or shared exact lexical nucleus is established, and no default changes.

A fresh representation hypothesis is to compare the **contexts of neighboring opaque words**, rather than requiring the same neighbor IDs on both sides. Different words can have similar distributional roles while direct ID overlap remains low. A minimal next test could use one scalar measuring similarity between aggregated left- and right-neighbor context representations, with source-only training and frequency/null controls. It should preserve strict target-type exclusion and avoid another large supervised feature bundle on thirteen labels. This is a proposal, not an established linguistic fact or a result.

## Verification

Independent review verifies fourteen frozen input hashes, reconstructs thirteen source probabilities and fifteen threshold settings, replays the source choice, verifies sixteen target selection arms including tie/support handling, and checks 32 reference-metric groups. It confirms all primary target selections are empty. Fifteen focused tests pass. No new annotations, model fitting, PP inference, reserve features, sealed-work query, or lexical recovery test occurs. Frozen artifacts are in `experiments/results/grammar-restoration/iteration140/`.
