# Marker-oracle isolation of remaining clause-link failures

## Frozen diagnostic

Keep iteration-5 marker and parent weights fixed. Compare predicted markers, oracle scopes with the same learned vocabulary/classes, and a broader oracle supplying all reference marker positions, classes and scopes. The broader condition measures marker coverage/type ambiguity as well as attachment and must not be conflated with scope correction alone. No model is retrained, selected or promoted using these diagnostics.

Cross all three marker conditions with detected versus gold finite positions and hidden versus supplied sentence boundaries on the preserved twelve target streams. Missing predicate endpoints remain unavailable: the marker oracle cannot insert a predicate or let a token serve simultaneously as a predicate and marker. Add fresh-source-confirmation comparisons only for gold predicates and hidden boundaries to distinguish target transfer from the response to oracle evidence. Reuse validated predicted-marker baseline outputs rather than rerunning their timed-out cases.

For every oracle-predicate condition, calculate the reference forest's exact typed score and its gap to the selected forest. The true skeleton is feasible with the full parent pool; a positive optimum-minus-reference gap demonstrates objective misranking under that condition. Inspect correct-parent and correct-typed-choice margins, mistaken ROOT choices and wrong non-root parents. This can diagnose parent scoring; it cannot prove that the operational finite-only skeleton is linguistically adequate. Preserve unsupported annotations, solver abstentions and all metric denominators. No dictionary search or blind restoration claim.

## Result: marker errors are not the only bottleneck

**Supplying correct markers does not consistently repair parent selection. Even with gold predicates, complete gold markers and gold sentence boundaries, both models strictly prefer a wrong reference-compatible forest in 10 of the 12 target streams.** The optimizer has a feasible reference available and finds a higher-scoring alternative; this is a demonstrated remaining failure of the fixed parent objective under the declared finite-skeleton target.

This does not prove that marker inference is unimportant or that the finite-only representation is adequate for unrestricted Latin. It shows that perfect marker information alone cannot rescue the current trained parent models. Improving optimization effort cannot force them to select a lower-scoring reference.

### Isolating marker occurrence, scope and type

`oracle_scope` corrects each recognized spelling's active/NULL decision and target predicate while preserving its learned candidate classes. It therefore fixes occurrence disambiguation as well as head choice; it is not merely a correction of the heads of already-active predicted markers. It cannot insert a marker spelling outside the learned vocabulary.

`oracle_full` additionally supplies every reference marker position and its operational class, removing vocabulary omissions and class ambiguity. With gold predicates, this condition achieves **100% marker-attachment F1** on the evaluated source and target conditions. It supplies no predicate-parent links. All parent weights and candidate-parent choices remain unchanged.

With **gold predicates and hidden sentence boundaries**, marker-only parent linking gives:

| Author | Predicted markers | Correct scope/NULL, learned classes | Complete gold markers/classes/scopes |
| --- | ---: | ---: | ---: |
| Cicero | 36.84% | 37.84% | 37.84% |
| Sallust | 50.00% | 16.67% | 30.77% |
| Suetonius | 26.67% | 44.44% | 44.44% |

Values are **non-root edge F1**, not lexical recovery or complete parse accuracy. Marker correction helps Suetonius, barely changes Cicero, and worsens Sallust under fixed weights. The Sallust gap between the two oracle variants also exposes an effect of marker coverage/classes beyond scope alone. Four small streams per author do not support a broad quantitative generalization.

The interaction model behaves similarly unevenly: complete gold markers change hidden-boundary F1 from **44.44% to 37.84% on Cicero**, **61.54% to 28.57% on Sallust**, and **25.00% to 52.63% on Suetonius**.

On the source-confirmation set, marker-only changes from **44.18% to 43.65%** with the full marker oracle, and interactions from **44.62% to 43.18%**. Thus perfect markers are insufficient even for the admitted source domain. Because parent fitting used model-predicted source markers, replacing them with oracle markers changes the feature distribution; worsening is compatible with training/exposure mismatch or reliance on spurious cues, but this diagnostic does not isolate those causes.

Detected-predicate runs are also retained. Their marker oracle is deliberately blocked when a reference predicate endpoint was missed, or when the marker token itself was selected as a predicate. It cannot silently repair the finite detector. All forced NULLs and blocked reference targets are recorded.

### Exact reference-forest scoring

With **gold predicates, full gold markers/classes and supplied gold sentence boundaries**:

| Author | Marker-only edge F1 | Interaction edge F1 | Reference strictly outscored, each model |
| --- | ---: | ---: | ---: |
| Cicero | 55.56% | 51.43% | 4/4 streams |
| Sallust | 30.77% | 28.57% | 2/4 streams |
| Suetonius | 58.82% | 66.67% | 4/4 streams |

For every oracle-predicate condition, the reference parent/type assignments occur in the full candidate set and form an acyclic forest. Its score is computed directly from the same saved arc logits used by optimization, with the same million-scale integer rounding. A strictly positive **optimum minus reference** gap is an objective counterexample, not a retrieval or search failure. A zero gap is a tie or an optimum reference; it is not automatically evidence that every structure is correct.

In the complete-oracle condition, marker-only's positive target score gaps range from **1.15 to 22.31 score units**, while the interaction model's range from **0.91 to 26.67**. Two Sallust streams have zero gap for each model; the other ten strictly favor a wrong forest. Exact values, local parent/type margins and selected errors are saved per condition. These scores are within-model differences, not probabilities or comparable absolute scores across models.

The remaining errors include both missed attachments and wrong parents. Under full markers, gold predicates and hidden boundaries, marker-only still makes **ten false-ROOT and five wrong-parent decisions on Cicero**, **four false-ROOT and two wrong-parent decisions on Sallust**, and **five false-ROOT and two wrong-parent decisions on Suetonius**. There are additional false attachments of true ROOT predicates. This is not a single missing-marker mechanism.

### Concrete scoring explanation

In `Cicero/1`, the reference attaches **`faciebam` to `agam` as subordination**. The full marker oracle correctly assigns both **`quod` (relative)** and **`etsi` (subordination)** to `faciebam`, and reference sentence boundaries are supplied. Nevertheless, the marker-only scorer prefers ROOT by **0.594950** units.

Because this parent model is linear in standardized features, the ROOT-minus-reference difference has an exact additive decomposition:

| Feature blocks | Contribution to ROOT minus reference |
| --- | ---: |
| Existing typed morphology/context blocks | +4.131934 |
| Explicit correct-marker blocks | −3.536984 |
| **Total** | **+0.594950** |

Here the explicit marker evidence pushes in the correct direction, but the generic learned feature blocks outweigh it. The interaction model likewise prefers ROOT by **0.999611**: approximately **+3.501754** from generic blocks and **−2.502143** from explicit marker/interactions. A separate script verifies both decompositions against the recorded arc-score differences. This is an explanation of these choices, not proof that globally increasing marker weight would improve recovery; markers can also legitimately accompany ROOT predicates.

## What is now established

- **Predicate detection remains a separate upstream limit.** The marker oracle does not create missing predicate positions.
- **Marker inference matters but is insufficient.** Correcting it helps some conditions and harms others under frozen weights.
- **Parent scoring/feature use is a demonstrated bottleneck.** Correct marker evidence can be outweighed, and complete references are strictly misranked even after the main oracle factors are supplied.
- **The optimizer is not the explanation in those completed cases.** The selected forest is optimal for its supplied integer objective; more search would not select the lower-scoring reference.
- **Representation remains an open issue.** The measured target is nearest-finite-ancestor structure, with coarse coordination/subordination labels. It collapses nonfinite, copular and nominal constructions. The oracle results do not distinguish deficient features/training from information lost by that projection.

This is therefore evidence against spending the next increment solely on marker retrieval or a larger search budget. It does not invalidate better marker models, conditional parent ranking generally, or grammar-based restoration.

## Reproduction and validation

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_marker_oracle_iteration6
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_marker_oracle_iteration6_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_marker_oracle_score_explanation
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_marker_oracle.py tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

Outputs are preserved in `experiments/results/grammar-restoration/iteration6-v2/`; the runner refuses to overwrite them. The initial `iteration6/` output and runner snapshot are retained. V2 fixes audit labels so solver-abstained cases are labeled unresolved rather than treated as fallback ROOT predictions; the scored forest results are unchanged. There is no fitting, target-based model selection, change to production scorers or dictionary optimization.

The benchmark contains **684 conditions**: 288 target conditions and 396 source-confirmation conditions. It reuses **228 validated predicted-marker baselines** and runs **456 new oracle forests**. The main diagnostic took approximately **36.69 seconds**, excluding tests, replay and the score explanation. Peak memory was not measured. Source-confirmation's same difficult block remains a solver abstention in the six model/marker conditions; these cases retain their gold denominators and have no claimed optimum/reference gap. Target conditions have no abstentions.

**Twenty-five relevant tests pass**, including six oracle-specific checks for preserved vocabulary/classes, missing-marker insertion only in the broader oracle, unavailable predicate/role-conflict blocking, NULL decisions, exact reference score gaps and unresolved audit handling. The validator replays all 456 new forests, verifies the identities of 228 reused baselines, recomputes metrics and oracle interventions, independently checks **570 completed reference-forest score comparisons**, and checks model/input hashes and scored witness validity. A replay that resolves an originally abstained case does not overwrite its historical score or promote it into the reported metrics. The separate feature-block explanation checks its decomposition directly against saved linear arc scores.

The treebank editions, Latin-period/style variation, short discontinuous excerpts and previously inspected target authors retain the limitations recorded in iteration 3–5. All oracle evidence is explicitly diagnostic and is unavailable to real target inference.

## Next step

Prioritize **source-only parent-score alignment with correct structural evidence**: contrast gold forests with the actual optimized wrong forests, use out-of-fold marker predictions, and include a gold-marker training/evaluation ablation to isolate exposure mismatch. Before another target run, require the parent scorer to rank correct or minimally corrupted structures appropriately on separate source constructions, while retaining ROOT-versus-attachment calibration. Audit nonfinite/copular examples separately to determine whether the finite projection hides the relevant relation. Do not tune a global marker weight on these target failures or interpret a higher objective score as better grammar.
