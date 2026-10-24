# Weak boundary-dependence calibration

Seven plan → test → assessment iterations tested whether the frozen character predictor detects weak injected order dependence while preserving manuscript word inventories and lengths. **This loop did not establish reliable detection at the manuscript effect size.** It establishes exact matching controls and a small dose response, but the injection was too constrained: even the strongest tested setting produced gains below the prior manuscript's 0.00915 bits/character.

## Protocol

The prior second-order character/position/preceding-suffix predictor remains frozen; both it and its position-only baseline are refitted for each control. No model selection or Z3 calls occur. Each case reuses 1,024 training words and 2,848 evaluation words from the existing manuscript split.

Words are assigned without replacement from pools keyed by folio, four-bin line position and word length. Thus every case preserves exact per-folio word inventories, position-bin inventories, every slot's length, within-word spellings, novelty counts, layout, and split provenance. Only word order changes. The position-only model's folio scores are invariant, checked numerically.

At each eligible within-line transition, with preset probability 0, 0.25, 0.5 or 1, the generator favors remaining words whose first unit equals the preceding output word's final unit. If none are available, it chooses uniformly from the remaining pool. Cross-line/block-start slots receive uniform choices. This is a **final-to-initial equality** injection, not the full suffix-to-initial relationship learned from the manuscript.

Each dose has three fixed realizations, seeds 27001–27003. Train/evaluation stream seeds are separately derived with SHA-256 from seed and split name, correcting the earlier calibration's stream reuse. Doses share stream seeds to reduce unrelated setup variation, but different candidate pools cause different random trajectories. Injected attempt probability is not realized matching frequency. Rate 1 takes an available matching candidate at every eligible slot; it is a greedy procedure, not a globally maximal matching optimization.

All cases and the stage schedule are frozen before scoring. There is no result-based dose selection.

## Seven iterations

| Iteration | Test | Assessment → next step |
|---|---|---|
| 1 | Three zero-dose random reorderings | All overall gains negative. Test preset weak dose. |
| 2 | Dose 0.25, seed 27001 | Gain negative. Test middle dose. |
| 3 | Dose 0.5, seed 27001 | Approximately zero, slightly negative. Test rate 1. |
| 4 | Rate 1, seed 27001 | Small positive gain. Replicate weak dose. |
| 5 | Dose 0.25, seeds 27002/27003 | Both negative. Replicate middle dose. |
| 6 | Dose 0.5, seeds 27002/27003 | Both small positives. Replicate rate 1. |
| 7 | Rate 1, seeds 27002/27003 | One positive, one negative. Calibration remains inconclusive at manuscript effect size. |

Gains are folio-equal bits per EVA character over the position-only baseline, including end-of-word cost in loss. “Positive” means lower loss, without a significance threshold.

| Attempt probability | Gain seed 27001 | Gain seed 27002 | Gain seed 27003 | Mean | Positive runs |
|---|---:|---:|---:|---:|---:|
| 0 | −0.000966 | −0.000500 | −0.000067 | −0.000511 | 0/3 |
| 0.25 | −0.000626 | −0.000737 | −0.000397 | −0.000587 | 0/3 |
| 0.5 | −0.000074 | +0.000789 | +0.000390 | +0.000368 | 2/3 |
| 1 | +0.001132 | −0.000306 | +0.001620 | +0.000815 | 2/3 |

The prior manuscript gain is **+0.009152**, reused for scale comparison rather than new replication. Evaluation boundary equality rises from 3.4–3.7% at zero dose to only 6.7–7.7% at rate 1. Suitable initial/final equality matches are scarce within the fixed pools, and depletion limits later choices. The largest observed gain, +0.001620, is under one fifth of the manuscript gain.

## Assessment and next priority

The controls show that a small injected ordering change can improve prediction, but detection is unstable. Three realizations cannot estimate power or establish a false-positive rate. Preserving word inventories avoids the earlier strong control's spelling changes, yet this specific equality injection is a poor vehicle for reaching the target effect. It does not follow that the manuscript effect is meaningful encryption evidence, nor that the predictor cannot detect other weak relationships.

Next, audit which suffix-to-initial relationships account for the development signal, then construct controls with a **fixed mapping from common endings to common initials**, rather than requiring equal labels. Freeze that mapping using training data only, preserve the same inventory constraints and independent streams, and measure realized training/evaluation dependence before interpreting predictive gains. If those controls still cannot span the manuscript effect, change the calibration design rather than increasing solver timeouts or ranking historical mechanisms.

## Verification and reproduction

```sh
.venv/bin/python -m benchmarks.weak_boundary_calibration --run
.venv/bin/python -m benchmarks.weak_boundary_validation
.venv/bin/python -m pytest tests/integration/test_weak_boundary_calibration.py -q
```

Three tests pass. Independent probability reconstruction verifies **68,352 word/model scores** for the context and position-only models across all twelve cases. Validation also checks all seven plan/result chains, independent split seeds, exact folio/position/length/spelling inventories, layout, slot lengths, realized matching counts, aggregates and invariant position-baseline losses. Other stored gains are summarized from the shared frozen predictor but not separately reconstructed in this validator.

Artifacts: `experiments/results/weak-boundary-calibration/{prepared,plan-1…7,iteration-1…7,validation}.json`. Prior modules and results remain unchanged. This is a synthetic calibration on reused manuscript material, not a new manuscript hypothesis fit or fresh-text test.
