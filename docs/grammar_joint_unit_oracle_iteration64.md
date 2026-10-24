# Iteration 64: joint-triple feasibility before building a decoder

The proposed shared-head/role-exclusivity constraints do not provide useful additional copular discrimination. Shared-carrier head agreement preserves every gold unit, but there are only **four** gold carrier groups with multiple subjects, **none copular**. It eliminates **zero of the 479** baseline copular outrankers at true endpoints. With predicted endpoints, enforcing shared heads lowers full-source exact-unit F1 from **56.86% to 55.99%**.

This rejects the tested restricted decoder with mandatory frozen subject assignments. It does **not** reject joint selection of subjects, carriers and NONE, or a complete sentence parse. The results identify a reason those are different problems: every one of the 608 predicted multi-subject carrier groups contains a wrong endpoint assignment.

## Design

The experiment reuses the same 4,070 source sentences, five frozen iteration-57 models, 3,365 gold units (519 selected), candidate domains and iteration-56 endpoints. There is no fitting, calibration, candidate injection, score modification or test-selected policy. The carrier-ambiguous frame is excluded from joint groups and evaluation.

For each sentence, enumerate subject/head/carrier/type candidates and retain their frozen logits. Independent decoding reproduces iteration 57. Shared decoding groups active subjects by carrier, intersects their allowed `(head,type)` domains, and maximizes the sum of logits for one common choice. This is exact for this restricted constraint system; with mandatory frames the softmax normalizers are constants. Empty intersections or tied maxima abstain for the entire group. There is no new NONE score and no subject/carrier reassignment.

Fixed diagnostic arms separate:

- Shared head/type for subjects assigned to one carrier. This uses no additional annotations.
- Predicate-head exclusion when that token is another active subject, globally or within the same gold clause. The global version uses only active assignments; clause scoping is an oracle.
- A gold-role version using nominal source nsubj labels, including subtypes, within the same gold clause.
- The previous gold phrase/clause masks, alone and with joint constraints, to measure incremental benefit over the known unary oracle.
- Strict versus coordination-permissive subject–carrier Number/Person agreement, and copular ADJ-head Number/Gender/Case agreement. Noun predicates are not required to agree. Unknown morphology passes; nominal NOUN/PROPN subjects default to third person when Person is absent.
- A full oracle combination.

Coordination uses gold conjunction components. The permissive rule retains root alternatives, adds plural and a highest-priority known person alternative, and suppresses gender restrictions for coordinated subjects. It does not implement complete Latin agreement resolution. A one-subject-per-carrier cap is **audited but not imposed**.

Except baseline/shared/global-assigned-role arms, these rules use extra gold morphology or parse information. Their pipeline results remain oracle diagnostics even when the carrier endpoints are predicted. True-endpoint and true-type results are labeled separately.

## Gold compatibility and actual opportunity

| Constraint | Gold units retained / 3,365 | Copular units retained / 650 | Copular outrankers blocked while preserving gold / 479 |
|---|---:|---:|---:|
| Shared head/type | 3,365 | 650 | 0 |
| Active-subject exclusion, global | 3,363 | 648 | 7 |
| Active-subject exclusion, gold clause | 3,363 | 648 | 0 |
| Gold-subject exclusion, gold clause | 3,362 | 647 | 2 |
| Unary phrase/clause oracle | 3,364 | 649 | 312 |
| Unary + active-clause/shared constraints | 3,362 | 647 | 311 |
| Subject–carrier agreement, strict | 3,297 | 643 | 0 |
| Subject–carrier agreement, coordination-permissive | 3,314 | 646 | 0 |
| ADJ-head agreement, strict | 3,351 | 636 | 60 |
| ADJ-head agreement, coordination-permissive | 3,353 | 638 | 60 |
| Full oracle combination | 3,298 | 630 | 312 |

Candidate counts are comparisons, not separate sentence errors. Subject–carrier agreement is constant across heads when endpoints are supplied; it can reject an endpoint pair but cannot select its head. Its blocked outrankers occur in frames where it also excludes gold, hence zero in the preserving-gold column.

The gold set has 3,361 carrier groups, four with two subjects each, zero shared-head/type conflicts, and 122 units whose subject belongs to a conjunction component. None of the four multiple-subject groups is a single conjunction component, so adding only a coordination exception would not make a one-subject cap preserve the targets. Shared-head agreement is compatible but almost uninformative. Role exclusion is neither perfectly target-compatible nor effective against the hard alternatives.

## Frozen predicted endpoints

| Arm | Full-source correct units | Full-source F1 | Selected correct units | Selected F1 |
|---|---:|---:|---:|---:|
| Independent baseline | 2,098 | 56.86% | 346 | 64.85% |
| Shared head/type | 2,066 | 55.99% | 344 | 64.48% |
| Shared + active-subject exclusion in gold clause | 2,065 | 55.96% | 344 | 64.48% |
| Unary phrase/clause oracle | 2,167 | 58.73% | 356 | 66.73% |
| Unary + active-clause/shared constraints | 2,123 | 57.53% | 354 | 66.35% |
| Subject–carrier agreement, coordination-permissive | 2,073 | 57.88% | 342 | 66.02% |
| ADJ-head agreement, coordination-permissive | 2,098 | 56.86% | 345 | 64.67% |
| Full oracle combination | 2,026 | 57.20% | 338 | 66.14% |

All non-SV arms above emit 4,015 source predictions; subject–carrier and full-oracle arms emit 3,798 and 3,719 respectively. Agreement's F1 increases come partly from removing predictions, while correct recovery decreases. They are not improvements in restored grammatical coverage.

There are 608 predicted multi-subject carrier groups versus four in gold. **All 608 contain at least one endpoint error** under the frozen task labels. Shared decoding changes 157 predictions, gaining 12 exact units but losing 44. Adding it and clause-scoped role exclusion to the unary oracle loses 44 net exact units relative to unary alone. Making every noisy subject assignment mandatory propagates errors instead of resolving which subjects belong.

## True-endpoint localization

With true subject/carrier endpoints and unknown type, shared decoding recovers 2,872/3,365 versus 2,870 independently, but copular recovery remains 316/650. Unary phrase/clause yields 347 copular units; the added joint constraints leave that at 347. With true type supplied, copular head recovery is 420 independently, 420 shared, 523 unary and 521 unary plus joint constraints. Thus even the easier oracle conditions show no useful incremental copular benefit from these particular joint rules.

## What the counterexamples mean

`iteration64b/counterexamples.json` preserves the three gold-role exclusions and twelve coordination-permissive adjective exclusions, including source tokens and features. They are diagnostic cases, not a manually corrected evaluation set.

For example, source sentence 76543 contains `nos ... in formiano erimus`: the task records an ADJ-tagged, ablative singular head inside an ADP-marked phrase, with a plural subject/carrier. The ADJ tag alone does not establish that this head must agree with the subject. Three of the twelve rejected ADJ heads are in ADP-marked phrases. Other cases include surprising source tags or relations; the role exclusions include heads themselves labeled nsubj, and the existing clause-anchor function can merge nested predications. These observations require distinguishing target heterogeneity, annotation problems and scope limitations. They are not evidence that every conflicting annotation is wrong, or that agreement has no grammatical value.

Do not turn these checks into universal hard constraints. A predicate-complement classification or a label-quality audit would need to precede stronger agreement claims. No labels were rewritten here.

## Correction, reproducibility and decision

The initial iteration-64 coordination rule accidentally converted unknown Number/Person into constrained values when adding coordination alternatives. That violated its intended permissiveness. The original code, freezes and outputs remain preserved. The corrected run uses `joint_unit_oracle_v2.py` and `iteration64b/`; all tables above use that run. Unknown values remain unrestricted. Tests and a full comparison verify monotone coordination masks and 583,275 unchanged non-coordination decisions. Only three saved pipeline decisions differ between the initial and corrected runs; no thresholds, models or scores were tuned.

Both runs have independent replay audits: each replays 103,320 active decisions, 47,110 true-type decisions, 47,110 feasibility records and 151,648 candidate checks, preserving old prediction fields and recomputing evaluation. **103 relevant tests pass.** Initial and corrected artifacts have separate design/prediction freezes and verification manifests. The proposal tracker records the experiment and its limits.

Keep the independent baseline. Do not build a larger mandatory shared-head decoder on this evidence. If pursuing joint inference, the next distinct question is whether competing subject assignments can be selected **with a NONE alternative**, rather than holding all predicted endpoints active. Multiple subjects must remain possible; the gold set already disproves an unconditional one-subject cap. That experiment remains untested and should not be described as a consequence-free fix.

All results reuse development source data with POS available. The 200-sentence reserve remains unscored and no prior target queries were scored. This is a structural diagnostic, not evidence of Voynich restoration.
