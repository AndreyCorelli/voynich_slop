# Iteration 19: oracle morphology for blocked construction interiors

Supplying the missing morphology recovers **two of five lexically blocked infinitive-governor links**. Typed support increases from 14 to 16 correct links, out of 66 reference infinitives. All 21 reference links reachable in the frozen candidate pool now pass lexical/POS coverage, but five still fail typed coverage. This is an oracle diagnostic on previously inspected development, not an improvement to deployable morphology or full grammatical restoration.

## Intervention

We kept iteration 18's candidate units, finite predicates, marker scopes, sentence-boundary conditions, infinitive/governor readings and construction grammar fixed. Five absent token readings were supplied from the pinned PROIEL annotations:

| Stream:position | Token | Added reading |
|---|---|---|
| 34:42 | olerum | noun, genitive neuter plural |
| 34:43 | pulices | noun, accusative masculine plural |
| 49:2 | sua | adjective, ablative feminine singular |
| 56:34 | ferulis | noun, ablative feminine plural |
| 61:14 | aluearia | noun, accusative neuter plural |

The source tags `sua` as DET; the explicit adapter projection uses ADJ, which the existing modifier grammar supports. Only POS, case, gender and number enter recognition. Dependency heads, relations and reference governors do not. Readings are additive and restricted to the four affected streams; each affected word occurs exactly once in its stream. No existing ambiguity is removed, and the production dictionary remains unchanged. The selected tokens were identified by the prior failure audit, so the intervention deliberately uses oracle information.

## Results

Primary condition: reference marker scopes, sentence boundaries hidden. Numbers count reference governor links retained; single supported governors remain conditional because unknown ownership is available.

| Screen | Original morphology | Missing readings supplied |
|---|---:|---:|
| Input candidate pool | 21 / 66 | 21 / 66 |
| Finite barrier | 21 / 66 | 21 / 66 |
| Dictionary/POS cover | 16 / 66 | 21 / 66 |
| Typed construction cover | 14 / 66 | 16 / 66 |

All 16 single supported governors in the oracle typed arm match the reference. The six initially ambiguous reachable cases now all have their reference governor as the sole supported candidate, compared with five before this intervention. The aggregate retained-link counts are unchanged across the four scope/boundary conditions; these are repeated conditions, not independent samples. The nearest-governor baseline from iteration 18 already retained all 21 reachable correct governors, so this experiment does not establish a recovery gain over proximity.

- `olerum pulices necare`: both added noun readings are needed to recover `necare → fertur`; the grammar builds a genitive modifier plus accusative object.
- `sua praesentia fecundare`: the added modifier reading recovers `fecundare → creduntur`, but **its internal role witness is wrong**. The recognizer licenses the ablative phrase as an instrument of passive `creduntur` (position 0); the source attaches it to `fecundare` (position 4). Correct owner selection therefore overstates grammatical recovery here.
- `possunt tamen et ferulis fieri`: the new noun reading removes the lexical block but leaves `no_role_cover`. Inspection identifies at least two missing mechanisms: discourse/additive `et` (dictionary CONJ, source ADV) and a bare ablative material phrase with `fieri` (dictionary active SEMIDEP; source passive). This experiment does not isolate their individual causal contributions.
- `ne c conlocare ne c aperire aluearia nisi uespere instante debemus`: the new object reading lets the coordinated unit pass POS coverage, but typed cover still fails. The grammar lacks the exceptional `nisi` participial construction and a suitable ablative-phrase role. The source attaches the post-coordinate object to the first infinitive, whereas the current segment rule assigns such a phrase to the second. That is another representation limitation even if the interval could be covered.

The other two already known typed failures remain unchanged: coordinated `et animam et corpus` with `perdere`, and ablative participial `defensis sedibus` with `apricare`. Thus **five reachable links now expose grammar failures**, while 45 of the 66 reference infinitives still lack their correct governor in the original candidate pool. This ablation does not address that larger retrieval/frame inventory problem.

Five leave-one-reading-out experiments verify necessity: removing either `olerum` or `pulices`, or removing `sua`, lowers supported correct links from 16 to 15. Removing `ferulis` or `aluearia` leaves typed support at 16, while restoring their lexical blockage. Candidate pools and the finite-barrier results remain unchanged throughout.

## Next diagnostic

Prioritize a small **argument attachment and coordination diagnostic** over another owner score: support coordinated accusative nominal arguments with explicit shared versus separate object representations, and judge the entire argument structure rather than just the infinitive's governor. Then test ablative adjunct/material/participial constructions and `et`/`nisi` functions in separate ablations, including case/agreement mismatches and false-attachment contrasts. The `sua praesentia` example should be a negative control for accepting the wrong attachment merely because the owner is correct. Keep oracle readings explicitly separate until a real morphology repair is independently justified.

## Reproduction and validation

Artifacts are in `experiments/results/grammar-restoration/iteration19/`, including added readings with source provenance, 264 natural conditions, 1,320 leave-one-out conditions, evaluation and a per-construction audit. The validator checks pinned input hashes, rederives the oracle readings, replays all conditions, verifies monotonicity and unchanged unaffected streams, checks 84 successful local witnesses using iteration 18's independent accounting/role checker, and recomputes the metrics. These witness checks establish feasibility under the implemented grammar, not correctness of its linguistic role inventory.

Run `.venv/bin/python -m benchmarks.grammar_oracle_morphology_iteration19_validate`. The relevant regression suite passes 154 tests. The 200 reserved source sentences remain unscored. No full relative-chain restoration or complete-clause parsing experiment was run.
