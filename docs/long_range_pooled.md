# Bounded pooled-lag calibration

This seven-stage follow-up tests whether pooling distant-context counts increases the separation margin for weak synthetic dependencies. Model selection uses calibration training data only; final scoring uses three untouched seeds. It remains a synthetic calibration, not a manuscript or historical-language experiment.

## Frozen method

Reuse the preceding sparse generator: 26 letters, uneven emissions, variable three/four-letter words, two artificial 16-word lines per block, and lag contexts confined to a line. Training has 32 blocks (1,024 words, 512 eligible initial-letter events); evaluation has 89 blocks (2,848 words, 1,424 eligible events). Seven generator types are independent, local-only, strong lag 4, strong lag 8, weak lag 4, shared-state independent and shared-state local.

The original position/length/immediate-final baseline remains fixed with backoff strength 20 and pseudocount 0.5 per letter. For each lag, the new estimator first pools target counts by `(lag, distant final letter)` across positions, lengths and immediate contexts, backing off to the current baseline distribution. Fine `(lag, position/length, immediate final, distant final)` counts then back off to that pooled distribution. Blend this extension with the baseline. Average the seven lag probability distributions; never select the strongest lag.

Six predeclared candidates combine pooled/fine strength 10, 50 or 200 with extension weight 0.25 or 0.75. On each of two calibration seeds (38001, 38002), split the 32 **training** blocks into first 16 fit and next 16 validation. Choose the candidate with the lowest mean mixture log loss, equally weighting all seven generator types and both seeds. Selection knows the balanced synthetic control suite; this is not unsupervised calibration on manuscript data. No calibration held-out split or final evaluation enters selection.

Final seeds 38011, 38012, 38013 were not used in calibration or earlier loops. Both the pooled estimator and the frozen old estimator are fitted on the same new training fixtures and scored on the same evaluation fixtures. Each receives three refitted conditional feature controls. These permute distant features within position/length/immediate groups while leaving targets and baseline features unchanged. They are feature controls, not coherent reordered texts or a claimed permutation significance test.

## Seven stages

1. Freeze the six candidates, generator suite, calibration/evaluation/null seeds and criterion.
2. Select smoothing/weight using only internal training splits.
3. Evaluate all seven types on seed 38011.
4. Replicate on seed 38012.
5. Replicate on seed 38013.
6. Score three matched refitted controls for each estimator/fixture.
7. Assess the predeclared descriptive criterion: minimum weak planted excess exceeds the maximum independent/local/shared-state control excess. If it fails, close this weak-effect branch at the current budget.

All stage plans precede scoring and link preparation/preceding-result digests. There is no post-evaluation estimator tuning. Selection chose **strength 10, extension weight 0.75**. Final records contain 21 fixtures, 168 estimator evaluations including nulls, and 84 calibration candidate evaluations.

## Results

Matched-null excess in bits per eligible initial-letter event, ranges across three evaluation seeds:

| Generator | Pooled estimator | Frozen old estimator |
|---|---:|---:|
| Independent | −0.011672 to 0.024777 | −0.001327 to 0.001848 |
| Local only | −0.001603 to 0.002152 | −0.002504 to 0.003051 |
| Strong lag 4 | 0.437180 to 0.485658 | 0.039946 to 0.045970 |
| Strong lag 8 | 0.439333 to 0.477093 | 0.032808 to 0.044713 |
| Weak lag 4 | 0.086489 to 0.128345 | 0.006398 to 0.010319 |
| Shared-state independent | 0.005580 to 0.022831 | −0.000246 to 0.000869 |
| Shared-state local | −0.012036 to 0.007466 | −0.001244 to 0.000213 |

The predeclared descriptive criterion passes: minimum pooled weak excess 0.086489 exceeds maximum control excess 0.024777. Pooling substantially increases the effect and the separation margin, while also increasing control variability and residual gains in shared-state independent cases.

**The old estimator also separates weak positives on these particular new seeds.** Its minimum weak excess 0.006398 exceeds its largest control excess 0.003051. Therefore the new run does not prove that pooling alone fixed the earlier overlap. Earlier seeds showed the old method's weak-effect overlap; three successful new seeds do not invalidate that limitation. The paired comparison supports a larger margin on these fixtures, not a reliable false-positive rate or statistical power estimate.

No decision threshold or classifier was fitted, and numerical separation is not proof that real texts have direct distant-copy operations. Shared state, vocabulary constraints, topic and layout can create other distant associations. The generator family and copy rule are unchanged from calibration; final seeds are independent streams, not independent mechanism families.

## Verification and reproduction

Two focused tests check normalized baseline/per-lag/mixture distributions under unseen contexts and uniform predictions without training information. Independent validation reconstructs hierarchical and original probabilities, including all calibration candidates; checks selection arithmetic, line-reset features, null conditional inventories, identical baseline losses, plan chains and grouped contrasts. Raw synthetic generation is reused.

```sh
.venv/bin/python -m benchmarks.long_range_pooled --run
.venv/bin/python -m benchmarks.long_range_pooled_validation
.venv/bin/python -m pytest -q tests/integration/test_long_range_pooled.py
```

Records: `experiments/results/long-range-pooled/`. Prepared records hash the new estimator and reused generator/null code; further experiments require a separate module/output directory.

## Assessment and next priority

The bounded estimator attempt passed its descriptive criterion, so the weak-effect branch need not be closed for lack of sensitivity. Stop estimator tuning here. The next check should change the **control family**, not smoothing: mapped rather than identity-copy positives, and stronger persistent shared-state/template negatives, all scored with the frozen selected estimator. This tests whether the improved margin survives a new mechanism family and stronger confounding. It should precede manuscript scoring. Failure should be documented as a specificity limit rather than trigger more local tuning.

Verification passed: both focused tests and 2,346,624 independently reconstructed probability/loss checks, including calibration and final paired/null scores. Training-only selection, feature construction, control invariants and final criterion all passed the audit.
