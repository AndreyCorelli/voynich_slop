# Iteration 130: the five-anchor PP finding does not replicate across authors

The frozen five-anchor branch gives **five correct PP selections and zero wrong** on Jerome's original context, but **no selections** with expanded Jerome context or either Caesar context. Binary class accuracy is below the majority-class baseline in all four views. Preserve iteration 129's source result, but attach this failed transfer: it does not establish a generally reliable low-anchor grammatical recovery method.

## Frozen branch and scored positions

Exactly the source-fit-ranked mappings `ut`, `me`, `cum`, `quod`, and `te` remain visible. Other surrounding identities and grammatical tags are removed, and all target function-word identities/classes are hidden. The iteration-124 classifier and scalar calibration, original PP model, and old 0.80 PP cutoff remain unchanged. There is no author-specific model, budget, or threshold selection.

Class profiles use exactly the already cached Jerome 100/829-sentence and corrected Caesar 100/2,494-sentence contexts. PP inference scores only each author's original 100 sentences, with pooling limited to those positions; added text influences the class assignments only. Cached PP labels are reused, and all class predictions/PP views are frozen before inference and metrics. Original-unmapped, target, and other-original-anchor cohorts are fixed before masking.

The five visible mappings cover **32/913 scored tokens (3.50%)** in Jerome and **31/1,514 (2.05%)** in Caesar. These remain supplied mappings, not discovered nuclei. Target catalogue membership, opaque occurrence grouping, and treebank segmentation also remain privileges. These author texts have been reused in development; this is not fresh validation. No new annotations, reserve features, sealed lexical tests, or defaults change.

## Binary class transfer

| Context | Correct / present types | Majority-class prior correct | AUC | Mean NLL |
|---|---:|---:|---:|---:|
| Jerome 100 | 7/13 | 8/13 | 0.7875 | 0.6547 |
| Jerome 829 | 7/16 | 8/16 | 0.7188 | 0.6957 |
| Caesar 100 | 6/13 | 7/13 | 0.5714 | 0.7331 |
| Caesar 2,494 | 7/15 | 8/15 | 0.7500 | 0.7214 |

All present types are retained, with missing and support flags saved separately. Jerome's original context classifies only `a` and `ab` as ADP. In its expansion, these two become incorrectly classified as conjunctions, while `atque` is incorrectly classified as ADP. Over thirteen common types, accuracy falls **7/13→5/13**, with no gains; two newly present conjunctions are correct and `atque` wrong.

Both Caesar contexts classify every present target type as a conjunction, missing every preposition. Their thirteen common types remain **6/13 correct**; added `uel` is correct and `sine` wrong. The expanded class ranking retains some separation (AUC 0.75), but the fixed decision rule supplies no ADP tags. More context alone does not fix this branch.

## PP membership on the unchanged original samples

| Class-profile context | Unknown target classes | Inferred hard target classes | Originally unmapped, inferred |
|---|---:|---:|---:|
| Jerome 100 | 0/0 | **5/0** | **4/0** |
| Jerome 829 | 0/0 | 0/0 | 0/0 |
| Caesar 100 | 0/0 | 0/0 | 0/0 |
| Caesar 2,494 | 0/0 | 0/0 | 0/0 |

Cells are correct / wrong PP selections at the fixed 0.80 cutoff. The original other-anchor cohort contributes Jerome's remaining one correct selection; this cohort includes mappings removed by masking. Target-token selections remain empty. Jerome's five original successes disappear after its two correctly identified prepositions are lost in the expanded class profile.

The maximum hard PP score falls from approximately 0.864 to 0.221 for Jerome and stays approximately 0.166 for Caesar. These are observations, not a license to lower thresholds using author answers. The matching unknown-class predictions are invariant between base and expanded context because PP positions and unknown inputs remain identical.

## Implication and next diagnostic

The source five-anchor result remains a conditional success, but this replication does not support it as a dependable input to decipherment across texts. Broader conditional class/ranking findings from iterations 118–125 remain separate; failure of this sparse branch does not erase them. No exact word identity is recovered here.

Next isolate the two stages before changing another cutoff: compare low-anchor PP inference supplied with correct target classes (an explicit oracle ceiling) against the inferred classes. Also separate class-context budget from PP-context budget with frozen mixed-budget controls. This would establish whether scarce known mappings primarily break class inference, PP inference, or both. Oracle labels and extra visible context would remain diagnostic privileges, never proposed discoveries or a deployable low-anchor solution.

## Verification

The independent audit verifies 27 frozen input hashes, recomputes 57 type probabilities and eight PP score vectors, checks 32 fixed-cohort confusion/transition groups, reconstructs anchor masking and original-prefix scoring, checks context-invariant unknown baselines, and verifies reserve exclusion. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration130/`.
