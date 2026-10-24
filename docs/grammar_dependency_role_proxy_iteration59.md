# Iteration 59: soft dependency-role evidence

The tested role-proxy addition does not improve typed-unit restoration. Selected-sentence F1 stays **64.85%**; full-source F1 changes **56.86%→56.80%**. Calibration rejects all head evidence and nearly all carrier-type evidence. Keep the existing head scores; do not enable this scored variant by default.

The proxy itself learns token roles reasonably well. The failure is transferring that evidence into the current unit ranking, not an inability to predict any dependency-role information. A narrow next control is to remove the POS-prior normalization before changing the proxy model or supervision.

## Fixed design

Reuse the same five outer partitions, 4,070 source sentences, iteration-56 endpoint outputs, iteration-57 head domains/scores and unique-carrier task. Gold unit counts remain 519 selected and 3,365 across source. The one ambiguous frame remains excluded only from expanded-task evaluation. No head or endpoint model is refitted.

Fit a four-class token-role proxy on **all tokens in the outer fit sentences**:

- `dependent`: amod/det/nmod/appos/flat/fixed/compound/case, including relation subtypes;
- `cop`;
- `aux`;
- `other`: all remaining relations.

The POS-context variant uses a ±2 POS window plus immediate POS pairs/flanks. The lexical variant also uses the current/adjacent word identities and current-word suffixes of length two, three and four with POS. Both use multinomial logistic regression, fixed L2 0.001, feature minimum frequency three and convergence-checked optimization. Unknown feature values are ignored. No lemma, morphology annotation, dependency head or gold relation enters inference.

The lexical variant explicitly adds readable-word access to the head stage; the upstream endpoint model already uses readable Latin. The POS-only variant controls that additional access.

The score additions are **POS-prior-normalized** log ratios:

```
head evidence = log P(non-dependent | context) − log P(non-dependent | head POS)
type evidence = log P(carrier role | context) − log P(carrier role | carrier POS)
```

Direct maps to proxy class `other`, cop and aux to their respective classes. Probabilities are clipped at 1e−6. Normalization was fixed before evaluation to discount role information already predictable from POS; it is a design choice tested here, not an established requirement.

Head-only, type-only and joint additions choose nonnegative weights from 0, 0.5, 1, 2, 4 on calibration sentences. Selection maximizes unique exact unit recovery with correct endpoints supplied, matching iteration 57's conditional calibration task. Ties prefer lower total weight. Zero reproduces the frozen scorer. Actual pipeline evaluation uses the original predicted endpoints, including mistakes.

No in-sample proxy predictions are used to train a new head scorer: the proxy fits on outer fit data, then only calibration/test predictions supply the new evidence. This avoids the training-feature issue examined in iteration 54. Test labels evaluate outputs only.

## Token prediction quality

Held-sentence token-role evaluation covers 52,757 source tokens. The POS-only role-prior reference has negative log likelihood 0.2557.

| Proxy | Token accuracy | Negative log likelihood | Dependent precision / recall | Cop precision / recall | Aux precision / recall |
|---|---:|---:|---|---|---|
| POS context | 91.95% | 0.2130 | 92.82% / 71.82% | 72.36% / 86.04% | 64.33% / 64.23% |
| POS + lexical context | 93.61% | 0.1784 | 93.44% / 79.79% | 73.34% / 87.87% | 69.51% / 63.45% |

These are token classification measurements, not parsing accuracy or predicate-unit recovery. Frequent easy `other` tokens and preposition/modifier patterns contribute heavily; quality on the difficult head contrasts is evaluated separately below.

## Calibration and unit results

All head-only weights are zero in all folds for both proxies. All POS-context type/joint weights are also zero. The lexical type/joint condition selects type weight 0.5 only in outer fold two, with head weight zero; every other fold chooses zero. That fold's calibration exact count rises 564→570/663. The held-out effect does not follow that gain.

| Pipeline setting | Selected correct / wrong | Selected F1 | Full-source correct / wrong | Full-source F1 |
|---|---|---:|---|---:|
| Frozen baseline | 346 / 202 | 64.85% | 2,098 / 1,917 | 56.86% |
| POS proxy, any arm | 346 / 202 | 64.85% | 2,098 / 1,917 | 56.86% |
| Lexical head-only | 346 / 202 | 64.85% | 2,098 / 1,917 | 56.86% |
| Lexical type-only / joint | 346 / 202 | 64.85% | 2,096 / 1,919 | 56.80% |

Selected outputs, including both authors, remain exactly unchanged. Across source, lexical type evidence changes 20 unit predictions: four become correct and six previously correct units become wrong. Six wrong outputs are added and four removed. Total output stays 4,015 units.

By gold kind, full-source exact pipeline counts change direct 1,690→1,693, copula 259→254 and auxiliary 149→149. Selected copular pipeline recovery remains seven of 32. With true endpoints supplied, full-source exact units change 2,870→2,865/3,365, and copular units 316→309/650. Thus the small active addition does not realize the desired copular benefit.

## Why token accuracy does not settle the issue

Among 650 genuine copular heads, only one is actually in the nominal-dependent class, but the POS proxy classifies 45 and the lexical proxy 38 as dependent. These false positives occur in the critical head population despite good global dependent precision. A hard proxy mask would therefore be inappropriate.

The frozen copular scorer has 479 higher-scoring wrong head candidates. Of these, 193 truly have nominal-dependent relations; the POS proxy predicts 118 candidates as dependent and the lexical proxy 142. Those counts include both correctly and incorrectly classified distractors and are not independent constructions or guaranteed recoveries.

The normalization also deserves an isolated control. On those 479 head contrasts:

| Evidence ordering | POS: favors genuine head / competitor | Lexical: favors genuine head / competitor |
|---|---|---|
| Tested POS-normalized head evidence | 230 / 249 | 244 / 235 |
| Raw non-dependent probability | 290 / 189 | 283 / 196 |

Raw probabilities order more of these difficult pairs favorably than the tested normalized score. This is only a descriptive diagnostic: no unnormalized score was calibrated, no new output was selected from these counts, and it does not prove an improved pipeline. It motivates a controlled ablation rather than dismissing role supervision generally.

## Decision and next control

Keep the proxy as an experimental diagnostic, with zero weights preserving the previous model. Do not treat high token accuracy as evidence that the oracle phrase-role headroom is available to the unit scorer.

Next, hold the fitted proxies, head scores, candidates and endpoints fixed and compare **raw log probabilities** with the current POS-normalized evidence. Recalibrate the same head/type grids on calibration sentences, retaining zero controls and reporting every unit kind and the actual pipeline. This isolates the normalization choice before increasing model capacity, changing losses or adding another parser component. It is proposed, not tested here.

All results remain on reused development data with readable Latin and supplied POS. No fresh confirmation or encrypted grammar restoration is established.

## Artifacts and checks

Code: `src/voynich_smt/dependency_role_proxy.py`, `benchmarks/grammar_dependency_role_proxy_iteration59.py` and its `_audit` module. Models, calibration grids, token confusions, unit predictions and contrast audits are under `experiments/results/grammar-restoration/iteration59/`. Existing output directories are rejected.

The run verifies 14,762 zero-weight decisions and 608 selected-sentence proxy-inference mutation checks. Independent audit checks 20 hashes, refits all ten proxies, reselects 30 calibration policies, replays 212,100 prediction fields and reproduces 28 unit-metric groups and both token confusions. Five new tests cover annotation-independent features, numerical gradients, POS normalization/zero weights, conservative calibration and probability normalization/nonmutation; 74 relevant tests pass. All prior fields and models remain intact. The 200-sentence reserve remains unscored and no prior target queries were scored.
