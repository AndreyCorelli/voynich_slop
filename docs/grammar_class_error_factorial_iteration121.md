# Iteration 121: false ADP assignments drive the precision gap

**Preserve the diagnosis:** the two false ADP assignments (`c`, `uel`) drive excess PP false positives; the two missed ADP assignments (`per`, `sine`) mainly suppress correct memberships. This distinction holds across every background combination in the primary factorial. It motivates asymmetric caution before asserting ADP, not a word-specific correction rule.

## Oracle diagnostic, not a new restoration method

The four errors are derived from the disagreement between120's predicted and supplied modal classes, not selected from PP outcomes. All16 subsets of correcting them are evaluated. Every target lexical identity stays hidden, and corrections are global/type-consistent. All other inputs,9956 token positions, fixed evaluation cohorts, PP models, and thresholds are identical to120. The zero-correction and full-correction cases reproduce120's predicted and oracle scores exactly.

Assignments are frozen before new inference and all scores before metrics. Both frozen PP models and all four existing settings are retained. No author data, new annotations, reserve features, sealed lexical data, model fitting, or threshold selection is used. The labels that authorize these corrections are privileged reference information; **none of the corrected conditions is a deployable improvement**.

## Primary original PP model at.80

| Classes corrected using the reference | Correct PP selections | False selections | Precision |
|---|---:|---:|---:|
| None:120 predicted classes |235|34|87.36%|
| c only |236|22|91.47%|
| per only |245|35|87.50%|
| sine only |243|34|87.73%|
| uel only |235|27|89.69%|
| c + uel |236|15|94.02%|
| All four |255|16|94.10%|

The false-positive effects are exactly additive across all eight backgrounds for each correction: `c` removes12, `uel` removes7, `per` adds1, and `sine` changes none. The two false ADPs thus account for19 removable false positives; correctly restoring `per` introduces one additional PP-model false positive, giving the net18-FP oracle gap.

True-positive effects are almost additive: `c` adds one, `sine` adds eight, `per` adds10–11, and `uel` adds0–1, depending on whether the other is corrected. The only primary count interaction is one additional correct membership when `per` and `uel` are both corrected.

Exact contributions averaged over all24 correction orders allocate the net20 recovered true positives as:

| Correction | Allocated net TP gain | Allocated FP reduction |
|---|---:|---:|
| c |1|12|
| per |10.5|−1|
| sine |8|0|
| uel |.5|7|

These fractional values allocate a fixed factorial's interactions; they are not fractional restored words or general causal importances. Full correction gives21 newly correct selections, one lost correct selection,19 removed false positives, and one new false positive. Those gross losses remain counted despite the net improvement.

## Do not confuse overall precision with unmapped-token precision

On the fixed originally unmapped-token cohort:

| Oracle correction | Correct / false selections | Precision |
|---|---:|---:|
| None |174 /33|84.06%|
| c |175 /21|89.29%|
| uel |174 /26|87.00%|
| c + uel |175 /14|92.59%|
| All four |190 /15|92.68%|

Correcting `c` alone crosses90% overall, but not on originally unmapped tokens. Within these16 oracle subsets, unmapped-token precision crosses90% only when both `c` and `uel` are corrected. For overall precision, `c` is sufficient but not necessary: `sine+uel` also reaches90% by recovering true positives. This is a diagnostic description, not a choice of a deployable subset.

The conservative augmented.80 model shows the same qualitative separation: its four-FP oracle gap is allocated two each to `c` and `uel`; its ten-TP gap is allocated five to `per`, four to `sine`, and one to `uel`. All other predeclared settings and cohorts are preserved in the artifacts.

## Next practical test

Test an identity-free, asymmetric confidence gate before injecting an inferred ADP tag. A low-confidence proposed ADP would stay `X` (unknown), rather than being forced to CCONJ. Keep the existing CCONJ assignments initially. Select the confidence threshold using cached source-calibration PP labels only, with frozen precision/coverage requirements, then evaluate on the reused source-test text before considering authors.

This tests whether generic uncertainty can avoid false government while retaining useful structure. The current oracle results do not show that such a gate will work: leaving a class unknown is not equivalent to supplying its correct class, and class-score ranking overlaps remain. No `c`/`uel` blacklist or reference-class lookup is justified. The earlier class-transfer and downstream structural-utility findings remain preserved; no new nuclei or default algorithm change is claimed here.

Verification:31 focused tests pass. The audit verifies49 input hashes, recomputes all32 PP score vectors, checks256 fixed-cohort confusion/transition results, and verifies60 defined attribution vectors independently over all24 correction orders. Four undefined target-cohort precision allocations are excluded from interpretation. All16 interventions and both120 cache endpoints are verified. Artifacts are in `experiments/results/grammar-restoration/iteration121/`.
