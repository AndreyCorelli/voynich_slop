# Iteration 58: what distinguishes copular heads?

The audit favors **phrase-role evidence**, with clause structure as a second source of headroom. Hard nominative or preposition exclusions are harmful. With correct copular endpoints/type supplied, the frozen learned scorer recovers 420/650 heads; a gold nominal-dependent mask raises this to 479, and adding gold clause locality raises it to 523. These are oracle diagnostics, not restoration gains or new inference rules.

Type selection remains consequential: when the true type is withheld, the same phrase + clause masks improve exact units only 316→347/650. In the selected pipeline-reachable subset, they leave exact recovery at seven. Head-locality evidence alone therefore does not solve the current pipeline.

## Frozen diagnostic design

Reuse iteration 57's models, candidate domains, linear scores and distance baseline without fitting or recalibration. Audit the same 650 gold copular units, including 32 selected-sentence units. Correct subject/carrier positions are supplied throughout. In `cop_type` mode, additionally reveal the true type; `free_type` retains direct/cop/aux competition.

Four annotation-dependent cues are evaluated in all 16 combinations:

- **Case:** permit Nom, ambiguity containing Nom, or missing Case; exclude known other cases.
- **ADP phrase:** exclude heads bearing a case-ADP child, including membership reached through nominal-dependent paths.
- **Phrase role:** exclude tokens with relations `amod`, `det`, `nmod`, `appos`, `flat`, `fixed`, `compound` or `case`.
- **Clause locality:** require the head and carrier to share a gold clause anchor. Roots, clausal dependency relations and finite/copular conjuncts delimit anchors; cycles/unknown anchors remain permissive.

Masks remove candidates, never add heads or recompute scores. They apply consistently to every candidate head; type filtering is a separate explicit condition. The carrier-correct subsets contain 509 source units and 24 selected units, revealed only for diagnostic attribution. All earlier endpoint and unit outputs remain unchanged.

Clause anchoring follows the annotated carrier dependency toward its actual head. This can directly encode part of the desired attachment. Its strong survival is not independent evidence that observable conjunction markers alone can provide the same information. Phrase membership also requires a parse at present; neither is a ready-made input to restoration.

## Main results

All-source learned-scoring results on the same 650 gold copular endpoint units:

| Oracle mask | Genuine heads retained | Exact, true type supplied | Exact, type unknown |
|---|---:|---:|---:|
| None | 650 | 420 | 316 |
| Case | 480 | 370 | 256 |
| ADP phrase | 546 | 377 | 277 |
| Phrase role | 649 | 479 | 337 |
| Clause locality | 650 | 449 | 326 |
| Phrase + clause | 649 | 523 | 347 |
| All four cues | 476 | 420 | 269 |

The phrase mask adds 60 correct head outcomes and removes one. Clause locality adds 29 and removes none. Their combination adds 104 and removes one. Case adds 51 but removes 101 previously correct outcomes; ADP phrase adds 16 and removes 59. All four together merely exchange 102 correct outcomes for 102 others when type is supplied, while degrading type-unknown results. Aggregating every apparently useful constraint is not justified.

On the 32 selected units, type-supplied recovery changes 17→19 with phrase role, 17→20 with clause locality and 17→24 with both. Type-unknown recovery changes 10→11 with the combined mask. Case preserves only 21 genuine selected heads, and ADP phrase only 27.

Phrase + clause improvements also occur in the two source authors: type-supplied exact heads change 398→495/617 for Cicero and 22→28/33 for Palladius. These are descriptive contrasts on reused source partitions, not independent confirmation or evidence of statistical reliability.

## Why the morphological exclusions fail

Gold copular head Case annotations are Nom 445, Abl 105, Gen 41, Acc 14, Dat ten and missing 35. Thus 170/650 genuine targets have known non-Nom Case. An ADP-phrase exclusion removes 104 genuine targets. These heads are part of the current annotation-derived predicate-unit task, including prepositional and non-nominative predicates; no annotation was changed to rescue the proposed masks.

For example, sentence 76841 has *modi* annotated Gen as the copular head in *eius modi sunt ii*. Sentence 76012 has the Abl head *utro* with a preposition. Their presence rules out a universal nominative-only or non-prepositional condition for this task.

The phrase-role mask has one genuine exclusion: *titus* in sentence 77696 is annotated `flat` and still serves as the subject's copular governor. This is recorded rather than overridden. Phrase-role evidence should therefore also begin as a soft score, not a universal deletion rule.

## Competing-head evidence

Across the 650 type-supplied units, there are 10,182 wrong copular head candidates, of which 479 strictly outscore the gold head. Phrase-role evidence blocks 193 of these while preserving the corresponding gold head; clause locality blocks 145. Case blocks 220, but only 158 when its own gold head survives; ADP blocks 96, only 64 with gold survival. Counts overlap and several competitors may belong to one unit, so they are not counts of recoverable constructions.

Of 230 baseline learned wrong/tied head outcomes with true type supplied, 104 chosen wrong heads fail phrase eligibility and 49 fail clause locality. Case rejects 118 wrong heads but also the genuine heads noted above. This explains why a cue can look discriminative among distractors while degrading restoration under hard masking.

In the 509 cases with a correct frozen pipeline endpoint, phrase + clause changes type-supplied head recovery 339→422, but type-unknown recovery only 259→277. For the selected reachable subset of 24, these are 12→17 and seven→seven. Both head selection and carrier type evidence are needed before expecting a substantial pipeline gain. These reachable-subset counts still use oracle correctness/type information and are not full-pipeline performance.

## Decision and next proposal

Do not introduce hard Case, ADP or phrase filters. Keep iteration 57's observable-feature baseline and typed-unit evaluation unchanged.

The next test is a **source-trained dependency-role proxy** using annotations from all fit tokens, rather than only overt-subject predicate units. Predict nominal-dependent versus cop/aux/other role probabilities from observable local context, then use them as soft head/type score evidence. A head's dependent probability can penalize phrase-internal distractors; carrier cop/aux probabilities address the type bottleneck that head masks leave behind. Keep the existing head scores frozen initially and choose added weights on calibration sentences, including zero as the baseline. No gold relation is available at inference, and all unit kinds/regressions must remain visible.

This is a proposed modification, not tested here. Its value depends on how well observable context predicts the oracle roles. The clause-locality oracle has additional headroom but is more circular, so it should not be treated as the first deployable feature. Morphology can remain soft evidence in later models without imposing the failed universal Case restrictions.

## Artifacts and verification

Code: `src/voynich_smt/copular_head_oracle.py`, `benchmarks/grammar_copular_head_oracle_iteration58.py` and its `_audit` module. Artifacts under `experiments/results/grammar-restoration/iteration58/` contain all cue combinations, candidate scores/flags, excluded genuine-head examples and paired changes. The output directory is protected against overwriting; a failed initial JSON-serialization run was preserved separately and rerun after converting a NumPy counter flag to a native bool, without changing the diagnostic design.

Independent validation checks 14 hashes, replays 1,300 frozen score decisions and 41,600 oracle-mask predictions, and reproduces all 384 accuracy groups. Five new tests cover Case ambiguity, PP modifiers, clause attachment dependence, cycles and factorial/type masks; 69 relevant tests pass. Earlier models and predictions remain intact, no new model is fitted, the 200-sentence reserve remains unscored and no prior target queries were scored.
