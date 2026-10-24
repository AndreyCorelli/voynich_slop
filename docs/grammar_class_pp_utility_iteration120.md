# Iteration 120: inferred opaque classes have structural value, but miss primary precision guard

**Preserve this downstream finding:** with every target word identity hidden, inferred classes increase correctly selected PP-governed nodes from23 to235. On the fixed originally unmapped-token cohort, correct selections increase11→174. This demonstrates conditional structural utility beyond class-label accuracy. **The predeclared primary gate nevertheless fails:** all-token precision is87.36%, below90%; unmapped-token precision is84.06%. No default algorithm changes.

## Frozen experiment

The input is exactly118's770 source-test sentences/9956 tokens. The16 target types' names are removed in every condition, including the oracle. Their opaque IDs and positions remain; all other supplied anchors remain unchanged. The predicted classes come directly from118's frozen116 class model and117 balanced scalar calibration, with no new fitting or confidence cutoff. This experiment supplies hard class tags, so the existing PP model treats inferred tags as one-hot class information.

The comparison includes unknown target classes, predicted classes, supplied modal classes as a privileged oracle, all-ADP and all-CCONJ controls, and three deterministic type-class shuffles. Shuffles preserve class counts over types, not class counts over occurrences. All public inputs and assignments are frozen before inference; all PP scores are frozen before evaluation. PP labels are reused from existing85 predictions at identical sentence/token positions; no new annotations are consumed.

The primary model is frozen85 at.80. Secondary settings are its pre-existing source-F1 cutoff.55, and frozen89 augmentation at.71/.80. None is selected from these outcomes. The primary utility gate requires increased TP and F1, at least90% precision, and F1 above the mean three shuffles. Results are descriptive development comparisons on previously used source-test text, not independent confirmation or a guarantee for an arbitrary cipher.

## Primary: original PP model at.80, all9956 positions

| Target class input, identities always hidden | Correct selections | False selections | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Unknown |23|0|100%|2.96%|.0575|
| **Predicted** |**235**|**34**|**87.36%**|**30.24%**|**.4493**|
| Supplied-class oracle |255|16|94.10%|32.82%|.4866|
| All ADP |256|198|56.39%|32.95%|.4159|
| All CCONJ |26|0|100%|3.35%|.0648|
| Shuffle0 |93|27|77.50%|11.97%|.2074|
| Shuffle1 |159|98|61.87%|20.46%|.3075|
| Shuffle2 |56|163|25.57%|7.21%|.1124|

Predicted classes add212 correct selections and34 false selections, losing none of the23 baseline true positives. Their F1 exceeds each shuffle and the all-ADP control, but the90% precision requirement fails. Compared with guessing all targets as ADP, learned classes remove164 false selections at a cost of21 true selections. This is evidence that class discrimination matters, not merely that adding preposition tags increases coverage.

## Fixed cohorts prevent a visibility-composition illusion

Giving an opaque token an inferred tag changes the old model's `visible` flag. No evaluation cohort is defined by that changing flag. Cohorts are fixed from the original input:6629 originally unmapped positions (defined without a POS filter),1143 target positions,2184 other given-anchor positions.

| Fixed cohort, original.80 | Unknown correct / wrong | Predicted correct / wrong | Oracle correct / wrong |
|---|---:|---:|---:|
| Originally unmapped tokens |11 /0|174 /33|190 /15|
| Other given anchors |12 /0|61 /1|65 /1|
| Target16 positions |0 /0|0 /0|0 /0|

The main unmapped-token gain is163 newly correct PP memberships and33 new false positives. It is not a recount of the target function words whose classes were just supplied. The reference marks coarse governed-node membership; it is not an exact PP boundary, governing predicate, Case, or dependency reconstruction. Several other anchor identities/classes are still supplied, and the downstream PP model was trained with target types in plaintext source data; lexical target identities are absent at inference.

## All predeclared secondary settings

| Model / cutoff | Unknown correct / wrong | Predicted correct / wrong | Oracle correct / wrong | Predicted precision |
|---|---:|---:|---:|---:|
| Original.55 |44 /5|474 /128|501 /90|78.74%|
| Augmented.71 |38 /1|310 /58|332 /34|84.24%|
| Augmented.80 |15 /0|86 /9|96 /5|90.53%|

The augmented.80 subset adds71 correct selections and nine false selections at observed90.53% all-token precision. This frozen secondary finding is preserved, but it does not replace the failed primary gate or establish a precision guarantee. Its originally unmapped-token subset is27 correct/six wrong (81.82% precision); the overall90.53% must not be presented as90% precision on originally unmapped tokens.

The remaining primary oracle gap is20 fewer true positives and18 extra false positives under predicted versus supplied classes. The classifier's four source-test type errors (`c`, `per`, `sine`, `uel`) are candidates for explaining this gap, but the downstream contribution of each has not yet been attributed. Correcting those tags with reference labels would be an oracle diagnostic, not an available restoration method.

Next: perform a source-only factorial oracle attribution over those four mistaken classes, with identities still hidden, to find which errors drive PP false positives and which suppress correct memberships. Evaluate every subset of class corrections; do not add a word-specific correction rule or tune on authors. Preserve the demonstrated class/structural gains even if no practical precision fix follows.

No lexical nucleus, full grammatical restoration, repair robustness, or default adoption is claimed. Verification:31 focused tests pass. The audit verifies34 frozen input hashes, recomputes all16 PP score vectors, independently checks128 fixed-cohort confusion/transition results, and confirms that poisoned private PP labels and poisoned target identity fields do not affect inference. Artifacts are in `experiments/results/grammar-restoration/iteration120/`.
