# Small joint dictionary-and-parse identifiability experiment

2026-10-12. **Joint inference succeeds in the restricted positive control: six synthetic clauses have one grammatical structure but 144 valid dictionaries. Widening the vocabulary leaves genuinely different structures.** This is a mechanism/identifiability experiment, not a decoder for unrestricted Latin.

## What the solver receives

Public inputs contain only ciphertext sentences, a surface dictionary with multiple possible readings, and an explicit finite grammar. Every ciphertext type gets the **same complete candidate inventory**; no candidate filtering uses gold POS, inflection or plaintext. Original dictionaries and intended trees are saved separately for evaluation and labeled controls.

A single SMT problem chooses:

- One decoded surface per ciphertext type, globally consistent across all occurrences; distinct types map injectively to distinct surfaces.
- One morphological reading **per occurrence**, compatible with that globally selected surface. Different occurrences may select different legitimate readings.
- One coherent sentence structure, with the selected noun/adjective cases, numbers and genders, finite-verb number/valency, and prepositional government jointly satisfied.

Each selected reading is shared by every relationship involving that occurrence. An ambiguous noun cannot use its singular reading for one adjective and its plural reading for another in the same sentence. There are no learned probabilities, lexical-identity rewards, supplied role predictions, grammatical score thresholds or search heuristics.

Enumerate solutions projected onto token dependency roles and heads: different vocabulary and morphology choices with the same structure count only once. Also enumerate dictionaries in the smallest cases. Query directly whether the intended structure is feasible and whether **any different structure** is feasible. An UNSAT result for that second query proves structural identifiability within this finite problem.

## Synthetic grammar and passages

The grammar permits all constituent orders of transitive subject/object/verb clauses, intransitive subject/verb clauses and copular subject/adjective/verb clauses. Noun phrases contain a noun and up to two agreeing adjectives, before/after/on either side of the noun. Subjects are nominative and agree with the finite verb in number; transitive objects are accusative. One optional prepositional phrase governs accusative or ablative. The baseline attaches it to the verb; an explicitly widened attachment condition also permits attachment to the subject/object noun.

The candidate readings are a deliberately restricted Latin-shaped fragment, not all readings of the displayed words. Verbs have explicit fixed valency, subjects/required objects cannot be omitted, and agreement is exact within the supplied inventory. The experiment excludes tense variation, coordinated constituents, subordinate clauses, unrestricted word discontinuity, ellipsis, semantics and many real Latin ambiguities. Restrictive valency/inventory assumptions can create identifiability that a realistic grammar would lose.

The first six clauses are:

1. `puella puerum amat`
2. `puella dormit`
3. `puer dormit`
4. `puer puellam amat`
5. `rosa dormit`
6. `rosa rosam amat`

Their ciphertext has 8 types / 15 occurrences. The base inventory has ten candidate surfaces: three nominative noun forms, their accusatives, two singular transitive verbs and two singular intransitives. `puella` and `rosa` also have ablative readings, unused in these six clauses. The construction is hand-designed as a positive control; it is not a random sample of Latin.

The syncretic inventory adds `bellum` and `donum`, each with nominative/accusative neuter singular readings. The rich inventory has 29 surfaces and adds adjectives, plural forms, copulas and prepositions. Six further clauses introduce those constructions and repeated contexts. Random renaming hides the surface dictionary; word order and sentence boundaries are preserved, as in earlier fixtures. No gold structure is fed to primary inference.

## Exact small-case results

| Candidate inventory | Sentences | Structures with independent sentence dictionaries | Structures with one global dictionary |
|---|---:|---:|---:|
| Base, 10 surfaces | 1 | 6 | 6 |
| Base, 10 surfaces | 2 | 12 | 2 |
| Base, 10 surfaces | 4 | 144 | 2 |
| Base, 10 surfaces | 6 | **1,728** | **1** |
| Add two NOM/ACC-ambiguous nouns, 12 surfaces | 1 | 6 | 6 |
| Add two NOM/ACC-ambiguous nouns, 12 surfaces | 2 | 12 | 4 |
| Add two NOM/ACC-ambiguous nouns, 12 surfaces | 4 | 144 | 8 |
| Add two NOM/ACC-ambiguous nouns, 12 surfaces | 6 | **1,728** | **7** |

All counts above are exhaustive. The base six-clause problem has **144 complete dictionaries**, all projecting to the same intended structure; the original is one of them. Exact lexical identity is therefore not required for the positive result. The solver proves that no structurally different solution exists under those assumptions.

Global injectivity, limited inventory and complete valency constraints are part of the information producing this uniqueness. In particular, alternative analyses that reinterpret object ciphertext types as verbs eventually run out of distinct transitive candidate surfaces. This is not evidence that an arbitrarily large vocabulary would behave similarly.

The syncretic case provides a concrete counterexample: select `bellum` for the type originally representing `puella` and `donum` for the type originally representing `puerum`. Then `bellum donum amat` can take `donum` as subject and `bellum` as object, while the later `bellum dormit` takes `bellum` as subject. The mapping never changes; its legitimate case reading changes by occurrence. Shared dictionary consistency cannot by itself eliminate that alternative.

## Richer vocabulary and longer context

With 29 surfaces, the first six clauses admit **9** global structures versus **32,768** independent combinations. Eight clauses admit **43** global structures versus **29,491,200** independent combinations. At 10–12 clauses, enumeration reaches the preset 2,000-structure cap; those full-passage results are **lower bounds**, not exact counts or timeouts. Direct queries still prove that wrong structures exist.

Adding sentence positions can increase a full-passage count even when old ambiguities shrink. Therefore, a separate audit projects every larger problem onto the **same first six clauses**, holding the rich inventory fixed:

| Available clauses | Surviving structures on the first six clauses |
|---|---:|
| 6 | 9 |
| 8 | 7 |
| 10 | 7 |
| 11 | 7 |
| 12 | 7 |

Those prefix counts are exhaustive. Repetition and additional constructions eliminate some alternatives but do not identify the original core structure in this widened condition.

As an explicit gold-dictionary diagnostic, fixing the original dictionary yields one structure in the baseline attachment grammar for all tested passages. Enabling noun attachment leaves **three** structures for the 11-clause passage even with the entire correct dictionary supplied: `cum rosa` can attach to the verb, subject noun or object noun. The finite grammar permits all three; dictionary recovery alone cannot determine the intended attachment.

## Interpretation

This provides a positive result for **joint inference**, unlike our previous independent-role scoring experiments: global grammatical evidence can make a synthetic construction identifiable without making its vocabulary unique. It also separates that result from search performance, because the small problem is solved exactly and wrong-structure feasibility is explicitly queried.

The widening controls reveal actual nonidentifiability under the stated grammar. More solver time cannot select the intended answer when other satisfying structures remain. Some alternatives may deserve to count as acceptable grammatical reconstructions rather than errors; the result shows that the **original role/head structure** is not uniquely determined, not that every alternative is ungrammatical.

A next experiment should use a predeclared, broader synthetic grammar and multiple generated passages, measuring how ambiguity changes with repetition and candidate inventory. Report structures that are forced versus ambiguous, rather than silently selecting one satisfying tree. Only then test bounded natural-Latin candidate sets and explicitly audit how omitted arguments and richer lexical valency affect the conclusion. This small positive control does not establish natural-text recovery or solve the earlier objective problem.

## Computation, verification and artifacts

Run 14 dataset/grammar conditions in both shared and independent modes: **28 problems**. Z3 4.16.0/Python 3.14.4; no new packages/models needed. Full experiment took about **103 seconds**, predominantly enumerating capped rich alternatives. Structural cap 2,000; dictionary cap 1,000; each solver check has a 10-second timeout. No reported structural result terminated as unknown.

Six focused tests pass: unique structure with multiple dictionaries; surviving syncretic alternatives; rejection of individually rescuable but jointly contradictory adjective agreements; distinct readings for repeated surfaces; global versus independent injectivity; and attachment ambiguity with a known dictionary. All saved examples pass separate concrete reading/agreement/government/tree checks. Full replay reproduces counts, SAT/UNSAT answers and independent Cartesian products; witnesses and timings are permitted to differ. Source/input hashes are frozen.

[Results](../experiments/results/latin-joint-identifiability/report.json), [prefix/known-dictionary audit](../experiments/results/latin-joint-identifiability/audit.json), [examples](../experiments/results/latin-joint-identifiability/examples.md), [manifest](../experiments/results/latin-joint-identifiability/manifest.json), [replay](../experiments/results/latin-joint-identifiability/validation.json). Input files and evaluation truth are in separate directories beside these artifacts.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_joint_identifiability
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_joint_identifiability --validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_joint_identifiability_audit
PYTHONPATH=src:. .venv/bin/python -m pytest tests/unit/test_joint_grammar.py -q
```

The synthetic dictionary and clauses were constructed locally; no public corpus or pretrained model enters this experiment.
