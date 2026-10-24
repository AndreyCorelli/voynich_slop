# Subject roles with supplied morphology — iteration 78

**Promising conditional result: correct morphology enables a useful selective subject-role policy.** Supplying POS raises subject-role F1 from23.66%to35.14%; supplying exact joint POS/Case/Number raises it to68.25%. A source-calibrated high-precision policy on the full-morphology arm selects34target positions,31correct (91.18%precision,28.97%recall), across24word types and28sentences.

This is an **oracle information diagnostic**, not inferred morphological restoration or a deployable high-precision parser. These reused target sentences are development evidence;34selected positions are a small sample. Grammatical restoration remains an independent success criterion, but its key morphology inputs are supplied here.

| Role evidence | F1 | Precision | Recall | Brier | Binary NLL |
|---|---:|---:|---:|---:|---:|
| Local inferred grammar | 23.66% | 16.60% | 41.12% | .07521 | .27564 |
| Correct POS + context | 35.14% | 24.29% | 63.55% | .06374 | .21328 |
| Correct POS + shuffled context | 29.44% | 18.77% | 68.22% | .07202 | .24986 |
| Correct POS + source prior | 28.65% | 16.83% | 96.26% | .07172 | .24275 |
| Correct POS/Case/Number + context | 68.25% | 69.23% | 67.29% | .04192 | .17662 |
| Correct POS/Case/Number + shuffle | 62.69% | 67.02% | 58.88% | .04732 | .19639 |
| Correct POS/Case/Number + prior | **68.66%** | 73.40% | 64.49% | .04269 | .17838 |

The last row matters: source morphology-conditioned role priors slightly beat context at the F1 policies. Much of the oracle gain comes from supplied morphology itself, not extra contextual discrimination. Context improves probability loss slightly versus that prior and enables a supported selective policy unavailable to the prior under the stated calibration rule.

## Frozen intervention

Use the iteration70joint dependency-role/POS/Case/Number model unchanged. For supplied-POS inference, zero labels with another POS and renormalize. For full morphology, zero labels whose exact joint profile differs and renormalize. Empty fields are exact categorical values, not wildcard matches. Unsupported profiles produce zero and remain counted. Reference dependency roles enter evaluation/calibration labels only; no reference subject identity enters conditioning.

Calibrate each arm on the same829source sentences/7,034content positions as77, disjoint from model fit. Select F1 thresholds on the fixed0.01grid, and a separate precision90 policy requiring at least20predictions and10word types. Freeze source predictions/policies before target predictions. The target remains1,273content positions/107reference nsubj roles from the same100declared Caesar sentences. Correct surrounding plaintext, sentence boundaries and content-position evaluation remain privileges. This does not recover predicate attachment or evaluate pronoun subjects outside the content cohort.

There is one unsupported source-calibration joint profile and zero unsupported target profiles; no examples are removed. No model refitting or target threshold selection occurs.

## Selective subject roles

The full-morphology/context precision90 threshold is0.88. On source calibration it selects155positions (140correct,15wrong;90.32%precision) across113types. On target:

| Source-calibrated high-precision arm | Correct | Wrong | Precision | Recall |
|---|---:|---:|---:|---:|
| Full morphology + context | 31 | 3 | 91.18% | 28.97% |
| Full morphology + shuffle | 10 | 2 | 83.33% | 9.35% |
| Full morphology + prior | — | — | No qualifying source policy | — |

The shuffled arm has its own source-selected threshold0.94, not the context threshold. All34context selections have noun nominative singular/plural profiles (17each). The result establishes conditional usefulness on this development material, not a guaranteed90%precision transfer rate. Local inference and POS-only arms have no qualifying source precision90 policy.

## Decision and next work

Preserve this as evidence that morphology is a substantial upstream limitation and that context can support selective grammatical-role restoration **when that morphology is right**. It does not prove morphology is the only bottleneck or that a different role model could not do better. Oracle conditioning is not an absolute information-theoretic ceiling.

Next isolate Case from Number with matched supplied-POS+Case and supplied-POS+Number controls. Then target the valuable morphology directly: a source-trained, separately calibrated nominative/other predictor using available contextual evidence rather than relying on the current many-class joint role/profile estimator. Keep source-only confidence/coverage calibration, prior/shuffle controls and uncertain readings. Do not propagate a guessed case as a certainty or adopt the oracle policy as actual restoration.

## Verification

All7,034calibration predictions/policies replay, and1,273target conditional probabilities independently replay by summing admitted role-label mass. Local predictions exactly match77; evaluation matches saved output. Fit/calibration disjointness and all prior input hashes are checked. Four new tests cover POS conditioning, joint-profile conditioning, unsupported profiles and exact empty fields; all43focused tests pass.

The grammar reserve and sealed lexical final test remain unscored; no new target annotations or dictionary search. Artifacts: `experiments/results/grammar-restoration/iteration78/`; runner and audit: `benchmarks/grammar_subject_morphology_oracle_iteration78*.py`.
