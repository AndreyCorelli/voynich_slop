# Iteration 34: detect context–candidate conflict, then selectively override

**Missing-class detection has a useful ranking signal, but the calibrated correction gate does not improve query accuracy.** At the primary .01 fallback, cavity probability mass outside the supplied candidate set achieves about .90 AUROC at 10% deletion and .85 at 50%. A background-calibrated confident-override gate breaks even on the low-deletion query scenarios and slightly harms the high-deletion scenarios. Detecting unreliable evidence and choosing a correct replacement class are separate problems.

Validated artifacts are **`iteration34-v2`**. A zero-gain/empty-threshold tie was corrected before query evaluation: calibration now explicitly requires positive net gain to enable a gate. The original pre-evaluation policy archive is preserved in `iteration34/` with a supersession note; it was never query-scored.

## Internal calibration/query split

The source observations and frozen models remain those of iteration33. Within the already inspected development corpus, thresholds use only the 200 background sentences (1,579 tokens), while evaluation uses the disjoint 40 query sentences (473 tokens). Sentence IDs do not overlap. Both deletion levels and all five perturbation seeds are pooled for calibration within each emission arm/fallback setting, so a policy does not receive the deletion rate.

This is **not a new held-out benchmark**. These query sentences were examined in earlier diagnostics, the upstream HMM fits are transductive, and oracle candidate inventories/class transitions already incorporate reference information from the corpus. The new threshold selection does not use query labels, but those earlier information channels remain privileged. No fresh targets or reserved sentences are scored.

There are ten calibration scenarios per arm/epsilon (two deletion rates × five seeds), giving 15,790 scenario-token exposures. These reuse 200 sentence IDs and are not 15,790 independent observations. Query summaries average five perturbed copies of the same 473 tokens at each deletion rate.

## Signals and policies

The gate receives only:

- the exact target-masked HMM posterior over eight classes;
- the ordinary HMM posterior;
- the supplied candidate membership for that word.

It receives no oracle neighboring tags, target reference class, excluded/covered indicator, perturbation flag, plaintext, or word-specific rule. Those labels are available only for calibration scoring and evaluation. Target masking is the independently checked cavity computation from iteration33; upstream emission parameters are not refitted.

The primary detector score is **outside mass**: the sum of cavity class probabilities outside the supplied candidate set. Two secondary ranking controls are posterior conflict (`1 − dot(cavity, ordinary)`) and cavity-top confidence when that top class lies outside the candidates (zero otherwise). A high outside mass can be distributed over several classes; it need not identify a confident single replacement.

The primary correction gate considers a token only when the cavity top class differs from the ordinary prediction and lies outside the supplied candidate set. It then requires both a minimum cavity-top probability and a minimum cavity probability ratio of top class to ordinary class. The secondary gate allows any disagreement, including an alternative class inside the candidates.

Before scoring, the fixed grid is:

- confidence: .25/.35/.45/.55/.65/.75/.85/.95;
- probability ratio: 1/1.5/2/4/8;
- disabled gate as a genuine alternative.

Each gate maximizes background corrected-minus-spoiled tags, subject to spoiling at most 1% of baseline-correct **covered** calibration tags. Positive calibration net gain is required. Ties prefer fewer spoiled tags, fewer overrides, then stricter thresholds. Epsilon .01 remains primary; .30 is a sensitivity condition. No objective or query accuracy selects epsilon.

Application is one simultaneous local tag-edit pass using the original frozen cavity features. It does not refit emissions, recompute context, or establish a coherent grammatical parse.

## Detection ranking on query tokens

Equal-weight means across five perturbation seeds:

| Arm | Fallback | Deletion | Outside-mass AUROC | Average precision | Excluded-token prevalence |
|---|---:|---:|---:|---:|---:|
| Word | .01 | 10% | .904 | .575 | .089 |
| Ending | .01 | 10% | .905 | .583 | .089 |
| Word | .01 | 50% | .845 | .835 | .490 |
| Ending | .01 | 50% | .846 | .836 | .490 |
| Word | .30 | 10% | .920 | .631 | .089 |
| Ending | .30 | 10% | .922 | .636 | .089 |
| Word | .30 | 50% | .880 | .880 | .490 |
| Ending | .30 | 50% | .880 | .881 | .490 |

For the primary word arm, AUROC ranges .893–.920 at 10% deletion and .823–.862 at 50%. These are perturbation-seed ranges, not population confidence intervals. Average precision depends on prevalence, so its values across deletion rates are not directly comparable as evidence of stronger detection.

The simpler conflict score has primary word-arm AUROC .801/.750 and average precision .330/.749 at10/50%. Cavity-top outside confidence is weaker: AUROC .725/.657 and AP .194/.603. Thus the strongest ranking signal is aggregate probability outside the candidate inventory, rather than confident choice of one outside class. Ranking metrics do not establish a useful thresholded precision/coverage operating point or generalization to a learned candidate system.

## Calibrated gates are sparse

For both arms at primary epsilon .01, both gate families select the same thresholds: **cavity confidence at least .75 and probability ratio at least 8**. Background results pooled across deletion rates/seeds:

| Arm | Overrides | Corrected | Spoiled | Remained wrong | Net gain |
|---|---:|---:|---:|---:|---:|
| Word | 27 | 7 | 6 | 14 | +1 |
| Ending | 23 | 7 | 5 | 11 | +2 |

All seven corrections per arm recover excluded classes. The spoils are baseline-correct covered tags. The tiny net gains among 15,790 calibration exposures give little evidence of a robust correction policy, despite meeting the fixed risk budget.

At epsilon .30, neither family achieves positive background gain under the calibration rule; both are disabled. Disabled means no query intervention, not a high-confidence zero-override threshold that might behave unexpectedly on queries. No query-driven rescue threshold is substituted.

## Query corrections and false overrides

Counts below are totals over five perturbation scenarios at each deletion rate: 2,365 scenario-token exposures, still only 40 unique query sentences. Primary .01 results:

| Arm | Deletion | Overrides | Corrected | Spoiled | Remained wrong | Net correct tags | Mean query accuracy change |
|---|---:|---:|---:|---:|---:|---:|---:|
| Word | 10% | 3 | 1 | 1 | 1 | 0 | 0.000 points |
| Ending | 10% | 2 | 1 | 1 | 0 | 0 | 0.000 points |
| Word | 50% | 6 | 0 | 3 | 3 | −3 | −0.127 points |
| Ending | 50% | 4 | 0 | 2 | 2 | −2 | −0.085 points |

At low deletion, the single recovered excluded tag is canceled by a spoiled correct covered tag. At high deletion, no excluded tag is recovered; all net changes are harmful. The two gate families produce identical query decisions in this experiment, so the general-disagreement variant supplies no separate improvement. At .30 all policies remain disabled, preserving the unchanged fallback-model predictions.

These query results are too small and repeatedly inspected for deployment claims. A paired sentence-cluster bootstrap resamples the 40 query sentence IDs jointly across all five perturbations. With 1,000 replicates, 95% intervals for accuracy change are:

- low deletion, either arm: [−0.121,+0.123] percentage points;
- high deletion, word: [−0.263,0.000];
- high deletion, ending: [−0.212,0.000].

These quantify variation in this finite reused query set; they do not repair prior inspection, upstream oracle information, or the absence of new target validation.

## Interpretation and next action

The detector finds an observable contradiction signal: posterior mass wants to leave the candidate inventory more often when a reference class is missing. Yet a high score does not say which outside class is correct. The earlier oracle-neighbor result already showed weak first-order top1 discrimination, and the calibrated override test confirms that a confident single-class repair is not a validated use of this signal.

The useful next step is to treat outside mass as a **candidate-quality flag**, rather than a replacement tag: calibrate a flag/abstention policy on the same background split, report excluded-token precision/recall and false flags on correct covered tags on the separate queries, then assess retained-tag precision versus coverage. Candidate-set expansion or richer contextual inference could follow if this flag isolates a useful subset. This experiment supplies ranking evidence for that direction, not a ready threshold or evidence of restored grammar. Further searches for override thresholds on these query outcomes would be post-hoc tuning.

## Artifacts and reproduction

Current artifacts: `experiments/results/grammar-restoration/iteration34-v2/` contains the frozen label-free features, separate truth, manifest, background-calibrated policies, evaluation freeze, query decisions, detection/paired metrics, clustered intervals, and validation report. Previous verified iteration33 and earlier files are unchanged.

```
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_context_override_iteration34
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_context_override_iteration34_evaluate
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_context_override_iteration34_validate
```

Runners preserve outputs. Four new tests check signal/gate behavior, disabling zero-gain policies, correction/risk accounting, and tie-aware ranking against pairwise AUC. Validation checks 40 label-free feature projections, disjoint 200/40 sentence IDs, all eight calibration replays, 80 query decision audits, 120 independent pairwise AUROCs, 16 sentence-cluster bootstrap replays, risk/positive-gain rules, and prior hashes. The combined relevant suite passes 317 tests. The 200 reserved sentences remain unscored.
