# Iteration 16: joint nonfinite-predicate ownership

Joint ownership removes the targeted `fecundare → debemus` bridge and preserves `locare → debemus`, **under a bounded frame-completeness assumption**. It does not establish general grammatical restoration: predicted-scope complete relative recovery remains 4/67 reference cases. An unrestricted unknown-owner ablation restores the ambiguity, showing exactly where the apparent resolution depends on that assumption.

## Mechanism

New module: `src/voynich_smt/nonfinite_ownership.py`. Inference receives tokens, supplied finite positions, optional sentence boundaries and reference/predicted relative-marker scopes. It receives no annotated nonfinite positions, UD heads, reference owners or antecedents.

It proposes active infinitives and active nominative participles from the pinned dictionary. Candidate ownership frames are:

- Active `debere`/`posse` with an active infinitive.
- Passive `credere`/`dicere`/`ferre` with an active infinitive. These are explicitly declared construction licenses, not frames learned from the evaluation paths; the reporting use of a root is not guaranteed in every context.
- An active nominative participle with an explicit compatible nominative subject shared with a third-person finite governor.

Candidates have a fixed 32-token radius. Exposed finite predicates block attachment; a supplied minimal relative interval wholly between endpoints can shield its finite predicate. A predicate before a relative marker cannot become an internal dependent of that following relative's finite endpoint. These are partial scope rules, not inferred complete clause boundaries.

A joint CSP gives each selected nonfinite predicate one owner, one consistent reading per involved word, and shared gender/number bindings. Each simple finite complement frame has one infinitive slot. Selected ownership arcs cannot cross; nesting is allowed. Participial adjuncts do not consume the infinitive slot. There is no fitted score, distance objective or maximum-coverage objective.

The solver retains all feasible owners. Unlicensed tokens, conflicting components, lexical alternatives and multiple owners produce explicit uncertainty. Conflicts in one component do not erase predictions in an independent component.

### The important completeness assumption

A licensed, lexically unambiguous infinitive is required to take one of its modeled owners. A noun/infinitive homograph or participle can instead retain an unselected lexical/modifier reading. Unsupported tokens also abstain. Thus “unique owner” means unique **within this bounded grammar**, not proof that every real Latin governor was considered.

This distinction matters for `praesentia`, which the dictionary also analyzes as an active participle. It can remain a noun in the relative witness instead of being forcibly converted into a predicate. Initial `iteration16` artifacts forced that conversion; current `iteration16-v2` preserves optional lexical selection. The initial runner/module snapshots and outputs remain archived.

## Controlled tests

Ten fixed probes each have at least three finite predicates. They test crossing competition, one-slot competition, a farther valid owner within one sentence, genuine ambiguity, reporting voice, shared participial subjects, number mismatch, unsupported coordination and component-local abstention.

One single-sentence contrast is:

`creditur agricola semper diligenter multum laborare et puellam diligere debet dum pueri currunt`

Both infinitives have `creditur` and `debet` available. Nearest attachment wrongly prefers `debet` for `laborare`. Capacity alone leaves two complete assignments; noncrossing eliminates the swapped assignment, yielding `laborare → creditur` and `diligere → debet`. No sentence-boundary oracle separates those alternatives.

The ambiguity probe retains two owners instead of picking the closer one. Coordinated infinitives competing for one modeled slot cause explicit abstention; that is a grammar-coverage failure, not a claim that coordinated Latin infinitives are ungrammatical. A conditional owner ambiguity also prevents publication of an otherwise unique relative chain.

All ten expected ownership outputs pass. Additional tests check shared finite readings, optional noun/participle readings, crossing geometry, independent checker failures and the unknown-owner assumption.

## Evaluation and ablations

The same 66 inspected development streams contain 163 annotated nonfinite predicates: 49 active infinitives, 17 passive infinitives, 33 active participles and 64 passive participles. The primary reference is the nearest projected finite ancestor, including supported predicate complexes. There are 145 cases with an annotated finite owner. This reference is an evaluation proxy, not expert linguistic adjudication.

The dictionary proposes 77 nonfinite sites: 69 are annotated nonfinite tokens and eight are other annotated word classes. Optional lexical selection prevents a unique ownership assertion for those eight spurious proposals in the primary condition. Only 27 reference owners occur in the initial licensed pool, before joint constraints; the pool is already very incomplete.

Arms hold morphology, windows and relative candidates fixed:

1. Independent compatible ownership, with shared readings but no slot/crossing constraints.
2. One-slot capacity without noncrossing.
3. Joint capacity and noncrossing.
4. Joint constraints without the added passive-reporting inventory.
5. Nearest-compatible attachment, retaining distance ties.

Relative candidates are frozen from iteration 15-v2. The new reporting frames license ownership but do not introduce new reporting-parent relative paths. This isolates rejection/ambiguity of existing candidates rather than broadening the relative grammar simultaneously.

### Ownership results

With reference relative scope and hidden sentence boundaries:

| Method | Correct firm owner choices / claims | Correct coverage of 163 annotated nonfinites | Reference owner reachable |
|---|---:|---:|---:|
| Independent | 13/17 (76.5%) | 8.0% | 27 |
| Capacity only | 8/9 (88.9%) | 4.9% | 22 |
| Joint | 10/11 (90.9%) | 6.1% | 22 |
| Joint without reporting | 4/4 (100%) | 2.5% | 16 |
| Nearest compatible | 16/20 (80.0%) | 9.8% | 27 |

A firm choice requires both selected nonfinite status and a unique owner. Participles/homographs can have a conditional owner while their predicate status remains unresolved; those are not firm claims. Including such conditional unique owners gives 19/26 correct for the joint model, a different and weaker claim.

The joint grammar trades coverage for precision; it does not dominate nearest attachment. With supplied sentence boundaries, joint ownership reaches 12/12 firm choices versus nearest attachment's 16/17. These small, selected samples do not establish generalization. Predicted relative scopes give the same firm hidden-boundary ownership counts as reference scope.

### Relative-chain results

A relative bridge must use an owner feasible under its own selected readings. A complete chain is published only when ownership is entailed under those readings and selection of the bridge's nonfinite predicate. Compatible-but-ambiguous ownership is retained as uncertainty.

| Method, hidden boundaries | Correct unique chains / claims, reference scope | Correct unique chains / claims, predicted scope |
|---|---:|---:|
| Original iteration 15 pool | 5/10 | 4/9 |
| Independent ownership | 4/8 | 3/7 |
| Capacity only | 4/9 | 3/7 |
| Joint | 5/10 | 4/8 |
| Joint without reporting | 4/9 | 3/7 |
| Nearest compatible | 5/9 | 4/8 |

The joint model preserves the correct nonfinite chain and removes the wrong one: nonfinite relative claims go from 1/2 correct to 1/1. However, another case becomes uniquely wrong after a competing nonfinite path is removed: `foramen → possit` remains as a direct attachment. Consequently reference-scope whole-chain precision does not improve overall. Predicted-scope correct coverage remains **4/67 = 6.0%** (the evaluation union has 74 positions including spurious markers).

With supplied boundaries the joint model retains 5/8 complete reference-scope chains and 4/7 predicted-scope chains, unchanged from iteration 15. No source confirmation, target decoding or dictionary optimization follows.

## What happens in the motivating case?

In the inspected stream containing:

`creduntur ... fecundare quae spectant ... locare debemus quae ... submoueat`

both infinitives initially admit `creduntur` and `debemus`. Independent compatibility and capacity alone leave the ownership swap possible. With both infinitives selected, the swapped assignment crosses; the joint grammar therefore entails:

- `fecundare → creduntur`;
- `locare → debemus`.

The old false `praesentia → fecundare → debemus` bridge is excluded, while `parte → locare → debemus` survives. Nearest attachment also gets this natural example right. The farther-owner controlled contrast establishes that the joint mechanism can use evidence beyond proximity; it does not establish a natural-text advantage over the heuristic.

### Unrestricted unknown-owner diagnostic

`unresolved-owner-diagnostic.json` relaxes the independently encoded CSP so **every** nonfinite predicate may have an unknown owner, without a penalty or coverage objective. An all-unknown assignment is feasible. Both infinitives again admit both finite governors, and even the false relative bridge's own readings permit its old attachment when the other infinitive can remain unknown.

Therefore the targeted exclusion depends on requiring the selected infinitives to use the modeled frames. Constraints alone do not compensate for an incomplete frame inventory. The open-owner diagnostic is preserved separately and does not change the primary table.

## Failure audit and next bottleneck

All four primary conflicting components and the single wrong firm owner are recorded in `failure-audit.json`:

- `timere` is annotated under `nolite`, outside the current inventory, and competes with correctly owned `occidere` for a later modeled slot. Both abstain.
- `nocere` belongs under `solent`, also unmodeled, but competes with correctly owned `operire` for `debebis`. Both abstain.
- `conlocare` and `aperire` genuinely share an annotated governor. A one-infinitive slot cannot represent that coordination and loses both correct attachments.
- Another component mixes a correctly owned `accipere` with a root/unowned `fugere` analysis and abstains.
- The wrong firm choice is `instare → fertur`; its annotated owner is later `uiderint`, whose perception construction is absent. The only licensed candidate is uniquely wrong. Supplied boundaries remove the earlier `fertur` candidate.

The next experiment should audit governor-candidate coverage before asserting uniqueness, then test narrowly specified negative-imperative, habitual and perception complements alongside coordinated infinitive units. Use controlled contrasts to distinguish coordination from unrelated competing complements; simply raising every slot capacity would undo the useful competition. Keep an explicit unknown-owner option and report the completeness assumption rather than hiding it with score weights. Continue on inspected material until the construction inventory and acceptance criterion are fixed.

## Artifacts and verification

Current artifacts: `experiments/results/grammar-restoration/iteration16-v2/`. They include all candidate licenses and components, ownership projections, frozen relative-pool filtering, lexical lattice, evaluation paths, failure audits, the unknown-owner diagnostic and pinned manifests. Earlier iterations remain unchanged.

Twenty-five new tests and 99 combined relevant tests pass. Validation replays 40 controlled conditions, 1,056 ownership conditions and 1,410 filtered relative conditions. An independently encoded Boolean/cardinality CSP checks 1,176 components, 1,296 owner projections and 32 conditional bridge-ownership decisions; 346 retained relative witnesses receive independent local SMT checks. All 44 metric conditions replay. The morphology proposal pool and component separation are checked, and all 200 reserved sentence IDs remain disjoint and unscored. These are implementation checks, not proofs of complete Latin grammatical analyses.

```sh
.venv/bin/python -m benchmarks.grammar_nonfinite_ownership_iteration16
.venv/bin/python -m benchmarks.grammar_nonfinite_ownership_iteration16_evaluate
.venv/bin/python -m benchmarks.grammar_nonfinite_ownership_iteration16_validate
.venv/bin/python -m benchmarks.grammar_nonfinite_ownership_iteration16_audit
.venv/bin/python -m benchmarks.grammar_nonfinite_ownership_iteration16_unresolved
.venv/bin/python -m pytest tests/test_nonfinite_ownership.py -q
```

The runner refuses to overwrite saved predictions. Use the validator for replay. No scorer integration was performed.
