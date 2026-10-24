# Iteration 14: consistent relative–antecedent–governor bridges

The local mechanism works on controlled probes, but it does **not yet restore the construction reliably on natural text**. Morphological compatibility leaves several possible antecedents, and getting the parent predicate right can hide a wrong nominal bridge. Do not add this signal to dictionary restoration or the parent scorer yet.

## Mechanism and scope

New implementation: `src/voynich_smt/relative_bridge.py`. It enumerates a relative pronoun, a preceding nominal within eight tokens, and a governing finite predicate. One selected nominal reading must satisfy both pronoun gender/number agreement and the nominal's role under its governor. Pronoun and antecedent cases may differ: `puellam quae cantat` permits an accusative antecedent and nominative relative subject. The relative pronoun also needs a compatible role under the relative predicate. Nominative subjects agree in number/person; accusative objects require independently marked transitive active verbs; a preceding recognized preposition can license an oblique. Passive ablative instruments are a permissive compatibility hypothesis.

The pinned Whitaker dictionary supplies readings and verb kinds. Unknown valency does not license an object; deponent morphology alone does not establish transitivity. Surface personal nominatives `ego/nos` and `tu/uos/vos` require first/second-person governors. This remains a partial role inventory, with unsupported dative/genitive frames and many legitimate default-valency verbs.

A candidate direct governor cannot cross another exposed finite predicate. Supplied marker-to-child intervals are opaque minimal intervals, **not complete inferred relative-clause spans**. Other relative intervals restrict crossing. Inference receives tokens, supplied finite positions, marker-to-child links, and optional sentence boundaries; it never receives annotated antecedents, UD heads, parent arcs, or reference predicate-complex membership. It reports every feasible antecedent/governor pair and selects a parent only when all pairs agree. Several antecedents can still survive under one parent. There is no fitted score or distance tie-break.

These are local witnesses, not complete grammatical parses: argument uniqueness, whole-clause constituency, coordination, nonfinite complements, copular complexes and free relatives are not solved here.

## Controlled checks

All ten probes contain at least three finite predicates. They cover singular/plural subjects, an accusative antecedent with a nominative relative, an accusative relative object, gender/number contradictions, ambiguous governors, passive ablative versus subject agreement, and unknown-valency abstention. Some closer governors are wrong. These are controlled local construction probes in unsegmented multi-predicate contexts, not ten independently validated complete Latin sentences.

The key consistency counterexample is:

`pueri currunt puellae quae cantat hodie laete semper ridet`

`quae cantat` requires a singular reading. The singular readings of `puellae` are genitive/dative/locative; the nominative reading is plural. The consistent mechanism produces no licensed bridge in its supported inventory. An explicit ablation that permits different nominal readings on the two links wrongly attaches to plural `currunt`. This demonstrates a real improvement over independent feature-existence checks; abstention here does not prove the text ungrammatical.

All ten expected candidate sets pass. Separate tests check personal subject agreement, sentence-boundary conditioning, unequal pronoun/antecedent case and deponent-versus-transitive distinctions.

## Natural development results

All 67 reference-relative cases in the previously inspected 66 development streams are retained, including free relatives and unsupported forms. With predicted scope, the evaluation union has 74 positions: the 67 reference positions plus seven spurious predictions; three reference positions have missing predicted scope. Predicted scope is correct on 64 reference positions. Finite predicate positions are supplied in every condition.

| Marker scope | Sentence boundaries | Unique parent claims | Correct parents | Precision on claims | Correct reference parent in any candidate set |
|---|---|---:|---:|---:|---:|
| Reference | Hidden | 19 | 11 | 57.9% | 19/67 |
| Reference | Supplied | 14 | 12 | 85.7% | 15/67 |
| Predicted | Hidden | 16 | 9 | 56.3% | 16/74 |
| Predicted | Supplied | 14 | 11 | 78.6% | 13/74 |

The realistic-scope arm still supplies finite positions. Its nine correct claims cover only 9/67 reference-relative positions (13.4%); 9/74 is 12.2% of the evaluation union. Reference scope and supplied boundaries give only 12/67 correct coverage (17.9%). There is no fresh confirmation or transfer claim.

On the same 16 unique-claim positions under predicted scope/hidden boundaries, the existing decoder has 11 correct parents versus nine for the bridge. Substituting the bridge would correct two decisions and spoil four. With reference scope/hidden boundaries it would correct four and spoil five. These are comparisons on the mechanism-selected subset, not whole-forest F1 or an actual integrated decoder evaluation.

## Does a correct parent imply the correct structure?

No. An evaluation-only audit follows annotation paths, contracting reference predicate complexes only for evaluation. Among the 19 unique reference-scope/hidden-boundary claims:

- Eleven choose the annotated parent.
- Only three of those have **any** surviving antecedent on the annotated nominal path.
- None has **all** its surviving antecedents on that path.

UD path overlap is a diagnostic, not expert-adjudicated antecedent truth. Nevertheless, this makes parent accuracy an insufficient success criterion for the requested grammatical restoration.

Examples explain the failure:

- For `qui est in caelis`, a compatible earlier `eum` can yield the correct parent while missing the annotated bridge through `patre`.
- For `qui amat ... non est me dignus`, the dictionary supplies a nominal homograph of an earlier `aduersus`. Local morphology can accept that spurious antecedent and still select the correct `est`.
- In `quae ... submoueat` and `quibus excipiatur`, the annotated paths require `locare → debemus` and `habens → accedat`. Direct finite governance cannot express those paths. The dictionary also supplies no reading for corpus `aluearia`, a separate coverage limitation.
- Under hidden sentence boundaries, compatible nouns in a preceding sentence can generate a unique wrong parent. Supplying boundaries removes some of these errors, but does not recover the missing nominal/nonfinite structure.

## Outcome and next experiment

Consistent morphology is necessary but insufficient. The next bounded experiment should choose the antecedent **constituent**, jointly with the relative span and one nominal head; require explicit support for nominal homographs instead of treating every dictionary noun reading as equally plausible. Evaluate antecedent identity and governor identity separately, with abstention. Then extend the governor path by one independently licensed participial/infinitival step, targeting `nominal → habens/locare → finite predicate`; keep multiple plausible paths rather than inventing valency or choosing the nearest noun.

Do this on controlled contrasts and the already inspected development cases first. Keep the reserved 200 sentences unscored until the representation and a construction-level success gate are fixed. No objective/scorer integration follows from this iteration.

## Artifacts and verification

Current artifacts: `experiments/results/grammar-restoration/iteration14-v3/`:

- `controlled.json`, `predictions.json`, `report.json`, `morphology-lattice.json`, `manifest.json`;
- `annotation-audit.json`: all 67 reference construction audits;
- `validation.json`: 302 exact decision replays, membership/consistency checks on 152 natural witnesses, metric replay and baseline comparisons, and disjointness from all 200 reserved IDs.

Fifteen mechanism tests pass; the combined relevant regression selection has 51 passing tests. Replay verifies implementation and artifact consistency, not linguistic validity. Earlier artifacts and code remain unchanged.

Two implementation corrections are preserved transparently. Initial `iteration14` assumed third-person nominal subjects even for personal pronouns. `iteration14-v2` fixes person agreement. `iteration14-v3` additionally stops treating the dictionary's `DEP` label as evidence of transitivity; that label supplies voice behavior, not an object frame. Earlier outputs and runner/module snapshots are retained. These are corrections on reused development, not separate confirmation studies; the table above uses v3 only.

Commands:

```sh
.venv/bin/python -m benchmarks.grammar_relative_bridge_iteration14
.venv/bin/python -m benchmarks.grammar_relative_bridge_iteration14_audit
.venv/bin/python -m benchmarks.grammar_relative_bridge_iteration14_validate
.venv/bin/python -m pytest tests/test_relative_bridge.py -q
```

The runner deliberately refuses to overwrite saved artifacts; replay uses the validator.
