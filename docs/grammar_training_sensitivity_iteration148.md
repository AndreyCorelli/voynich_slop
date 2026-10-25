# Iteration 148: the joint boundary depends strongly on one conjunction exemplar

The positive full-text result is real under exact replay, but the supervised boundary is fragile. Removing siue, one of only three conjunction training types, reverses the role-similarity coefficient and sharply reduces accuracy in six texts. This identifies training-exemplar dependence as a concrete limitation, rather than a new deciphering result.

Before fitting, the design fixed all13 leave-one-training-type-out omissions. Each refit retained the original two scalar features, class-balanced regularized fitting and raw0.5 cutoff, with standardization recomputed on retained types. No offsets, new labels, annotations, contexts, reserved material or sealed works were used. The frozen source feature cache and seven full-text target feature caches were reused. All models were frozen before predictions and predictions before evaluation. No omission was selected as an improved replacement.

| Text | Full model | Range after an ADP omission (10 models) | Omit an | Omit siue | Omit ue |
|---|---|---|---|---|---|
| Caesar | 12/15 | 12/15–12/15 | 10/15 | 9/15 | 12/15 |
| Jerome | 12/16 | 11/16–12/16 | 11/16 | 7/16 | 11/16 |
| Gellius | 12/15 | 11/15–13/15 | 12/15 | 4/15 | 13/15 |
| Livy | 10/14 | 9/14–10/14 | 9/14 | 5/14 | 11/14 |
| Apuleius | 6/13 | 7/13–9/13 | 7/13 | 6/13 | 9/13 |
| Curtius | 12/15 | 10/15–12/15 | 11/15 | 5/15 | 12/15 |
| Suetonius | 12/16 | 11/16–12/16 | 11/16 | 6/16 | 11/16 |

Ranges summarize all predeclared ADP omissions, not a deployable choice. Full per-omission metrics, paired correct-to-wrong and wrong-to-correct flips, and mean/max absolute probability changes are retained. A net accuracy change can conceal many flips: omitting siue changes64 of104 supplied candidate decisions across the seven texts, whereas omitting an changes29 and omitting ue changes19. These104 cases are correlated type/text observations, not independent replications.

In original feature units, the logit coefficients are:

| Omission | Corrected adjacent overlap | Role similarity | Intercept |
|---|---|---|---|
| None | 5.6301 | 3.0891 | .2020 |
| an | 2.1950 | 4.2930 | −.5064 |
| siue | 1.5854 | −14.2193 | 1.1137 |
| ue | 55.5849 | 54.3066 | −.4590 |

The siue omission reverses the role coefficient. The ue omission produces extreme coefficients and poor NLL even where hard accuracy looks good (Caesar remains12/15 while NLL worsens from.4731 to1.4520). Inspecting accuracy alone would miss this probability instability. Source siue has six occurrences, an21, ue10; the class-balanced objective gives each conjunction considerable influence. This experiment shows dependence on an exemplar, but does not yet establish that any individual occurrence is responsible or that its annotation is wrong.

The milestone therefore remains: the full model classifies71–80% of supplied candidate types in six of seven full texts. It remains development evidence for a narrow grammatical signal, not robust general token POS tagging, certified confidence or exact lexical recovery. The current experiment does not justify deleting troublesome types or promoting favorable per-author omissions.

Next proposed check: source-only occurrence sensitivity for siue. Freeze its six source positions and, for each occurrence, remove the containing source sentence, recompute both scalar features and refit the original13-type model. Compare feature/parameter changes and all seven target predictions against the unchanged full model. This distinguishes a single-context accident from dependence on the conjunction type as a whole, without acquiring annotations or treating agreement as a validated confidence gate.

Verification independently checked retained-type membership/standardization, retrained all13 omission models, replayed logits with a separate linear calculation, and recomputed accuracy/NLL/AUC and paired changes. Both prior manifests were verified and all seven full baselines matched exactly. The focused suite passed18 tests. Frozen artifacts and verification manifest: `experiments/results/grammar-restoration/iteration148/`.
