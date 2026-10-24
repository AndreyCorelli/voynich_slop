# Iteration 18: local infinitive construction interiors

The next bottleneck is coverage of constructions and morphology, rather than another ownership score. Local case and agreement can separate governors in controlled contrasts, but the natural screen loses correct analyses. It does not yet improve grammatical restoration.

We reused iteration 17's open-owner candidate units, adding an exact token cover of each unit's minimal interval. The screens are cumulative: no intervening supplied finite predicate; dictionary and permitted POS coverage; then typed nominal phrases, preposition government, subject agreement, declared object/argument licenses and an explicit accusative subject for perception. Coordination arguments must stay in their segment. Unknown owners remain available, and nearby unexplained nominal/nonfinite edges are recorded. A supported interior is neither a complete clause nor an entailed owner. Participles are outside this experiment's target grammar.

The only new lexical argument license is **nocere + dative**, manually declared; a dictionary-only ablation removes it. No training or scoring of the reserved 200 sentences was performed. All natural results use the previously inspected 66 development streams. Reference infinitives number 66; only 21 have their reference governor in the input candidate pool. The full reference inventory includes passive infinitives, whereas proposal eligibility requires a dictionary active infinitive reading.

## Results

Primary condition: reference marker scopes, sentence boundaries hidden. Counts describe infinitives with a single supported governor; unknown ownership is still possible.

| Screen | Reference governor retained / 66 | Correct / single supported governor |
|---|---:|---:|
| Input candidates | 21 | 15 / 16 |
| Nearest governor (ties retained) | 21 | 21 / 22 |
| Finite predicate barrier | 21 | 20 / 20 |
| Dictionary/POS cover | 16 | 16 / 16 |
| Typed argument cover | 14 | 14 / 14 |
| Typed, without new nocere license | 13 | 13 / 13 |

Of six cases with a reachable reference governor plus a distractor, the finite barrier resolves five and keeps the reference governor in all six. POS coverage resolves the remaining `instare` ambiguity by rejecting a span containing the unrecognized `transcurrere`, but also rejects the correct `fecundare` span. Thus its apparent discrimination is partly lexical incompleteness, not successful argument recognition. Typed roles resolve no additional natural ambiguity beyond POS coverage and reject two more correct candidates. Equal-distance synthetic cases establish that morphology can discriminate beyond proximity; this has not been demonstrated as a natural-data gain here.

With reference sentence boundaries, the finite barrier gives 21/21 single supported governors; typed support remains 14/14. Predicted marker scopes yield the same aggregate counts in both boundary conditions. These repeated conditions are not independent samples. No full relative→antecedent→predicate restoration was rerun, and no firm ownership claims were made.

## What fails

Five of the 21 reachable infinitives fail dictionary/POS coverage: `necare` (unknown `olerum`, `pulices`), `fecundare` (unknown `sua`), `fieri` (unknown `ferulis`), and both coordinated `conlocare`/`aperire` (unknown `aluearia`). These are missing readings in the pinned analyzer; they are not evidence that the corresponding constructions are ungrammatical. In particular, `creduntur enim sua praesentia fecundare` remains unresolved.

The two additional typed-cover failures expose missing construction rules: `potest et animam et corpus perdere` needs coordinated nominal arguments, whereas `possit defensis sedibus apricare` contains an ablative participial phrase that this bounded role inventory cannot explain. A successful adjacent `locare → debemus` fragment also leaves its external arguments unparsed. Selecting the shortest surviving fragment would therefore be misleading.

The next useful diagnostic is a **separate oracle-morphology ablation**: supply independently annotated readings only for the five blocked correct constructions and measure whether typed cover still fails. Keep baseline morphology frozen and report synthetic/oracle additions separately. Then add coordinated nominal phrases and ablative absolute/participial constructions with positive and negative contrasts. Requiring complete clause coverage should wait until these representations can express the actual clauses.

## Validation and artifacts

Fourteen controlled probes cover equal-distance number/case contrasts, retained ambiguity, modifier agreement, preposition government, perception subjects, finite barriers, unknown tokens, coordination argument placement, normalized `ne c`, and exposed nested edges. The validator replays 14 controls and 264 natural conditions from frozen morphology, checks 95 successful witnesses for source-reading membership, fixed readings, exact token accounting, role licenses, unique argument slots and required perception subjects, recomputes evaluation, verifies pinned inputs, and checks disjointness from the 200 reserved sentences. This witness checker checks local feasibility, not completeness of Latin grammar; phrase generation still uses iteration 15's bounded NP grammar.

Artifacts: `experiments/results/grammar-restoration/iteration18/`. Reproduce validation with `.venv/bin/python -m benchmarks.grammar_construction_spans_iteration18_validate`. Evaluation labels are loaded only by the separate evaluator. The combined relevant regression suite passes 143 tests.
