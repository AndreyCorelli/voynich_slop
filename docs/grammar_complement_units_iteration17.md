# Iteration 17: governor coverage and coordinated complement units

The missing constructions are now representable without forcing ownership. Correct finite-governor coverage rises from **27/163 to 31/163** annotated nonfinite predicates. On a fixed subset of covered reference edges, joint compatibility improves from **18/23 to 23/23 streams**. Those are partial reference-subgraph checks, not complete parses or restored ownership decisions. Unknown owners remain possible everywhere, and this iteration makes **zero firm ownership claims**.

## What was implemented

New module: `src/voynich_smt/complement_units.py`. It preserves the earlier dictionary, supplied finite positions, 32-token ownership window, reading consistency and noncrossing constraints. No UD heads, reference owners, annotated nonfinite positions or evaluation requirements enter production model construction.

Three explicitly declared frame families supplement the previous modal, passive-reporting and shared-subject participial licenses:

- Negative imperative: active second-person imperative `noli/nolite` plus an active infinitive, identified by the dictionary root `nol` and morphological reading.
- Habitual: an active finite reading of `soleo`, identified by root `sol`, plus an active infinitive.
- Perception: an active finite reading of `uideo`, root `uid`, plus an active infinitive with a nearby explicit accusative nominal hypothesis between the finite verb and infinitive. The nominal must be within three tokens of the infinitive. Its number need not agree with the finite verb.

The perception rule selects one accusative reading and retains it consistently. It does not prove whether that nominal is an embedded subject or an infinitive's object. Passive perception, nonimperative `nolo`, additional governor families and many legitimate word orders remain outside these added licenses.

### Complement units

A simple finite frame still has one complement slot. The slot can contain one infinitive or an **optional pair of coordinated infinitives**. The pair requires:

- Adjacent infinitive proposals, at most eight tokens apart, with no supplied finite predicate or supplied sentence boundary between them.
- A recognized conjunction such as `et`, `aut`, `uel`, `nec` or `neque`, with a dictionary conjunction reading; or the explicitly paired split-marker pattern `ne c INF … ne c INF` used in this corpus.
- Nominal/adverbial argument or modifier material in the remaining gap, compatible source readings, and a common licensed finite governor.

The two members share one selected finite reading and consume one slot. Pairing is an alternative to separate ownership, not an instruction to merge every marked sequence. A conjunction can still support ambiguous analyses. Longer coordinated lists are not implemented: three infinitives cannot be squeezed into a two-member unit.

Every nonfinite proposal may have an unknown owner, without a penalty or coverage preference. No fitted score, nearest-owner tie-break or global frame-completeness assumption selects an owner. An all-unknown assignment remains feasible. Conditional candidate uniqueness is reported separately from entailment.

## Controlled contrasts

Fourteen fixed multi-predicate probes check the three new frame families, absent accusative evidence, unsupported frame variants, plain and paired-negative coordination, missing coordination markers, intervening finite predicates, nominal conjunctions, separate owners for unrelated complements, and the unsupported three-member case. All expected joint-feasibility results pass.

Additional tests check that sharing a slot requires selecting a real pair unit, an accusative reading cannot be swapped for a nominative reading, and one finite word cannot simultaneously use singular and plural readings. Independent checker tests reject a forged coordination marker. These are local construction probes; full Latin grammaticality of every multi-predicate context is not adjudicated.

## Natural development experiment

The same 66 inspected development streams and 163 annotated nonfinite predicates are retained. The dictionary proposes 77 sites, of which 69 are annotated nonfinites and eight have another annotated word class. No morphology patch was added.

The three ablations are:

1. Previous frame inventory, open unknown owners, singleton complements.
2. Added governor frames, open unknown owners, singleton complements.
3. Added frames and optional coordinated pairs, open unknown owners.

Evaluation uses the frozen iteration 16 nearest-projected-finite-ancestor reference. It is an annotation proxy, not expert-adjudicated ownership. Reference queries are applied **after model construction**, solely to test whether annotated assignments could coexist. They do not choose production owners.

### Governor-candidate coverage

With reference relative scope and hidden sentence boundaries:

| Model | Annotated owner available | Conditional unique candidates correct / candidates | Firm owner claims |
|---|---:|---:|---:|
| Previous frames, open owners | 27/163 (16.6%) | 22/32 | 0 |
| Added frames | 31/163 (19.0%) | 23/30 | 0 |
| Added frames and pair units | 31/163 (19.0%) | 23/30 | 0 |

“Conditional unique” means exactly one **modeled** owner is available if a modeled owner is chosen. Unknown ownership is still possible, so these are not restored assignments or unconditional precision estimates.

The four additional reference edges are two `timere → nolite` cases, `nocere → solent`, and `instare → uiderint`. Three previous uniquely wrong candidate sets become ambiguous instead:

- `timere`: previously only `possunt`; now `nolite` or `possunt`.
- `nocere`: previously only `debebis`; now `solent` or `debebis`.
- `instare`: previously only `fertur`; now `fertur` or `uiderint`.

The remaining added `timere → nolite` edge previously had no licensed owner. This is useful coverage repair, not disambiguation of the three competing cases.

### Can the covered correct edges coexist?

Two fixed evaluation subsets prevent changing coverage from masquerading as improved parsing:

| Reference subset | Eligible streams | Previous frames | Added frames | Added frames and pairs |
|---|---:|---:|---:|---:|
| The 27 edges covered by the baseline pool | 21 | 20 feasible | 20 feasible | 21 feasible |
| The 31 edges covered by the expanded pool | 23 | 18 feasible | 22 feasible | 23 feasible |

A stream is eligible only when that subset contains at least one edge in it. All other annotated edges are left untested in these queries; unrequired proposals can remain unknown. Thus **23/23 is not a complete-parse success rate**. The expanded pool still omits 132 of the 163 annotated nonfinite targets, including cases without a projected finite owner.

Candidate coverage and these feasibility totals are identical under reference/predicted relative scope and hidden/supplied sentence boundaries. That does not mean all candidate sets or all aspects of parsing are identical across conditions.

### The targeted failures

- The annotated `timere → nolite` and `occidere → possunt` assignments now coexist. The infinitives need not compete for the same modal slot.
- `nocere → solent` and `operire → debebis` now coexist.
- `instare → uiderint` becomes available through the explicit accusative `malum` reading.
- `conlocare` and `aperire` can both use `debemus` through the paired `ne c … ne c` unit. Singleton-slot models cannot admit both edges together.
- The earlier `accipere`/`fugere` conflict already disappears in the baseline open-owner model: `accipere` can use its annotated owner while `fugere` remains unknown. No additional frame or pair is needed for that partial assignment.

There is exactly **one** natural pair with a common licensed governor in this development cohort, `conlocare/aperire`. It matches a direct annotated infinitival coordination relation. One positive pair is too little evidence for broad coordination quality. The controls additionally show that unrelated complements can retain separate owners and that a nominal conjunction alone does not create an infinitive pair.

## What remains unresolved

In the motivating `creduntur … fecundare … locare debemus` stream, both infinitives still have both finite governors available when other owners may remain unknown. The added construction coverage does not restore the earlier closed-inventory exclusion. No objective was added to make the unknown state artificially unattractive.

This iteration repairs representational gaps and joint compatibility. It does not resolve the remaining ownership ambiguity, integrate the signal into relative restoration, or rerun restoration as a new accuracy result. The earlier 4/67 predicted-scope complete-chain figure must not be treated as a new iteration 17 measurement.

The next useful diagnostic is **local construction-span recognition**: require independently supported clause/argument structure around a proposed governor-complement unit, and measure which spans distinguish competing governors. Test complete local analyses against overlapping, coordinated and elliptical alternatives before making commitments. Candidate availability alone, or a preference for explaining more tokens, would reintroduce the previous completeness problem. Keep unknown analyses for spans the grammar cannot distinguish.

## Artifacts and verification

Artifacts: `experiments/results/grammar-restoration/iteration17/`:

- `controlled.json`, `models.json`, morphology lattice and pinned manifests;
- `reference-queries.json`: evaluation-only edge requirements and feasibility results;
- `target-audit.json`, `coordination-audit.json`, `report.json`, `validation.json`.

Twenty-five new tests and **124 combined relevant tests pass**. Validation replays 42 controlled and 792 natural models, independently checks 924 owner projections, and verifies 1,584 reference-subgraph queries by exhaustive compatible-unit-cover search rather than the primary SMT solver. It checks source reading membership, frame/marker licenses, slot usage, noncrossing, shared wildcard bindings, coverage and feasibility aggregation, and the coordination audit. These prove implementation consistency within the declared grammar, not linguistic correctness or complete Latin parses.

All 200 reserved sentence IDs remain disjoint and unscored. This is development on known failures, with no fresh confirmation, transfer claim, scorer integration or dictionary optimization. Earlier code and artifacts remain unchanged.

```sh
.venv/bin/python -m benchmarks.grammar_complement_units_iteration17
.venv/bin/python -m benchmarks.grammar_complement_units_iteration17_evaluate
.venv/bin/python -m benchmarks.grammar_complement_units_iteration17_validate
.venv/bin/python -m pytest tests/test_complement_units.py -q
```

The prediction runner refuses to overwrite saved artifacts; use the validator for replay.
