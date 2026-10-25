# Iteration 138: four-text class evidence remains uneven

The frozen sentence-free corrected-overlap predictor agrees with supplied class references on **10/15 Gellius types (66.67%)** and **6/14 Livy types (42.86%)**. Gellius shows a useful ranking tendency (AUC 0.8393), but Livy does not replicate the strong Caesar result. Across four texts, this is not yet reliable general grammatical classification or the desired shared lexical nucleus.

## Frozen replication on inspected works

Use exactly the existing normalized Gellius I stream (9,670 tokens) and Livy I stream (16,983 tokens), without adding sentence boundaries or changing tokenization. The same iteration-135 corrected-overlap classifier, calibration, and 0.5 class cutoff remain primary. Raw overlap and frequency are frozen controls, not author-specific replacements.

Livy's old provenance still says `sealed-test`, but it was already opened and evaluated in the earlier trigram confirmation. The existing confirmation design and completed comparison are hashed and verified before this run. This experiment reads only those already inspected word streams; the remaining sealed Ammianus and Quintilian works are not opened. No decoder truth file, new grammatical annotation, or new lexical restoration test is queried.

Words are mapped to salted opaque IDs before feature computation. Only ID equality, counts, and order enter the predictor; supplied translations and sentence boundaries do not. The same sixteen-type function-word catalogue remains given. All present types are retained, missing types reported, and no enclitic splitting or initial correction is introduced.

Each original stream has sixteen fixed global word-order shuffles (seeds 13800–13815), preserving all token counts. Streams and transformations are frozen before statistics, and predictions before supplied source-modal class references are attached. There is no fitting, cutoff selection, PP inference, or default change. These texts have previous development history, so this is transfer testing of this frozen model, not a fresh-data guarantee.

## New-work results

| Work / frozen arm | Correct / present | AUC | Mean NLL | Null AUC at least actual |
|---|---:|---:|---:|---:|
| Gellius, **corrected primary** | **10/15** | **0.8393** | **0.6356** | 1/16 |
| Gellius, raw overlap control | 11/15 | 0.8750 | 0.5119 | 0/16 |
| Gellius, frequency control | 8/15 | 0.4643 | 1.6660 | 16/16 |
| Livy, **corrected primary** | **6/14** | **0.6458** | **0.7224** | 2/16 |
| Livy, raw overlap control | 9/14 | 0.7396 | 0.6124 | 0/16 |
| Livy, frequency control | 8/14 | 0.5833 | 1.4412 | 16/16 |

The all-ADP majority prior gives eight correct types in each work. Thus corrected overlap improves hard agreement over that prior in Gellius but loses in Livy. Balanced-prior NLL is 0.693: corrected overlap improves it in Gellius and worsens it in Livy. Raw overlap shows additional order-sensitive information in these two works, but is not substituted after inspecting results; it does not reproduce Caesar's strong corrected-overlap performance.

Gellius corrected overlap gets all seven supplied conjunction references right but misses prepositions `a`, `ad`, `de`, `per`, and `sine`. Livy misses seven preposition references and `uel`. Weighted type-class agreement is 81.24% and 59.30%, respectively, against constant type references, not newly annotated token POS.

The shuffle comparisons are descriptive, with sixteen correlated null streams per work, not formal generalization probabilities. Frequency predictions are exactly invariant to shuffling, as expected. One Gellius null and two Livy nulls match or exceed the primary's AUC.

## Normalization and reference limitations

The cached raw streams use lowercase, u/v and i/j normalization, with no newly introduced changes. Standalone `que` is absent from both streams; treebank component segmentation in earlier texts can expose it separately. It is reported missing, not counted as wrong or artificially split out.

Gellius also has **eight standalone `c` tokens**, while the source catalogue's `c` conjunction reference originated from treebank component segmentation. The raw tokens may represent initials; source-modal class agreement is not a validated POS label for those occurrences. The predeclared primary includes `c` and does not silently drop or relabel it. Livy has no standalone `c`, so its poor result is not explained by that particular mismatch. References and preprocessing need explicit compatibility checks before treating raw-versus-treebank differences as purely linguistic.

Only occurrence support (at least five tokens) can be reported for raw streams; original sentence-count support is unavailable and is not manufactured by chunking. No present type is filtered from primary metrics.

## Four-text perspective

These are the same frozen primary model's sentence-free results; input volumes differ materially.

| Text | Tokens | Correct / present types | AUC | NLL |
|---|---:|---:|---:|---:|
| Caesar expanded | 52,691 | **13/15 (86.67%)** | **1.0** | 0.4146 |
| Jerome expanded | 7,713 | 10/16 (62.50%) | 0.6719 | 0.7170 |
| Gellius I | 9,670 | 10/15 (66.67%) | 0.8393 | 0.6356 |
| Livy I | 16,983 | 6/14 (42.86%) | 0.6458 | 0.7224 |

The strongest text supplies substantially more tokens than the others. Earlier sentence-count curves do not by themselves control this difference. Different segmentation and content also matter; these are not four comparable independent accuracy estimates to pool.

Preserve the Caesar milestone and the weaker Gellius ranking signal, but do not claim a dependable four-text POS result. No exact plaintext word identities are inferred: the original requirement of shared trustworthy lexical nuclei remains unmet. Useful grammatical evidence may still seed another decoder, but candidate-set discovery and cross-text reliability remain unresolved.

Next compare the four texts at fixed token budgets, with all present types and paired common-type/support reporting, keeping this model unchanged. That would test whether the apparent cross-author gap is partly an evidence-volume difference before adding another calibration or feature variant. Predeclare windows/mixtures without inspecting target outcomes and retain normalization/reference caveats.

## Verification

Independent audit verifies nineteen frozen hashes, reconstructs the two opaque streams and all 34 transformations, independently recomputes 493 type/context statistics with combinatorial null probabilities, replays 1,479 class probabilities and 306 metric groups, checks exact frequency preservation, and reconstructs the four-text table. It verifies Livy's previously inspected provenance without opening other sealed works. Fifteen focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration138/`.
