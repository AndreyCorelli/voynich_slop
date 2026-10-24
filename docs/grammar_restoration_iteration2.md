# Grammar restoration: coherent-analysis iteration

## Frozen scope and gates

This iteration replaces the independent-obligation relaxation with one selected morphological reading and one dependency attachment per token, a single finite root per supported clause, explicit nominal roles, agreement and preposition government, and full token coverage. It is a bounded grammar for controlled examples, not unrestricted Latin. Unknown words, unsupported analyses, length limits and solver timeouts must remain explicit; no token can be dropped to rescue a parse. No dictionary search is part of this iteration.

Before scoring examples, freeze a development set of eight minimal pairs (two each for subject number, modifier agreement, preposition case and finite-predicate replacement), valid word-order/omitted-subject controls, and an eight-pair lexical confirmation set with different core nouns and predicates. All supplied examples are authored grammatical diagnostics, not independently human-adjudicated natural text. A second benchmark phase hides supplied clause boundaries, retaining them only for evaluation. An analysis must cover every token in both phases. A boundary costs one point; multiple readings/parses never add a score bonus. The gate is all eight development references supported and all eight paired corruptions rejected, all valid controls retained, followed by the same requirements on the frozen confirmation set. Boundary-free valid two-clause examples must retain full coverage; fragments cannot be discarded. No post-result threshold changes.

If these narrow controls pass, evaluate the unchanged eighteen natural passages and ten historical first corruptions as a coverage/transfer diagnostic. A positive controlled result alone does not authorize full-dictionary stability tests. Unsupported natural constructions or incomplete coverage cannot be counted as rejected grammatical errors. Keep all failures and ambiguous parses visible.

## Results

**The coherent parser passes the controlled gate, but has insufficient natural-text coverage for dictionary search.** It supports all 16 intact minimal-pair examples and finds no parse for all 16 paired corruptions, both with supplied boundaries and with latent boundaries. It also retains all 14 valid controls and correctly handles all four two-clause reference/corruption pairs in both modes. The same examples are reused between boundary modes; these are ablations, not independent replications.

| Split | Boundary mode | Intact references supported | Corruptions with no parse | Valid controls retained | Two-clause pairs correct |
| --- | --- | ---: | ---: | ---: | ---: |
| Development | Supplied | 8/8 | 8/8 | 7/7 | 2/2 |
| Development | Latent | 8/8 | 8/8 | 7/7 | 2/2 |
| Lexical confirmation | Supplied | 8/8 | 8/8 | 7/7 | 2/2 |
| Lexical confirmation | Latent | 8/8 | 8/8 | 7/7 | 2/2 |

The old independent-obligation relaxation, evaluated on these exact 16 pairs without a boundary confound, strictly preferred intact text in **10/16**, tied in **6/16**, and preferred corruption in **0/16**. This compares the old penalty ranking with new feasibility distinctions; it is not a comparison of normalized model probabilities.

The controlled examples cover singular/plural subject agreement, modifier case/number/gender agreement, preposition case government, and replacing the only finite predicate with a participle. Controls retain different constituent orders, omitted subjects, and compatible changes in lexical identity. A noun's ambiguous readings cannot be used independently to agree with a singular modifier and plural predicate: a focused test confirms that the coherent parser rejects this previously possible shortcut.

The confirmation set changes core nouns/predicates (`agricola`, `miles`, `equus`, `laborat`, `audit`, `dormit`), but reuses the construction templates and some vocabulary. These examples were authored in this repository, with morphology checked against Whitaker; they have not been independently adjudicated by a Latin expert. Passing them establishes implementation behavior on the declared subset, not broad Latin grammatical accuracy. Participial fragments are deliberately excluded from this task, although fragments and ellipsis can be legitimate in natural text.

## Transfer to the unchanged natural diagnostics

All **18 natural 64-token passages** from iteration 1 remain **unsupported as complete streams**, with either supplied reference sentence boundaries or latent boundaries. Therefore there is **no valid restoration/ranking improvement claim** on Cicero, Sallust or Suetonius. Supplied sentence boundaries are an oracle diagnostic here and are not necessarily clause boundaries; a multi-predicate sentence exceeds the single-root clause model even when its boundary is supplied.

Within the supplied partitions, five small regions totaling **25 of 1,152 tokens** receive complete analyses; this is **2.17% partial token coverage**, not five successful passage reconstructions. Across 97 supplied regions, results are:

| Region status/reason | Count |
| --- | ---: |
| Supported complete analysis | 5 |
| Beyond the configured ten-token clause limit | 43 |
| Missing morphology | 25 |
| Unsupported POS/construction | 13 |
| No complete analysis in restricted grammar | 8 |
| No supported finite predicate | 3 |

These reasons are reported in check order and are not disjoint causal diagnoses: a long region may also have unknown words or unsupported constructions. The 13 unsupported POS regions mostly expose the deliberately narrow grammar's lack of clause-linking/function-word support; improving dictionary coverage alone would not address that.

None of the **ten historical first-corruption tests** has a fully supported intact set of cropped contexts. Across 12 crops, both sides together produce 22 `unsupported` and two `no_parse` results. These are **unresolved comparisons**, not successful corruption rejections. No unsupported span is dropped or assigned a convenient negative score.

## Implemented analysis and boundary contract

[The coherent grammar](../src/voynich_smt/coherent_grammar.py) uses Z3 to select exactly one dictionary reading and one dependency attachment for every token in a candidate clause. A supported clause has exactly one finite root; every other token connects to that root through an acyclic dependency tree. Subject and direct-object capacity are each at most one. Nominative subjects agree with the root in person/number; subjects may be omitted. Modifiers attach to a particular nominal with a compatible case/number/gender reading. Genitives may attach to nominals. Obliques must each have exactly one licensed preposition, and a preposition has only one nominal head. Adverbs attach to the finite root.

The Latin adapter preserves independent Whitaker morphological alternatives and uses an explicit small preposition-government table. Eight controlled surface forms of *curro*, *ambulo*, *dormio* and *laboro* are marked intransitive; other active verbs have an optional direct-object slot. This is a transparent, limited lexical valency table, not learned or comprehensive Latin valency. Passive roots do not take the baseline direct-object role. Copular predicates, coordination, subordinate clauses, infinitive clauses, participial argument structures, broad oblique/adjunct constructions, nominal ellipsis and many pronoun behaviors remain outside this grammar. The core uses Latin/Whitaker feature conventions behind a morphology interface; a genuinely language-independent rule system is not yet delivered. The dictionary optimizer remains unchanged.

The output is a **feasibility diagnostic with a boundary cost**, not a calibrated or smoothly graded grammaticality score. A fully covered stream receives minus its number of clauses, with a separately recorded boundary component. A failed or unsupported analysis has `score: null`; it is not assigned a score that can be optimized by dictionary search. Identical extra readings or additional parses do not increase reward. An alternative-parse query records whether another assignment is found, with a distinct unknown flag if that check times out. This is not an exhaustive ambiguity count.

Without supplied boundaries, exact dynamic programming searches partitions whose clauses contain **1–10 tokens** and have complete supported analyses. The shorter minimum permits omitted-subject finite predicates. Every boundary costs one point, so the model prefers fewer complete clauses and cannot rescue a nominal fragment by dropping it. The boundary cost is a fixed structural regularizer, not a normalized segmentation probability. Timeout is 250 ms per clause-solver query; unresolved queries cannot be treated as proof of grammatical failure or of segmentation optimality. The experiment recorded no solver-unresolved outputs. Since this iteration establishes feasibility only, it does not yet measure beam or marginalization approximation error.

## Reproduction and verification

```sh
.venv/bin/python -m benchmarks.grammar_restoration_iteration2
.venv/bin/python -m benchmarks.grammar_restoration_iteration2_ablation
.venv/bin/python -m benchmarks.grammar_restoration_iteration2_validate
.venv/bin/python -m pytest -q tests/unit/test_coherent_grammar.py tests/unit/test_grammar_diagnostic.py
```

Outputs are preserved in `experiments/results/grammar-restoration/iteration2/`; the runner refuses to overwrite them. The [fixed fixture file](../benchmarks/fixtures/grammar_coherent_v1.json) records examples, construction labels, explanations and gates. Outputs include the manifest, complete chosen morphology/attachment witnesses, ambiguity flags, supplied/latent comparisons, old-relaxation ablation, natural/historical transfer results, and saved morphology for replay. Source morphology provenance is retained in the manifest; the natural excerpts and corruption crops are checked against preserved iteration-1 artifacts.

**Twelve relevant tests pass**, including eight new coherent-grammar tests. They cover inconsistent reading reuse, witness tampering, government/head sharing, dropped fragments, person agreement and omitted subjects, complete latent partitions, duplicate-analysis invariance, ambiguity flags, cycles and length limits. The standalone validator replays **168 stream scores** from saved morphology, without the live dictionary or target annotations, and checks **76 complete clause witnesses without invoking the solver for the witness check**. It also verifies gates, summaries, fixture/code identities and transfer provenance; SMT is still used separately to replay feasibility results. The old-relaxation ablation is reproducible via its separate command.

The principal benchmark took approximately **1.40 seconds** in this run, excluding subsequent replay validation, ablation and tests. Peak memory was not measured. These small-fixture timings do not predict unrestricted grammar or dictionary-search costs.

## Decision and next step

Keep this coherent-analysis module and its regression cases. It improves the intended controlled behavior over the relaxation, but **do not integrate it into dictionary optimization yet**. The next falsifiable increment is source-only construction coverage: audit the short, fully analyzed natural regions that still fail, add explicitly supported constructions with independent minimal-pair controls, and measure whole-clause coverage before returning to flat 64-token streams. Extend morphology and valency without converting missing evidence into rewards. Keep the original eighteen passages as an already-inspected regression set and reserve fresh author-level material for confirmation after the expanded grammar is frozen.

No correct-dictionary stability run, blind-start recovery, nucleus estimate, lexical restoration percentage or Voynich inference was performed.
