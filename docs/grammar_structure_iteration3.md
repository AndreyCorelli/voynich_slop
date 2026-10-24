# Predicate and clause-structure restoration: natural-text pilot

## Frozen experiment

The target of this iteration is structure, not word identity or complete acceptance by a hand-written grammar. Train lexical-frequency-free structural classifiers on annotated Jerome/Palladius source material. Use independent Whitaker analyses at inference, preserving alternatives and missing readings. No target POS, morphology, dependency arcs or punctuation enter inference. Reference sentence boundaries are supplied only in the explicitly labeled boundary-oracle ablation; hide them for the primary condition. Use an inferred forest of finite predicates rather than requiring one finite verb per sentence or discarding unparsed tokens.

Define the gold skeleton before scoring: finite predicates are UD VERB/AUX tokens marked `VerbForm=Fin`; a predicate's parent is its nearest finite dependency ancestor, or ROOT if there is none. A token's clause anchor is its nearest finite ancestor (itself if finite), or unresolved if no finite ancestor exists. This operational target omits nonfinite and some copular predicates; it is not a full theory of Latin clauses. Keep unresolved tokens in all coverage denominators. Report finite-predicate P/R/F1, finite-parent attachment accuracy, non-root edge P/R/F1, token-anchor accuracy/coverage, and inferred sentence-boundary P/R/F1 separately.

Freeze source authors to Jerome/Palladius in PROIEL train. Use 12 deterministically selected 8–48-token Cicero sentences from PROIEL dev for development. For confirmation, use 12 8–48-token sentences each from Sallust and Suetonius in Perseus train, beginning after token offset 512, beyond the earlier pilot's 384-token prefixes. These are author-disjoint from fitting, not newly sealed authors or independent Latin editions. Group three retained source-order sentences into each public stream; omitted sentences remain explicit provenance gaps, never silently claimed as continuous text. Exclude sentences with multiword-token surface/annotation mismatch or nonsingle normalization, recording losses. Do not screen on morphological coverage or grammatical success.

Fit finite-predicate and candidate-parent classifiers on source annotations. Use morphology/context/relative-position features, no word identity or target word frequency. Choose the finite threshold on Cicero development only from a fixed grid; freeze it before confirmation. Parent candidates are ROOT and the nearest three predicted predicates in each direction; use an acyclic maximum-score forest, retaining competing scored candidates. Token-anchor nearest-predicate assignment is an explicitly weak baseline, not argument recovery. Compare to any-finite-reading predicate detection, ROOT-only parent and nearest-previous-predicate baselines.

Before outcomes, set a provisional transfer gate: predicate F1 at least 0.80 on each confirmation author and non-root skeleton-edge F1 at least five percentage points above the stronger ROOT-only/nearest-previous baseline on each author. This is a structural pilot gate, not a threshold for dictionary integration. If it fails, preserve useful subcomponents and diagnose attachment/coverage errors; no restoration search. Corruption robustness is measured at 0%, 5%, 10%, 25% and 50% of distinct dictionary entries, with seeds 101/202/303 and injective source-vocabulary replacements. Interpret unchanged gold structure under substituted words as an explicit recovery diagnostic, not a gold syntactic annotation of the corrupted text.

## Outcome

**Finite-predicate detection transfers to these natural excerpts; predicate hierarchy and clause grouping do not.** The frozen structural gate fails because every detected predicate is assigned to ROOT. This iteration produces measurable partial structure without requiring a complete grammatical parse, but does not establish grammatical reconstruction or a usable dictionary objective.

The final benchmark comprises **36 annotated sentences, grouped into 12 public streams, totaling 601 tokens**: 226 Cicero, 175 Sallust and 200 Suetonius tokens. Every token remains represented. Source fitting used **8,117 tokens in 797 sentences** from Jerome/Palladius: take the first 400 retained sentences per author, group three at a time, and omit the one three-sentence group crossing authors. The two source classifiers use 6,545 candidate arcs. No target-author annotation enters fitting; Cicero alone selects the finite threshold of **0.50** from the declared five-value grid. All three authors have zero exact shared twelve-token windows with the admitted source streams under this audit, which does not rule out shorter overlap or general prior exposure.

### Finite predicates

Primary results hide target sentence boundaries. Percentages are precision, recall and F1 of **finite-predicate positions**, not lexical restoration percentages.

| Author | Precision | Recall | F1 | Any finite-reading baseline F1 | Morphology candidate recall ceiling |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cicero | 93.10% | 77.14% | 84.38% | 69.57% | 91.43% |
| Sallust | 94.12% | 80.00% | 86.49% | 68.00% | 85.00% |
| Suetonius | 100.00% | 86.96% | 93.02% | 72.73% | 86.96% |

The detector improves precision over accepting every finite reading, at the cost of recall. Three reference predicates per author have no finite reading in the independent morphology lattice, so this candidate policy cannot recover them. The source-trained classifier additionally loses five candidate-supported Cicero predicates and one Sallust predicate; it retains all twenty candidate-supported Suetonius predicates. Morphological token coverage is 92.92%, 88.57% and 88.00%, respectively. Unknown tokens retain unresolved morphology and can receive a tentative clause anchor; an anchor is not a recovered morphological analysis.

Seeded stream-cluster bootstrap intervals for predicate F1 are **71.64–94.12%** on Cicero, **76.92–94.12%** on Sallust and **84.44–100%** on Suetonius. There are only four streams per author, so these are descriptive, broad intervals rather than reliable author-population bounds. The finite decision threshold is uncalibrated outside development and the weights are fitted on a small source sample.

### Clause structure

| Author | Learned non-root edge F1 | Nearest-previous edge baseline F1 | Token-anchor accuracy, all tokens | With supplied boundaries | Hidden-boundary F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cicero | 0.00% | 38.30% | 50.44% | 54.87% | 6.06% |
| Sallust | 0.00% | 19.05% | 39.43% | 46.86% | 0.00% |
| Suetonius | 0.00% | 37.04% | 62.00% | 73.50% | 0.00% |

The token-anchor method assigns each token to its nearest detected finite predicate, restricting candidates to the supplied sentence in the oracle condition. This is a **baseline clause-membership approximation**, not subject/object attachment, morphological disambiguation or a recovered dependency tree. Tokens with no gold finite ancestor remain in the all-token denominator; the report also records the covered-gold denominator separately. Supplied boundaries improve this approximation, but do not fix predicate linking. Predicate detection is identical in supplied/hidden modes because its morphology window is unchanged; only parent and token-anchor candidates are restricted by oracle boundaries.

Every learned parent choice is ROOT. The model therefore recovers **0/22 Cicero, 0/8 Sallust and 0/11 Suetonius** non-root links. Correct endpoints and parent candidates are available for **14/22, 5/8 and 8/11**, respectively: candidate absence cannot explain all failures. Root scores exceed the best non-root alternative by approximately 1.86, 2.18 and 2.36 logits on average. Source gold skeletons contain 63.83% ROOT assignments; the fitted independent binary arc scores, unconstrained ROOT count and limited contextual features admit the degenerate all-ROOT solution. This is an observed collapse; the experiment does not isolate which modeling change would fix it.

The ROOT-only baseline can still obtain 28.57%, 45.00% and 47.83% parent accuracy on gold predicates because many gold parents are ROOT. Reporting non-root edge F1 prevents mistaking this for hierarchy recovery. The nearest-previous baseline uses the same predicate candidates and supplied-boundary restrictions in each mode. Its nonzero edge scores show that the learned model is weaker than even this simple linking heuristic. The hidden sentence cuts are merely changes in the nearest anchor's inferred forest ROOT; their low F1 confirms that this is not a sentence segmenter.

### Dictionary corruption and oracle repairs

Replace 0%, 5%, 10%, 25% or 50% of distinct word types with distinct source-attested forms, absent from the original stream, and change every occurrence of each selected type. Use seeds 101/202/303, with nested type selections per stream/seed and rounded type counts. All **180 evaluations** are retained, including repeated zero-damage controls. Replacement spelling comes only from source vocabulary. Type percentages differ from affected-token percentages; both are saved. Rates and source-attested replacement forms are synthetic diagnostics, not a model of historical corruption.

| Changed dictionary entries | Cicero predicate F1 | Sallust predicate F1 | Suetonius predicate F1 |
| --- | ---: | ---: | ---: |
| 0% | 84.38% | 86.49% | 93.02% |
| 5% | 82.05% | 77.88% | 86.36% |
| 10% | 78.61% | 69.42% | 79.71% |
| 25% | 64.49% | 50.72% | 67.52% |
| 50% | 45.41% | 36.36% | 44.44% |

At 50% changed entries, all-token clause-anchor accuracy drops to **24.34%, 11.62% and 19.17%**, respectively. Gold skeletons are the original annotations: the measurement asks how much original structure survives damaged lexical evidence, not whether the changed sentences possess those same true syntactic analyses. Non-root edge recovery remains zero and cannot support a link-repair claim.

A separate **72-run oracle repair diagnostic** restores one damaged dictionary entry at 25%/50% corruption, preferentially choosing an entry covering an original finite predicate. Its identity is supplied only to this diagnostic, never to the main inference or fitting. Predicate F1 increases in **44/72**, ties in **28/72**, and decreases in none; mean per-run F1 gains are **4.38, 9.97 and 4.83 percentage points** on Cicero, Sallust and Suetonius. Mean gains in correctly anchored tokens are 2.00, 2.00 and 1.42. This establishes sensitivity of the partial detector to a known repair, not automatic discovery of repairs or restoration of predicate hierarchy.

Confidence behavior is inadequate: mean binary entropy and parent-score margins are not reliably monotonic with corruption. For example, Sallust finite entropy initially decreases from 0.1206 to 0.1182 at 5% damage while predicate F1 falls. These source-trained probabilities and margins are descriptive model outputs, not calibrated correctness confidence. Do not derive trusted nuclei from them.

## Implementation and inference separation

[The structural model](../src/voynich_smt/predicate_structure.py) fits regularized logistic classifiers using dictionary POS/feature existence flags and nearby morphological context. No word spelling identity, token-frequency feature, target annotation, lemma identity or word n-gram likelihood enters these classifiers. Duplicate analyses cannot increase feature mass. The finite classifier uses a two-token context window in each direction; only tokens with at least one independently generated finite reading are eligible as predicates.

Candidate predicate parents are ROOT or one of the nearest three predicted predicates on either side, optionally restricted to the oracle sentence. Source supervision labels the nearest finite dependency ancestor. A Z3 optimization selects an acyclic maximum-score forest under integer-scaled arc logits; it allows multiple roots and does not force one verb per sentence. The report retains all scored arc alternatives and morphological readings. Those alternatives are not a posterior over complete analyses; the model does not select one globally consistent reading per token or infer nonfinite/nominal predicates. Token coverage, unresolved cases and grammar limits remain explicit.

The public stream file contains only IDs and surface tokens. The inference API accepts surface tokens and optional supplied boundaries; it has no annotation, head, gold vocabulary or key argument. Source supervision is permitted independently learned grammar evidence, not an unsupervised grammar-induction claim. The decoder remains unsupervised with respect to its target key, but no dictionary optimization is run here. Target annotations live in a separate evaluation artifact and are used for metrics, development threshold selection and explicitly labeled oracle boundary/repair diagnostics only.

Rows with solver uncertainty abstain from structure predictions while remaining in the metric denominators. No such unresolved forest occurred in this run. Surface multiword-token mismatches and sentences whose words cannot each normalize to a single token are excluded with recorded source-level losses. Punctuation is removed, and lowercase/j→i/v→u/diacritic normalization follows the existing Latin convention. This excludes difficult transcription cases rather than repairing them silently.

## Reproduction and verification

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_structure_iteration3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_structure_iteration3_diagnostics
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_structure_iteration3_repairs
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_structure_iteration3_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_predicate_structure.py tests/unit/test_coherent_grammar.py tests/unit/test_grammar_diagnostic.py
```

The runner refuses to overwrite `experiments/results/grammar-restoration/iteration3-v2/`. Inputs, source morphology provenance, raw-file/code hashes, selection offsets, normalized streams, private annotations, fitted weights, development threshold comparisons, every inference hypothesis, corruption/repair mappings, diagnostics and validation are preserved. An initial `iteration3/` artifact is retained; v2 makes the supplied-boundary nearest-previous baseline comparable and ensures solver-abstained streams stay in denominators. The intact predicate/learned-edge results are unchanged.

**Nineteen relevant tests pass**, including seven new tests of acyclic optimal forests, oracle-boundary restrictions, missing/nonfinite morphology, duplicated analyses, model fitting/serialization, unresolved metric denominators and gold ancestor extraction through nonfinite dependencies. The validator replays **276 main/corruption/repair predictions**, checks recorded forest feasibility and optimal score (without requiring identical tie-breaking), recomputes metrics/baselines/threshold selection/gates, and verifies injective full-entry corruptions and known repair maps. Alternative finite-reading baseline metrics are replayed separately as well. Numerical features are source-fixed; the replay reads saved morphology, without live target annotations in inference.

The main v2 benchmark took approximately **2.66 seconds**, excluding subsequent diagnostics, repair runs, validation and tests; peak memory was not measured. This small pilot does not estimate full-decoder cost. PROIEL/Perseus r2.17 provenance and licenses remain in `data/latin-grammar-benchmark/`; these are edited, annotated prose excerpts from different Latin periods, not diplomatic medieval transcription. The target examples were not withheld from all previous repository work, and the selected sentences may be discontinuous. Source fingerprints and exact locations permit audit without implying universal corpus independence.

## Decision

Keep the finite-predicate detector as a partial structural component, together with its morphology recall ceiling and damage tests. **Revise predicate linking before claiming clause restoration or integrating a dictionary objective.** The next source/development experiment should compare a conditional parent-ranking objective against ROOT-versus-attachment decomposition, measure whether it learns non-root links on source validation before target confirmation, and distinguish coordination from subordination using explicit construction evidence. An oracle-gold-predicate diagnostic can isolate linker failure from missed predicate positions; it must remain separate from real inference. Expand nonfinite/copular predicate targets and evaluate genuine token-to-clause attachment instead of nearest-anchor assignment. Reserve fresh author-level confirmation after that design is frozen; these evaluated excerpts are now regression/development material.

No exact-word restoration percentage, trusted nucleus, dictionary search or Voynich result is claimed.
