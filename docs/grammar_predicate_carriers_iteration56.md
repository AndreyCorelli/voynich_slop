# Iteration 56: finite copula and auxiliary carriers

Carrier-aware supervision improves the expanded finite-subject task beyond recalibration alone. Selected-sentence F1 rises **67.0%→70.9%**, and full-source F1 **59.1%→67.1%**, comparing models calibrated on the same expanded targets. This is evidence for fixing predicate representation in supervision. It is not a replacement win on the old direct-edge task, which regresses when the retrained model is calibrated specifically for that task.

## Target definition and coverage

Freeze the original direct target unchanged: a nominal/pronominal `nsubj` directly governed by a finite VERB/AUX. Otherwise, if the governor is nonverbal or has a known nonfinite verbal form, use its unique finite VERB/AUX dependent with relation `cop` or `aux` as the subject's finite carrier. An already finite direct governor takes priority. Unknown/non-atomic verbal-governor form is separately audited and not projected. Coordination is not projected.

More than one qualifying carrier makes the frame ambiguous. Such a frame remains in the old direct task but is unscored in the expanded task and omitted from carrier-target training. No candidate is injected, and no carrier is chosen with a distance heuristic. These annotation-derived rules supply supervised labels and evaluation targets only; inference receives no gold head, dependency relation or carrier choice.

| Scope | Original direct links | New copula links | New auxiliary links | Expanded links | Retrievable expanded links | Ambiguous frames |
|---|---:|---:|---:|---:|---:|---:|
| 304 selected sentences | 470 | 32 | 17 | 519 | 515 | 0 |
| All 4,070 source sentences | 2,423 | 650 | 292 | 3,365 | 3,318 | 1 |

The one ambiguous frame is subject 13 in sentence 78052, with candidate carriers 14 and 19. It is recorded rather than resolved. There are 1,858 selected frames; full-source evaluation has 17,675 direct-task frames and 17,674 expanded-task frames. Of 942 newly projected gold links, 928 are already in the broad candidate graph. All original 326 selected reference links keep their original targets and 324/326 candidate survival.

This experiment predicts a **subject-to-finite-carrier endpoint**, not the carrier's lexical/nonverbal head. It therefore does not yet restore an entire predicate unit.

## Controls

Reuse the same five outer sentence partitions, morphology models, broad candidates, local-POS/morphology feature vectors and attachment optimization. Carrier-trained models use the same in-sample morphology training features as iteration 52; iteration 54 found no material performance benefit from cross-fitting them. The new experiment changes training labels, not inference access to annotations.

For each outer fold, compare the frozen direct-trained model with a model fitted on expanded carrier targets. Calibrate each model separately on both old direct and expanded carrier calibration labels using iteration 53's unchanged cutoff grid and F1/precision90 objectives. Freeze fit-target coverage before attachment fitting and test-target inspection. Test labels never select a cutoff or training option.

Three distinct comparisons are retained: frozen outputs evaluated on the new task, recalibration for the new task without retraining, and retraining plus recalibration on that same task. The old direct metric remains unchanged alongside them.

## Expanded-task results

Primary evaluation uses the same 519 expanded gold links in the selected sentences for every row:

| Training / calibration task | Correct | Wrong | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Direct / direct: frozen iteration 53 | 309 | 149 | 67.5% | 59.5% | 63.3% |
| Direct / carrier: recalibration only | 382 | 239 | 61.5% | 73.6% | 67.0% |
| Carrier / direct | 342 | 138 | 71.3% | 65.9% | 68.5% |
| Carrier / carrier | 378 | 170 | 69.0% | 72.8% | 70.9% |

Relative to recalibration alone, carrier-target retraining has four fewer true links and 69 fewer wrong links. Paired outcomes add 35 correct and remove 39, while adding 24 wrong and removing 93. Its selected-sentence F1 gain is primarily improved precision, not increased total recovery.

New carrier links improve much more directly: the frozen model recovers 8/49, recalibration alone 23/49, and carrier training/calibration **39/49** (24 copular and 15 auxiliary). In exchange, recovery of the original 470 direct gold links changes from 359 with recalibration alone to 339 with carrier training/calibration. Both groups are reported; improvements in projected targets do not conceal direct-link losses.

Exact expanded edge sets rise from 124/304 sentences under recalibration alone to 149/304 under carrier training/calibration. The frozen iteration-53 outputs give 117/304 on this expanded task; its previously reported 127/304 concerned the different, direct-only target set.

| Expanded-task scope | Recalibration-only precision / recall / F1 | Carrier-trained precision / recall / F1 |
|---|---|---|
| All source | 53.0% / 66.7% / 59.1% | 61.7% / 73.6% / 67.1% |
| Cicero selected | 62.1% / 74.5% / 67.7% | 69.1% / 74.5% / 71.7% |
| Palladius selected | 58.8% / 69.8% / 63.8% | 68.5% / 65.6% / 67.0% |

Across source, retraining adds 421 correct outputs and removes 188, while adding 289 wrong outputs and removing 740: net **233 more correct and 451 fewer wrong**. It recovers 509/650 copula links and 214/292 auxiliary links, versus 315 and 110 after recalibration alone. Both selected authors improve in F1, although Palladius recall decreases.

These are held-sentence predictions from reused Cicero/Palladius development data, with readable Latin and supplied POS. The targets are derived from source dependencies, not independently adjudicated semantic predicate units. Improvements on this expanded task are not directly comparable with old-task percentages or evidence of Voynich restoration.

## Old-task guard and confidence limits

On the unchanged direct task, calibrating each model for that task gives:

| Scope | Frozen direct model F1 | Carrier-trained model F1 |
|---|---:|---:|
| Selected sentences | 64.9% | 64.0% |
| All source | 56.8% | 54.5% |

The original 326-reference recovery is 220 for the frozen model versus 215 for the carrier-trained/direct-calibrated model. The carrier-trained/carrier-calibrated setting recovers 236, but the direct-trained/carrier-calibrated setting recovers 258; these use different calibration objectives from the original baseline. They do not establish better preservation of the narrow task.

The carrier-trained models find no margin cutoff satisfying calibration precision90 with at least 20 predictions, so those policies abstain. One direct-trained/carrier-calibrated fold qualifies; on the full expanded task it emits 16 links with 14 correct (87.5% precision, 0.4% recall). No reliable high-precision operating point is established.

## Decision and next proposal

Keep carrier-aware supervision as a promising option for the broader grammar task, while preserving iteration 53 for the old direct task. This separates an expanded task definition from a measured learned gain under that definition. Do not silently replace the old benchmark or treat the projected labels as newly restored structure.

The next proposal is to **predict the carrier's lexical/nonverbal head and relation type**, producing a typed predicate unit alongside the subject link. Evaluate head–carrier attachment against distance and report exact `(subject, head, carrier, cop/aux)` recovery separately from carrier-endpoint recovery. Candidate generation and scoring must use observable features, with annotation-derived units only as training/evaluation labels. Coordination remains a separate future issue because aggregate subject agreement is required.

## Artifacts and validation

Code: `src/voynich_smt/predicate_carriers.py`, `benchmarks/grammar_predicate_carriers_iteration56.py` and its `_audit` module. Target rules, fit-target coverage, ambiguous examples, models and dual-task evaluations are frozen under `experiments/results/grammar-restoration/iteration56/`. Existing output directories are rejected.

Independent validation checks 28 hashes, refits all five new attachment models, reselects 20 calibration policies, replays all 17,675 targets, 70,700 scores and 141,400 decisions, and reproduces 64 dual-task metrics plus eight frozen baseline metrics. All 304 selected sentences pass inference mutation checks; previous candidate/prediction fields remain unchanged. Five new tests cover unique carriers, direct-target priority, ambiguity, no target injection and scope exclusions; 59 relevant tests pass. The 200-sentence reserve remains unscored, with no prior target queries scored.
