# Iteration 139: token matching reduces Caesar's accuracy advantage, not its ranking advantage

At a common **7,000-token budget**, the frozen primary classifier gives **Caesar 7/13, 9/14, and 10/14 correct**, versus **Jerome 10/16 throughout**, **Gellius 9/15, 10/15, and 8/15**, and **Livy 5/14 throughout**. Caesar's score ranking remains stronger, with AUC **0.8438–0.9167**, but the 13/15 full-stream result depends partly on its much larger evidence volume. Token matching does not establish reliable cross-text hard classification or repair Livy.

## Frozen comparison

Use the exact four sentence-free streams from iterations 137–138, with no supplied mappings or sentence boundaries in the features. Keep iteration 135's model, calibration, and 0.5 cutoff fixed. Corrected overlap remains primary; raw overlap and frequency remain frozen controls, without selecting a model per author.

For each work, choose three 7,000-token contiguous windows by a fixed SHA256 rule using seeds 13900–13902. Center nested 1,000- and 3,000-token windows inside each larger window. These three starts are frozen before statistics and metrics. Full streams are scored once as references, giving forty total views. Windows overlap and are not independent replications; no favorable window is selected.

All present types remain in primary results. Report occurrence support of at least five tokens as metadata, not a filter. A secondary fourteen-type common set is defined solely by presence in all four full streams, excluding `c` and `que`; missing members in shorter windows remain explicit. The primary still retains raw Gellius `c` with its previously documented reference mismatch. This common-set comparison is not an outcome-based relabeling or candidate-discovery result.

Comparisons against full-stream metrics use the same present types to avoid conflating prediction changes with type admission. Original sentence-count support is not inferred from artificial chunks. No fitting, PP inference, new annotation, raw normalization, initial/enclitic repair, reserve feature, sealed-work query, default change, or lexical nucleus is introduced.

## Matched 7,000-token results

Triples list the three fixed seeds in order. All results below use corrected overlap.

| Text | Correct / present types | AUC range | NLL range |
|---|---|---:|---:|
| Caesar | **7/13 · 9/14 · 10/14** | **0.8438–0.9167** | 0.569–0.683 |
| Jerome | 10/16 · 10/16 · 10/16 | 0.6406–0.6562 | 0.726–0.743 |
| Gellius | 9/15 · 10/15 · 8/15 | 0.6964–0.8304 | 0.650–0.705 |
| Livy | **5/14 · 5/14 · 5/14** | 0.5729–0.6875 | 0.805–0.854 |

For comparison, the full streams yield Caesar **13/15 on 52,691 tokens**, Jerome **10/16 on 7,713**, Gellius **10/15 on 9,670**, and Livy **6/14 on 16,983**. Caesar's greater raw volume was a material confound in the earlier four-text accuracy table. Its ranking advantage remains in all three selected windows, though these small correlated comparisons do not prove a general author effect.

NLL is better than the balanced prior's 0.693 in all three Caesar windows, two Gellius windows, and none of the Jerome or Livy windows. Hard accuracy alone does not capture the different quality of the class probabilities.

## Same candidate types and missing data

On the fixed common fourteen-type set, the 7,000-token results are:

| Text | Correct / present common types |
|---|---|
| Caesar | 7/13 · 9/14 · 10/14 |
| Jerome | 10/14 · 10/14 · 10/14 |
| Gellius | 8/14 · 9/14 · 7/14 |
| Livy | 5/14 · 5/14 · 5/14 |

Caesar's first window lacks `uel`; it is not counted as a failure or success. The other two windows contain all fourteen common types. Jerome's common-set accuracy exceeds Caesar in one window and ties it in another, despite lower AUC, highlighting the distinction between score ordering and the fixed decision boundary. These class-agreement counts are not exact word translations.

Full-catalogue missing-type accounting is saved separately from each work's lookup coverage, including Caesar's globally absent `c`. No present candidate is silently omitted. Complete 1,000/3,000-token results, all controls, support strata, and paired full-stream comparisons remain in the artifacts rather than being selected for favorable presentation.

## Implication for decipherment research

The anchor-free word-order signal remains worth preserving, especially Caesar's long-context separation. The current model does not yet provide reliable general Latin classification, and more tokens do not automatically cure a weak text such as Livy. Observed differences may reflect evidence volume, actual contextual distributions, normalization/segmentation, and reference compatibility; token matching isolates only one part of that problem.

A useful next question is whether a small confidence-ranked grammatical subset transfers more reliably than all-type classification. Predeclare the selection rule from source-only evidence, keep all four texts and reference caveats, and distinguish correctly inferred classes from exact lexical nuclei. This would test the high-level objective of preserving a dependable information seed without claiming that the entire grammar must first be solved.

## Verification

Independent review verifies sixteen frozen hashes, reconstructs all forty windows, recomputes 554 type/context statistics with combinatorial null probabilities, replays 1,662 class probabilities and 1,080 metric groups, checks common-set and missing-type accounting, and reproduces the four full-stream results from iteration 138. Models and thresholds remain unchanged. Fifteen focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration139/`.
