# Predicate-linker isolation and conditional parent ranking

## Frozen design

Keep iteration 3's finite detector, weights, 601 target tokens and operational gold finite-predicate skeleton fixed. First diagnose the existing linker with (a) detected predicates and (b) oracle gold finite positions, each with hidden or supplied sentence boundaries. Compare ROOT-only and nearest-previous parent baselines. Predicate positions and boundaries are independent oracle factors, never supplied to the real detected/hidden condition.

Fit two new source-only linkers: conditional parent ranking with the previous features, and joint parent/relation ranking with ROOT, coordination and subordination alternatives plus fixed conjunction/morphology cues. Use the same source training selection as iteration 3. ROOT is a scored choice in each child's candidate set, not an unconstrained separate binary event. Select the best acyclic labeled forest, preserving scored alternatives without summing rewards for ambiguity. Compare nearest-three, nearest-six and full parent pools with fixed weights; train ranking models on full pools, report true-parent reachability separately and do not tune weights per pool.

Use the next 100 retained sentences per source author (positions 400–499 after the first 400 used by iteration 3) as source validation; exclude training sentence IDs. Group three source-order sentences within authors. Before seeing results, set the source gate on oracle-predicate, hidden-boundary, full-pool validation: non-root edge F1 must exceed nearest-previous by at least five points, ROOT F1 must be no more than five points below the previous binary linker, and gold-ROOT recall must reach 80%. Freeze regularization at 0.01 and feature definitions; no source-validation hyperparameter search. A new linker is evaluated on target excerpts only if it passes this source gate. Existing-linker oracle diagnostics and candidate ceilings can always be evaluated because they do not change target inference or tune a model.

Source fitting uses Jerome/Palladius annotation only. ROOT means no finite ancestor, coordination means a `conj` dependency along the path to the nearest finite ancestor, and other non-root paths are operationally called subordination. These labels collapse diverse UD constructions and are not a complete linguistic taxonomy. Typed features use fixed coordination/subordination marker classes, relative-pronoun morphology and finite mood, never target labels or general lexical frequency. Report ROOT P/R/F1 and non-root P/R/F1 separately to expose either all-ROOT or indiscriminate-attachment collapse. Solver failures abstain with denominators retained. No dictionary optimization.

## Outcome

**The old linker fails even with oracle predicates and boundaries. Typed conditional ranking learns useful source-validation links, but does not pass the frozen improvement gate.** No new linker was evaluated on the Cicero/Sallust/Suetonius target excerpts, and no dictionary optimization was run.

Both new models were fitted from the same admitted source material as iteration 3: **1,385 gold finite-predicate choice groups**, with no gold parent absent from the full training pool. Untyped ranking has 8,353 candidate choices; joint parent/relation ranking has 15,321. Source validation contains **197 sentences grouped into 66 streams, totaling 2,101 tokens**, including **342 gold finite predicates, 208 gold ROOT assignments and 134 non-root links**. The requested 100 sentences per source author become 197 after excluding the one three-sentence group crossing authors. Training and source-validation sentence IDs are disjoint.

### Source validation: isolate linking with gold predicate positions

Primary source-validation results hide sentence boundaries and expose all predicate parents. These are **oracle-predicate diagnostics**, not end-to-end predicate detection results.

| Model | Non-root precision | Non-root recall | Non-root F1 | ROOT precision | ROOT recall | ROOT F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Previous independent binary scorer | 0.00% | 0.00% | 0.00% | 60.82% | 100.00% | 75.64% |
| Conditional ranking, previous features | 14.29% | 2.24% | 3.87% | 60.44% | 93.27% | 73.35% |
| Typed conditional ranking + marker cues | 51.00% | 38.06% | **43.59%** | 73.97% | **86.06%** | **79.56%** |
| Nearest-previous baseline | — | — | **40.49%** | 78.79% | 25.00% | 37.96% |

Untyped conditional ranking selects 21 non-root links and gets three right: changing normalization alone does not fix the old feature set. The typed model selects 100 non-root links and gets **51 right**, retaining **179/208 gold ROOT assignments**. Its ROOT F1 exceeds the binary model, so this improvement is not obtained simply by attaching everything somewhere. Typed-edge F1, requiring both the parent and operational relation label to match, is **42.74%**.

The typed model's edge-F1 gain over nearest-previous is **3.10 percentage points**, below the declared **5-point** requirement. It passes the two ROOT safeguards, but fails the overall source gate. A seeded paired bootstrap over the 66 streams gives a descriptive 95% interval of **−5.51 to +11.61 points** for that edge-F1 difference. Streams share two source authors and may be dependent; this is not strong evidence of a general advantage. The threshold was not relaxed after seeing the result.

Supplying source sentence boundaries raises typed edge precision to **65.43%**, recall to **39.55%**, and F1 to **49.30%**; ROOT F1 becomes **82.30%**. However, nearest-previous also improves to **56.85% edge F1**, surpassing the typed model in this easier condition. Boundary information helps, but neither the new objective nor the marker/type features yet establish a stronger general linker.

All source conditions also include the unchanged detected-predicate alternative in the saved report. The frozen source gate uses gold predicates to isolate linking; these oracle numbers must not be presented as performance of a real surface-only pipeline.

### Target oracle diagnostics and candidate reachability

The following tests retain the **previous binary scorer only**, because neither new model passed source validation. They use the exact 601 target tokens from iteration 3. The scored alternatives, candidate pools, explicit oracle flags and matched ROOT/nearest-previous baselines are saved for every condition.

| Target author | Gold non-root links | Gold predicates, three-neighbor pool | Gold predicates, wider/full pool | Detected predicates, three-neighbor pool | Detected predicates, wider/full pool |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cicero | 22 | 21/22 reachable | 22/22 | 14/22 | 15/22 |
| Sallust | 8 | 8/8 reachable | 8/8 | 5/8 | 5/8 |
| Suetonius | 11 | 11/11 reachable | 11/11 | 8/11 | 8/11 |

The nearest-six and full pools have the same ceiling on these excerpts. With oracle predicates, **40/41** gold links are reachable with the original three-neighbor pool and **41/41** with wider pools. With detected predicates, **27/41** rise to **28/41**; missed predicate endpoints explain most of that remaining ceiling. Reachability is an evaluation statistic: it does not reveal the correct parent to inference.

Despite full availability, the old model predicts **zero non-root links in every condition**, including gold predicates plus supplied sentence boundaries plus all parents. This directly separates its scoring failure from finite-predicate retrieval and boundary uncertainty. Merely widening its pool is insufficient.

Under gold predicates, hidden boundaries and full pools, nearest-previous edge F1 is **52.83% on Cicero, 16.67% on Sallust and 46.67% on Suetonius**. These are oracle baselines, not new model improvements. Target results for the typed model are deliberately absent; its promising source numbers are not evidence of target transfer.

## Implementation and limitations

[Conditional ranking](../src/voynich_smt/parent_ranking.py) minimizes the mean source negative log probability of the correct choice within each predicate's candidate set, with fixed L2 regularization 0.01. A common group intercept cancels and is fixed at zero. The untyped variant retains the previous morphology/context/distance features. The typed variant uses relation-specific feature blocks and fixed cue classes for conjunctions, potential subordinate markers, pronoun availability, possible relative forms and subjunctive mood. Relative-form and conjunction indicators retain lexical ambiguity: `quod`, `cum` and related forms are cues, not gold clause labels. No target annotations or corpus word-frequency features enter scoring.

Each non-root parent can have coordination/subordination alternatives; ROOT has only its own label. Inference maximizes the sum of selected raw choice logits under an acyclic forest constraint. Conditional normalization is constant within each child's choice set, so using logits yields the same forest objective as conditional log probabilities. It does not sum rewards over alternative labels or analyses. Group probabilities are retained for inspection but are not calibrated posteriors over complete grammatical structures. The independent source softmax training objective is also not a globally normalized forest-training objective.

The scoring core takes surface tokens, predicate positions and optional boundaries. Real callers supply detected positions; oracle diagnostics explicitly supply gold positions. Missing morphology can therefore remain at an oracle predicate position without suppressing its inclusion. Those runs isolate attachment only; they do not establish that the real detector can recover that predicate. Entire streams retain all tokens in metric denominators, and unresolved optimization abstains rather than silently removing gold cases. The saved results contain no solver-unresolved forest.

Relation labels are derived on source/evaluation data from the path to the nearest finite ancestor: a path containing UD `conj` is called coordination, and remaining non-root paths are grouped as subordination. This coarse convention can include constructions that deserve different linguistic labels. The model does not yet infer modifier/argument heads, nonfinite or nominal predicates, marker attachment, or globally consistent morphological readings. Token-to-predicate anchors remain the earlier nearest-predicate baseline. These trials improve and diagnose predicate linking only; they do not constitute grammatical reconstruction.

## Reproduction and verification

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_linker_iteration4
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_linker_iteration4_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

The runner refuses to overwrite `experiments/results/grammar-restoration/iteration4/`. It preserves the frozen manifest, source training/validation IDs, independently fitted weights, saved morphology, oracle-factor labels, all scored parent/type alternatives, chosen forests, gold reachability, complete metrics, gate decisions and target-evaluation restrictions. Source morphology and raw treebank provenance are recorded; target streams and skeletons are checked against iteration 3. An oracle diagnostic is never relabeled as an ordinary inference result.

**Thirteen relevant tests pass**, including six new tests for grouped ranking and cancellation of shared features, parent-pool restrictions, typed choice legality, acyclic optimality, conditional normalization, absence of a label-multiplicity reward, and invalid inputs. The validator independently refits both rankers from source annotations using the saved morphology, verifies train/validation separation, and replays **936 forests: 792 source-validation and 144 target-oracle/baseline experiments**. It checks scored alternatives, typed witness feasibility, acyclicity, optimal objective, ROOT/non-root metrics, baseline matching, oracle flags, reachability and source gates. It also reconstructs the paired bootstrap and verifies that models failing the source gate have no target rows.

The main benchmark took approximately **21.98 seconds**, excluding validation/refitting and tests. Peak memory was not measured. No expensive full-decoding experiment, target model-selection sweep, blind lexical restoration or dictionary-objective integration was performed.

## Recommendation

Keep the typed conditional ranker as a source/development prototype, and retain the untyped failure as an ablation. The most concrete next step is **explicit marker-to-clause and predicate-to-predicate interaction modeling**, using source errors to distinguish missed links from incorrect parents and to improve coordination/subordination evidence. Evaluate joint ROOT/attachment tradeoffs against nearest-previous on source validation before exposing a revised model to target authors. Use fresh source validation for any claimed confirmation after tuning on these now-inspected cases. Candidate widening can remain a diagnostic control, but it is not the primary explanation for the old linker's collapse.
