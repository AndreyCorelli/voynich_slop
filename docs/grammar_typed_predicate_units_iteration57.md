# Iteration 57: recovering typed predicate units

The head/type stage now predicts `(subject, head, finite carrier, direct/cop/aux)` using observable POS and positions. A learned scorer adds little over a source-prior + distance baseline: selected-sentence full-unit F1 is **64.85% versus 64.78%**, and full-source F1 **56.86% versus 56.25%**. The main new bottleneck is locating copular heads; the strong overall conditional accuracy is dominated by direct predicates.

No existing endpoint prediction or metric changes. These typed-unit scores require extra correct fields and must not be compared as if they were the same task as iteration 56's carrier-endpoint scores.

## Design and controls

Keep iteration 56's unique-carrier targets, same five sentence partitions, 304 selected sentences and 4,070 reused source sentences. Ambiguity handling is unchanged: one frame is excluded only from expanded-task evaluation. There are 519 selected gold units and 3,365 across source.

Gold units are `(s, v, v, direct)` for an original direct finite governor, or `(s, h, v, cop/aux)` where the subject's governor is the nonverbal/nonfinite head and `v` its unique finite carrier. Annotation-derived heads/types are used only for fitting, calibration and evaluation.

For any supplied subject/carrier positions, inference enumerates the self-head/direct option and every other token except the subject/carrier as a possible cop or aux head. This is based on token positions, with no gold-head injection or POS restriction on head candidates. Every gold unit is in its head/type domain, including all fit and calibration units. This coverage result is conditional on supplying the correct endpoint, not evidence of endpoint retrieval.

Compare two scorers:

- **Prior + distance:** source-fit carrier-POS type priors and type-conditioned head-POS priors, with add-half smoothing, minus a weighted log head–carrier distance. Calibration chooses weight from 0, 0.5, 1, 2, 4 by unique exact unit recovery. All five folds select weight two. Type is predicted, never supplied.
- **Learned:** conditional linear scoring over head/type choices, using role-specific blocks of POS, distances, direction, intervening VERB/SCONJ/CCONJ counts, subject POS and neighboring ADP/SCONJ cues. Fixed L2 0.01 and the previous conditional-softmax optimizer; no NONE choice at this stage because it conditions on an endpoint.

The learned model has 96 features and receives no words, lemmas, dependency edges or morphology annotations at inference. Fit uses correct source endpoints with their supervised head/type targets. Both scorers abstain on tied best choices. No extra confidence cutoff or endpoint reranking is introduced.

Two evaluation modes remain explicit: **oracle endpoint** supplies the true subject/carrier and measures head/type recovery; **pipeline** uses iteration 56's frozen carrier-trained/carrier-calibrated F1 endpoint predictions, including their mistakes. Only pipeline results are unanchored full-unit recovery.

## Pipeline results

An output is correct only if all subject, head, carrier and type fields match. A wrong head or type contributes both a false positive unit and a missed gold unit.

| Scope / scorer | Correct units | Wrong units | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Selected / prior + distance | 344 | 199 | 63.35% | 66.28% | 64.78% |
| Selected / learned | 346 | 202 | 63.14% | 66.67% | 64.85% |
| All source / prior + distance | 2,053 | 1,882 | 52.17% | 61.01% | 56.25% |
| All source / learned | 2,098 | 1,917 | 52.25% | 62.35% | 56.86% |

The learned scorer resolves ties left by the baseline, increasing output from 543 to 548 units in selected sentences and from 3,935 to 4,015 across source. Its aggregate gain is small. Selected-author F1 changes 66.13%→65.98% for Cicero and 58.51%→59.57% for Palladius, so it is not uniformly better.

For the learned pipeline on selected sentences, the 519 gold units break down into 346 exact units, 90 endpoint abstentions, 51 wrong endpoints and 32 correct endpoints with a wrong head/type. The frozen endpoint model correctly recovers 378/519 carrier links; the additional head/type requirement costs 32 of those successes.

| Gold kind | Selected gold | Correct endpoints | Exact units, distance | Exact units, learned |
|---|---:|---:|---:|---:|
| Direct | 470 | 339 | 323 | 325 |
| Copula | 32 | 24 | 7 | 7 |
| Auxiliary | 17 | 15 | 14 | 14 |

Thus learned scoring does not improve the selected copular units in the actual pipeline. Across source it improves exact copular units 236→259 out of 650, improves direct units 1,651→1,690 out of 2,423, but reduces auxiliary units 166→149 out of 292. These regressions matter despite the slightly higher overall F1.

## Conditional head/type diagnostic

With the true endpoint supplied, head/type recovery is:

| Scope / kind | Gold | Prior + distance exact | Learned exact |
|---|---:|---:|---:|
| Selected / all | 519 | 470 (90.56%) | 476 (91.71%) |
| Selected / direct | 470 | 445 | 450 |
| Selected / copula | 32 | 9 | 10 |
| Selected / auxiliary | 17 | 16 | 16 |
| All source / all | 3,365 | 2,816 (83.69%) | 2,870 (85.29%) |
| All source / direct | 2,423 | 2,294 | 2,343 |
| All source / copula | 650 | 287 | 316 |
| All source / auxiliary | 292 | 235 | 211 |

The selected auxiliary sample is especially easy relative to the full source; its 16/17 result does not generalize to all auxiliary units. Overall percentages are also dominated by the frequent direct class.

For learned copular predictions across source, 316 are exact, 143 have the correct type but wrong head, 59 the correct head but wrong type, and 132 both wrong. Of 650 true copular units, 107 are predicted direct and 84 auxiliary. The difficulty includes both identifying a copular unit and choosing its nonverbal head.

Further annotation-dependent masks isolate these components. Given the true copular type, learned scoring recovers 420/650 exact units; given the true head, it recovers 549/650. Selected-sentence figures are 17/32 and 24/32. These are additional **oracle diagnostics**, not inference inputs or restoration gains. Head selection remains difficult even when type is solved, so adding a type classifier alone will not finish the task.

## Decision and next proposal

Keep typed-unit evaluation and the simple prior + distance baseline. The learned POS/position scorer is an experimental alternative with only a small aggregate gain and an auxiliary regression; there is insufficient evidence to prefer its added complexity generally. Existing direct/carrier endpoint configurations remain intact.

The next focused diagnostic is **copular head localization**. Compare the true and competing heads by Case, ADP attachment, phrase membership and clause locality using source annotations only for auditing. Estimate which distinction offers head-selection headroom before training a new feature. Any later Case/agreement evidence should be learned or explicitly scoped: nominal predicates do not universally share subject gender/number, and hard morphological constraints need their own survival checks.

Current results restore only this limited typed predicate structure on readable Latin with supplied POS. They do not recover all dependency relations, coordination or encrypted Voynich grammar, and all evidence remains on reused development partitions.

## Artifacts and validation

Code: `src/voynich_smt/typed_predicate_units.py`, `benchmarks/grammar_typed_predicate_units_iteration57.py` and its `_audit` module. Models, domain checks, typed predictions and partial-oracle diagnostics are frozen under `experiments/results/grammar-restoration/iteration57/`. Existing output directories are rejected.

Validation verifies all 3,365 gold unit domains and performs 1,096 selected-pipeline inference checks after mutating words, lemmas, morphology and dependency annotations. Independent audit checks 20 hashes, refits five models, reselects five distance policies, replays 70,700 unit predictions and reproduces eight unit-metric groups plus all 64 previous endpoint-metric groups. Five new tests cover target tuples, annotation-independent candidates/features, non-oracle type choice, ties and conditional training/indexing; 64 relevant tests pass. All previous prediction fields remain unchanged. The 200-sentence reserve remains unscored and no prior target queries were scored.
