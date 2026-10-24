# Iteration 53: calibrating attachment versus NONE

Calibrating the NONE decision substantially improves the frozen iteration-52 model. On the selected sentences, local + morphology F1 rises **50.1%→64.9%**: recall rises **37.2%→64.0%**, while precision falls **76.8%→65.7%**. This operating point also improves both precision and recall over distance. No model was refitted and no candidate link was added.

The improvement supports a concrete algorithm addition: choose the attachment/NONE operating point on calibration data instead of fixing it at the softmax MAP boundary. It remains development evidence from readable Latin with supplied POS, not demonstrated Voynich restoration.

## Fixed design and controls

Reuse iteration 52's ten learned models, morphology models, broad candidate sets, vectors, source sentences and five outer partitions. Score every nominal token's compatible predicates and retain its unique best edge. The margin is its unchanged linear score minus the fixed NONE score of zero. Tied edges and empty domains still abstain.

Compare two calibration policies on each structural/local model:

- **MAP control:** choose a score cutoff restricted to zero or above. This cannot recover edges suppressed by NONE.
- **Free cutoff:** allow negative cutoffs. This changes acceptance, never predicate order.

The predeclared grid is −1,000,000, −8, −6, −4, −3, −2, −1.5, −1, −0.5, 0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 1,000,000. Extreme cutoffs accept/reject all unique edge proposals; score magnitudes are checked. Acceptance requires margin strictly above the cutoff, with numerical tolerance. A zero cutoff reproduces the original unthresholded MAP decision, including abstention on a tie with NONE.

For each outer fold, select thresholds only on that fold's calibration sentences, either for maximum micro F1 or for maximum true positives at empirical precision ≥90% with at least 20 predictions. Ties favor fewer predictions. Keep iteration 52's probability-gated results as a separate frozen comparison: margin and full-softmax confidence need not order proposals identically.

All five structural models select F1 cutoff −1.5. Local + morphology selects −1 in folds 0–3 and −1.5 in fold 4. MAP controls select zero. No test outcome selects a cutoff, and no parameter is refitted.

## Primary results

The same 304 selected sentences contain 1,858 task frames and 470 annotated finite-subject links, of which 467 are retrievable. Other annotated sentence links count as valid, including those outside the original 326 selected references.

| Model / F1 policy | Correct | Wrong | Missed | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Distance, iteration 52 | 273 | 550 | 197 | 33.2% | 58.1% | 42.2% |
| Structural, MAP control | 0 | 0 | 470 | Undefined | 0% | 0% |
| Structural, free cutoff | 315 | 471 | 155 | 40.1% | 67.0% | 50.2% |
| Local + morphology, old probability policy | 175 | 53 | 295 | 76.8% | 37.2% | 50.1% |
| Local + morphology, MAP control | 175 | 53 | 295 | 76.8% | 37.2% | 50.1% |
| Local + morphology, free cutoff | 301 | 157 | 169 | 65.7% | 64.0% | 64.9% |

Relative to the old local model, all 230 additional predictions were previously suppressed by the raw NONE/tie decision: 126 are correct and 104 wrong. No previously correct output is removed on these sentences. The added band alone is therefore only 54.8% precise; the recall improvement is not free.

Non-subject false attachments increase from 21 to 108, and accepted wrong-governor attachments from 32 to 49. Abstentions fall from 1,630 to 1,400. Exact recovery of the limited finite-subject edge set rises from **89/304 to 127/304 sentences**; sentences with multiple predicted links rise from 40 to 131. These are not complete dependency parses.

On the original 326 selected references, the free local policy recovers **220**, chooses a wrong predicate for 27 and abstains on 79. The old local policy recovered 133, chose 20 wrongly and abstained on 173; distance recovered 190, chose 44 wrongly and abstained on 92. These are unanchored predictions; no true subject or predicate is supplied.

## Broader evaluation and limits

| Scope / model | Precision | Recall | F1 |
|---|---:|---:|---:|
| All source / distance | 22.6% | 60.0% | 32.9% |
| All source / old local model | 66.2% | 39.8% | 49.7% |
| All source / free local cutoff | 51.6% | 63.1% | 56.8% |
| Cicero selected / old local model | 77.2% | 41.1% | 53.6% |
| Cicero selected / free local cutoff | 65.8% | 65.3% | 65.5% |
| Palladius selected / old local model | 73.1% | 21.1% | 32.8% |
| Palladius selected / free local cutoff | 65.4% | 58.9% | 62.0% |

The full source evaluation still processes the same 4,070 sentences and 2,423 gold links; 3,910 sentences contain at least one task frame. Of the free local model's 2,962 predicted edges, 1,529 are correct and 1,433 wrong. The lower precision outside the selected subset is material. Both selected authors improve in F1, reversing iteration 52's Palladius regression, but these are reused development partitions with no independent reliability claim.

No margin cutoff in the fixed grid meets the calibration precision90 requirement with 20 predictions for any model/fold. Those policies therefore abstain completely. This does **not** prove 90% precision impossible: the grid/support requirement and score ordering constrain this diagnostic. The old probability policy remains separately available; it had 96.6% precision at 6.0% recall on selected sentences and 88.7% precision at 5.2% recall over all source data. A raw margin ignores competing-predicate probability mass, so it should not silently replace that confidence score.

The free local model's 169 missed gold edges divide into three absent candidates, 70 whose wrong predicate ranks first, and 96 correctly ranked edges rejected by the cutoff. Thus calibration explains a substantial part of the previous failure, but neither eligibility nor attachment discrimination is solved.

## Decision and next control

Keep the calibrated NONE cutoff as a promising experimental modification alongside feature-shared morphology and the proper-name fallback. Preserve a separate high-confidence policy and the original candidate lattices. Do not treat the new F1 operating point as a universally better precision setting or a default confirmed on fresh data.

Next, test the already proposed **cross-fitting of morphology confidence used to train attachment**. Iteration 52 trained with in-sample morphology scores; their optimism can distort learned eligibility and NONE decisions. Hold candidates and outer partitions fixed while generating each fit sentence's morphology probabilities from other fit sentences only. Recalibrate on the untouched outer calibration portion. This isolates training-feature optimism from changing candidate recall, before fresh confirmation of a combined configuration.

## Artifacts and checks

Code: `src/voynich_smt/none_gate.py`, `benchmarks/grammar_none_gate_iteration53.py` and its `_audit` module. Frozen proposal snapshot, calibration policies, margins and per-frame predictions are under `experiments/results/grammar-restoration/iteration53/`. Runs reject existing output directories.

Validation reproduces 35,350 zero-cutoff MAP decisions and checks inference invariance on all 304 selected sentences. Independent audit checks 17 hashes, reselects all 20 calibration policies, replays 35,350 best-edge scores and 141,400 gate decisions, and reproduces 32 aggregate metrics. Previous prediction fields and all frozen models remain unchanged. Five new tests cover negative-margin recovery, MAP/tie/empty equivalence, calibration below zero, target-independent inference and invalid/nonfinite inputs; 46 relevant tests pass. The 200-sentence reserve remains unscored, and no prior target queries were scored.
