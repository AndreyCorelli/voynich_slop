# Exact source-calibration cutoffs for fixed anchor detector — iteration 94

**Finding: a finer source-only cutoff enables limited wrong-class detection, but sensitivity and direction coverage are inadequate for PP integration.** It flags one wrong assignment in each of the four unseen source swaps; misses remain, transfer is uneven, and clean source has one false alarm. Preserve this narrow signal without claiming recovered mappings.

## Separate refinement

Iteration93 is preserved unchanged: its coarse grid selected OFF for every arm. This refinement was motivated by the source-calibration gap between clean maximum disagreement0.273 and wrong-in disagreement0.469. It changes only the cutoff grid to all attainable supported nonnegative source-calibration scores, plus0 andOFF. Exact scores enumerate attainable decision sets; no source-test or author scores select a cutoff.

Keep all fixed93 models, features, whole-type masking, occurrence pooling, support requirements, class labels, tie rules and false-alarm guards unchanged. Calibrate each arm on source-calibration clean and known in/et only. Require no more than one clean false-flagged type and no more than5% clean candidate occurrences flagged; maximize known-error detections, then minimize corrupted false flags, clean flagged tokens, and choose the higher cutoff. Freeze all five policies before applying them to cached evaluation records.

The context cutoff is0.4686615669173992. It detects the wrong CCONJ assignment to in on calibration, with zero clean false alarms and no corrupted false alarms; it misses the wrong ADP assignment to et. Prior and all three permutation controls still selectOFF. These calibration limits are empirical, not statistical transfer guarantees.

All evaluation scores were already computed in93; the new policy is applied without recomputing features, fitting or changing scores. This is adaptive development on previously evaluated source and cached author sets, not fresh independent confirmation. Error labels compare proposed classes with original supplied source-modal classes, not token-level target POS. Same-class identity swaps are negative controls for this class-only task.

## Frozen evaluation

| Dataset | Scenario | Detected / present wrong-class types | False-flagged correct types | True flags | False flags | Missed errors |
|---|---|---:|---:|---|---|---|
| source | correct | 0 / 0 | 1 | — | atque | — |
| source | rehearsed_in_et | 0 / 2 | 1 | — | atque | et, in |
| source | unseen_ad_que | 1 / 2 | 0 | ad | — | que |
| source | unseen_ad_sed | 1 / 2 | 0 | ad | — | sed |
| source | unseen_de_que | 1 / 2 | 1 | de | atque | que |
| source | unseen_de_sed | 1 / 2 | 0 | de | — | sed |
| source | same_adp | 0 / 0 | 1 | — | atque | — |
| source | same_conjunction | 0 / 0 | 0 | — | — | — |
| Jerome | correct | 0 / 0 | 0 | — | — | — |
| Jerome | rehearsed_in_et | 0 / 2 | 0 | — | — | et, in |
| Jerome | unseen_ad_que | 1 / 1 | 0 | ad | — | — |
| Jerome | unseen_ad_sed | 1 / 2 | 0 | ad | — | sed |
| Jerome | unseen_de_que | 1 / 1 | 0 | de | — | — |
| Jerome | unseen_de_sed | 1 / 2 | 0 | de | — | sed |
| Jerome | same_adp | 0 / 0 | 0 | — | — | — |
| Jerome | same_conjunction | 0 / 0 | 0 | — | — | — |
| Caesar | correct | 0 / 0 | 0 | — | — | — |
| Caesar | rehearsed_in_et | 1 / 2 | 0 | et | — | in |
| Caesar | unseen_ad_que | 0 / 2 | 0 | — | — | ad, que |
| Caesar | unseen_ad_sed | 0 / 2 | 0 | — | — | ad, sed |
| Caesar | unseen_de_que | 1 / 2 | 0 | de | — | que |
| Caesar | unseen_de_sed | 0 / 2 | 0 | — | — | de, sed |
| Caesar | same_adp | 0 / 0 | 0 | — | — | — |
| Caesar | same_conjunction | 0 / 0 | 0 | — | — | — |

Clean source flags atque incorrectly (one of16 present/supported types); Jerome and Caesar have zero clean false alarms. Only5Jerome and10Caesar candidate types meet the five-occurrence/three-sentence support requirement, versus16source. Absent types are not counted as detected errors; present unsupported errors remain misses.

Each unseen source swap detects ad or de presented as a conjunction and misses que or sed presented as a preposition. The de/que scenario also incorrectly flags atque. Jerome detects ad/de in every unseen swap, but que is absent and sed is unsupported, so apparent one-out-of-one successes must not be read as two-endpoint recovery. Caesar detects only de in the de/que scenario; sed is unsupported in its two scenarios. The four repeated pair probes are correlated and their eight erroneous assignments are not eight independent observations.

The known in/et calibration success does not persist uniformly: source detects neither and falsely flags atque; Jerome detects neither; Caesar detects et but misses in. This adds a clear sensitivity/generalization limitation beyond the coarse-grid failure. Every prior/permutation arm remainsOFF across all evaluation scenarios. The context result exceeds those inactive controls in sensitivity but is not a validated high-precision detector.

## Decision and next hypothesis

Do not hide, correct or use flagged mappings automatically in PP inference. A class flag is not a correct lexical mapping, and the usually missed conjunction-as-preposition direction is especially relevant to false PP assignments. Preserve the masked-class discrimination result92 and this limited detection result alongside the failed generalization cases.

Next check a paired class-consistency score: enumerate all proposed ADP/CCONJ pairs, compare their contextual likelihood under the current and exchanged class assignments, and source-calibrate abstention without revealing which pair was corrupted. A relative pair score may exploit the separation between classes even when neither endpoint has a decisive independent margin. Include correct-data false pair alarms and same-class controls. This would be restricted to bijective class-swap hypotheses; it would not establish recovery under arbitrary missing or non-bijective mappings. The next experiment is proposed, not tested.

Validation: all five policy selections, all24 scenarios and named flag details replayed; frozen93 input hashes checked; false-alarm guards unchanged; 2,534 prior frozen input hashes verified;94 focused tests passed across the shared helpers. No PP integration, mapping correction, lexical recovery, new annotations, reserve or sealed-test evaluation. Artifacts: experiments/results/grammar-restoration/iteration94/.
