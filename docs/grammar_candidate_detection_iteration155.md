# Iteration 155: structural scalars do not recover the candidate set

The two structural features fail as a practical ADP/CCONJ candidate detector among ordinary word types. Nested held-out-type evaluation recovers7 of9 eligible positives but also flags239 negatives:2.85% precision. Frequency alone gives3.13% precision at the same recall. The earlier useful ADP-versus-CCONJ classifications therefore remain conditional on supplied candidate membership; this experiment does not remove that privilege.

Before feature computation, the design fixed eligibility at>=5 source-fit occurrences and>=80% modal POS agreement across all annotations. All eligible ordinary types were included without negative sampling, and the entire16-type target catalogue was excluded from every training/selection fold. The source partition, opaque equality/order stream and two structural features were unchanged. All labels are cached source-fit annotations; no new annotations, reserved material or sealed works were used.

There are787 eligible types:16 catalogue targets held aside, plus771 evaluation/training types, of which9 are modal ADP/CCONJ and762 other POS. Stratified deterministic three-way word-type folds provide outer evaluation. Within each outer training set, three inner type folds select one of four fixed ridge strengths by class-balanced NLL. Final selection is source-only; standardization uses retained fit types. The graph contains unlabeled held-out-type occurrences, so this is transductive type-label evaluation, not unseen-document transfer.

The primary detector uses corrected adjacent overlap and role similarity, without a monotonic constraint because function-candidate membership is a new task. The mandatory comparator uses log1p occurrence count alone, with identical nested fitting. All models were frozen before output probabilities and all predictions before metrics. Positives are ADP/CCONJ, negatives every other modal POS; raw probability>.5 predicts positive.

| Nested OOF metric | Structural | Frequency only |
|---|---|---|
| True positives | 7 | 7 |
| False positives | 239 | 217 |
| False negatives | 2 | 2 |
| Precision | 2.85% | 3.13% |
| Recall | 77.78% | 77.78% |
| Average precision | .0296 | .0271 |
| ROC AUC | .7017 | .7751 |
| Type-macro NLL | .6450 | .6708 |
| Correct among top5 | 0/5 | 0/5 |
| Correct among top10 | 0/10 | 0/10 |
| Correct among top20 | 1/20 | 0/20 |
| Correct among top50 | 1/50 | 0/50 |

Positive prevalence is1.17%, so structural average precision is above a random-prevalence reference, but only slightly above frequency's AP and with worse ROC AUC/threshold precision. These weak ranking associations do not supply a useful shortlist. Raw probabilities come from class-balanced fitting and should not be interpreted as calibrated prevalence probabilities. Overall accuracy is uninformative here because predicting every type negative already achieves98.83%.

The frozen purity rule leaves eight preposition types and only one conjunction type, ue. Four original binary-training types are ineligible: an and siue have66.7% modal agreement, ob77.8%, post66.7%. This is intentional application of a new predeclared eligibility rule, not deletion selected from detector outcomes. Consequently this experiment has especially weak conjunction coverage, and does not refute every possible open-vocabulary detector.

The16 entirely withheld eligible targets are all reference-positive. The final structural model recalls11/16; frequency recalls16/16. This positive-only diagnostic supplies no target-set precision estimate and is not combined with OOF negatives to fabricate one. Those targets are much more frequent than most original non-target exemplars, emphasizing the distribution shift already present in the benchmark design.

Leading structural false positives include initials, formulaic expressions and content words (d, supra, publica, publicae, consulto); frequency ranks pronouns and verbs highly (me, te, est, non, esse). These are inherited source-modal references; no manual relabeling or claim that every false positive is linguistically meaningless is made. The detector does not uniquely identify the requested pair of POS among these other patterns.

Next proposed direction: a broader, explicitly defined grammatical target comprising ADP/AUX/CCONJ/DET/PART/PRON/SCONJ versus the remaining modal POS. Keep the same eligibility, source partition and strict held-out-type evaluation, with the16 old targets excluded from fitting; compare structural, frequency-only and one predeclared combined model using source-only selection. This would test a different potentially useful grammatical input with more positive exemplars. It must be described as that coarse class distinction, not all POS tagging, nuclei, or a rescue of this failed ADP/CCONJ detector. A frequency-based success should be reported as such rather than attributed to structural features.

Independent verification reconstructed all eligibility and source counts, recomputed787 vectors with combinatorial overlap/dictionary role implementations, checked all source folds and target exclusion, and independently optimized104 nested models with gradient checks. Detector AUC/AP and all reported metrics were replayed; the focused suite passed18 tests. Artifacts and verification manifest: `experiments/results/grammar-restoration/iteration155/`.
