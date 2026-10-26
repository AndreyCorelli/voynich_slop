# Iteration215: supported-center neglect is already present in source fits

All four frozen applicability variants retain only10/39 supported **source evaluation instances** at.5. The same13 centers are each evaluated by three models that trained on their author;39 is not an independent sample size. Held-out retention is2/13 or3/13. Thus author transfer is not the sole explanation: the present source objective/features/regularization already fail to retain the relevant subpopulation in-sample. This does not isolate which of those modeling choices is responsible.

## Frozen diagnostic

Apply all16 iteration214 models to all four authors, retaining explicit three-source/one-held-out roles per model. Freeze all64 score vectors before metric aggregation. Report each author separately: applicability classification, supported retained/rejected opaque IDs, supported probability range/mean and fixed.5 retention. No fits, threshold changes, features, raw text, new annotations or reserve use. All held-out predictions, applicability metrics and retained lists must exactly reproduce214.

| Variant | Source supported instances retained | Held-out supported centers retained |
|---|---:|---:|
| full12 |10/39 (25.64%)|3/13 (23.08%)|
| no frequency |10/39 (25.64%)|2/13 (15.38%)|
| no reuse |10/39 (25.64%)|3/13 (23.08%)|
| neither |10/39 (25.64%)|2/13 (15.38%)|

There are12 source-author evaluations and4 held-out evaluations per variant. Source instance totals count repeated centers in overlapping training folds. The percentages are descriptive, not independent estimates or a significance test; similar rates do not prove that transfer has no effect.

## Author breakdown

| Author | Source supported instances | Full12 retained in source fits | Other three variants, each | Full12 held-out retained |
|---|---:|---:|---:|---:|
| Aquinas |21|7|6|0/7|
| Caesar |0|0|0|0/0|
| Cicero |9|1|2|0/3|
| Jerome |9|2|2|3/3|

Jerome's full12 source retention2/9 versus held-out3/3 also shows that inclusion of an author in training does not guarantee supported-center retention in this balanced pooled objective. Caesar has no supported examples, so its retention fraction is undefined. All source applicability confusion/calibration/NLL/AUC values and individual supported probability ranges remain in the detailed artifact; source metrics are explicitly in-sample, not evidence of generalization.

The binary applicability objective is trained on recognized Case existence, while the downstream desired examples are the much smaller conditional-support subset. Broad applicability fit can sacrifice that subset even when it is in training. The observed source failure warrants testing that objective mismatch before blaming author transfer alone. It does not establish that anonymous features can reliably identify supported centers, recover named cases/POS, or identify exact Latin nuclei.

## Audit and next step

Independent scalar logits/sigmoids reproduce4880 predictions; all64 role/metric groups, summary counts, supported identities, exact214 held-out baselines and23 hashes pass. Artifacts: `experiments/results/grammar-restoration/iteration215/`.

Next test one source-only relevance-balanced applicability loss against the unchanged211 full12 baseline. Within each training author, give equal mass to each nonempty group: supported Case-bearing, other Case-bearing, and no recognized Case; then give authors equal total mass. Supported labels enter only source weighting, never target features or target selection. Keep features, ridge, scaling policy and fixed.5 gates/product/top3/top5 unchanged, report source and target supported retention separately, and evaluate applicability costs. This is a deliberately changed objective and probability prior, not a calibrated confidence upgrade. No author-specific selection or target threshold tuning follows; source repair without target yield is still insufficient.
