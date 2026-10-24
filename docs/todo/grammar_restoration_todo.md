# Agent task: Grammar-first Latin word-substitution decoder

## Objective

Build and evaluate a **grammar-first scoring module** for unsupervised, injective whole-word substitution decipherment. Start with Latin, but keep the optimizer and grammatical-scoring interfaces language-neutral so other historical languages can be added later.

The input is a continuous sequence of encoded word tokens. **Word boundaries and order are known; sentence and clause boundaries are not.** Do not assume plaintext hints, the target vocabulary, or the decoding key at inference time.

The immediate goal is **not** to decipher Voynich. It is to demonstrate on held-out Latin substitution benchmarks that grammatical structure provides a useful and independently validated decoding signal, without repeating the failures of frequency-dominated bigram/trigram scoring.

## Existing experimental evidence (do not rerun blindly)

- Earlier Latin decoder: 32,004-token development text, with all correct words included among distractors, recovered 6.94% at initialization and 6.74% after optimization; 9–11 correct types out of 8,220.
- Starting from a 100%-correct dictionary, the original objective degraded token accuracy to 82.80% under strict greedy ascent and 69.58% under annealing.
- With uniform fallback smoothing, all ten audited first corruption moves became score-decreasing, but full optimization degraded the correct dictionary further: 73.35% greedy and 58.25% annealing.
- An audited original corruption `intulerat → perlectam` gained 11× through smoothing, lost 2× on next-word probability, and therefore gained ln(5.5) ≈ 1.704748 despite no observed supporting bigram or trigram.
- All 30 searches in a fully covered calibration found incorrect dictionaries scoring above the true dictionary. Candidate coverage alone is not a solution.
- A separate **exact-plaintext-vocabulary-only, unknown-mapping** benchmark has not been documented. Do not claim otherwise.
- The later scalable decoder's dynamic shortlist was **not** tested with a guarantee that every correct candidate appears in each shortlist. Keep that limitation separate.

## Design principles

1. **Grammar is primary.** Evaluate whether candidate surface forms can participate in coherent syntactic analyses. Corpus word frequency and n-gram likelihood are secondary signals, not substitutes for grammar.
2. **Unknown boundaries are latent.** Jointly consider possible clause/sentence segmentation and grammatical analyses; do not insert reference punctuation at inference time.
3. **Do not hard-code rigid Latin word order.** Support inflectional agreement, free word order, subordinate clauses, participles, omitted subjects, and morphological ambiguity.
4. **Do not equate grammaticality with exact lexical identity.** Two compatible nouns or synonyms may be indistinguishable grammatically; report ambiguity instead of fabricating confidence.
5. **No oracle leakage.** Reference dictionaries, plaintext, gold annotations, and correct vocabulary may be used only in explicitly labeled diagnostic/oracle experiments, never in the actual unsupervised decoder.
6. **Prevent reward hacking.** Guard against artificial gains from training-vocabulary membership, backoff denominators, excessive parse ambiguity, or arbitrarily short segments.
7. **Generalizable architecture.** Keep language-specific analyzers, parsers, boundary priors, and lexicons behind explicit interfaces. Consider Universal Dependencies features as a shared representation, without assuming that a UD parser is accurate on all historical Latin.

## Proposed architecture

```text
Encoded word stream (known token boundaries)
       |
Injective dictionary assignment / search [language-independent]
       |
Candidate Latin surface-form stream
       |
Morphological lattice [Latin adapter: lemma, POS, case, number,
                      gender, person, tense, mood, voice, ambiguity]
       |
Latent segmentation + grammatical analysis
       |
Structural score with separately logged components
       |
Dictionary ranking and optimization
```

Define interfaces approximately as follows (adapt to repository conventions):

- `LanguageAdapter.analyze(surface_form) -> list[MorphAnalysis]`
- `LanguageAdapter.score_structure(tokens, segmentation, analysis) -> ScoreBreakdown`
- `BoundaryModel.candidates(tokens) -> bounded candidate segmentations`
- `GrammarScorer.score(tokens) -> ScoreBreakdown` (internally approximates or marginalizes over boundaries and parses)
- `DictionaryObjective.score(mapping, encoded_stream) -> ScoreBreakdown`

Avoid expensive full-document reparsing on every dictionary proposal. Explore cached morphological analyses, local windows, affected-region invalidation, and bounded/beam inference. Make approximation errors measurable.

## Scoring approach

Start with an interpretable structural baseline before adding a complex learned parser:

- Morphological agreement (e.g., modifier–noun case/number/gender; subject–finite verb person/number where applicable).
- Clause completeness and plausible predicate/argument structures, allowing ellipsis and Latin constructions.
- Verb valency and compatibility, with calibrated uncertainty.
- Dependency plausibility beyond adjacent word pairs.
- A segmentation prior learned or calibrated on Latin with punctuation removed; penalize pathological oversegmentation.

A conceptual objective is:

\[
S(D)=\log\sum_{B,G} P(B,G\mid \text{surface forms under }D)+S_{\mathrm{secondary}}(D),
\]

where `D` is a dictionary, `B` latent boundaries, and `G` grammatical analyses. **This is a design sketch, not a claim of a normalized or tractable model.** Explicitly specify probability normalization, parse ambiguity treatment, length normalization, and how approximations are made. Compare marginal/beam aggregation with best-parse scoring; avoid rewarding nonsense solely for having many possible parses.

## Implementation phases and gates

### Phase 0 — Repository audit and reproducible baselines

- Locate existing Latin corpora, encoded streams, saved corrupting moves, original and uniform-fallback scorers, and benchmark scripts.
- Reproduce the documented baselines when feasible; report any discrepancies rather than silently changing data or settings.
- Record corpus provenance, Latin period/style, train/development/test split, tokenization, vocabulary coverage, and available morphology/dependency annotations.
- Preserve all existing results and make new experiments reproducible with seeds and configuration files.

### Phase 1 — Standalone grammar diagnostic (no dictionary search)

- Strip punctuation and sentence-boundary markers from held-out Latin plaintext; retain reference segmentation only for evaluation.
- Score intact text, the ten saved first corruptions, and a broad, seeded set of synthetic substitutions.
- Stratify substitutions by: out-of-training-vocabulary vs attested; frequency; POS and morphology compatibility; token frequency; context; and corruption magnitude.
- Include grammatical near-substitutions and semantically wrong but grammatically valid replacements as **hard negatives**.
- Compare score deltas against intact text and report confidence intervals across texts/authors.
- Inspect each score component to identify shortcuts or artifacts.

**Gate:** Prefer intact references to known corruptions and to a substantial majority of structurally incompatible negatives on independent held-out texts. Do not set or claim a numerical pass threshold after inspecting test results; establish it using development data first. A grammar-only model is not expected to distinguish all grammatically equivalent replacements.

### Phase 2 — Correct-dictionary stability

- Initialize the dictionary at 100% token accuracy and run strict greedy ascent using the new objective.
- Track first improving corruption, score delta, token/type accuracy, changed entries, and grammatical explanations.
- Repeat across multiple Latin authors and styles; test annealing separately, since annealing is allowed to accept temporary deterioration.
- Compare against original and uniform-fallback objectives under identical data and budgets.

**Gate:** A meaningful reduction in greedy corruption, reproducible on held-out texts. Do not treat annealing's final accuracy alone as evidence of objective alignment.

### Phase 3 — Recovery without plaintext hints

- Run random and frequency-based initializations, multiple seeds, and identical search budgets.
- Measure token accuracy, type accuracy, precision and coverage of high-confidence frequent-word nuclei, objective rank of the reference dictionary, and runtime.
- Run ablations: grammar only; old LM only; grammar + secondary lexical evidence; with/without boundary model; best parse vs approximate marginalization.
- Separately test (a) oracle vocabulary with distractors, (b) exact plaintext vocabulary only but unknown mapping, and (c) realistic candidate retrieval. Clearly label oracle experiments.
- For shortlist-isolation, explicitly ensure the correct candidate is present in every relevant dynamic shortlist **only in a diagnostic condition**.

**Gate:** Demonstrate improvement over the old decoder on independent Latin texts, not merely better ranking near a known correct dictionary.

### Phase 4 — Transfer readiness

- Document which features are Latin-specific and which are reusable.
- Demonstrate that a second language adapter can be introduced without modifying the core dictionary optimizer or scoring orchestration; a full second-language benchmark is optional at this stage.

## Metrics and reporting

For every experiment, record:

- Text/author, split, number of tokens and types, OOV rate, candidate coverage, and exact dictionary constraints.
- Token accuracy, type accuracy, correct high-confidence mappings, nucleus token coverage, and calibration/precision of confidence claims.
- Correct-reference score, optimized-output score, and score differences; separate score components and normalized scores.
- Segmentation quality where reference boundaries exist, parser coverage/failure rate, inference approximation settings, wall-clock time, and memory use.
- Seeds, proposal counts, accepted moves, and whether optimization was greedy or annealed.

Do not report a fluent-looking reconstruction as decipherment without independent evidence of exact lexical recovery and generalization.

## Deliverables

1. A short repository audit and experiment plan before major implementation.
2. Modular code for Latin morphology/grammar scoring and latent-boundary handling, with tests.
3. Reproducible benchmark commands/configurations and saved outputs.
4. A concise report comparing baselines, diagnostics, ablations, failures, and held-out results.
5. A recommendation: integrate into dictionary search, revise the grammar model, or stop because the evidence is insufficient.

## Agent working instructions

Work incrementally. **Do not launch expensive full-decoding runs until the standalone grammar diagnostic passes its development gate.** Prefer the smallest falsifiable experiment at each step. Do not silently substitute modern-language grammar or punctuation-dependent parsers. State any data, tool, or compute limitations and distinguish observed findings from hypotheses. Preserve negative results: the goal is reliable recovery, not merely a higher model score.

## First iteration completed

The [Phase 0 / standalone Phase 1 pilot](../grammar_restoration_iteration1.md) is implemented and independently replay-validated. Its relaxed morphology/latent-segmentation score fails the frozen gate: 0/10 saved first corruptions are rejected, and intact preference on POS-disjoint substitutions is 17–33% across the three authors. Four focused tests pass. No Phase 2 stability or full-decoding runs were launched; the recommendation is to revise consistent grammatical analysis and predicate/argument modeling before integration.

## Coherent-analysis iteration completed

The [second iteration](../grammar_restoration_iteration2.md) adds consistent morphological choices, complete acyclic attachments and full-coverage latent segmentation. All 16 controlled minimal pairs, 14 valid controls and four two-clause pairs behave as specified in supplied/latent modes; twelve relevant tests pass and saved outputs independently validate. Natural-text transfer is still unsupported for all eighteen complete passages, so this is a controlled-subset success, not a passed natural-author gate or a restoration gain. Continue with construction/morphology coverage; dictionary search remains unrun.

## Natural structural-recovery iteration completed

The [third iteration](../grammar_structure_iteration3.md) evaluates partial predicate/clause structure directly on 601 natural Latin tokens, with source-only fitting and supplied/hidden boundary ablations. Hidden-boundary finite-predicate F1 reaches 86.49% on Sallust and 93.02% on Suetonius, but the linker collapses to all ROOT and recovers no non-root clause edges. Corruption and explicit oracle-repair diagnostics are preserved; nineteen relevant tests pass. The combined structural gate fails. Revise/validate the linker on source/development material before fresh confirmation or dictionary optimization.

## Predicate-linker isolation and ranking completed

The [fourth iteration](../grammar_linker_iteration4.md) isolates gold-predicate and boundary effects, audits three/six/full parent pools, and compares source-only conditional and typed parent ranking. The old model recovers no links even with both oracles and all parents available. Typed ranking reaches 43.59% source-validation non-root F1 versus 40.49% nearest-previous, with ROOT F1 79.56% and recall 86.06%; the 3.10-point gain misses the frozen five-point gate. Neither new model is evaluated on targets. Thirteen relevant tests pass; 936 forests and independent source refits validate. Continue with source marker/attachment evidence before target transfer or dictionary search.

## Explicit marker-attachment iteration completed

The [fifth iteration](../grammar_markers_iteration5.md) adds a source-trained marker-to-predicate/NULL model, single-target marker consistency and typed parent interactions. Both variants pass the frozen fresh-source point-estimate gate: non-root F1 44.18–44.62% versus 36.04% nearest-previous, with ROOT recall above 85%. Detected/hidden target edge F1 is 29–30% Cicero, 40% Sallust and 14% Suetonius; two authors remain below the simple baseline. Nineteen relevant tests pass; three source models independently refit and 1,680 forest/marker conditions validate, with six explicit source abstentions retained. No dictionary search; prioritize construction diversity and marker-scope/parent error analysis before further transfer claims.

## Marker-oracle bottleneck diagnostic completed

The [sixth iteration](../grammar_marker_oracle_iteration6.md) freezes parent weights and compares predicted markers, correct recognized-marker scope/NULL decisions, and complete gold marker/classes, crossed with predicate and boundary oracles. Perfect markers give inconsistent gains; even with gold predicates, markers and sentence boundaries, the reference forest is strictly outscored in 10/12 target streams for each model. An exact linear example shows generic feature blocks outweighing correct subordinate-marker evidence. Twenty-five tests pass; 684 conditions and 570 completed reference-score comparisons validate. Prioritize source-only parent-score alignment, exposure controls and representation audits; no dictionary optimization.

## Parent training alignment diagnostic completed

The [seventh iteration](../grammar_training_alignment_iteration7.md) crosses gold versus out-of-fold marker training with gold versus predicted source evaluation markers, holding parent features, pools and fitting groups fixed. Fresh same-author confirmation reaches 45.09% non-root F1 under gold/gold and 46.56% under predicted/predicted; the out-of-fold training gain with predicted markers is 2.46 points with a paired interval spanning zero. Gold/gold still strictly outscores the correct forest in 49/65 completed streams. No exact candidate-feature collisions were found, which does not establish linguistic sufficiency. One-round optimizer-negative training corrects all 47 collected fitting contrasts but collapses on confirmation to 1.41% edge F1 with gold markers. Thirty-one focused tests pass; eight model refits and 872 forest conditions independently validate, retaining eleven saved abstentions. Do not integrate into dictionary search. Next examine complete source-choice feasibility and a conditional objective retained alongside iterative structured constraints, using development before a new fresh confirmation.

## Boundary/role oracle checks and residual audit completed

The [eighth iteration](../grammar_boundary_role_iteration8.md) reuses inspected source passages with frozen iteration 7 scores and identical gold predicates/projected markers. Primary confirmation edge F1 is 44.37% unrestricted, 51.49% with gold boundaries, 62.66% with gold relation labels, and 71.52% with both; ROOT identity is supplied in the role oracle. Both-oracle accuracy among genuinely ambiguous non-root children remains 75/120 (62.50%), and 23/66 reference forests remain outscored. The 17-case development review exposes a concrete reference-projection issue: finite-ancestor traversal skips auxiliary child branches, misrouting some relative markers and omitting markers on nonfinite lexical heads. This qualifies earlier “gold marker” claims. Before another scorer, normalize predicate complexes and audit a separately versioned reference; preserve old metrics. All 1,056 conditions and 44 independent Z3 checks validate. No dictionary search.

## Predicate-complex reference repair completed

The [ninth iteration](../grammar_predicate_complex_iteration9.md) introduces `predicate-complex-v1` without changing tokens, finite positions, splits or old artifacts. Contracting supported auxiliary/copular complexes repairs the 13305 relative-parent/marker regression, adds 93 and retargets 35 training markers, and explicitly flags unsupported components. On a common revised confirmation reference and marker evidence, gold-trained parent refitting raises hidden-boundary F1 from 47.50% to 54.60% with reference markers and 45.16% to 52.51% with predicted markers; the out-of-fold refit reaches 55.36% with predicted markers. These are inspected same-author results, not fresh transfer. Both-oracle ambiguous-parent accuracy remains 84/138 (60.87%), and sixteen of seventeen reviewed errors persist. The marker-only block cannot distinguish same-role parent candidates; prioritize a parent-dependent interaction/scope ablation on the repaired target. Forty tests pass; 1,200 independent sentence projections, seven refits, 4,224 forests and 88 Z3 checks validate. No dictionary search.

## Repaired-reference parent-interaction ablation completed

The [tenth iteration](../grammar_parent_interactions_iteration10.md) tests the existing 282-feature parent interaction variant against the frozen 249-feature models, keeping repaired references, marker fits, out-of-fold evidence and 1,385 fitting groups fixed. Primary development ambiguous-parent accuracy with both oracles rises from 77.17% to 81.52% with reference markers and 84.78% with predicted markers, but unrestricted predicted-marker F1 falls from 62.30% to 60.67%. The predeclared primary gate fails; interaction models are not evaluated on confirmation or targets. Cross-sentence parent choices increase from 36 to 41 without oracles, while supplying boundaries improves predicted-marker F1 from 73.50% to 77.14%. Marker evidence now affects fixed-role parent choices, but reliable grouping is still needed. Forty-two tests pass; two refits, 2,112 conditions, 1,056 reproduced controls and 104 independent Z3 checks validate. Next test source-only predicate grouping/compatibility before promoting another scorer; no dictionary search.

## Source-trained predicate-grouping signal tested

The [eleventh iteration](../grammar_predicate_grouping_iteration11.md) fits distance-only and richer same-sentence classifiers on 3,484 source pairs using frozen out-of-fold marker evidence. The primary rich soft signal fails development: interaction-parent F1 falls from 60.67% to 55.83%, and cross-sentence parents fall only from 41 to 37. Distance-only soft scoring stays near baseline at 60.35%. Rich hard filters/contiguous grouping retain only 94/154 and 87/154 true parents. Overall pair AUROC near 81% hides poor separation of reference parents from decoder-selected cross-sentence errors (48.13% rich, 44.25% distance). No confirmation or target evaluation. Forty-five tests pass; two refits, 2,112 forests, 264 exhaustive partition checks covering 13,684 partitions, 528 reproduced controls and 104 independent Z3 checks validate. Next inspect distance-controlled, decoder-confusion pair discrimination with fully cross-fitted source negatives before composing another grouping score. No dictionary search.

## Distance-controlled decoder-confusion test completed

The [twelfth iteration](../grammar_decoder_confusions_iteration12.md) generates source errors with end-to-end nested cross-fitting (16 marker and four interaction-parent fits), then matches reference edges to actual cross-sentence errors within author, exact predicate gap and token-distance bucket. All 131 source negatives and 40/41 development negatives match without positive reuse; 37/40 development matches also have exactly equal token distance. The rich classifier fits source preferences at 92.37% but reaches only 42.50% matched development AUROC, 32.50% pooled preference and 35% same-child preference. The distance refit is mostly tied on matched pools; paired intervals are wide and show no useful rich-feature gain. The screen fails. No score composition, confirmation/target decoding or dictionary search. Forty-seven tests pass; 22 independent refits, 266 held source forests and 16 Z3 checks validate. Next inspect construction-level evidence and consistent analyses on controlled source contrasts before further scoring changes; numerical feature differences alone are insufficient.

## Small nonlinear capacity check and construction audit completed

The [thirteenth iteration](../grammar_nonlinear_contrasts_iteration13.md) tests five strongly constrained depth-two boosted trees on the unchanged 131 matched source contrasts. Rich nonlinear development preference improves from the linear model's 32.50% to 57.50% on forty matched pairs and from 35% to 60% on twenty same-child contrasts, but matched AUROC is only 57.88% and the diagnostic screen still fails. Intervals are wide; this does not establish a reliable gain over geometry. Auditing all twenty cases finds ten relative/free-relative, six conditional, three temporal and one causal construction; seven relative cases have an annotated nominal bridge. Prioritize a consistent relative-pronoun/nominal-antecedent/governor mechanism, with annotation ambiguities retained explicitly. A separate registry reserves 200 unscored source sentences at retained author positions 700–799, disjoint from earlier declared grammar samples. Fifty-one tests and independent refit/audit/holdout checks pass. Validated artifacts are `iteration13-v2`; the inclusive-screen numerical fix leaves models and predictions unchanged. No score integration or dictionary search.

## Consistent relative bridge diagnostic completed

The [fourteenth iteration](../grammar_relative_bridge_iteration14.md) enumerates relative-pronoun → nominal-antecedent → direct finite-governor bridges using one consistent nominal reading, independent morphology/valency and explicit abstention. All ten multi-predicate probes pass; a mixed-reading ablation demonstrably invents a false bridge. On 67 inspected development relatives, reference scope/hidden boundaries yields 11 correct among 19 unique parent claims; supplied boundaries gives 12/14. Predicted scope/hidden boundaries gives 9/16 versus the existing decoder's 11/16 on those cases. Crucially, only three of the eleven correct-parent reference-scope claims have any antecedent on the annotated nominal path, and none excludes all spurious antecedents. Parent hits do not establish restoration of the grammatical bridge. Current artifacts are `iteration14-v3`, preserving earlier person-agreement and deponent-valency corrections. Fifteen mechanism tests and 51 combined relevant tests pass; 302 decisions and 152 natural witnesses replay, and all 200 reserved sentence IDs remain unscored/disjoint. Next constrain relative span and antecedent constituency, then add one licensed nonfinite governor step; evaluate antecedent and parent separately. No scorer integration or dictionary search.

## Antecedent constituency and one nonfinite step completed

The [fifteenth iteration](../grammar_relative_constituents_iteration15.md) adds a bounded single-head nominal constituent with joint morphology, then one participial/shared-subject or modal/infinitive governor step. Fourteen multi-predicate probes pass. Against annotation-path identity on inspected development, reference-scope/hidden-boundary unique antecedents improve from 4/16 in the comparable readings control to 11/14; unique complete chains improve from 0/10 to 5/10. The mechanism recovers `parte → locare → debemus`; `aluearia → habens → accedat` remains blocked by dictionary coverage. With predicted scope it restores only 4/67 reference chains, and parent substitutions correct two decisions but spoil two. A false `praesentia → fecundare → debemus` chain exposes missing ownership of the earlier `creduntur ... fecundare` complex; supplied boundaries remove it. Optional declared `habere/locare` object frames help controlled probes but do not change natural predictions. Current artifacts are `iteration15-v2`; a shared wildcard-binding correction preserves all candidate sets and metrics. Twenty-three new tests and 74 combined relevant tests pass; 1,184 decisions replay and 429 witnesses pass independent local SMT checks. The 200 reserved sentences remain unscored. Next test competing ownership of nonfinite predicates within licensed finite complexes; keep morphology coverage and antecedent/path/parent evaluation separate. No scorer integration or dictionary search.

## Joint nonfinite ownership diagnostic completed

The [sixteenth iteration](../grammar_nonfinite_ownership_iteration16.md) adds consistent ownership choices, a simple one-infinitive slot per finite frame, passive reporting licenses and noncrossing constraints, retaining ambiguity and component-local abstention. Ten multi-predicate probes pass, including a single-sentence case where the correct owner is farther than the nearest compatible one. Under the bounded frame-completeness assumption it excludes `fecundare → debemus` and preserves `locare → debemus`. On 163 inspected annotated nonfinites, joint ownership makes 10/11 correct firm choices versus nearest attachment's 16/20: higher selected precision, lower coverage. The initial pool contains only 27 reference owners. Predicted-scope complete relative recovery stays 4/67; removal of one path can also make a wrong direct path unique. An unrestricted unknown-owner ablation restores the motivating ambiguity, exposing dependence on frame completeness. Four conflicting components identify missing `nolite`/`solent` constructions and coordinated infinitive units; the sole wrong firm owner misses a perception construction under `uiderint`. Prioritize governor-candidate coverage and explicit coordinated units before uniqueness or scorer integration. Current artifacts are `iteration16-v2`, preserving optional noun/participle selection and the initial archived run. Twenty-five new tests and 99 combined relevant tests pass; independent Boolean CSPs verify 1,176 components, 1,296 owner projections and 32 conditional bridge decisions, alongside artifact/local-witness/metric replay. All 200 reserved sentences remain unscored. No scorer integration or dictionary search.

## Governor coverage and coordinated complement units completed

The [seventeenth iteration](../grammar_complement_units_iteration17.md) adds negative-imperative, habitual and bounded explicit-accusative perception licenses, plus optional two-infinitive coordination units sharing one finite complement slot. Unknown ownership remains available everywhere without a penalty. Fourteen controlled probes pass. On inspected development, reference-owner coverage rises from 27/163 to 31/163, repairing two `timere → nolite` edges, `nocere → solent` and `instare → uiderint`; the competing owners remain ambiguous. A fixed expanded subset of covered reference edges is jointly feasible in 18/23 streams with previous frames, 22/23 with added frames, and 23/23 with coordinated units. This is partial reference-subgraph compatibility, not complete parsing or restored ownership: all models make zero firm owner claims. The sole natural pair, `conlocare/aperire → debemus`, matches annotated coordination; broader quality is untested. Controls retain split ownership for unrelated complements and reject markerless/finite-crossing pairings. The motivating `fecundare/locare` ambiguity remains open. Next test local construction-span/argument recognition against competing governors before any commitment; do not substitute candidate availability or token-coverage preference for that evidence. Twenty-five new tests and 124 combined relevant tests pass; 792 natural models, 924 owner projections and 1,584 reference-subgraph queries replay with independent exhaustive unit-cover checks. All 200 reserved sentences remain unscored. No restoration rerun, scorer integration or dictionary search.

### Iteration 18 — construction interiors (completed)

See [local construction-span diagnostic](../grammar_construction_spans_iteration18.md). Fourteen controlled probes pass. On inspected development, a finite barrier retains 21 reachable reference infinitive governors and yields 20/20 single supported governors; typed interior cover drops to 14/14 and does not improve natural ambiguity resolution beyond POS coverage. Missing dictionary readings block five correct infinitives; coordinated nominal arguments and an ablative participial construction block two more. The nocere+dative license is explicit and ablated (14→13 supported correct). No firm ownership claims, no complete-clause or restoration rerun, and the 200 reserved sentences remain unscored. Next: separate oracle-morphology ablation for blocked constructions, then bounded coordinated-NP and ablative-participial support with negative contrasts.

### Iteration 19 — oracle missing morphology (completed)

See [oracle morphology diagnostic](../grammar_oracle_morphology_iteration19.md). Five absent readings, supplied only on inspected development with frozen candidates/grammar, lift lexical/POS reference-link retention 16→21 and typed retention 14→16 (66 reference infinitives). Both noun readings in `olerum pulices` and the modifier `sua` are necessary for the two gains; `ferulis` and `aluearia` still expose grammar failures. The accepted `sua praesentia` witness attaches the ablative to the wrong predicate, so correct owner links do not establish grammatical restoration. Five reachable links now fail typed coverage; another 45 lack their reference governor in the input pool. Next: argument-attachment and coordinated-object contrasts, then separate ablative and particle ablations, with oracle morphology kept separate. 264 oracle + 1,320 leave-one-out replays; reserved 200 sentences unscored.

### Iteration 20 — coordinated arguments and attachment (completed)

See [argument structures diagnostic](../grammar_argument_structures_iteration20.md). Eleven controlled cases and 2,112 natural conditions distinguish nominal coordination, explicit `perd` object valency, and attachment alternatives. Coordinated `et animam et corpus perdere` adds one matching local structure only with the declared frame. Joint governor-link retention reaches 16 with dictionary / 20 with oracle morphology, but only 14 / 16 have a saved local-link-and-POS matching witness; these are bounded fragments, not full restoration. `sua praesentia` retains both matrix and infinitive attachment and is unresolved. Broad ablatives admit incorrect participial/nominal covers for `defensis sedibus` and `nisi uespere instante`. Next: explicit agreeing ablative participial constructions and a separate `nisi` frame, with internal dependency/POS contrasts against nominal homographs. 179 tests; 1,083 structures independently checked; 200 reserved sentences unscored.

### Iteration 21 — agreeing ablative participles and nisi (completed)

See [participial-structure diagnostic](../grammar_participial_structures_iteration21.md). Explicit subject–VPAR ablative agreement in either order, plus a separately enabled `nisi` marker frame, makes the motivating reference structures available. Dictionary local matching-analysis coverage rises 14→15; oracle-morphology coverage rises 16→19. Unique matching counts remain 13 / 14, and governor retention stays 16 / 20: this fills a representation gap without resolving selection. `defensis sedibus` has one reference match among eight structures per unit; the coordinated `nisi uespere instante` case has one among 27 with oracle `aluearia`. Nominal homographs and attachment/sharing alternatives remain. Next: contrastive selection audit on fixed structures, distinguishing lexical-category evidence from attachment ambiguity, with no dependency-oracle selection. 207 tests; 1,584 natural replays; 1,276 structures checked; 200 reserved sentences unscored.

### Iteration 22 — challenge selection and measurement (completed)

See [structure preference challenge](../grammar_structure_preferences_iteration22.md). After deduplicating lexical readings and scope repeats, only four oracle-morphology examples have an available reference structure plus competitors. A post-hoc, tie-preserving construction/frame preference uniquely matches 3/4 with no unique mismatch; both global matrix and infinitive defaults fail a case. The remaining first/second/shared object tie collides in structural/frame features. A linear fit needs a positive distance coefficient to favor the farther reference attachment, demonstrating an overfitting route rather than validated selection. Oracle reading constraints leave 1/2/4/9 candidates. Relaxed NP/participle and shared-object equivalences do not remove the final ambiguity; a separate substantivized-ADJ/matrix-object ↔ nominal-ACI-subject correspondence reveals compatible `malum` readings hidden by strict evaluation. Diagnosis is mixed: preferences, feature distinctions, unit scope and annotation normalization. Next: freeze evaluation correspondences, then challenge the frame default on fresh training-material contrasts; keep candidate absence distinct from ranking error. 231 tests; reserved 200 sentences unscored.

### Iteration 23 — grammar under artificial ciphers (completed)

See [cipher relation benchmark](../grammar_cipher_relations_iteration23.md). Fresh declared tests (100 Jerome / 100 Caesar), 767 source training sentences, 40 separate tuning sentences, models/thresholds frozen before scoring. Directed labeled edge F1 for repetition / anonymous endings / revealed Latin ending oracle / dictionary morphology oracle is 12.1/17.2/26.8/52.4% on Jerome and 10.3/10.7/12.5/35.2% on Caesar. Anonymous-ending gain does not clearly transfer to the new author; opaque outputs are often cyclic. Masked context Number balanced accuracy is near chance for blind signals. A direct masked-link/oracle-context-Number audit shows that number prediction can improve with mostly incorrect dependencies, so it is not a substitute for labeled-link evaluation. Cipher keys are unseen and features invariant; unlabeled full-split frequency statistics are transductive; privileged ending/morphology arms are explicit upper bounds. Next: unlabeled distributional word/ending-class signatures, mask-aware fitting and coherent abstaining decoding, with a newly declared evaluation slice. 254 tests; reserved 200 sentences remain unscored.

### Iteration 24 — distributional profiles and reliable skeleton (completed)

See [distributional skeleton experiment](../grammar_distributional_skeleton_iteration24.md). New 40-sentence tuning and 100+100 tests, matched 400-sentence unlabeled test backgrounds, source-only 8 word/8 ending prototypes, leave-current-sentence-out profiles, shuffled-context control and three-bootstrap consensus with acyclic abstaining decoding. Profile F1 is 14.1 vs baseline 12.7% on Jerome, 5.8 vs 7.6% on Caesar; shuffled profiles reach 11.1% on Caesar. No anonymous arm qualifies even for the conservative 50% precision policy, and ordered profiles recover no complete shared-head S/O fragment. Source-mapped morphology probes remain weak. A separate privileged 20-target-sentence readout diagnostic lifts simpler frequency-class coarse POS to ~75% balanced accuracy on the remaining 80, while context prototypes improve much less. Next: isolate anonymous-class alignment from information loss using oracle/inferred/shuffled alignments before adding parse complexity. 270 tests; 3,200 prediction rows verified; reserved 200 sentences unscored.

### Iteration 25 — exact anonymous-class alignment (completed)

See [class alignment experiment](../grammar_class_alignment_iteration25.md). New 100+100 query sentences and 200+200 background sentences; source-only fixed class distributions. The primary channel supplies true POS classes under an unknown permutation, so it is an alignment upper bound, not class induction. Pooled transition scoring exactly recovers all 3/8 classes on both corpora; fine frequency-only accuracy is 25/37.5%. Through 25% injected class noise, pooled transition scoring reaches the oracle alignment ceiling. Shuffling context and single-author source templates expose order/domain sensitivity; 50% noise breaks fine Jerome alignment. A separate bounded eight-frequency-group proxy reaches 45.3/40.5% balanced accuracy versus oracle 54.2/47.4%, showing representation loss plus an alignment gap; it is not the full iteration24 representation. Next: induce latent soft classes with fixed source transitions and word/ending sharing, comparing oracle/learned/shuffled emissions and checking state collapse. 286 tests; 1,851,156 objective/map scores independently checked; reserved 200 sentences unscored.

### Iteration 26 — fixed-transition latent class induction (completed)

See [latent class induction](../grammar_latent_classes_iteration26.md). Five EM starts per arm, pooled/single-author fixed source transitions, fresh100+100 queries and100+100 backgrounds, old development calibration, anonymous words and factorized ending sharing. Word balanced eight-class accuracy reaches27.52/13.64% (Jerome/Caesar); ending28.45/13.13%, below shuffled-ending29.10/15.35%. Oracle-permuted clusters remain weak; all eight states are occupied, but high confidence is unreliable. Oracle supervised emissions reach98.61/97.19%, a privileged in-sample capacity check. Word/ending edge F1 is6.08/6.13% Jerome and2.82/2.99% Caesar, with no correct anonymous shared-head S/O fragment. Oracle-class edge F1 is38.36/23.14%, exposing a separate attachment limit. All90 primary fits hit80 updates; development-only continuation converges at445/370 total updates without improving class accuracy. Next challenge the unlabeled objective from supervised emission initialization on existing development, tracking the first class-corrupting update; do not assume the global optimum was tested. 292 tests,90 full deterministic fit replays; reserved200 unscored.
