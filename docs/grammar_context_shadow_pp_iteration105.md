# Iteration 105: extra-context repairs restore the clean grammatical predictions in more cases

**Preserve the conditional grammatical finding:** every one of the nine primary exact anchor repairs enabled by expanded Caesar context reproduces the clean PP model's full probability vector on the original 100 sentences. Original-context recommendations restore it in four cases. This adds five successfully repaired corruption cases without changing the PP model, its thresholds or its 1,514 scored token positions.

This restores the existing clean grammatical subset under more synthetic errors. It does not expand clean-input grammatical coverage, establish arbitrary mapping discovery, or recover lexical nuclei.

## Frozen blind application

Use all 54 iteration-104 cases: fifteen cross-class errors and three clean/same-class controls in each of the original, Civil-added and primary-expanded contexts. Apply every recommendation from all five frozen policies, including the original-context wrong recommendation and all abstentions. Never gate an intervention on pair correctness. Swap the recommended opaque types' public anchor names and tags at every occurrence in the original 100-sentence input; retain IDs, positions and private evaluation labels.

Added prose influences only the already frozen anchor-pair recommendation. It never enters PP feature extraction or pooling. Compute all unique repaired and corrupted inputs with the unchanged iteration-85 original model at 0.80 and iteration-89 augmented model at 0.71 and 0.80. Save interventions and predictions before computing metrics. No training, threshold adjustment, new annotation, reserve scoring or sealed lexical test access occurs.

The grammatical target is governed-node PP membership: a node with an ADP `case` child, including the previously defined inheritance through amod/conj/flat/fixed links. It is not exact governor recovery, full PP spans or Case restoration. The setup still supplies 195 context anchors and assumes one bijective cross-class swap among the eight candidate types.

## Results on the fixed 100 sentences

The clean original model selects **72 correct / 4 wrong** PP memberships: 94.74% precision and 45.28% recall among 159 reference positives. The clean augmented model selects 62 / 4 at 0.71 or 27 / 1 at 0.80. Exact anchor repair restores these full probability vectors, including their existing errors and omissions.

| Recommendation context and rule | Exact pair repairs / wrong repairs | Cases reproducing clean PP probabilities |
|---|---:|---:|
| Original context, original cutoff | 4 / 1 | 4 |
| Civil-added, original cutoff | 8 / 0 | 8 |
| Primary expansion, original cutoff | 9 / 0 | 9 |
| Original context, gain-gap rule | 4 / 0 | 4 |
| Civil-added, gain-gap rule | 8 / 0 | 8 |
| Primary expansion, gain-gap rule | 7 / 0 | 7 |

The probability-restoration counts hold for both PP models. All control interventions are no-ops; all three OFF policies remain no-ops. The primary expansion preserves the four original-cutoff successes and restores five additional cases:

| Corruption | Original-context result: correct / wrong PP memberships | Expanded-context result |
|---|---:|---:|
| ad ↔ sed | 58 / 4 | 72 / 4 |
| de ↔ que | 76 / 25 | 72 / 4 |
| de ↔ sed | 66 / 4 | 72 / 4 |
| ex ↔ sed | 67 / 4 (after a wrong pair action) | 72 / 4 |
| in ↔ sed | 36 / 2 | 72 / 4 |

These are alternative corruptions of the same text, not five disjoint sets of newly restored words. Clean recovery can reduce correct classifications that were accidentally produced by a corrupted input. For de/que, the exact repair adds six correct memberships, loses ten, and removes 21 false positives. For in/sed it adds 37 correct memberships and three false positives, while losing one correct membership and removing one false positive. All individual changes are retained.

## All-error totals and counterexamples

Across all fifteen alternative error cases, the original model's corrupted baseline has 928 correct / 208 wrong selections. Original-context recommendations give 988 / 182; primary-expanded recommendations give 1,045 / 163. Precision over these repeated case outcomes changes from 81.69% before repair to 84.44% with original-context repair and 86.51% with primary-expanded repair. The clean comparator repeated fifteen times is 1,080 / 60. Thus the full mixed set, including six abstentions, remains below 90% precision.

Primary-expanded repairs versus corruption produce 135 new correct memberships, lose 18, add eight false positives and remove 53. Net: +117 correct and −45 false selections. Relative to original-context repair, the primary expansion yields net +57 correct and −19 false selections. These sums repeatedly count the same 1,514 positions under different synthetic mappings; they are neither unique restored tokens nor independent observations.

Both augmented settings also improve on aggregate. At 0.71, original-context outcomes are 850 / 190 versus primary-expanded 889 / 165; at 0.80, 364 / 68 versus 384 / 47. The stricter gain-gap rule retains the iteration-104 coverage regressions: primary expansion restores only seven cases, fewer than the Civil view's eight. No view or threshold is selected using these results.

The original-context wrong ex/sed action is applied and evaluated: it changes original-model selections from 64 / 4 to 67 / 4, but introduces six lost true positives alongside nine new ones and leaves seven decisions different from clean. A favorable net PP count does not certify a correct anchor mapping.

## Verification and next challenge

Replay all 270 case-by-policy actions, recompute both PP models for all nineteen unique inputs (38 inferences), and independently verify 2,430 confusion-count checks, hidden counts and all token transitions. Forty exact-repair actions across overlapping views/rules reproduce clean probabilities; this is not forty independent successes. Original clean predictions match the prior iteration-86/89 caches. Verify 185 input hashes and 720 aggregate count fields; all 57 focused tests pass. Artifacts, frozen design, prior tracker snapshot, public deltas, full score arrays, all actions and audits are in `experiments/results/grammar-restoration/iteration105/`.

The next challenge should broaden the candidate bank before further tuning: retain the frozen extra-context selection and original 100-sentence evaluation, enumerate all sixteen source-defined candidate types and all 64 cross-class swaps plus controls, and measure exact repair, wrong actions and downstream PP effects with fixed rules. Earlier broader-bank experiments exposed failures hidden by small candidate cores. This tests whether the added-context benefit survives distractors and rarer anchors; no additional target annotations are needed.
