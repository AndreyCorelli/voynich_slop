# Iteration 61: type-balanced unit training

Type balancing gives a small improvement in head ranking but does not establish a useful pipeline improvement. With micro calibration, full-source exact-unit F1 is 56.96%, versus 56.86% for the original model; selected-sentence F1 falls from 64.85% to 64.67%. Retain the original baseline. This experiment does not support making balanced training the default.

## Controlled comparison

The task remains recovery of `(subject, head, finite carrier, type)`, with direct, copular and auxiliary types. The source contains 4,070 Cicero/Palladius sentences and 3,365 gold units, including 519 units in the 304 selected sentences. The single carrier-ambiguous frame is excluded from expanded-unit evaluation. The five sentence partitions, candidate domains, 96 POS/position features, L2 regularization (0.01), optimizer and iteration-56 carrier predictions are unchanged. There are no new lexical or dependency-role-proxy features.

The original iteration-57 model supplies the unweighted control. The balanced model weights each training frame by `N / (K * count_of_its_gold_type)`, so each present type contributes equal total loss mass while total weight remains N. Every real fold contains all three types. This changes the relative emphasis on types without changing regularization strength through a loss-scale change. Gold types determine training weights only; inference uses POS and position features.

Both models receive identical calibration options: direct offset fixed at zero, and copular/auxiliary offsets independently chosen from −2, −1, −0.5, 0, 0.5, 1, 2. Zero is included. Separate policies maximize micro exact-unit count or macro per-type exact recall; ties prefer smaller total absolute offset. Calibration supplies true subject/carrier endpoints, following iteration 57. It therefore optimizes conditional recovery, not the complete pipeline. No grid extension was made after evaluation; the balanced micro auxiliary offset hits −2 in two folds.

## Actual pipeline results

Wrong units count as both a false positive and a false negative. All arms emit the same 4,015 full-source and 548 selected predictions because carrier endpoints are frozen.

| Training / offsets | Full-source exact units | Full-source F1 | Selected exact units | Selected F1 | Full-source macro F1 |
|---|---:|---:|---:|---:|---:|
| Original / zero | 2,098 | 56.86% | 346 | 64.85% | 48.36% |
| Original / micro | 2,084 | 56.48% | 345 | 64.67% | 47.62% |
| Original / macro recall | 2,079 | 56.34% | 342 | 64.10% | 47.21% |
| Balanced / zero | 2,080 | 56.37% | 341 | 63.92% | 48.01% |
| Balanced / micro | 2,102 | 56.96% | 345 | 64.67% | 48.38% |
| Balanced / macro recall | 2,081 | 56.40% | 340 | 63.73% | 47.59% |

Against the equally micro-calibrated control, balancing adds 18 correct units; against the stronger original zero-offset baseline it adds only four. Calibration itself worsens the original model. The comparison with the original baseline is therefore essential. Macro-recall calibration does not improve macro F1: these are different objectives.

| Full-source type | Original zero: correct / F1 | Balanced micro: correct / F1 |
|---|---:|---:|
| Direct (2,423 gold) | 1,690 / 63.51% | 1,670 / 64.01% |
| Copular (650 gold) | 259 / 37.48% | 264 / 38.37% |
| Auxiliary (292 gold) | 149 / 44.08% | 168 / 42.75% |

Balanced micro predicts 494 auxiliary units rather than 384. Auxiliary recall improves from 51.03% to 57.53%, but precision declines from 38.80% to 34.01%; the additional auxiliary recovery does not improve auxiliary F1. Full-source macro recall rises from 53.54% to 55.69%, while macro F1 is essentially unchanged. The uncalibrated balanced model pushes this further: macro recall 56.89%, but micro F1 56.37%.

## Does training improve head ranking?

With true endpoints and true type supplied, constant type offsets cannot change the ordering of heads within that type. This diagnostic isolates ranking changes caused by training.

| Gold type | Original correct | Balanced correct |
|---|---:|---:|
| Direct | 2,423 / 2,423 | 2,423 / 2,423 |
| Copular | 420 / 650 | 427 / 650 |
| Auxiliary | 269 / 292 | 272 / 292 |

The direct result is automatic because the direct candidate has head equal to carrier. Copular accuracy rises from 64.62% to 65.69%, auxiliary from 92.12% to 93.15%. Thus balance produces a real but small head-ranking change, alongside the larger shift in type preference. It recovers seven of the 230 previously missed copular heads net; it does not resolve copular localization.

With true endpoints but unknown type, original zero recovers 2,870/3,365 units, balanced zero 2,848 and balanced micro 2,872. Even in this easier diagnostic the balanced micro gain over the original baseline is only two units. These oracle figures are not restoration performance.

## Validation and decision

Artifacts are in `experiments/results/grammar-restoration/iteration61/`. The design snapshot, fitted models and predictions were frozen before the relevant downstream evaluation. The audit independently refits all five balanced and five unweighted models, replays the calibration grids and saved predictions, checks preservation of prior fields, and recomputes evaluation. The runner also checks inference after masking words, lemmas, dependency heads/relations and morphology, and verifies that role offsets preserve true-type head ranking. The relevant 83 tests pass.

The evidence weakens the hypothesis that frequent direct units dominating the loss are the main bottleneck. Keep balanced training as a recorded ablation, not a default. A more useful next diagnostic is to cross true type with the phrase-role/clause-locality head oracles from iteration 58 and explicitly separate type errors, within-type head errors and joint errors. That would identify whether a hierarchical type-then-head model has room to help before implementing another scorer; oracle improvements must remain separate from deployable results.

All results reuse development partitions with source POS available. They provide neither fresh confirmation nor evidence of Voynich restoration. The 200-sentence reserve remains unscored; no prior target queries were scored.
