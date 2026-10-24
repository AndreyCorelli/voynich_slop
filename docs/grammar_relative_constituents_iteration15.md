# Iteration 15: antecedent constituents and one nonfinite governor

The tighter grammar improves **antecedent identity**, and recovers one inspected nonfinite chain, but whole-construction restoration remains unreliable. With reference marker scope and hidden boundaries, unique antecedent choices improve from 4/16 correct in the new readings-only control to 11/14 with constituency and one nonfinite step. Unique complete chains improve from 0/10 to 5/10. With predicted scope the final grammar yields only four correct unique chains among 67 reference-relative cases. Do not integrate this into the scoring objective yet.

## What changed

`src/voynich_smt/relative_constituents.py` adds a bounded construction grammar without changing the frozen iteration 14 implementation:

- One nominal head and jointly compatible agreeing adjectives, determiners, numerals and participles; genitive dependents and simple prepositional modifiers are allowed. At most three tokens precede the head, and the antecedent search window is sixteen tokens.
- A constituent must reach the relative marker, or end immediately before a gap containing only its selected finite/nonfinite governors. An adjectival homograph cannot discard an immediately preceding compatible unambiguous noun and become the head of the suffix alone. PREP/CONJ/ADV homographs need positive modifier support for nominal use. These are explicit conservative grammar restrictions, not a learned noun classifier or a full NP parser.
- Unknown/common noun gender and unknown number bind once across the pronoun and constituent. A noun cannot separately satisfy a feminine modifier and a masculine relative by reusing an unknown gender. Source dictionary readings and the latent binding are saved separately.
- One active nominative participle can govern the antecedent if an explicit nominative subject jointly agrees with the participle and finite governor. An active infinitive can govern it under a finite form of `debere` or `posse`. The infinitive's nominal argument does **not** have to agree in number/person with the modal.
- Lexical verb roots and verb kinds are preserved for both verbs and participles. Dictionary `TRANS` licenses an active object. A separate ablation adds the declared object frames `habere` and `locare`, whose dictionary verb kind is `X`. These two hand-specified Latin construction frames are not extracted from UD paths. Unknown valency elsewhere remains unsupported.

All feasible head/path signatures in this bounded procedure are retained. No nearest-noun or highest-score tie-break is used. A unique parent can still coexist with multiple antecedents or paths; the metrics distinguish those decisions. The local grammar chooses one compatible modifier reading per grounded head binding, so it is not an exhaustive enumerator of all Latin analyses.

Finite positions remain supplied. Marker-to-child links are either reference links or frozen predicted links. Sentence boundaries are either hidden or supplied. No UD head, annotated antecedent, parent arc or reference complex membership enters inference. Minimal relative-marker intervals remain an approximation to full clause scope. Predicate positions cannot simultaneously serve as nominal readings in the same witness.

## Controlled checks and ablations

Fourteen probes, each with at least three finite predicates, check NP heads versus adjectival homographs, differing antecedent/pronoun case, gender/number contradictions, ambiguous governors, shared participial subjects, wrong participial number/case, modal licensing, and relatives following the modal complex. The final grammar passes all fourteen expected candidate sets.

The `habens` object probe works only when its declared object frame is enabled. A dictionary-marked transitive infinitive works without the additions. Independent tests verify that plural/first-person `debemus` can govern an infinitive whose nominal argument is singular, and that mixed wildcard genders cannot manufacture agreement. The added `habere`/`locare` object frames make **no difference** to natural development predictions: the recovered `locare` argument is prepositional, while corpus `aluearia` remains absent from the dictionary.

The fixed ablations are:

1. Readings only, direct finite governor.
2. Constituent constraint, direct finite governor.
3. Constituents plus one dictionary-supported nonfinite step and the declared modal inventory.
4. The same grammar plus the two declared object frames.

The readings-only arm is a **new comparable control**, with the same sixteen-token radius and consistency restrictions as this iteration. It is not an exact replay of iteration 14, which used radius eight and a different witness representation. Earlier metrics remain preserved separately.

## Natural development results

All 67 reference relatives in the same 66 previously inspected streams are retained. Annotation paths contain a nominal node for 38 cases; nine of those paths contain nonfinite verbs. Thirty-six cases have the nominal/at-most-one-nonfinite/finite-parent path shape, before checking morphology or the grammar's other restrictions. Free relatives, copular analyses and coordination complicate the remaining cases.

The reference is an **evaluation-only annotation proxy**: the first nominal node on the relative-predicate-to-parent path is the antecedent target; intervening nonfinite verbs define the intermediate target. Supported projection of predicate complexes is used only to construct this evaluation target. Exact-chain success requires the same nominal, intermediate verb (or none), and finite parent. Annotation agreement is not expert adjudication of grammatical truth.

With reference marker scope and hidden boundaries:

| Method | Correct unique antecedents / claims | Correct unique complete chains / claims | Reference chain in any candidate set |
|---|---:|---:|---:|
| Readings, direct | 4/16 (25.0%) | 0/10 (0%) | 7/67 |
| Constituents, direct | 10/12 (83.3%) | 4/9 (44.4%) | 7/67 |
| Constituents, nonfinite | 11/14 (78.6%) | 5/10 (50.0%) | 8/67 |
| Plus declared object frames | 11/14 (78.6%) | 5/10 (50.0%) | 8/67 |

Each column conditions on its own unique decision: a unique antecedent need not have a unique governor. Higher precision is therefore not a claim that most relatives have been restored. The final five correct unique chains cover **5/67 = 7.5%** of reference cases, or 5/36 of the potentially compatible annotated path shapes.

For the final grammar across scope/boundary conditions:

| Relative scope | Boundaries | Correct unique antecedents / claims | Correct unique chains / claims | Correct unique parents / claims |
|---|---|---:|---:|---:|
| Reference | Hidden | 11/14 | 5/10 | 6/11 |
| Reference | Supplied | 9/11 | 5/8 | 6/8 |
| Predicted | Hidden | 8/11 | 4/9 | 5/9 |
| Predicted | Supplied | 7/9 | 4/7 | 5/7 |

The predicted-scope evaluation union includes seven spurious relative positions, giving 74 positions; three reference positions have missing scope and scope is correct at 64 reference positions. The four correct unique chains cover **4/67 = 6.0%** of reference relatives (4/74 = 5.4% of the union). All conditions supply finite positions and reuse inspected material; there is no fresh confirmation or transfer result.

On the nine unique-parent claims under predicted scope/hidden boundaries, the existing decoder and new mechanism each get five parents right. Substitution would correct two decisions and spoil two. With reference scope/hidden boundaries it would correct three and spoil three. The antecedent gain has not become a net parent-decoding gain.

## What the construction audit shows

There is a concrete successful extension:

`in horti parte secreta et aprica et a uentis remota et calidiore locare debemus quae ... submoueat`

The grammar selects **`parte → locare → debemus`**. The noun phrase preserves singular feminine ablative agreement, its leading `in` licenses the oblique under `locare`, and the modal is first-person plural. This does not rely on invalid antecedent-to-modal number agreement. The reference marker scope supplies `quae → submoueat`; the nominal and governor chain are inferred.

Other recovered direct chains include `hyacinthum → nutriat`, `locus → uitetur`, and `parte → constituemus`. The constituent constraint removes competing nearby nominal candidates that iteration 14 could retain under the same parent.

The corresponding participial target **`aluearia → habens → accedat`** remains unsupported: the pinned analyzer gives no reading for corpus `aluearia`. The construction works in controlled dictionary-covered examples, but that is not recovery of this natural example. No evaluation-driven morphology patch was added.

One false nonfinite chain selects **`praesentia → fecundare → debemus`**, crossing from an earlier sentence into a later modal construction. Its reference has no nominal bridge of this shape. The earlier `creduntur ... fecundare` complex is not owned jointly by this grammar, so compatibility with a later modal can win by uniqueness. Supplied sentence boundaries remove that false chain: nonfinite claims change from 1/2 correct to 1/1, without adding another correct chain.

Remaining errors include a correct nominal with a wrong governor, lexical homographs, omitted/free-relative and copular structures, and unsupported constituent spans. Some annotation choices are themselves open to linguistic review. The mechanism cannot establish whole-text grammaticality or ungrammaticality.

## Outcome and next check

The low-cost constituency restriction is useful: it materially improves the identity of selected antecedents and exposes a real nonfinite bridge. The missing structure now includes **ownership of nonfinite predicates and competition among complete predicate complexes**, alongside morphology coverage and limited scope inference. Changing objective weights would not supply those distinctions.

The next bounded diagnostic should make an infinitive choose among its locally licensed finite complexes before using it as a bridge, retaining competing analyses and testing the `creduntur ... fecundare` versus later `debemus` contrast. Keep the coverage issue separate: measure unknown antecedents without supplying their annotation-derived analyses. Continue on controlled contrasts and inspected development, with antecedent/path/parent metrics separate. The reserved 200 sentences remain unscored until a construction-level method and success criterion are fixed.

## Artifacts and verification

Current artifacts: `experiments/results/grammar-restoration/iteration15-v2/`. They include the morphology lattice, all four ablations, all 67 reference construction audits, evaluation-only paths, manifests, report and validation results. Initial `iteration15` artifacts and runner/module snapshots are retained; v2 adds a single shared gender/number binding across the full noun phrase. This consistency correction changes witness bookkeeping but leaves candidate head/path sets and reported metrics unchanged.

Twenty-three mechanism tests pass; 74 tests pass in the combined relevant regression selection. Independent validation replays 56 controlled and 1,128 natural conditions, checks 34 controlled and 395 natural witnesses with a separately encoded SMT formulation, reconstructs evaluation paths, replays all sixteen metric conditions, and verifies disjointness from all 200 reserved sentence IDs. Corrupted-witness tests confirm the checker rejects mixed gender bindings and wrong argument roles. These checks establish local feasibility and reproducibility, not complete grammatical parses.

```sh
.venv/bin/python -m benchmarks.grammar_relative_constituents_iteration15
.venv/bin/python -m benchmarks.grammar_relative_constituents_iteration15_evaluate
.venv/bin/python -m benchmarks.grammar_relative_constituents_iteration15_validate
.venv/bin/python -m pytest tests/test_relative_constituents.py -q
```

The prediction runner refuses to overwrite artifacts. Use the validator to replay the saved experiment. No scorer integration or dictionary optimization was performed.
