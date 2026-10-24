# Iteration 21: ablative participles versus nominal analyses

The explicit participial construction fills the representation gap for both `defensis sedibus` and `nisi uespere instante`. It does **not** distinguish the reference analysis from the competing nominal and attachment analyses. Local matching-analysis coverage improves, while the number of uniquely matching local analyses is unchanged. The next bottleneck is selection among represented alternatives.

## What changed

A new diagnostic module extends iteration 20's joint grammar with a bounded, two-token ablative participial clause: an N/PRON subject and a VPAR, in either order, jointly agreeing in case, number and gender. Wildcard gender is bound to a common value rather than independently accepted for each token. A separate arm permits prefixed `nisi`, explicitly read as a clause marker with a source ADV/CONJ reading. The clause contributes subject→participle, participle→predicate and, when present, marker→participle edges. It can attach to the supplied finite predicate or an infinitive; these alternatives are retained.

Three arms compare the frozen iteration 20 joint grammar, participles without the `nisi` frame, and participles with that frame. The baseline reproduces iteration 20's saved joint predictions exactly. The coordination and explicit `perd` valency additions remain in all arms. No old code or results were changed, no nominal homographs were removed, and the five oracle morphology additions remain a separate condition.

The new construction is deliberately small: two adjacent content tokens, with an optional adjacent prefix. It is not an unrestricted absolute-construction parser. One reading witness is retained per structural signature; signatures now include the new internal dependencies. Enumeration is capped at 256 signatures per unit, with truncation preventing a supported result. No natural condition hit this limit.

## Results

Primary condition: reference marker scopes with sentence boundaries hidden. There are 66 reference infinitives, with only 21 reference governors reachable in the original candidate pool. All counts below concern fixed construction interiors, not full clauses.

| Morphology | Grammar arm | Correct governor links retained | Reference links with a locally matching analysis | Reference links with a unique matching local analysis |
|---|---|---:|---:|---:|
| Dictionary | Baseline | 16 | 14 | 13 |
| Dictionary | Participles | 16 | 15 | 13 |
| Dictionary | Participles + nisi | 16 | 15 | 13 |
| Oracle missing readings | Baseline | 20 | 16 | 14 |
| Oracle missing readings | Participles | 20 | 17 | 14 |
| Oracle missing readings | Participles + nisi | 20 | 19 | 14 |

The added constructions change internal representation, not governor-link coverage. `nisi` contributes the two additional reference infinitives in the coordinated `conlocare/aperire` unit, conditional on the oracle reading of `aluearia`. Without that noun reading, lexical coverage still blocks the entire interval. The table's aggregate counts are identical under the four repeated scope/boundary conditions; these are not independent samples.

Evaluation loads source annotations separately from inference and compares the represented nominal/participial dependency edges, the `nisi` marker edge, and source POS plus nominal/participle case, gender and number compatibility. Nominal conjuncts inherit their coordinated nominal head's predicate. The explicit DET→ADJ and discourse/marker ADV→CONJ projections are allowed. This checks more than the governor link, but still omits full NP-internal trees, semantic adjunct labels, external arguments and complete clause structure. A match means a saved witness agrees with this bounded annotation projection; a mismatch does not by itself prove an alternative ungrammatical.

## The two motivating cases

**`possit defensis sedibus apricare`.** The new construction represents `sedibus → defensis → possit`, with ablative feminine plural agreement. There is one reference-matching structure among eight recorded structures for each of two lexical unit readings. The other analyses include nominal readings and attachment to the infinitive. The source representation is now available with the original dictionary, but remains unresolved. An agreeing participle used as a nominal modifier may also be a legitimate competing linguistic analysis; this diagnostic does not establish the treebank analysis as the only grammatical one.

**`ne c conlocare ne c aperire aluearia nisi uespere instante debemus`.** With oracle `aluearia` and the separately enabled marker frame, the coordinated unit contains one reference-matching structure among 27. Its edges are:

- `aluearia → conlocare` (object);
- `nisi → instante` (marker);
- `uespere → instante` (participial subject);
- `instante → debemus` (participial adjunct).

The competing structures vary object sharing, participial attachment, and nominal versus clausal interpretation. Participles alone cannot account for the marker as the source does. The singleton `aperire` unit still cannot match the complete local reference structure, because the annotated object belongs to `conlocare`, which that unit omits.

The earlier `sua praesentia` matrix-versus-infinitive attachment ambiguity is unchanged. No oracle annotation is used to select an analysis.

## Controlled checks

Eleven controls cover both subject/participle orders, number/gender/case mismatches, a non-participle adjective, `nisi`, an intervening finite predicate, an unknown subject, and the natural `defensis` pattern. The mismatches produce no participial-clause structures, although nominal homographs can still permit other covers. A separate test removes only the noun readings of `nisi`: the declared marker construction still works using its CONJ reading, so its success does not depend on the misleading genitive-noun interpretation.

The independent witness checker verifies source-reading membership, simultaneous agreement bindings, exact token accounting, internal subject/marker dependencies, permitted attachment sites, argument slots and required perception subjects. Corruption tests reject an incorrect number binding and a deleted subject edge. A truncation test verifies that incomplete enumeration cannot claim a unique attachment.

## Next step

The representation can now express both motivating reference structures. More permissive coverage rules alone will not select them. The useful next diagnostic is a **contrastive selection audit** on these fixed candidate structures: compare the reference-matching structure against its strongest nominal/attachment competitors and identify which contextual signals could distinguish them without dependency-oracle information. Treat genuinely ambiguous alternatives as unresolved, and distinguish coarse lexical-category decisions from adjunct attachment. Any learned selector should be evaluated on a newly separated development partition before the reserved holdout; this inspected set is suitable for debugging, not a generalization claim.

## Artifacts and validation

Artifacts: `experiments/results/grammar-restoration/iteration21/`. There are 1,584 natural conditions (66 streams × four scope/boundary conditions × two morphology conditions × three grammar arms) and 11 controlled cases. The validator replays all predictions, verifies exact baseline equivalence with iteration 20, independently checks 1,276 recorded structures, recomputes evaluation, checks pinned hashes and verifies disjointness from the 200 reserved sentences.

Run `.venv/bin/python -m benchmarks.grammar_participial_structures_iteration21_validate`. The relevant regression suite passes **207 tests**. No full relative-chain restoration was run, no firm ownership claims were made, and the 200 reserved sentences remain unscored.
