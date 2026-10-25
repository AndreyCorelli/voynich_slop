# Iteration 157: coarse shortlist enrichment survives removal of purity filtering

**Preserve the applicability gain:** both frequency and combined models retain8/10 correct broad-class members when every supported word type is eligible for scoring, including mixed-POS types. Known modal purity no longer filters inference/evaluation candidates. The result remains source-only, coarse-class shortlist enrichment, not exact word identity or full POS restoration.

The seven-tag positive union is unchanged: ADP/AUX/CCONJ/DET/PART/PRON/SCONJ, with every remaining modal POS negative, including ADV. All types with at least five source-fit occurrences enter the scoring pool. Purity>=80% is used only to select source training labels within each fit. Outer word-type folds cover every supported non-target type; each model trains only on pure types outside its held-out fold. Inner source-only selection uses pure training types, the unchanged four-strength grid and class-balanced NLL. Standardization is fit-specific, and the unlabeled source graph remains transductive.

The entire16-type historical catalogue is still excluded from fitting and primary OOF rankings and scored separately as a withheld reference set. These exclusions define this benchmark; they are not a proposed identity-based filter for Voynich. Inference features use only opaque ID equality/order and counts. Eligibility/folds were frozen before features, models before predictions, and predictions before metrics. No new annotations, reserved material or sealed works were used.

There are882 supported types:16 withheld catalogue types, plus866 primary evaluation types. The latter include771 pure and95 mixed types;211/866 are modal positive (24.36% prevalence). The final source training pool remains771 pure non-target types,150 positive. New predeclared outer fold assignments mean changes from iteration156 cannot be attributed solely to adding mixed types.

| Nested OOF metric, all supported non-target types | Structural | Frequency | Combined |
|---|---|---|---|
| True positives | 82 | 123 | 126 |
| False positives | 245 | 166 | 169 |
| Precision at raw>.5 | 25.08% | 42.56% | 42.71% |
| Recall | 38.86% | 58.29% | 59.72% |
| Average precision | .2460 | .4735 | .4926 |
| ROC AUC | .5106 | .7151 | .7225 |
| NLL | .6933 | .6232 | .6166 |
| Correct top5 | 1/5 | 4/5 | 4/5 |
| Correct top10 | 2/10 | 8/10 | 8/10 |
| Correct top20 | 5/20 | 13/20 | 14/20 |
| Correct top50 | 11/50 | 30/50 | 33/50 |

All shortlist budgets are reported without selecting an optimal cutoff. The combined top10 is ut, non, est, cum, mihi, si, me, quod, quam, te. Under inherited source-modal references, non and quam are outside the seven-tag union. These identities are shown for evaluation; no plaintext identities enter the predictor. Mixed types are evaluated by their modal class, so these are word-type decisions, not claims that every occurrence has that POS.

Frequency alone accounts for most of the shortlist success. Combining the structural scalars improves AP by.0191 and AUC by.0074 over frequency, with three additional true positives and three additional false positives at the fixed threshold. Structural-only AUC is near chance. The incremental combined benefit needs author-level replication before being treated as a reliable structural contribution.

Pure/mixed subgroups are retained without filtering predictions. Combined pure-type precision is37.19% and recall60.00%; mixed-type precision67.92% and recall59.02%. Mixed prevalence is64.21%, so the higher subgroup precision alone is not evidence of strong detection. Overall threshold precision42.71% is insufficient for a reliable general classifier, even though top10 enrichment is useful. The experiment does not establish corpus-independent80% precision.

This removes the held-out-type purity privilege from ranking eligibility, while preserving legitimate source label-quality filtering. It does not yet test cross-author transfer, unsupported rare types, arbitrary POS, or lexical nuclei. The preceding source finding remains worth exploring as a possible grammatical input for deciphering, with its frequency-led character stated explicitly.

Next step: replicate the frozen three models on already cached annotated author streams. First establish which complete word/POS references are available without new annotations or opening reserved/sealed texts, then freeze the author set, occurrence-only eligibility and all shortlist budgets before scoring. All supported types should be eligible regardless of purity or source vocabulary membership; score unknown references explicitly rather than silently dropping them. Preserve the frequency comparator and report each author separately. Avoid retraining, author-specific choices or treating a shared broad class as recovered shared Latin word identities.

Independent verification reconstructed882 supported word types and labels, recomputed882 feature vectors by combinatorial overlap/dictionary roles, checked all pure-only training memberships and unrestricted held-out evaluation, and independently optimized156 nested models with gradient checks. All nine detector/subgroup metric sets were replayed;18 focused tests passed. Frozen artifacts and manifest: `experiments/results/grammar-restoration/iteration157/`.
