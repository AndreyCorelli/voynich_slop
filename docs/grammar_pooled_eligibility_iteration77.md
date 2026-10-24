# Pooled POS for grammatical eligibility — iteration 77

**Grammatical restoration is an independent objective, whether or not exact words can be identified.** This experiment tests whether the promising repeated-type POS evidence from76 yields reliable grammatical decisions. The result is mixed and insufficient for adoption: overall subject-role F1 improves slightly, but repeated-position F1 and nominative eligibility regress; no tested arm meets the source-calibration high-precision support requirement.

| Grammatical task / cohort | Local F1 | Pooled F1 | Pooled-shuffle F1 |
|---|---:|---:|---:|
| Subject role, all1,273content positions | 23.66% | 24.90% | 16.78% |
| Subject role,641repeated positions | 28.94% | 28.03% | 21.32% |
| Nominal nominative eligibility, all | 24.79% | 22.53% | 18.73% |
| Nominal nominative eligibility, repeated | 21.98% | 21.58% | 17.39% |

Overall subject-role pooling finds62correct subjects instead of44, but raises false positives221→329. Precision falls16.60%→15.86%; recall rises41.12%→57.94%. This is a threshold/recall tradeoff, not reliable subject restoration. On source calibration, pooled subject F1 is already slightly below local18.97%versus19.15%.

## Fixed intervention and calibration

Retain the iteration70joint dependency-role/POS/Case/Number model and iteration71source-word POS predictor. For each position, replace its POS marginal with the mean POS marginal across repeated occurrences of that word type, while preserving its local conditional distribution of role/Case/Number given POS. Roles and cases are not forced to be constant across a word's occurrences. A leave-current-occurrence-out arm uses the other occurrences, falling back to local for singletons. Prior and local/pooled shuffled-context arms provide controls.

Pooling uses **every token occurrence**, including function-word positions. Gold content labels select the evaluation cohort only. This removes76's content-only grouping privilege; the repeated evaluation cohort consequently has641positions rather than635. The model remains trained over content labels, so this is a content-position task, not unrestricted all-word parsing. Correct surrounding plaintext and sentence boundaries are still supplied.

Use the829sentences/7,034content positions in the existing source-fold0calibration split, disjoint from the frozen model's fit split. Each arm/task independently selects its F1 threshold on the fixed0.00–1.00grid in steps of0.01; ties prefer a higher threshold. Local/pooled subject thresholds are0.09/0.08, and nominative thresholds0.14/0.12. All policies are frozen before target predictions. No target threshold selection or refitting occurs.

A separate high-precision policy requires at least90%source-calibration precision,20predictions and10distinct word types. **No tested arm/task has a qualifying threshold.** This statement applies to the specified grid and support requirement; it is not a claim that high precision is impossible with another model or task.

## Task distinctions

The primary label is reference dependency role `nsubj`, evaluated on the previously declared1,273content positions (107positive). It is a subject-role decision, not a subject–predicate attachment or full grammatical-unit reconstruction. Pronoun and other noncontent positions are outside this evaluation.

The secondary label is membership in NOUN/PROPN/ADJ with an explicitly annotated nominative Case (123positive). It measures reference morphological eligibility, not actual subjecthood; absent Case does not count as an explicitly annotated nominative. Its labels, probabilities and scores are reported separately.

Soft probability quality improves a little: overall subject Brier score0.07521→0.07377, nominative0.08498→0.08482(lower is better). On repeated positions, subject Brier0.09299→0.09013. These are useful diagnostics but do not offset low precision or establish calibrated structural restoration. The other-occurrences-only arm has overall subject F1 21.57%, below local23.66%.

## Decision and next diagnostic

Do not adopt this role/eligibility addition. Preserve74's direct contextual-prediction signal and76's promising pooled soft-POS classification result without extrapolating them to reliable roles. The task remains grammatical restoration; exact word identity is not its success criterion.

Next, estimate the **subject-role information ceiling of the current features**: compare local inference with explicit oracle POS, then oracle joint POS/Case/Number, while keeping role prediction and source-only calibration separate. If correct morphology still does not resolve subject roles, richer clause/attachment information is needed; another POS pooling variant is unlikely to address that bottleneck. In parallel, any future claim of solid POS restoration should report source-calibrated confidence, coverage and transfer performance, not only average accuracy. These follow-ups remain untested.

## Verification

All7,034source-calibration and1,273target predictions and policies replay. Replacing every target center annotation with arbitrary POS/role/Case labels leaves inference scores unchanged, demonstrating that annotations affect evaluation rather than pooling/scoring. Fit/calibration disjointness is checked; audit verifies1,551prior manifest input hashes. Five new tests cover conditional-preserving reweighting, leave-current-out pooling, token-specific role retention and calibration support/thresholds; all39focused tests pass.

No new target grammar queries, reserve scoring, sealed lexical final-test scoring or dictionary search occurs. The target is the same reused100Caesar sentences; these are development diagnostics, not independent confirmation.

Artifacts: `experiments/results/grammar-restoration/iteration77/`; code: `src/voynich_smt/pooled_grammar.py` and `benchmarks/grammar_pooled_eligibility_iteration77*.py`.
