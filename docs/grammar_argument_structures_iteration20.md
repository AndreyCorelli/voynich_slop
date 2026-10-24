# Iteration 20: coordinated objects and argument attachment

The coordination extension yields one concrete local-structure gain: `potest et animam et corpus perdere`. It requires both a coordinated nominal phrase and an explicit object license for `perdere`; coordination alone cannot repair the dictionary's unknown verb kind. Broader ablative attachment increases governor-link coverage but also admits incorrect internal structures. Those additions are not established grammatical restoration.

## Diagnostic

Iteration 17's candidate units and all prior artifacts remain frozen. We evaluate 66 previously inspected development streams with dictionary morphology and, separately, iteration 19's five oracle missing readings. We compare four grammar arms:

- **Coordination:** two accusative nominal conjuncts, either `NP et/uel NP` or `et NP et NP`, share one object slot.
- **Coordination + frame:** additionally allow the dictionary root `perd` to take an object. This is a declared manual valency addition, not an inferred dictionary property.
- **Attachment:** keep the old nominal inventory but allow an exterior object to attach to either coordinated infinitive or be shared. A bare ablative may attach to the finite predicate or an infinitive as an **unresolved ablative**, without claiming instrument, material, or absolute semantics.
- **Joint:** combine coordination, the explicit `perd` frame, and attachment alternatives.

Objects inside a coordination segment stay in that segment; exterior objects have explicit single/shared alternatives. Unmarked adjacent double-object constructions are excluded from this bounded grammar. Each complete cover records argument groups, heads, attachment targets, and source readings. We enumerate distinct group signatures, keeping one reading witness per signature, with a limit of 256 signatures per unit. A limit hit is marked truncated and cannot produce a supported governor claim. None occurred here. Enumeration is bounded by this grammar, not exhaustive over Latin or all morphological witnesses.

Only the fixed unit interior is covered. Adjacent arguments can still lie outside it. Unknown ownership remains available; a single surviving structure means unique within this grammar, not proven linguistic uniqueness.

## Owner links versus local structure

Primary condition: reference marker scopes, sentence boundaries hidden. There are 66 reference infinitives, of which 21 have their reference governor in the input pool.

| Morphology | Arm | Correct governor links retained | With a saved witness matching local nominal links and POS | With a unique matching local analysis |
|---|---|---:|---:|---:|
| Dictionary | Coordination | 14 | 13 | 13 |
| Dictionary | Coordination + frame | 15 | 14 | 14 |
| Dictionary | Attachment | 15 | 13 | 12 |
| Dictionary | Joint | 16 | 14 | 13 |
| Oracle missing readings | Coordination | 16 | 14 | 14 |
| Oracle missing readings | Coordination + frame | 17 | 15 | 15 |
| Oracle missing readings | Attachment | 19 | 15 | 13 |
| Oracle missing readings | Joint | 20 | 16 | 14 |

The joint counts are identical across the four scope/boundary conditions; those conditions reuse the same streams. All single supported governor candidates match the reference, but structural comparison rejects several of their witnesses. The unit-level reference comparison checks direct nominal-head→predicate links, with nominal conjuncts inheriting their coordinated head's governor, plus coarse source POS compatibility. It does **not** establish semantic adjunct roles, all NP-internal dependencies, external arguments, or complete clause structure. A treebank's single attachment also does not exclude linguistically valid shared alternatives. Counts are deduplicated by reference infinitive for this table, not by repeated lexical unit readings.

The coordination arm without the new frame reproduces iteration 18/19's governor-retention totals; it does not yield a new natural governor link by itself. Comparing the coordination arms isolates the one additional `perdere` construction. The nearest-governor baseline already retained all 21 reachable links in iteration 18. These results therefore support a representation improvement, not a superior owner-selection method.

## Cases that decide the outcome

**Coordinated nominal arguments.** In `potest et animam et corpus perdere`, `animam` and `corpus` form a single coordinated object group attached to `perdere`. The group passes both reference local-link and source-POS checks. The pinned dictionary labels `perdere` VerbKind X, so the explicit `perd` object license is essential. Controlled negatives reject datives in place of accusatives, a missing coordinator, incompatible object modifiers, two unmarked objects in one segment, and an object of intransitive `laborare`.

**Shared versus separate objects.** The controlled trailing-object example `capere et accipere librum debet` retains first-infinitive, second-infinitive, and shared attachment alternatives. `debet puellam capere et librum accipere` retains the separate object slots. These contrasts show that the model represents sharing; they do not demonstrate natural disambiguation of sharing.

**The original wrong-attachment control.** With oracle `sua`, `creduntur enim sua praesentia fecundare` now yields two analyses: ablative attachment to `creduntur` and to `fecundare`. Only the second matches the source nominal link. The model marks the result unresolved rather than selecting the old, misleading passive-instrument witness. It still cannot choose the reference attachment or establish the adjunct's semantic role.

**Ablative broadening creates false covers.** The joint oracle arm admits `apricare → possit` and coordinated `conlocare/aperire → debemus`, but none of their saved witnesses matches the audited local structure. In `defensis sedibus`, nominal readings compete with the intended participle, and the actual participial construction is absent. In `aluearia nisi uespere instante`, `nisi` can be swallowed as a genitive noun while `instante` becomes a nominal modifier. Moving the trailing object to the first infinitive fixes that particular attachment alternative but does not repair the exception/participial construction. These are correct governor links with invalid or incomplete internal analyses.

The synthetic ablative modifier mismatch also survives via separate noun readings of `bonis`, not an agreeing modifier phrase. Removing only those noun readings makes the mismatch fail. This contrast separates agreement enforcement from ambiguity in lexical category.

## Next bottleneck

The unresolved task is distinguishing **nominal homographs from genuine participial constructions**, while retaining genuine adjunct-attachment ambiguity. The next bounded diagnostic should introduce an explicit ablative participial construction with subject–participle case/number/gender agreement and a separately declared `nisi` frame. Compare it against the current nominal alternatives using source-POS and internal dependency checks. Keep the successful coordinated-object rule and its explicit lexical ablation separate; a broad bare-ablative escape hatch is not sufficient evidence of restoration.

## Validation

Artifacts: `experiments/results/grammar-restoration/iteration20/`. The runner saves 11 controlled cases and 2,112 natural conditions (66 streams × four scope/boundary conditions × two morphology arms × four grammar arms). The independent checker verifies 1,083 recorded argument structures for source-reading membership, fixed readings, exact token accounting, role licenses, object-slot sharing, argument-target restrictions and required perception subjects. Replay reproduces all conditions and evaluation, checks pinned hashes, and verifies disjointness from the 200 reserved sentences. These checks validate the implemented grammar, not its linguistic completeness.

Run `.venv/bin/python -m benchmarks.grammar_argument_structures_iteration20_validate`. The relevant combined regression suite passes **179 tests**. No full relative-chain restoration was rerun, no firm ownership claims were made, and the reserved sentences remain unscored.
