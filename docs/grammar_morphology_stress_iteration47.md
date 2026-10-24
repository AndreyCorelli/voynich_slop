# Iteration 47: does agreement survive imperfect morphology?

**Agreement tolerates extra readings much better than lost or confidently replaced readings.** At25% of eligible word types given an extra reading,22 of the previous28 additional links remain uniquely recoverable on average. Replacing a reading on only10% of types already loses about58/326 reference links and produces5.8 unique wrong links. The practical requirement is a morphology lattice with high reference coverage, rather than narrow point tags.

These are controlled perturbations of the reused iteration46 oracle lattice, not an evaluation of a real morphology predictor or ciphertext restoration.

## Frozen setup

Keep iteration46's326 overt-subject constructions in304 sentences, oracle POS/eligibility, whole-sentence candidate domains, and unchanged subject–finite-verb agreement. The clean comparison has55 unique correct links without agreement and83 with agreement:28 additional links among the fixed270 initially ambiguous constructions.

Perturb Number/Person only. Case, VerbForm and POS remain unchanged, so this isolates the agreement channel. Preserve NOUN/PROPN grammatical third person. Perturbations are shared by every occurrence of a selected normalized word/POS type, including across sentences; errors are not independent per token.

There are934 eligible types among2477 observed word/POS keys in the selected sentences. Eligibility requires an observed relevant nominal/finite reading for which a number/person edit adds a support state not already represented. Fully unconstrained types cannot gain a new state and are not eligible. The generator sees dictionary readings and observed word/POS keys, never reference links or occurrence-specific reference morphology.

Freeze five seeds and nested type orders. Rates0/10/25/50/100% select0/93/233/467/934 types. The same selected types and one fixed original/alternative reading per type are used across four modes:

- **Extra:** keep every original reading and add one synthetic, source-unattested number/person reading.
- **Masked:** hide number/person for the selected type, retaining noun third person. Unknown features expand the candidate set.
- **Deleted:** remove the selected original reading. Removing the last eligible reading can remove a subject or finite-predicate candidate.
- **Substituted:** remove that same original reading and add exactly the alternative used by Extra.

“Unattested” refers to the oracle corpus dictionary, not a proof that an alternative is linguistically impossible. Rates are fractions of eligible **types**, not token error rates. Corrupting either endpoint can damage a relation, and frequent types affect many examples.

Freeze all100 prediction cells before evaluation. Each cell compares raw morphology candidates with agreement-filtered candidates. Exact reading survival, reference-link survival, unique correct/wrong links, empty sets and propagation are separate measurements. Five seeds reuse the same constructions; reported ranges are perturbation ranges, not confidence intervals.

## Added ambiguity degrades gracefully

The table counts additional unique correct links within the original270 ambiguous examples. The denominator is fixed before perturbation, rather than reselected from surviving references.

| Affected types | Extra reading: additional links, mean [range] | Features masked: additional links, mean [range] |
|---|---:|---:|
| 0% | 28 | 28 |
| 10% | 25.8 [23–28] | 24.2 [22–27] |
| 25% | **22.0 [20–24]** | **14.8 [14–17]** |
| 50% | 16.8 [14–19] | 6.6 [3–9] |
| 100% | 7.6 [5–11] | 0 |

Every reference link survives in both modes at every rate, with zero unique wrong links and zero empty sets. Adding one extra reading is less destructive than erasing all number/person distinctions for that type. When all informative types are masked, the extra agreement benefit disappears, matching iteration46's hidden-feature control.

**The zero-error result is conditional on support preservation.** These modes expand candidate sets that already contain every reference link; a singleton cannot then be a different link. The empirical result is how much discrimination survives the expansion, not proof that a real morphology predictor can supply this coverage.

Without agreement, raw link candidates remain unchanged in these modes and retain55 unique correct links. At25% Extra, agreement therefore yields77 unique correct links overall, versus55 raw, while preserving all326 references.

## Deletion and substitution are much less forgiving

Values are means across five perturbations. “Reference exact” refers to the full subject/verb number-person reading tuple; the clean agreement model already rejects one stored mismatched reading while retaining its link.

| Mode | Affected types | Reference links /326 | Exact reference readings /326 | Unique correct links | Unique wrong links | Empty candidate sets |
|---|---:|---:|---:|---:|---:|---:|
| Clean | 0% | 326 | 325 | 83 | 0 | 0 |
| Deleted | 10% | **267.0** | 266.0 | 72.2 | **6.6** | 21.2 |
| Deleted | 25% | 183.8 | 183.2 | 53.2 | 21.0 | 58.0 |
| Deleted | 50% | 80.6 | 80.2 | 30.8 | 36.2 | 132.8 |
| Deleted | 100% | 0 | 0 | 0 | 3.0 | 323.0 |
| Substituted | 10% | **268.2** | 266.0 | 69.8 | **5.8** | 18.8 |
| Substituted | 25% | 193.4 | 183.2 | 50.0 | 14.8 | 45.2 |
| Substituted | 50% | 115.2 | 80.2 | 33.6 | 22.0 | 78.2 |
| Substituted | 100% | 113.8 | **0** | 31.4 | 24.4 | 87.8 |

At10% Substituted, agreement retains252–281 reference links across seeds and generates4–9 unique wrong links. An incorrect singleton is a failure, not confident recovery. Empty sets should also be explicit failures or abstentions.

At100% substitution, some correct token links remain uniquely identified even though **no exact reference reading tuple survives**. Link accuracy alone would conceal complete morphology-support loss. There is no claim of grammatical recovery for those links.

## Retrieval loss versus agreement filtering

| Condition | Raw reference links | Agreement reference links | Raw unique correct/wrong | Agreement unique correct/wrong |
|---|---:|---:|---:|---:|
| Clean | 326 | 326 | 55 / 0 | 83 / 0 |
| Extra25% | 326 | 326 | 55 / 0 | 77 / 0 |
| Deleted10% | 267.0 | 267.0 | 48.0 / 4.8 | 72.2 / 6.6 |
| Substituted10% | 326 | 268.2 | 55 / 0 | 69.8 / 5.8 |
| Substituted25% | 326 | 193.4 | 55 / 0 | 50.0 / 14.8 |

Deletion usually removes the true link before agreement is applied: its raw domains have already lost an endpoint reading. Substitution preserves the endpoint identities but supplies incompatible features, so the true link disappears when hard agreement is imposed. Exact reading support is already missing upstream in both cases.

Extra and Substituted share the same synthetic reading. Their difference is whether the original reading is retained. The contrast therefore directly isolates the cost of committing to the replacement. At25% substitution, agreement has fewer unique correct links than the raw55-link baseline, plus14.8 unique wrong links.

Do not interpret candidate shrinkage or ambiguous-cohort wins alone as improvement. For example, Deleted50% still uniquely resolves17.2 of the original ambiguous examples, but loses most references and generates36.2 unique wrong links overall.

## Propagation and wrong-anchor rejection

With the correct subject token supplied, the number of newly resolved predicate choices falls from61 clean to47.6 under Extra25%,31.0 under Masked25%, and0 under Masked100%. This follows the available agreement information, rather than an optimizer changing its preference.

Replay exactly the487 wrong-token probes from iteration46, including248 wrong predicates with the opposite reference subject supplied. Among probes where the exact reference remains agreement-compatible and the wrong pair is present in raw support:

| Condition | Eligible wrong-predicate probes | Rejected by agreement |
|---|---:|---:|
| Clean | 247 | 143 |
| Extra25% | 247 | 122 |
| Masked25% | 247 | 89.4 |
| Substituted10% | 201.6 | 118.8 |
| Substituted25% | 138.8 | 87.0 |
| Substituted100% | **0** | **0** |

Coverage matters. With full substitution, the unconditioned test would appear to reject184.8/248 wrong predicates, more than the clean143. But no exact reference readings survive, so this cannot be credited as successful grammatical discrimination. The covered denominator prevents that misleading conclusion. It is a diagnostic based on gold availability, not a deployable confidence gate.

## Implication

The agreement hypothesis survives **overgeneration**: the correct reading can coexist with extra possibilities and still permit useful relation filtering. It does not tolerate unsupported certainty. A practical next step must obtain a high-coverage morphology lattice without using the analyzed sentences' gold readings, then measure coverage/cardinality and the structural gain together on held-out source data.

Missing analyses should be compared with an explicit unknown-reading fallback rather than silently forbidding the token; Masked and Deleted illustrate the very different outcomes. Applying such a fallback to uncertain cases in practice requires an independently estimated uncertainty signal—the synthetic perturbation flags are not a usable oracle.

Do not yet add a hard-agreement stage over one-best predicted tags. Preserve alternatives and abstain from treating uniqueness as correctness when candidate support may be incomplete. The tested POS, case, finite-status and construction-existence channels remain privileged, and their errors were not studied here.

## Verification and artifacts

377 regression tests pass. Validation reconstructs all100 cells, replays60,800 sentence/arm predictions and65,200 reference summaries, decodes1,421,486 reading tuples, and checks51,680 support inclusions. It verifies nested additions/masks expand support, deletion shrinks it, and matched support satisfies Deleted⊆Substituted⊆Extra⊆Masked. Case/VerbForm and nominal third person are preserved. All115 frozen-input hash checks pass; prior queries and reserved200 remain unscored.

Run `python -m benchmarks.grammar_morphology_stress_iteration47` (refuses overwrite), then `python -m benchmarks.grammar_morphology_stress_iteration47_validate`. Core code is `src/voynich_smt/morphology_stress.py`. Artifacts under `experiments/results/grammar-restoration/iteration47/` include the frozen declaration, word-type schedules, compact full morphology supports, per-cell evaluations for both authors, aggregated seed means/ranges, wrong-anchor diagnostics and validation. Previous artifacts and the shared todo remain unchanged.
