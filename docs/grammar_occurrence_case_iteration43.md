# Iteration 43: occurrence context without target-phrase case clues

**This occurrence-context model gives no reliable improvement over predicate-lemma counts.** It corrects three Jerome predictions but spoils one Caesar prediction, worsens probability quality on both authors, and does not improve the source cross-validation result consistently. The available training support for within-predicate ambiguity is small: 29 examples across six verbs.

## Scope and available evidence

Keep the existing 767 source sentences from Jerome/Palladius and the reused query slices from iterations40–42. There are 171 source *in* + accusative/ablative examples, 17 target Jerome examples and 41 Caesar examples. This is another diagnostic on development data, not new independent confirmation. Neither iteration39's queries nor the reserved 200 sentences are scored.

Only six source predicates have both case labels:

| Predicate lemma | Accusative | Ablative |
|---|---:|---:|
| uenio | 6 | 3 |
| baptizo | 1 | 3 |
| mitto | 6 | 1 |
| eicio | 3 | 2 |
| ascendo | 1 | 1 |
| trado | 1 | 1 |

These 29 examples include just two to nine examples per lemma. There is insufficient support here for a strong claim about general within-predicate disambiguation. We nevertheless run the fixed diagnostic to identify whether a simple occurrence model adds predictive evidence.

**Correction to the frozen iteration42 report:** its prose counted Caesar *sum* as seven examples (five ablative, two accusative). The saved records actually contain **six: four ablative, two accusative**. Earlier metric artifacts were calculated from the correct records; this was a prose counting error. The frozen report is preserved, and this correction is also saved as a machine-readable erratum in iteration43. The observation that one lemma occurs with both cases remains valid.

## Frozen design and exclusion rules

Use the same oracle verbal ancestor and nearest-verb definitions as iteration41. At each occurrence, extract:

- Predicate VerbForm, Mood, Tense, Voice and Person.
- Other immediate children: dependency relation/POS and lemma, plus ADP lemmas among their immediate children.
- Predicate parent POS and lemma.

Exclude the **entire target nominal subtree**, including its preposition and modifiers, before extracting lexical or morphological features. Do not read Case anywhere, or Number/Gender. Do not use the target nominal dependency relation, predicate lemma as a context feature, target-phrase identity, or word endings. Predicate identity remains available solely through the unchanged lemma-count prior. If a nearest-verb candidate lies inside the excluded subtree, context reduces to the bias feature.

Topology, POS, lemmas, verbal morphology, reference target head, and oracle predicate links are privileged. The reference subtree supplies the exclusion mask; this is not a deployable way to find phrase boundaries in ciphertext. Non-target context can still correlate with the label; the test asks whether such correlations transfer.

Fit ridge1 logistic residuals over the source-only mass4 predicate-lemma probability. Source fitting uses **leave-entire-sentence-out priors**, so the current sentence's case labels do not help construct its own offset. Binary context features must occur at least twice in source training; prediction ignores target-only features. Fix ridge, feature rules, threshold0.5 and all controls before target prediction. No hyperparameter selection.

Controls:

- The unchanged iteration41 lexical-count estimator.
- A bias-only calibration model using the same lexical offsets.
- A context-only model using a global source-frequency offset.
- Matched nearest-verb training and oracle-trained model with nearest-verb inference.
- One hundred source-context permutations **within predicate lemma**, preserving lexical case distributions while disrupting occurrence–case associations. This control has limited power because only six source lemmas have both labels.
- Deterministic five-fold source cross-validation, grouped by sentence ID. Rebuild vocabulary, lexical counts and leave-sentence-out training offsets independently in each fold.

All source/target context features and full-source models are frozen before prediction; predictions are frozen before evaluation.

## Reused query results

| Author | Estimator | Accuracy | Balanced accuracy | Log loss |
|---|---|---:|---:|---:|
| Jerome | Lemma counts | 47.1% | 55.3% | **0.7371** |
| Jerome | Bias calibration | 47.1% | 55.3% | 0.7680 |
| Jerome | Occurrence context + lemma | **64.7%** | 68.9% | 0.8458 |
| Jerome | Context with global prior | 58.8% | 60.6% | 0.8310 |
| Caesar | Lemma counts | **58.5%** | **64.6%** | **0.7238** |
| Caesar | Bias calibration | 58.5% | 64.6% | 0.7516 |
| Caesar | Occurrence context + lemma | 56.1% | 62.5% | 0.8362 |
| Caesar | Context with global prior | 41.5% | 46.6% | 0.8851 |

Lower log loss is better. Brier scores also worsen for context+lemma: 0.2710→0.2970 Jerome and 0.2625→0.3013 Caesar. Jerome's accuracy gain is therefore not an improvement across probability-quality measures or across authors.

Against lemma counts, the context model corrects two *introeo* and one *exeo* accusative examples on Jerome, with no spoiled tags. It spoils one Caesar *mitto* accusative example, with no corrected tags. In the audit, Jerome corrections include contributions from parent *possum*, tense/person, and clause-marker features. The Caesar error is pushed toward ablative by other-clause/argument frame features. These are empirical correlations, not established semantic or grammatical rules.

Among source-unseen *in* predicates, context accuracy changes from 4/11 to 6/11 Jerome and stays 16/30 Caesar. Their log losses worsen from 0.8615 to 1.0430 and from 0.7356 to 0.8060. In particular, all six Caesar *sum* occurrences still receive p(Acc)<0.5; the model does not resolve its two accusative readings.

The target “source-mixed predicate” cohort contains only two Jerome and seven Caesar examples, **all accusative**. It therefore cannot establish within-predicate discrimination of both cases. Its accuracy changes from 2/2 to 2/2 and from 7/7 to 6/7 respectively.

## Uncertainty and controls

Ten thousand paired sentence-cluster bootstrap draws, conditional on the source models, give context-minus-lemma accuracy intervals of [0,+35.3] points Jerome and [-8.1,0] Caesar. Log-loss reduction intervals are [-0.3246,+0.1372] and [-0.2535,+0.0069]. They do not support a robust probability improvement. Bias-calibration comparisons are also saved; no target threshold or intercept is fitted.

The within-lemma shuffled models have mean Jerome accuracy55.8%, versus64.7% for the actual contexts, but their mean log loss0.8392 is similar to the actual0.8458. On Caesar, shuffled mean accuracy49.3% is lower than actual56.1%, while shuffled mean log loss0.8057 is better than actual0.8362. The actual context mapping sometimes helps discrete decisions relative to disrupted mappings, yet still fails the stronger unchanged lexical-model comparison. These results do not justify promoting the context model.

Matched nearest-verb context reaches64.7% Jerome and56.1% Caesar, with log losses0.6430 and0.7950. Oracle-trained nearest inference reaches70.6% and53.7%, with log losses0.7913 and0.8463. These are declared controls, not selected replacements; the small Jerome sample does not make its best arm a validated improvement. Exact oracle linkage again does not consistently dominate a simple nearest-verb choice.

## Source cross-validation

| Estimator | All171 accuracy | All171 log loss | Mixed29 accuracy | Mixed29 log loss |
|---|---:|---:|---:|---:|
| Lemma counts | **76.0%** | 0.5393 | 55.2% | **0.7551** |
| Bias calibration | 73.1% | **0.5342** | 37.9% | 0.7657 |
| Occurrence context + lemma | 74.9% | 0.5704 | **58.6%** | 0.9471 |
| Context with global prior | 67.8% | 0.6785 | 48.3% | 1.0778 |

On the small mixed cohort, context adds one net correct classification but worsens log loss substantially. Across all source examples, it loses two net correct classifications and worsens log loss. Context-only prediction is weaker than the lemma model. We do not tune the model against these outcomes.

## Conclusion and next useful check

This representation has not demonstrated a transferable occurrence-level grammatical signal beyond predicate counts. The broader idea is not disproved: these are sparse source annotations, a narrow *in* contrast, reused targets, and a simple residual model. But increasing scoring complexity now is not supported by the evidence.

The next useful step is a **source-support audit before another model**: determine whether additional permissible source sentences supply substantially more examples of the same predicate with both cases, and how many such predicates overlap the intended evaluation. Keep target IDs/authors and the reserve excluded. If adequate support cannot be obtained, report the limitation instead of repeatedly tuning on the same17/41 examples. Any expanded-source model needs explicit held-predicate and held-sentence tests, with target-phrase case/agreement still excluded.

## Verification and artifacts

355 regression tests pass. The validator refits all six source models, all100 shuffled-context models and the sentence-grouped CV models, and replays6,832 probabilities. Replacing Case/Number/Gender everywhere leaves458 feature extractions unchanged. Tests separately mutate target-subtree lexical identities and POS/morphology, verify cycle-safe exclusion, show real non-target context can affect features, and check that the optimizer learns a synthetic repeated context signal while the calibration control cannot use it. Source/target IDs are disjoint and the reserved200 remain unscored.

Code is `src/voynich_smt/occurrence_case.py`; run `python -m benchmarks.grammar_occurrence_case_iteration43` (refuses overwrite), then `python -m benchmarks.grammar_occurrence_case_iteration43_validate`. Artifacts under `experiments/results/grammar-restoration/iteration43/` include declarations, explicit annotated truth, case-free features, source models, frozen probabilities, shuffle controls, source CV, uncertainty summaries, feature-contribution audit and validation. Previous artifacts and the shared todo remain unchanged.
