# Frozen anchor-conditional PP transfer — iteration 86

**Positive held-out-author development transfer:** the frozen selective policies retain high observed precision on cached Jerome and Caesar sentences, with content forms opaque and no supplied token POS. The models/thresholds are unchanged from85; neither author was used to fit or calibrate this pipeline.

| Frozen policy | Author | Correct / wrong | Observed precision | Recall | Selected types |
|---|---|---:|---:|---:|---:|
| 20 supplied anchors, empirical source policy | Jerome | **21 / 0** | **100% (21 selections)** | 31.82% | 20 |
| Same | Caesar | **42 / 3** | **93.33%** | 26.42% | 34 |
| 195 supplied anchors, stricter source policy | Jerome | **40 / 1** | **97.56%** | 60.61% | 36 |
| Same | Caesar | **72 / 4** | **94.74%** | 45.28% | 57 |

This supports a **conditional partial grammatical-restoration module** for governed-node membership. It does not establish guaranteed precision, discovered anchors, full phrase boundaries, exact attachments, Case values or blind Voynich restoration. The small Jerome sample with zero observed errors does not establish universal100%precision.

## Cached material and fixed protocol

The iteration40cache contains full word/POS/head/relation annotations for the previously declared iteration26author slices. Use all100Jerome sentences as primary and all100Caesar sentences as a secondary check. Counts are913tokens/66positive memberships for Jerome and1,514tokens/159positives for Caesar. No POS/Case/construction filter or example selection is applied.

These sets are disjoint from every source49fit/calibration/test sentence and from the closed reserve. Cached normalized tokens exactly match the declared datasets. No raw treebank parsing, new annotation requests or reserve access occurs.

Both author sets were used by earlier development experiments, including40's separate PP-contrast model. Thus this is **held-out-author transfer for the current pipeline**, not fresh independent confirmation on previously unseen research material. No prior model from those experiments is used here.

Use exactly85's20-anchor empirical policy (threshold0.81) and195-anchor conservative policy (threshold0.80), their frozen source-selected anchor lists and model weights. No refitting, threshold adjustment, anchor replacement or budget selection occurs. The latter calibration criterion retains85's binomial/dependence limitations and is not a transfer guarantee.

Visible anchor positions: Jerome178/913(19.50%)at20anchors and311/913(34.06%)at195; Caesar241/1514(15.92%)and434/1514(28.67%). Exact anchor identities/source-modal tags and sentence boundaries remain supplied. All other forms, including unrecognized function words, have only opaque equality IDs; no hidden-form dictionary, POS, suffix, length or finite lookup is used.

PP labels use the same governed-node rule: own case-linked ADP or inherited membership through amod/conj/flat/fixed links. Markers themselves and arbitrary descendants are not automatically members. Private cached annotations define reference labels only; public model features contain anchor/equality context, not reference morphology or links.

## Hidden-form results

Every20-anchor selected position is hidden: Jerome21/0andCaesar42/3. For195anchors:

| Author | Hidden correct / wrong | Hidden precision | Hidden-positive recall |
|---|---:|---:|---:|
| Jerome | 35 / 1 | 97.22% | 60.34% |
| Caesar | 67 / 4 | 94.37% | 49.26% |

The high observed precision therefore is not only an easier visible-anchor effect. Sample sizes remain limited and the broader source benchmark still includes the weaker Palladius results from83–85.

## Strong proximity control

Apply the previously frozen source-F1policies to both model and nearest-left-preposition control; do not tune on either transfer author.

| Setting / author | Model F1 | Nearest-left F1 |
|---|---:|---:|
| 20 anchors / Jerome | 81.03% | 81.03% |
| 20 anchors / Caesar | 67.42% | 67.42% |
| 195 anchors / Jerome | 81.36% | 79.66% |
| 195 anchors / Caesar | 76.98% | 73.12% |

At20anchors the broad F1policies make **identical position predictions**, not just equal aggregate scores. The selective model filters that proximity candidate set; none of its20-anchor selections lies outside it. At195anchors, broad prediction sets differ slightly and one selective Caesar position lies outside the nearest-control set. The result supports calibrated selective grammatical labels, but does not demonstrate that a complex learned model is needed for the20-anchor broad task.

The nearest control has no qualifying high-precision source-calibration policy under85's rule. Its good transfer F1andprecision cannot be used to select a new threshold retrospectively. Preserve its strength when assessing algorithmic novelty.

## Decision and next work

Preserve these frozen policies, the cached author selections and all control outcomes. This is stronger evidence of useful partial grammar than another gain confined to the original source split. Anchor correctness remains a central untested prerequisite:20or195mappings are supplied, not recovered from ciphertext.

The next diagnostic should perturb **missing and mistaken anchors** under fixed policies, using source-frozen choices of frequent anchors and error patterns rather than author-outcome selection. Separate loss of coverage from falsely confident grammatical assignments. Do not claim cipher-side readiness until the effect of uncertain anchor mappings is measured. Extending membership to exact governor links or Case sets remains a separate, untested task.

## Verification

All four transfer predictions and evaluations replay, with frozen thresholds checked explicitly. Re-keying opaque IDs and replacing private reference POS/heads/roles leave inference scores unchanged. Cached/source/reserve disjointness, complete author-slice membership and token alignment are checked. Audit verifies1,769prior input hashes.

Three new tests cover cached-token conversion, unseen reference POS categories and private-annotation feature invariance; all81focused tests pass. No source model/policy changes, reserve scoring, sealed lexical final-test scoring or dictionary search.

Artifacts: `experiments/results/grammar-restoration/iteration86/`; runner/audit: `benchmarks/grammar_anchor_transfer_iteration86*.py`.
