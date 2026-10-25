# Iteration 163: normalized frequency does not transfer for binary grammatical classes

Reject explicit normalized frequency as a demonstrated improvement to this binary classifier. Frequency improves source held-type accuracy, but the combined model loses accuracy against the matched structural arm in six of seven target texts. This does not invalidate the distinct frequency-led broad grammatical shortlist; finding common function-related words and distinguishing prepositions from conjunctions are different tasks.

The frozen experiment uses the29-type source inventory and folds from162, explicitly retaining source exposure to the16 historical catalogue types. It therefore remains anonymous author transfer with lexical exposure, not the original strict word-type exclusion. Three arms were fixed: two structural scalars with nonnegative slopes; frequency alone with unrestricted slope; and all three features with only the structural slopes constrained. Frequency is log1p(n*31884/Nstream), exactly log1p(n) on the source. Source/target names or mappings are not feature inputs.

Each arm selected regularization on source-only nested three-fold validation, from the same four-value grid and balanced-NLL rule. Standardization is fit-specific. All outer folds selected.5; the final structural fit selected.05 and final frequency/combined fits.5. Final strengths were held fixed for every29 type omission and seven existing focal perturbations. All source models/selections were frozen before target predictions and all predictions before evaluation. No author-specific arm, cutoff or perturbation was selected.

| Source nested OOF,29 types | Structural | Frequency | Combined |
|---|---|---|---|
| Correct | 15/29 | 20/29 | 17/29 |
| AUC | .5606 | .6237 | .6364 |
| NLL | .6817 | .6864 | .6704 |

The majority source baseline is18/29. Frequency improves hard accuracy by two above majority; combined NLL improves modestly over structural, but its accuracy remains below majority. These source results alone do not establish transfer.

| Full target text | Structural correct/types | Frequency correct/types | Combined correct/types |
|---|---|---|---|
| Caesar | 11/15 | 6/15 | 10/15 |
| Jerome | 11/16 | 5/16 | 8/16 |
| Gellius | 13/15 | 7/15 | 12/15 |
| Livy | 9/14 | 6/14 | 7/14 |
| Apuleius | 8/13 | 8/13 | 9/13 |
| Curtius | 11/15 | 8/15 | 9/15 |
| Suetonius | 10/16 | 7/16 | 7/16 |

The combined arm improves only Apuleius, from8/13 to9/13, still a small supplied-candidate result. It worsens NLL relative to structural in six texts as well. All arms are retained and no favorable Apuleius exception is adopted. Source-modal references and candidate membership remain supplied, with prior segmentation/development caveats.

Frequency-only AUC is.3214 Caesar,.2500 Jerome,.5357 Gellius,.4167 Livy,.7750 Apuleius,.4911 Curtius and.4219 Suetonius. Its fitted source slope is positive, but several author rankings are reversed. Normalizing total text length does not change within-text ordering, so a count rescaling or cutoff adjustment cannot repair this ranking reversal. Frequency can enrich a broad union without providing a stable ADP-versus-CCONJ ordering.

All29 omission and seven focal-substitution variants were evaluated. Frequency-only hard decisions barely change; that stability accompanies poor accuracy, not reliable grammar. Combined results remain mixed under perturbation. The complete per-variant metrics are preserved rather than selecting a favorable subset.

Next proposed diagnostic: test **shared two-sided frames as grammatical relations** without learning a scalar class boundary. On the four fully annotated cached text sets, connect supported opaque word types that occur between the same left/right opaque neighbors. Freeze a primary requirement of at least two distinct shared frames, retain the one-frame comparison and coverage, and compare exact modal-POS agreement against fixed frequency-preserving word-shuffle controls. No word meanings, POS or candidate catalogue should select edges; labels are evaluation only. This asks whether local substitution relations offer high-precision grammatical constraints, even if they cannot assign named POS or recover nuclei. A sparse relation graph is acceptable only with explicit coverage and no claim of complete tagging.

Independent verification checked source/target normalization, all12 nested selections and retained-type splits, independently optimized/KKT-checked264 fits, replayed87 source OOF and11,544 target probabilities, and verified777 metric groups including every omission/perturbation. The focused suite passed18 tests. No new annotations, reserved material or sealed works were used. Artifacts and manifest: `experiments/results/grammar-restoration/iteration163/`.
