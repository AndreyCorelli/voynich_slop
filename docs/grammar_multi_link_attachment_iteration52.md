# Iteration 52: multiple attachments with a non-subject alternative

A source-trained attachment model with a NONE alternative produces cleaner but fewer links than distance. On the selected sentences, combined local-POS/morphology evidence raises precision from 33.2% to 76.8%, lowers recall from 58.1% to 37.2%, and raises F1 from 42.2% to 50.1%. This is a useful experimental tradeoff, not a general replacement: Palladius F1 declines, and the structural-only model abstains everywhere.

## Task and frozen design

Each NOUN/PROPN/PRON token chooses one compatible VERB/AUX predicate or NONE. Multiple subjects can attach in one sentence, including to the same predicate. This imposes neither a full dependency tree nor coordination constraints. A target is an annotated direct `nsubj` of a finite VERB/AUX; other nominal tokens are NONE for this limited task. Nonverbal/copular governors, other subject POS and nonfinite subject relations are outside scope, not claims of grammatical non-subjecthood.

The unchanged broad morphology candidates come from iteration 49's expanded total99 model plus iteration 50's no-fit-number-label PROPN fallback. Candidates are never pruned by this experiment. Predictions use readable Latin words and supplied POS, without supplied subject or predicate anchors, gold morphology, clause boundaries or dependency edges.

The same five sentence partitions are retained: three fit, one calibration, one test. Three fixed arms are compared:

- **Distance:** choose a unique nearest compatible predicate; abstain on a distance tie. Calibration chooses maximum accepted distance.
- **Structural:** conditional linear softmax over all compatible predicates plus a zero-score NONE. Edge features are bias, log distance, direction, log counts of intervening verbal/SCONJ/CCONJ tokens, and subject POS.
- **Local + morphology:** add immediate-neighbor POS around both endpoints, source-model nominative/finite log odds, and number/person compatibility scores. This combines two additions; it does not isolate local POS from morphology confidence.

The learned models minimize mean conditional cross-entropy plus fixed L2 regularization 0.01. Optimization must converge. A positive fit frame whose gold edge is absent is omitted, never mislabeled NONE. Calibration and evaluation retain such positives in their denominators. Source morphology probabilities on fit tokens are in-sample; this can cause overfitting and is a limitation to test separately.

For learned models, a unique edge must beat NONE before a probability threshold can accept it; ties abstain. Calibration chooses either maximum F1 or maximum true positives subject to empirical precision ≥90% and at least 20 predictions. Threshold grids were frozen before evaluation, and no qualifying precision threshold means abstain. The precision target is not a coverage or reliability guarantee. Each arm receives its own calibration policy.

## Evaluation scope

Primary evaluation covers all 1,858 nominal/pronominal frames in the same 304 selected sentences, including **470** annotated finite-subject edges, rather than only the original 326 selected references. Of these 470 edges, 467 remain in the candidate lattice. The candidate graph contains 3,520 distinct edges after sentence deduplication. This prevents other valid sentence links from being counted as errors.

Secondary evaluation processes all 4,070 source sentences with held-sentence predictions; 3,910 have a frame in this task. These contain 17,675 frames, 2,423 gold edges and 2,390 retrievable gold edges. This is reused Cicero/Palladius development data, not fresh confirmation. The original 326-reference metric is also retained separately; its candidate survival remains 324/326.

## Results

Primary evaluation, with each arm's calibration-selected F1 operating point:

| Arm | Correct edges | Wrong edges | Missed edges | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Distance | 273 | 550 | 197 | 33.2% | 58.1% | 42.2% |
| Structural | 0 | 0 | 470 | Undefined | 0% | 0% |
| Local + morphology | 175 | 53 | 295 | 76.8% | 37.2% | 50.1% |

Wrong attachment counts as both a false positive edge and a missed gold edge. Distance falsely attaches 477 non-subject tokens and selects the wrong governor for another 73 gold-subject tokens. Local + morphology reduces these to 21 and 32, respectively, while abstaining on 1,630/1,858 frames instead of 1,035. Many abstentions are correct non-subject decisions, but many omit subjects.

Exact recovery of the limited gold edge set improves from 48/304 sentences with distance to 89/304 with local + morphology. The latter predicts multiple links in 40 sentences, compared with 216 for distance. These are finite-subject edge sets, not complete grammatical structures.

The original 326 selected references show the recall cost clearly: distance recovers 190, attaches 44 to a wrong predicate and abstains on 92; local + morphology recovers 133, attaches 20 wrongly and abstains on 173. The increase in F1 therefore must not be described as increased reference restoration.

At the calibration precision90 setting, local + morphology predicts 29 links in the selected sentences: 28 correct and one wrong, for 96.6% precision and 6.0% recall. Distance and structural models find no qualifying threshold and emit nothing. This high precision is limited to very small output, not a solution to the remaining recall problem.

Secondary and author-specific F1 operating points:

| Scope / arm | Precision | Recall | F1 |
|---|---:|---:|---:|
| All source / distance | 22.6% | 60.0% | 32.9% |
| All source / local + morphology | 66.2% | 39.8% | 49.7% |
| Cicero selected / distance | 33.2% | 57.9% | 42.2% |
| Cicero selected / local + morphology | 77.2% | 41.1% | 53.6% |
| Palladius selected / distance | 32.9% | 58.9% | 42.2% |
| Palladius selected / local + morphology | 73.1% | 21.1% | 32.8% |

At the precision90 setting across all source sentences, 125 of 141 links are correct: precision **88.7%**, recall 5.2%. Thus calibration's 90% target does not uniformly transfer. Two folds have no qualifying local-model high-precision threshold and abstain completely at that operating point.

## Bottleneck audit

Of the 470 primary gold edges, local + morphology recovers 175, loses three before ranking, has a wrong predicate win in 32 cases, and abstains through NONE/ties in 260. No gold edge is additionally lost solely to the F1 probability threshold. Structural-only loses three candidates and abstains on all 467 representable gold edges.

The learned scores are not wholly uninformative: with **oracle subject eligibility**, removing NONE and ranking predicates alone uniquely recovers 383/468 subjects with candidates using structural features and 397/468 using local + morphology. Two gold subjects have no candidate predicate at all; a further gold edge is absent despite other candidates existing. These oracle figures do not establish unanchored restoration, but show that the hard NONE comparison suppresses many usable rankings.

The current probability threshold cannot recover such cases: proposals already become NONE when its zero score beats the best edge, even if the acceptance threshold is zero. The next focused proposal is to calibrate the best-edge-versus-NONE decision directly, allowing a calibration-selected threshold below the current fixed MAP cutoff. Preserve the explicit non-subject option and evaluate precision/recall against the present frozen models without refitting them. This will separate an operating-point problem from deficient attachment scores. Cross-fitting morphology features within the fit portion is a separate pending control for in-sample feature optimism.

## Decision and validation

Keep the multi-link formulation and combined model as experimental options; do not adopt the current policy as a default. It reduces false attachments substantially and improves aggregate F1, but loses recall and does not improve both authors. Source POS, readable words and source annotations remain privileged relative to Voynich restoration.

Implementation: `src/voynich_smt/multi_link_attachment.py`, `benchmarks/grammar_multi_link_attachment_iteration52.py` and its `_audit` module. Frozen design snapshot, models, per-frame predictions and evaluations are under `experiments/results/grammar-restoration/iteration52/`. Existing output directories are rejected.

The independent audit checks 17 frozen hashes, refits all ten learned models, reselects 15 calibration policies, replays 106,050 frame/policy decisions, and reproduces 24 aggregate metrics. All 304 selected sentences pass inference invariance under mutation of gold morphology/dependencies, and all 326 original-reference survival checks reproduce iteration 50. Six new tests cover analytic gradients, inference invariance, NONE/ties, unrepresentable-positive handling, edge metrics and precision-policy failure; 41 relevant tests pass. The 200-sentence reserve remains unscored and no prior target queries were scored.
