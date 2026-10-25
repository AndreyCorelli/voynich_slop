# Iteration 136: long-context Caesar class signal survives passage mixtures

**Preserve the robustness finding:** the frozen anchor-free corrected-overlap predictor gets **13/15, 15/15, and 13/15 Caesar types correct** in three fixed 1,600-sentence mixtures, with AUC **0.9643, 1.0, and 0.9821**. At 800 sentences, all three mixtures give twelve correct types, with AUC at least 0.927. This supports the long-context Caesar signal beyond one particular passage mixture, but the overlapping samples are not independent confirmations and Jerome does not show comparable reliability.

## Frozen volume and composition check

Keep exactly iteration 135's corrected-overlap statistic, trained model, calibration, and class cutoff. Raw-overlap and frequency controls also remain frozen and are reported without selecting an arm per text. There is no fitting or PP inference.

For each cached author expansion, construct three SHA256 orders over all sentence IDs using seeds 13600–13602. Take nested prefixes at 100, 200, 400, and 800 sentences, plus 1,600 for Caesar. Original 100-sentence views remain separate references; the full 829-sentence Jerome and 2,494-sentence Caesar contexts are each scored once. There are 31 total views, all selected and frozen before statistics.

The random mixtures do not protect the original 100 sentences. They vary passage composition as well as size. All present target types remain included, with missing/support flags reported rather than filtered out. Saved comparisons evaluate the same present types in the full view and track the original thirteen-type cores, explicitly reporting missing core types. Full and original outputs reproduce iteration 135.

Inference features use opaque-ID equality and boundaries only, with no supplied mappings or tags. The candidate function-word set and sentence segmentation remain given. These are repeatedly used development texts and correlated overlapping samples, not independent validation. No annotations, reserve features, sealed lexical tests, target-selected thresholds, defaults, or lexical nuclei are added.

## Caesar: strong long-context behavior

Each row lists the three fixed mixtures in seed order. Fractions use all present types.

| Sentences | Correct / present types | AUC range | NLL range |
|---|---|---:|---:|
| 100 | 6/13 · 6/14 · 6/14 | 0.7188–0.8571 | 0.7596–0.7966 |
| 200 | 7/15 · 6/14 · 6/14 | 0.7500–0.8750 | 0.7094–0.7421 |
| 400 | 10/15 · 8/15 · 7/14 | 0.8542–0.9643 | 0.6059–0.6366 |
| 800 | **12/15 · 12/15 · 12/14** | **0.9271–1.0** | 0.4905–0.5693 |
| 1,600 | **13/15 · 15/15 · 13/15** | **0.9643–1.0** | **0.4286–0.4693** |
| Full 2,494, once | **13/15** | **1.0** | **0.4158** |

The original thirteen Caesar types are present in every sampled mixture. On this fixed core, accuracy rises from **6/13 in all three 100-sentence mixtures** to **11/13, 13/13, and 11/13 at 1,600**. This shows improvement on the same types, not merely admission of easier types at larger volumes.

The full model still misclassifies `atque` and `que`; one 1,600-sentence subset correctly classifies all fifteen present types. Thus hard accuracy is not strictly monotonic in size even though the long-context pattern is strong. No subset is selected as a preferred decoding context. The model and cutoff remain fixed throughout.

## Jerome: no comparable robust improvement

| Sentences | Correct / present types | AUC range | NLL range |
|---|---|---:|---:|
| 100 | 6/13 · 3/13 · 7/14 | 0.2250–0.7500 | 0.8656–1.1822 |
| 200 | 5/14 · 5/15 · 5/14 | 0.5000–0.6458 | 0.8184–0.9358 |
| 400 | 6/14 · 8/16 · 6/15 | 0.5625–0.6786 | 0.7440–0.7978 |
| 800 | **7/14 · 9/16 · 9/16** | **0.3958–0.6562** | **0.7243–0.8964** |
| Full 829, once | **10/16** | **0.6719** | **0.7182** |

Jerome's NLL remains worse than the balanced prior's 0.693 in every listed mixture and full context. Rare conjunction types are sometimes absent even in the 800-sentence sample. These omissions are reported, not counted as successes. Larger context does not reliably resolve the class distinction here.

Jerome and Caesar have different available maximum volumes, content, and segmentation conventions. Their curves do not isolate author effects from all other differences. The failure at roughly comparable 800-sentence sizes nevertheless prevents a general Latin accuracy claim.

## Meaning and next challenge

A long-context, anchor-free binary grammatical signal now has a within-author robustness result worth preserving as a possible input to another decipherment method. It still does not identify exact Latin word identities or reliably classify arbitrary opaque word types: function-word membership is supplied and Jerome fails. No claim about a shared nucleus or Voynich translation follows.

The next direct Voynich-relevance challenge is sentence-boundary dependence. Keep the same model and words but remove supplied sentence boundaries, testing fixed sentence-order mixtures as needed, and add word-order shuffles that preserve word frequencies. This would distinguish a useful word-order signal from a segmentation privilege or a frequency-related artifact before moving to additional texts or PP integration. Freeze all transformations and report all contexts without choosing a target-favorable order.

## Verification

Independent review verifies seventeen frozen hashes, reconstructs all 31 selections, recomputes 448 type/context statistics using combinatorial null probabilities, replays 1,344 class probabilities and 558 metric groups, and checks original-core/full-present comparisons and missing-type accounting. Original and full iteration-135 predictions reproduce, no models or thresholds change, and reserve IDs remain absent. Fifteen focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration136/`.
