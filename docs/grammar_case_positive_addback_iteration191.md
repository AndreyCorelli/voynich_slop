# Iteration 191 — specific positive source examples help beyond class mass

**Diagnostic result:** individually restoring omitted positive source examples improves99/159 trials, worsens7 and leaves53 unchanged while class totals, scales and acceptance masks stay fixed. This supports missing source-example information as a real limitation beyond190's class-mass effect. It is not a selected rescue policy: target outcomes must not choose which omitted source example to restore.

## Frozen addbacks

Use all21 historical weak188 masks frozen by189, including masks improved in190. For each, copy its190 baseline and restore **every omitted positive source example separately**. Use only existing source labels; no new target annotations or target labels enter fitting. Retain original class mass18/52positive and34/52negative, full-source180 scales/features/ridge, rich19/control3 columns, optimizer and cutoff rules.

Keep each mask's base188 acceptance indices fixed for none/all-coordinate/entropy policies. Adding an example changes training information but not source class contribution totals or screened target coverage. Freeze all180 trials (21 baselines plus159 addbacks), models, predictions and selections before scoring. Cache identical training sets but retain every trial and regression;142 distinct training sets are evaluated.

Primary diagnostic: distribution of changes in rich entropy-refilled top10 applicability versus each190 baseline. Per-mask maxima are an **oracle over source addbacks using target outcomes**, not a deployable model-selection method or restored knowledge. All policies, models, probability metrics and threshold/top10/top20 lists are retained.

## Individual-trial results

| Rich entropy-refill applicability change | Addback trials |
|---|---:|
| +3 applicable pairs | 3 |
| +2 | 19 |
| +1 | 77 |
| Unchanged | 53 |
| −1 | 7 |

These159 trials share17 distinct base training masks and the same target, so they are not159 independent confirmations. Some added source evidence hurts the selected list; the experiment does not establish monotonic benefit from adding data.

### Oracle best result per historical weak mask

| Best applicability among that mask's individual addbacks | Masks |
|---|---:|
| 9/10 | 15 |
| 8/10 | 5 |
| 7/10 | 1 |

Twenty of21 masks can reach at least8/10 with **some** single source-positive addback, but choosing that example requires observed target outcomes in this analysis. No such oracle selection is adopted. The worst mask `omit1160` starts4/10 and reaches only5–7/10 across its ten individual restorations; all help, none reaches8/10. One example alone cannot fill that remaining evidence gap.

Source example40 improves20/21 relevant trials, ties one and harms none, with gains up to3 pairs. Other examples are mixed, including example5 (8 improvements,4 regressions) and41 (15 improvements,2 regressions). These IDs are existing source rows, not recovered word identities or proposals to select a target-favorable training subset.

## Shared source-neighborhood dependency

All21 historical weak masks share the same omitted opaque source endpoint. It has nine incident source training pairs: seven positive rows0,5,7,32,40,41,42 and two negative rows34,39. Thus one source word accounts for **7/18 (38.89%) positive training examples**; deleting it removes a correlated neighborhood rather than a representative random sample. The second endpoint deletion can remove additional positives.

This explains why a low-positive-count association appeared189, while fixed class proportions190 did not resolve the ranking limitation. Individual restorations retain the class mass but partly restore feature-context coverage. The experiment does not isolate a unique linguistic cause or prove that this endpoint's identity is intrinsically special; identity itself is not a model feature.

## Implication and next direction

The source-trained applicability interface remains promising on its original transfer, but a52-pair source set with18 correlated positives is too narrow to claim robust broad grammatical recovery. Selecting rescues by target performance would conceal that limitation. No addback, training weight, cutoff or model variant is adopted here.

Next broaden **source training examples only** from the existing two-shared-frame pairs to all existing floor-five pairs sharing at least one frame, using the same cached source annotations. Keep the target primary two-frame graph,19 anonymous features, query-frame exclusion, ridge/model settings and target metrics fixed; include frequency/support and source-prior controls and the old small-source baseline. Freeze the complete protocol before scoring, and challenge the same source-hub omission. This tests richer source-example coverage without new annotations or target-based candidate expansion; the broader source graph's case agreement need not itself be strong, because the supervised target is applicability rather than case equality.

Same-author reused development data and vocabulary overlap remain. No new-author/Voynich validation, named cases, general POS tags, syntactic links or lexical nuclei are established. Preserve the evidence for a useful supervised grammatical interface while treating source-label diversity as the next bottleneck.

## Verification

Independent inventory replay checked all21 historical masks and159 eligible positive addbacks. Separate weighted Newton solutions verified284 model fits over142 distinct training sets, fixed class masses/scales/base masks, all target probabilities and5,400 selection metric groups. Exact190 baseline models/predictions/summaries, every per-mask/per-example effect and the common omitted endpoint's positive/negative incidence passed. Frozen input/trial/model/prediction/selection hashes passed. The broader test suite was not rerun for this reference-only diagnostic; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_positive_addback_iteration191.py`; reviewer: `benchmarks/grammar_case_positive_addback_iteration191_review.py`. Frozen design, complete trial inventory/models/predictions/selections/summaries, effects, per-mask/per-example results, audit and verification manifest: `experiments/results/grammar-restoration/iteration191/`.
