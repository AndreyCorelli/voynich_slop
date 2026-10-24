# Iteration 55: endpoint eligibility and attachment audit

The next bottleneck is subject eligibility and predicate representation, with a smaller contribution from finiteness. Of iteration 53's 157 false positives on selected sentences, 57 have a non-nominative subject, 18 a nonfinite predicate, and four both. The remaining 86 have morphologically eligible endpoints but the wrong task relation. Better morphology alone therefore cannot resolve all errors.

These are **annotation-dependent diagnostics**, not restoration improvements. Models, scores, candidates and acceptance cutoffs remain frozen. Iteration 53 remains the performance baseline.

## Design

Use the same 4,070 source sentences, five outer partitions and local + morphology model with the free F1 cutoff. Primary evaluation remains 304 selected sentences, 1,858 nominal frames and 470 direct finite-subject gold links; 467 are retrievable. Secondary evaluation has 2,423 gold links across the full source. Readable Latin and supplied POS remain inputs to the baseline.

Apply each oracle mask in two ways:

- **Postfilter:** reject a disallowed baseline prediction without choosing a replacement.
- **Rerank:** remove disallowed candidates, then select the best remaining edge using its original vector/linear score and the original cutoff.

Masks reveal Case, predicate VerbForm, the token's true direct finite-subject role, or the exact gold edge. Known Case excluding Nom and VerbForm excluding Fin reject a candidate; missing annotations remain permissive, and ambiguous values permit the required value when present. Unknown values are not silently treated as known morphology. All actual baseline false-positive endpoints in this evaluation have known, atomic Case/VerbForm.

The exact-edge/no-gate intervention retains only an existing gold edge and bypasses the cutoff to expose candidate coverage. It never injects an edge. Its postfilter version intentionally duplicates exact-edge postfilter; only its rerank version exposes the ungated ceiling. None of these masks is available at deployment. Fixed-cutoff oracle masks are diagnostic probes, not guaranteed mathematical upper bounds on every alternative scorer.

## False-positive decomposition

Counts cross two axes, avoiding double counting. “Not a finite subject” refers to the limited direct finite-VERB/AUX `nsubj` target; it does not mean a token cannot be a grammatical subject elsewhere.

| Baseline false-positive subject class | Finite predicate, selected | Nonfinite predicate, selected | Finite, all source | Nonfinite, all source |
|---|---:|---:|---:|---:|
| True finite subject, wrong attachment | 38 | 11 | 170 | 88 |
| Nominative, not a direct finite subject | 48 | 3 | 662 | 63 |
| Non-nominative, not a direct finite subject | 53 | 4 | 408 | 42 |
| **Total** | **139** | **18** | **1,240** | **193** |

On selected sentences, Case or finiteness excludes 71/157 false positives (45.2%); 86 remain. Subject-role knowledge excludes 108, while 49 are wrong attachments from an actual finite subject. Across all source sentences, Case or finiteness excludes 601/1,433; 832 remain. Before either mask, the source false positives comprise 725 nominative tokens outside the direct finite-subject target, 450 non-nominative out-of-task tokens and 258 wrong attachments from actual finite subjects. These are different diagnostic views of the same errors, not additive independent causes.

## Oracle intervention results

Primary selected-sentence results, all explicitly oracle except the baseline:

| Intervention | Correct | Wrong | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Frozen baseline | 301 | 157 | 65.7% | 64.0% | 64.9% |
| Case postfilter | 301 | 100 | 75.1% | 64.0% | 69.1% |
| Finiteness postfilter | 301 | 139 | 68.4% | 64.0% | 66.2% |
| Case + finiteness postfilter | 301 | 86 | 77.8% | 64.0% | 70.2% |
| Case + finiteness rerank | 307 | 90 | 77.3% | 65.3% | 70.8% |
| Subject-role postfilter | 301 | 49 | 86.0% | 64.0% | 73.4% |
| Subject-role + finiteness rerank | 307 | 40 | 88.5% | 65.3% | 75.2% |
| Exact-edge rerank, frozen gate | 337 | 0 | 100% | 71.7% | 83.5% |
| Exact-edge rerank, no gate | 467 | 0 | 100% | 99.4% | 99.7% |

Reranking can introduce new false positives: removing a nonfinite winner can reveal another wrong candidate. For example, Case + finiteness postfilter leaves 86 wrong edges, whereas reranking leaves 90 while recovering six more true edges. Oracle postfilter and rerank must not be conflated.

Exact-edge knowledge still leaves 130 retrievable gold edges below the frozen cutoff (467−337). Candidate retrieval is therefore not the major remaining limit: subject eligibility, attachment and gate scores all matter. Removing NONE without predicting eligibility is not a deployable remedy.

Full-source Case + finiteness postfilter changes baseline precision/recall from 51.6%/63.1% to 64.7%/63.0%; reranking gives 64.4%/65.2%. Subject-role + finiteness reranking gives 89.7% precision and 65.4% recall, while the ungated exact-edge candidate ceiling is 2,390/2,423 (98.6%). These remain oracle measurements.

## Annotation and task-scope findings

Hard nominative eligibility is not perfectly consistent with the existing target annotations: one gold edge in selected sentences and 15 across all source has known Case excluding Nom. The selected example is sentence 86737, *ea* annotated Acc/Plur but directly `nsubj` of finite *apparet*. No annotation was changed. The selected baseline does not recover that edge anyway, but Case postfilter removes three previously correct predictions across the full source. Thus even a gold Case mask is not guaranteed harmless under the current annotation/target definitions.

More substantially, some apparent errors concern predicate-unit representation. Among full-source baseline false positives, dependency-pattern auditing finds:

| Projection pattern outside the direct finite-subject task | Selected sentences | All source |
|---|---:|---:|
| Subject of a nonverbal head paired with its copula | 5 | 186 |
| Subject paired with a finite auxiliary of its annotated governor | 3 | 60 |
| Coordinated nominal paired with the subject head's governor | 2 | 41 |
| **Any such pattern** | **10** | **287** |

The coordinated check follows a chain of `conj` edges; 40 full-source matches are immediate and one is chained. All these predicted predicate tokens are annotated finite. The patterns are annotation-dependent scope diagnostics, **not adjudicated replacements for gold edges**, and have not been added to true-positive counts. They account for 20.0% of full-source baseline false positives, but only 6.4% on selected sentences.

For example, in sentence 76163, *seueritas* is the subject of a nonverbal head whose finite copula is *erat*; the predicted *seueritas → erat* edge is outside the present direct finite-governor task. Among 725 nominative out-of-task false positives across source, 417 tokens actually carry an `nsubj` relation to some governor. Treating all of them as bad subject eligibility would mix predicate representation with genuine role errors. Apposition, flat name components and other nominal roles form additional, distinct alternatives.

## Decision and next proposal

Do not add an oracle mask to the algorithm. The audit prioritizes **subject-role and predicate-unit modeling**, while preserving occurrence Case as a useful but incomplete direction. Predicate finiteness by itself offers less headroom in this sample.

The next focused proposal is to define and audit a finite **copula/auxiliary carrier** for subjects whose annotated governor is nonverbal or nonfinite. Start with uniquely identified finite cop/aux dependents; keep coordination separate because number agreement may require an entire coordinated subject. Freeze the existing direct-edge task and report the proposed carrier task alongside it. After checking ambiguity and coverage on fit annotations, test whether source-trained eligibility/attachment benefits from these explicit predicate units. No projected oracle count should be reported as newly restored grammar.

## Artifacts and validation

Code: `src/voynich_smt/endpoint_oracle.py`, `benchmarks/grammar_endpoint_oracle_iteration55.py` and its `_audit` module. Artifacts under `experiments/results/grammar-restoration/iteration55/` include every false-positive endpoint/sentence, mask predictions, gold-mask exclusions and the scope audit. Existing output directories are rejected.

The run reproduces 17,675 baseline frame decisions and checks 141,400 candidate-mask subsets. Independent validation checks 15 frozen hashes, replays 282,800 mask decisions, verifies 177,318 unchanged feature vectors, reproduces 64 aggregate metrics and reclassifies all 1,433 false positives. Four new tests cover missing/ambiguous annotation semantics, distinct oracle axes, score preservation/no gold injection and overlap-aware taxonomy; 54 relevant tests pass. No model is refitted or cutoff recalibrated. Earlier frozen files remain intact; the 200-sentence reserve remains unscored and no prior target queries were scored.
