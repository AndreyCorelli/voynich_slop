# Iteration 166: conditional case agreement is a grammatical signal worth preserving

**Positive, limited finding:** on the fixed two-frame Cicero relations, conditional case agreement reaches72.22% under the predeclared edge/frame-macro metric, above every frequency-preserving shuffle control (maximum50%, mean24.06%). This is stronger than the corresponding50.64% occurrence-POS agreement. It suggests a possible morphological compatibility input, not recovery of named cases, identification of case-bearing positions, or general grammatical restoration.

The exact frame graph from164 and occurrence descriptors from165 were retained: types>=5 occurrences, primary>=2 distinct shared frames, secondary>=1. No case labels select edges. Only the reference field changes to actual cached occurrence case. Recognized values were frozen as Nom/Gen/Dat/Acc/Abl/Voc/Loc; missing, ambiguous or other values never count as matches. Existing caches contain no nonempty unrecognized case values in these sets.

Within each edge/frame, all Cartesian occurrence pairs with both cases recognized are compared. Eligible pairs are averaged within frame, eligible frames equally within edge, and covered edges equally for the primary metric. Applicability among all original edges, frames and occurrence pairs is mandatory. Cases travel with their tokens through the exact16 word-shuffle permutations. Case inputs were frozen before comparisons, all comparison details before aggregate/null metrics. No fitting, new annotations, reserved material or sealed works were used.

| Cicero primary result | Value |
|---|---|
| Original inferred edges | 52 |
| Edges with comparable cases | 18/52 (34.62%) |
| Frames with comparable cases | 48/124 (38.71%) |
| Comparable occurrence pairs | 73/187 (39.04%) |
| Edge/frame-macro agreement (primary) | 72.22% |
| Pooled occurrence agreement (secondary) | 60/73 (82.19%) |
| Covered edges with no case conflicts | 10/18 (55.56%) |
| Supported types in case comparisons | 21/588 (3.57%) |
| Nonempty case-bearing nulls | 16/16 |
| Null primary agreement mean / maximum | 24.06% / 50.00% |

The82.19% pooled value gives more weight to repeated contexts and is not promoted over the primary72.22%. The10 conflict-free edges are evaluation-revealed and cannot be selected at inference using gold labels. Likewise, selecting the18 case-bearing edges requires reference knowledge; a decoder could apply a conditional compatibility score when its lexical candidates carry case, but this experiment does not supply an automatic case-bearing-position detector.

The three short texts have no primary edges and therefore no case comparisons. In the one-frame secondary results, Caesar's one edge, Jerome's two and Palladius's one contain no paired recognized cases. They remain unscored, not failures interpreted as agreement or evidence of cross-author replication.

Cicero's one-frame secondary graph has284/863 case-comparable edges and50.70% primary-style conditional agreement; pooled agreement is226/382 (59.16%). It exceeds all16 nulls (maximum30.40%) but is less precise than the fixed two-frame rule. No support threshold was changed to favor these outcomes.

Case annotations are available on873/1514 Caesar tokens,427/913 Jerome,9777/20136 Cicero and409/737 Palladius. The absence of short-text frame comparisons therefore is not simply absence of annotated case in the corpus. The current repeated-word/support filters and exact contexts restrict coverage sharply. All recognized and missing labels are retained in the inventory.

This is one long reused development text, a small correlated relation set and a reference-conditioned evaluation. It does not justify a universal72% constraint or a Voynich application yet. Nevertheless, equality of latent case at shared structural slots is a different possible deciphering input from lexical nuclei or POS naming, and merits preservation independently of the unsuccessful POS-equality rule.

Next proposed coverage check: lower only the word-type occurrence floor from5 to2, retaining the two-distinct-frame primary support and all original controls. Two is the logical minimum for a type to occupy two distinct frames; rare inflected forms may be excluded by the old floor. Freeze both arms and compare all four datasets, exact applicability denominators, case agreement and the same count-preserving nulls without selecting a favorable author or threshold. This tests coverage, not a claim that rare forms are inherently reliable.

Independent verification rebuilt all case inventories and directly enumerated Cartesian comparisons on every frozen descriptor, checked every applicability denominator, and replayed68 views,16,747 edge records,18,330 occurrence pairs and136 metric groups. Missing case never contributed agreement and all label permutations were verified. Artifacts and manifest: `experiments/results/grammar-restoration/iteration166/`.
