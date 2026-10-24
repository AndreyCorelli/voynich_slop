# Training-only joint-generator calibration

This bounded follow-up tests the original character predictor rather than substituting the direct mapped-boundary statistic. It uses the same four historical excerpts as the previous ordering checks. Their held-out words were previously inspected for direct statistics; they are held out from calibration, not newly collected independent fixtures.

## Frozen protocol and seven stages

1. Freeze the selected original predictor, four mixture rates, three evaluation keys, three null seeds, and source excerpts.
2. Calibrate separately per source using only its 32 training blocks: first 16 fit the mapping and predictor; next 16 measure prediction. Compare original prose with mixtures of beam avoidance and joint beam optimization. Rates are 0, 0.125, 0.5 and 1. Choose the rate whose matched-null excess is nearest prose, breaking ties toward the lower rate. One preset key and one refitted null are used for calibration.
3. Evaluate German 113.
4. Evaluate German 133.
5. Evaluate German 253.
6. Evaluate Italian.
7. Assess the fixed rates across all sources and stop local-feature tuning.

After rate selection, refit the mapping and predictor on all 32 training blocks and evaluate the separate 89 held-out blocks. Each generator receives exact per-block position-bin/length word inventories and public layout. A preset random stream chooses between complete beam-avoid and beam-joint blocks at the selected rate. Beam width is 16, with repeat minimization preceding mapped-match maximization. It is not an optimum proof or a historically reconstructed generator.

All arms use common reversible encoding with the same seed-specific key and 1/16 prefix schedule. Each active train/evaluation pair has three independently shuffled counterparts, with predictor models refitted on shuffled training. Shuffles preserve folio/position-bin/length word inventories. Primary predictive result is folio-equal gain over the position baseline, minus the mean matched-null gain, in bits per character. Companion repeat suppression is block-equal frequency-adjusted encoded adjacency, in fractions. The two units differ.

Plans are saved before scoring and linked by digests. No evaluation rate selection or predictor selection occurs.

## Calibration

Every source selected rate 0.5. Calibration excess values are non-monotonic across rates in some sources; this is a small internal split with one key/null, not a smooth response curve or a power estimate. The fixed coarse grid deliberately bounds tuning.

## Limitations and next direction

These checks address the specificity of local summary features. Similar gains and repeat suppression cannot identify encryption, generation, or a source language. Generator access to evaluation inventories makes the comparison an adversarial ordering test, not prediction of unseen lexical content. Three keys do not constitute three independent prose samples. German 133 retains four unresolved `k` and two `x` prayer-notation tokens in evaluation. Cached source parsing is reused.

Stop tuning these local features. Next, predeclare a longer-range prediction: whether context at distances 2–8 adds held-out predictive value beyond position and the immediate predecessor. Calibrate it first on positive controls with planted non-adjacent dependencies and local-only negative controls, using matched refitted nulls. Only proceed to manuscript interpretation if those controls are distinguishable. Longer-range dependence itself still would not prove a historical mechanism.

## Reproduce

```sh
.venv/bin/python -m benchmarks.joint_predictor_calibration --run
.venv/bin/python -m benchmarks.joint_predictor_validation
.venv/bin/python -m pytest -q tests/integration/test_joint_predictor_calibration.py
```

Records are in `experiments/results/joint-predictor-calibration/`. The prepared file hashes benchmark code; further variants require a new module/output directory.

## Held-out results

Means over three preset keys/ordering streams. Excess is bits per character; repeat adjustment is a fraction.

| Source | Prose predictive excess | Generator predictive excess | Prose repeat adjustment | Generator repeat adjustment |
|---|---:|---:|---:|---:|
| German 113 | 0.007599 | 0.006963 | −0.006214 | −0.006563 |
| German 133 | 0.006154 | 0.005644 | −0.006048 | −0.006812 |
| German 253 | 0.003231 | 0.005239 | −0.007571 | −0.007507 |
| Italian | 0.007198 | 0.006552 | −0.002831 | −0.002775 |

The calibrated generator is within approximately 8–9% of prose's mean predictive excess in German 113, German 133 and Italian. It exceeds German 253 by approximately 62%; training calibration does not reliably guarantee magnitude matching. All twelve generated evaluations have positive matched-null predictive excess and negative repeat adjustment. The two features can therefore coexist at comparable scales under deliberately constrained generation, with material source-specific differences. No equivalence threshold or classifier was fitted, so this is neither statistical equivalence nor universal indistinguishability.

This closes the narrow sign-and-scale concern sufficiently to stop local-feature tuning. It does not establish that the manuscript was generated, encrypted, or written in any of these languages.

Verification passed: two focused tests, 546,816 independently reconstructed held-out word/model scores, and 92,928 decoded training/evaluation words. The audit checks active and position-baseline likelihoods for all 96 evaluation/null cases, exact payload inventories, calibration/evaluation source-slot separation, selected-rate arithmetic, plan digests and grouped summaries. Calibration likelihoods were not independently reconstructed; the raw parser and beam optimizer are reused.
