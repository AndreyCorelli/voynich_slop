# Training-mapped boundary calibration

Seven plan → test → assessment iterations provide an initial sensitivity check at the manuscript's measured effect size. With exact word inventories and slot lengths preserved, three strong mapped-order controls gain **0.00863–0.00935 bits/EVA character**, comparable to the manuscript's previously measured **0.00915**. All nine nonzero-dose controls improve over the invariant position baseline; all three zero-dose controls lose slightly. This demonstrates detection of the specific injected relationship, not its historical cause or a general detection-power estimate.

## Training-only audit and frozen mapping

Only the original 1,024 development words determine the mapping. For within-line transitions, count each preceding final unit/current initial unit pair, stratified by four position bins. For each ending with at least ten transitions, choose the initial with at least ten global transitions maximizing its excess count over the position-bin marginal expectation. Ties are alphabetical; keep only positive excess.

| Ending | Chosen initial | Training transitions | Position-adjusted excess count |
|---|---|---:|---:|
| l | s | 152 | 11.25 |
| n | c | 156 | 18.70 |
| o | l | 27 | 6.93 |
| r | a | 107 | 17.00 |
| s | a | 12 | 5.20 |
| y | q | 395 | 61.73 |

These are associations among atomic EVA labels, not plaintext letters or a cipher key. Selection is based on absolute excess count, not entropy or causal attribution. The evaluation text does not choose the mapping or model. A separate event-table implementation independently reconstructs the mapping and excess counts.

## Matched controls

Each case reorders existing words without replacement within folio × position-bin × length pools. Every word spelling, per-folio inventory, per-bin inventory, slot length, layout and training/evaluation split is preserved. The frozen second-order character/position/suffix model and its position-only baseline are refitted to each control. The baseline's folio scores remain invariant.

At eligible within-line transitions, with preset probability 0, 0.25, 0.5 or 1, prefer remaining words whose initial equals the frozen mapping of the preceding output word's final unit. Otherwise choose uniformly; lack of a matching candidate also triggers uniform fallback. This extends the earlier equality injection by allowing different common ending/initial labels. Rate 1 is a greedy preference whenever a candidate is available, not a global optimum.

Seeds 28001–28003 each produce all four doses. Train/evaluation streams use different SHA-256-derived seeds. Same seeds across doses do not imply identical trajectories after candidate choices differ. All twelve cases and the seven-stage schedule are frozen before scoring; no model or dose is selected on evaluation results. No Z3 calls occur.

## Seven iterations and results

| Iteration | Test | Assessment → next step |
|---|---|---|
| 1 | Training mapping audit and three zero-dose controls | Freeze six associations; null gains slightly negative. Test weak dose. |
| 2 | Dose 0.25, seed 28001 | Small positive gain. Test middle dose. |
| 3 | Dose 0.5, seed 28001 | Larger positive gain. Test strongest setting. |
| 4 | Dose 1, seed 28001 | Gain close to manuscript scale. Replicate weak dose. |
| 5 | Dose 0.25, seeds 28002/28003 | Both positive. Replicate middle dose. |
| 6 | Dose 0.5, seeds 28002/28003 | Both positive. Replicate strongest setting. |
| 7 | Dose 1, seeds 28002/28003 | Both close to manuscript scale. Retain initial calibration; move to external prose comparisons. |

Scores below are folio-equal incremental bits/character over the position-only baseline, with end-of-word cost included. Positive means lower loss; there is no significance threshold.

| Attempt probability | Seed 28001 | Seed 28002 | Seed 28003 | Mean gain | Positive runs |
|---|---:|---:|---:|---:|---:|
| 0 | −0.000116 | −0.000356 | −0.000249 | −0.000240 | 0/3 |
| 0.25 | +0.000994 | +0.001328 | +0.002607 | +0.001643 | 3/3 |
| 0.5 | +0.004423 | +0.003603 | +0.002535 | +0.003520 | 3/3 |
| 1 | +0.008629 | +0.008895 | +0.009354 | +0.008959 | 3/3 |

Evaluation mapped matches rise from 13.9–15.4% at zero dose, through 17.0–18.9% and 19.7–20.4%, to 24.1–24.8% at dose 1. These are realized proportions; attempt probabilities are not match frequencies. Gain increases in the three-seed mean, but individual trajectories need not be monotone. Strong controls improve on 40–42/50 folios and retain positive novel-spelling gains of 0.00684–0.00802 bits/character.

## Assessment and limits

The earlier equality-based calibration failed to span the manuscript signal; this mapping-based control does. Exact spellings and lengths remain fixed, so the improvement comes from changing word assignment/order within the permitted pools. It establishes that the frozen scorer can detect this known injected association at approximately the observed scale on these inventories.

The mapping is trained on manuscript associations and the same manuscript words are reused in synthetic controls. Thus this is an internal sensitivity check, not independent manuscript replication or evidence that its real order was generated by this rule. There are only three realizations per dose, insufficient for a reliable power estimate or false-positive calibration. Depleting pools, folio-specific inventories, artificial ordering and limited training data constrain transfer. The model gates all transitions; the injection targets within-line transitions, while reordering can also affect cross-line scores. This is not a clean causal isolation of every component of the total gain.

The original manuscript gain is reused. Its cause might reflect language, encoding, layout/content effects or another production process; this experiment does not rank them. The score includes end-event cost and uses atomic EVA transcription units, not established glyph segmentation.

Next priority: **park internal calibration tuning and compare the frozen statistic across several independent natural-prose corpora and languages**, with explicit orthographic normalization, matched sample sizes and transparent layout handling. A single Caesar comparison is too narrow to establish whether the manuscript signal is unusual. Preserve all current fixtures for later solver or cipher-model work.

## Reproduce and verify

```sh
.venv/bin/python -m benchmarks.mapped_boundary_calibration --run
.venv/bin/python -m benchmarks.mapped_boundary_validation
.venv/bin/python -m benchmarks.mapped_boundary_assessment
.venv/bin/python -m pytest tests/integration/test_mapped_boundary_calibration.py -q
```

Three tests pass. Validation independently reconstructs the training mapping and **68,352 context/position-model word scores**, checks all seven plan chains, aggregate results, exact inventories, slot lengths, layout, matching counts, independent split seeds and invariant position-baseline folio losses. Other stored gains are summarized from the frozen predictor rather than independently reconstructed here.

Artifacts: `experiments/results/mapped-boundary-calibration/{prepared,plan-1…7,iteration-1…7,validation,assessment}.json`. Prior code/results remain unchanged.
