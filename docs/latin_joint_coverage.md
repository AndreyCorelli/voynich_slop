# Joint inference when the target uses an unsupported construction

2026-10-12. **An incomplete grammar can silently produce a unique, structurally wrong decoding. Broader coverage admits the intended structures but usually leaves ambiguity.** Joint inference does not automatically recognize that its grammar is inadequate.

## Question and protocol

Test whether the earlier finite joint mechanism rejects constructions outside its grammar or reinterprets them as supported constructions. Preserve all previous experiment sources/results; implement new coverage variants in a separate module.

The generator emits ten predeclared synthetic datasets: two covered controls, plus isolated/repeated/contextual omitted subjects, genitive noun modifiers and coordinated subjects. The generator's explicit word/role/head templates are separate from inference. It creates global injective word-substitution ciphertext, with seed 3219, preserving order and sentence boundaries. The public solver input contains ciphertext, a candidate dictionary and grammar settings; intended dictionaries/trees are saved separately and used only for evaluation or explicitly labeled true-dictionary diagnostics.

Every ciphertext type receives the same complete inventory. There are no supplied gold POS filters, original-word rewards, grammatical score thresholds or fitted language models.

Two inventories:

- **Lean:** 15 surfaces. Earlier ten-word inventory plus three genitive/nominative-plural noun forms, `et` and plural intransitive `dormiunt`.
- **Richer:** 31 surfaces. Earlier noun/adjective/verb/preposition inventory plus genitive readings, `rosae` and `et`.

For each dataset/inventory, compare:

- **Narrow grammar:** original complete-subject clauses, transitive/intransitive/copular patterns. Richer settings also permit adjective NPs and prepositional attachment. It has no genitive noun modifiers, omitted subjects or coordination.
- **Broader grammar:** includes all narrow patterns plus one genitive modifier adjacent to a nominal head, an omitted unmodified subject in a transitive/intransitive clause, or a coordinated subject with plural verb agreement. These extensions are an explicit union; arbitrary combinations/nesting and coordinated copular predicate gender rules remain unsupported.

Both grammars jointly select dictionary words, context-specific readings and coherent relationships. The broader grammar receives language-level construction rules, not knowledge that a particular target sentence uses them. This remains a finite hand-constructed Latin-shaped fragment with restricted lexical valency, not a realistic complete Latin grammar.

## The decisive counterexample

Generate these six clauses:

| Clause | Intended construction |
|---|---|
| `puella pueri dormit` | girl [of the boy] sleeps |
| `puella currit` | girl runs |
| `puer currit` | boy runs |
| `puer puellae dormit` | boy [of the girl] sleeps |
| `rosa currit` | rose runs |
| `rosa rosae dormit` | rose [of the rose] sleeps |

The last two are deliberately semantically odd but fit the supplied synthetic grammar; no semantic plausibility claim is made. Genitive forms have singular genitive and plural nominative readings in the dictionary, and the intended occurrences select genitive. The original dictionary is withheld.

With the **lean narrow grammar**, the ciphertext has **exactly one structural solution**. That solution treats all three genitive modifiers as accusative objects and changes the verb assignments to transitive verbs; it can produce clauses such as `rosa puellam videt`. The true dictionary and intended structure are both impossible under the narrow grammar. There is no UNSAT warning or structural ambiguity warning.

The exact-one-structure result is exhaustive, and a direct different-structure query confirms it. Different vocabulary assignments can still share that uniquely wrong structure.

With the **broader grammar**, the same ciphertext has **four structures**, including the intended one with its true dictionary. The extra rules expose the narrow result's conditional nature; they do not identify the original uniquely.

A separate direct-SAT audit finds all 30 role/head variables forced in the narrow case: **24 match the generator and six are wrong**. In the broader case, only 15 variables remain forced and all 15 match. Reporting only forced relationships therefore cannot by itself protect against missing grammar rules.

## Other mismatch outcomes

Among the **16 deliberately unsupported narrow-grammar cases** across both inventories:

| Outcome | Cases |
|---|---:|
| No solution | 5 |
| Multiple structures, all excluding the intended structure | 10 |
| One structure, excluding the intended structure | **1** |

These are hand-selected controls, not estimates of error prevalence. Every intended dictionary/tree is feasible in the broader grammar, checked directly. That is a coverage control, not recovery success: 19/20 broader problems are ambiguous and one has the unique original structure.

Selected lean-inventory results:

| Dataset | Narrow structural solutions | Broader structural solutions |
|---|---:|---:|
| Six ordinary covered clauses | 1, original | 4, includes original |
| `puerum amat`, omitted subject | 2, excludes original | 4, includes original |
| Same omitted-subject clause repeated four times | 2, excludes original | 4, includes original |
| Omitted-subject clause plus six covered contexts | 0 | 2, includes original |
| Six coherent genitive clauses | **1, wrong** | 4, includes original |
| One genitive clause plus six covered contexts | 0 | **1, original** |
| `puella et puer dormiunt`, coordinated subject | 0 | 26, includes original |
| Coordinated clause plus six covered contexts | 0 | 2, includes original |

Simply repeating an identical clause adds no new evidence here. Different repeated contexts can expose a grammar/key conflict, and with the missing genitive rule added they can identify the original structure in the restricted genitive-with-context positive control.

The richer inventory increases alternative explanations. For the ordinary covered six clauses, the narrow grammar admits nine structures and the broader grammar admits 194. Even covered input can lose apparent certainty when new legitimate construction hypotheses are allowed. In the richer coordination-with-context case, broader enumeration reaches the 512-structure cap: this is a lower bound, not an exact count or timeout.

A second partial-certainty failure occurs with the richer inventory and genitive-with-context dataset: the narrow grammar has seven structures but still forces one wrong relationship variable. Ambiguity in some parts does not make every apparently fixed part trustworthy.

## What the system can and cannot recognize

No solution detects an inconsistency among the current grammar, candidates and global key constraints. It does **not** distinguish grammar undercoverage from missing candidate words or another incorrect assumption. Multiple solutions expose ambiguity, but do not show whether any of them represents the target construction.

A unique solution certifies only that the supplied finite constraints permit one structure. The counterexample disproves the inference that uniqueness establishes grammar adequacy or original-structure recovery. Logical necessity is conditional on the modeling assumptions.

Comparing plausible grammar variants provides an uncertainty diagnostic: narrow uniqueness disappears under a broader grammar. This does not select the right variant without additional evidence. The broader solver includes the generator's three extra constructions by design; unseen constructions outside that broader fragment can create the same problem again.

Joint inference remains useful for tracking compatible hypotheses and eliminating inconsistent assignments. This experiment does not justify using its first satisfying parse—or even its unique parse—as a recovered target structure. Before natural-text application, grammatical coverage needs independent validation, and outputs should preserve ambiguity and indicate sensitivity to grammar choices. A purely hard-constraint solver has no demonstrated way to identify every missing rule from ciphertext alone.

## Verification and artifacts

**40 joint problems**, roughly **8.5 seconds** in the recorded run. Structural enumeration cap 512; each solver check has a 10-second timeout. Only one case hits the enumeration cap; no reported structural result is unknown. Primary status classifications and original/wrong-structure feasibility are explicit SAT/UNSAT queries.

Six new focused tests, plus the six previous joint-grammar tests, pass. They cover unique wrong output, broader coverage, context-dependent rejection, positive genitive restoration, plural agreement of coordinated subjects and exclusion of unimplemented coordinated copular gender behavior. Saved witnesses pass separate concrete reading/agreement/government/tree checks. Full replay reproduces counts, classifications and SAT/UNSAT results. A separate audit queries whether each role/head variable can change; it does not infer forced values from an incomplete enumeration.

[Report](../experiments/results/latin-joint-coverage/report.json), [examples](../experiments/results/latin-joint-coverage/examples.md), [forced-relationship audit](../experiments/results/latin-joint-coverage/audit.json), [manifest](../experiments/results/latin-joint-coverage/manifest.json), [replay](../experiments/results/latin-joint-coverage/validation.json). Public inputs and evaluation truth are in separate subdirectories.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_joint_coverage
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_joint_coverage --validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_joint_coverage_audit
PYTHONPATH=src:. .venv/bin/python -m pytest tests/unit/test_joint_grammar_coverage.py tests/unit/test_joint_grammar.py -q
```

No additional packages, models or external corpora are used. Synthetic readings and passages were constructed locally. This is an exploratory mechanism/coverage audit, not a held-out natural-Latin benchmark.
