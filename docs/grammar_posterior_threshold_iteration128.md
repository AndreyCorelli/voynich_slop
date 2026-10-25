# Iteration 128: score-scale correction recovers PP coverage, precision transfer fails

**Preserve the partial structural gain:** a source-selected threshold for posterior-mean PP scores yields **271 correct / 52 wrong** on the existing test text, improving F1 to **0.4927** versus **0.4519** for the new hard-class model. Precision is **83.90%**, so the 90% transfer requirement fails. This remains meaningful conditional structural information, not a validated high-precision policy or lexical nucleus recovery.

## Fixed diagnostic

Reuse exactly iteration 127's posterior-mean scores, based on 32 type-consistent class draws through the original PP model. No model, class calibration, draw count, mixture, input, or annotation changes. Enumerate all attained source-calibration PP thresholds, plus 1 for the empty selection, with inclusive score comparison and ties kept together.

Require at least 90% precision and 248 correct selections, retaining 80% of the hard-class calibration baseline's 310 correct selections. Select maximum correct coverage, then fewer errors, then higher threshold. Freeze the policy before loading the cached test scores. The experiment changes only the PP decision threshold; it does not relax either quality requirement.

## Source calibration

Among **10,501 threshold settings**, **78 qualify**. The selected threshold is **0.4849530056062174**, giving **319 correct / 35 wrong (90.11% precision)**. The best precision among settings retaining the required coverage is **91.27%**, with 303 correct / 29 wrong; that alternative is diagnostic and is not substituted for the predeclared selection rule.

The source result shows that iteration 127's coverage collapse at cutoff 0.80 was partly a score-scale issue. A qualifying source operating point exists, so fixed-cutoff failure was not a sufficient reason to discard posterior averaging.

## Frozen test result

| Policy | Correct PP | Wrong PP | Precision | F1 |
|---|---:|---:|---:|---:|
| Unknown classes, old 0.80 cutoff | 23 | 0 | 100% | 0.0575 |
| Earlier inferred classes, old 0.80 cutoff | 235 | 34 | 87.36% | 0.4493 |
| Balanced-training hard classes, old 0.80 cutoff | 244 | 59 | 80.53% | 0.4519 |
| Posterior mean, old 0.80 cutoff | 26 | 0 | 100% | 0.0648 |
| **Posterior mean, source-selected cutoff** | **271** | **52** | **83.90%** | **0.4927** |

Correct coverage exceeds the frozen test minimum of 196; precision is the failing requirement. Against balanced-training hard classes, there are **60 newly correct selections, 33 lost correct selections, 22 new errors, and 29 removed errors**. Against the earlier inferred classes, there are 69 newly correct, 33 lost correct, 36 new errors, and 18 removed errors. Net gains do not imply that all previous successes survive.

The fixed originally unmapped cohort yields **197 correct / 49 wrong (80.08% precision)**, compared with hard classes 183/56. Other supplied anchors contribute 74/3; target-token selections remain empty. The target word classes help predict structure at other positions, not exact word identities. No test threshold sweep or author evaluation is performed.

## Interpretation for decipherment

The posterior integration retains useful structural information after source-only score calibration, although it does not meet the chosen high-precision transfer bar. Preserve this result separately from that failed gate: a future decoder might exploit probabilistic structure at this quality level. It is not evidence of usable Voynich constraints yet, because surrounding anchor mappings, function-word catalogue membership, and segmentation are supplied, and development text is repeatedly reused.

No default changes or lexical nuclei are claimed. A more informative next challenge is to measure dependence on the supplied surrounding anchors, using fixed source-fit-ranked anchor budgets and frozen policies. This asks how much of an already known key the grammatical signal requires, directly addressing the gap between current conditional success and a practical decipherment input, rather than repeatedly adjusting thresholds on these test results.

## Verification

The independent audit verifies eight frozen input hashes, independently replays all 10,501 source thresholds and the 78 qualifying settings, reproduces the source selection, checks twelve test-cohort transition comparisons, and confirms the test precision failure. Existing score vectors and labels are reused without new inference. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration128/`.
