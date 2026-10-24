# Iteration 122: source-calibrated ADP confidence gate makes no test improvement

**Reject this as a demonstrated improvement.** Source calibration already meets the90% PP precision requirement without abstention, so the maximum-coverage selector keeps every proposed ADP. The frozen cutoff also keeps every test ADP, reproducing120's235 correct/34 false selections (87.36% precision). No default changes, and no author PP evaluation follows the failed test guard.

## Frozen practical rule

The class model and balanced scalar calibration remain116/117, with all target identities hidden. A predicted CCONJ remains CCONJ. A proposed ADP is injected only when its confidence `1−P(CCONJ)` reaches a global threshold; otherwise it stays `X` (unknown), never being forced to CCONJ. There are no word-specific rules or reference-class corrections.

The threshold is calibrated only on829 source-calibration sentences and the existing85 cached PP labels. The model does not consume new grammar annotations. Fit/test/reserve IDs are excluded before projecting cached calibration words. The cutoff grid contains zero, one, and all attained proposed-ADP confidences. Identical assignment states reuse inference, but every cutoff is reported.

Selection uses frozen85 PP inference at.80: at least90% precision and at least80% of ungated true positives. Among qualifiers, maximize TP, then minimize FP, then choose the largest tied confidence cutoff. All policy files are frozen before loading test inputs or probabilities. Test PP settings and fixed cohorts remain exactly120. Source-test text was already inspected in120/121, so this is developmental revalidation, not independent confirmation.

## Calibration selects no effective abstention

| ADP confidence cutoff | Accepted ADP types | Correct PP selections | False selections | Precision | Qualifies |
|---|---:|---:|---:|---:|---|
| 0, ungated |7|281|19|93.67%|Yes|
| **.512218, selected** |7|281|19|93.67%|Yes|
| .536092 |6|271|18|93.77%|Yes|
| .543131 |5|269|12|95.73%|Yes|
| .546790 |4|159|7|95.78%|No: coverage|
| .562250 |3|120|6|95.24%|No: coverage|
| .583816 |2|114|6|95.00%|No: coverage|
| .610269 |1|94|4|95.92%|No: coverage|
| 1 |0|35|1|97.22%|No: coverage|

The selected cutoff is the weakest accepted ADP's confidence, so its assignments equal the ungated assignments. Calibration originally unmapped-token precision is also91.59% (196 correct/18 false), so this is not merely an overall result dominated by given-anchor positions.

The more conservative qualifying.543131 setting sacrifices12 true positives to remove seven false positives. It is not chosen by the declared maximum-coverage objective. Its apparent calibration quality is not evidence that it would transfer; no alternative is selected using test outcomes.

## Test: exact120 input and scores

The lowest test ADP confidence is about.5311, above the selected.512218 cutoff. No type is withheld, and both original and augmented PP score vectors equal120's ungated vectors. The primary all-token result remains235/34, precision87.36%, with100% retention of ungated TP but failure of the90% precision requirement. The unmapped-token result remains174/33, precision84.06%. All secondary settings and gross changes likewise remain unchanged.

A post-hoc reference check explains the mismatch in error patterns. Calibration class errors are `a`, `ac`, `sine`; only `ac` is falsely asserted ADP (confidence.5361). Test errors are `c`, `per`, `sine`, `uel`; `c` and `uel` are the false ADPs, with confidences.5472 and.5548. Both exceed the learned cutoff. This check is explanatory only and never changes the policy.

The source-calibration precision constraint is already satisfied, so the selector has no reason to sacrifice coverage there. Its resulting threshold does not protect against the different test class errors. This does not establish that every ADP-abstention threshold is useless, nor that adopting an arbitrarily stricter cutoff is justified.

## Next diagnostic

Check whether **any** global ADP-confidence cutoff could satisfy90% PP precision and80% TP retention on this fixed test input. Enumerate it only as an explicitly privileged, test-label oracle ceiling; never deploy the winning cutoff or tune authors with it. If no setting works, the current confidence score cannot support this gate. If a setting does work, the next issue is source calibration that exposes the relevant failure patterns rather than another target-picked threshold.

The previous positive class-transfer and structural-utility findings remain preserved. This iteration adds no grammatical recovery, lexical nucleus, new annotation, reserve feature, or default-policy change. Verification:33 focused tests pass. The audit verifies39 input hashes, recomputes16 class profiles and ten PP score vectors, replays nine cutoffs, independently checks50 confusion/transition results, and verifies that selected test inputs/scores exactly reproduce120. Artifacts are in `experiments/results/grammar-restoration/iteration122/`.
