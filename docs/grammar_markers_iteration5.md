# Explicit marker attachments and clause-link interactions

## Frozen plan

Iteration 4's inspected source development has 44 missed subordinate links, 19 missed coordinated links, 29 false attachments of gold ROOT predicates and 20 wrong non-root parents. Use these errors to design explicit marker attachment, not to relax the gate or evaluate a revised model on target authors prematurely.

Keep source fitting at retained Jerome/Palladius sentence positions 0–399, inspected development at 400–499, and reserve positions 500–599 as fresh source confirmation. Preserve sentence IDs, group three at a time with cross-author groups excluded, and verify split disjointness. Freshness here is relative to this structural modeling sequence, not every historical use of the raw treebank. Freeze two variants before scoring: (1) typed conditional ranking plus explicit marker attachments, (2) the same plus marker/predicate/parent interaction features. Keep iteration 4's typed ranker and nearest-previous baseline as controls.

Learn a source-only marker vocabulary and a conditional marker-to-finite-predicate-or-NULL classifier. A source clause marker is a `cc`/`mark` token directly governing a finite predicate, or a relative-pronoun token with a finite dependency ancestor; other occurrences of a candidate spelling are NULL examples. This finite-skeleton definition deliberately excludes nonfinite marker scope and nominal coordination. Predict one attachment per marker, retaining alternatives and allowing NULL. Parent training uses model-predicted source attachments, not gold marker heads. Marker alternatives are not summed into multiple clause rewards. This two-stage design fixes marker decisions before forest inference; joint marker/forest search remains unimplemented.

Use complete parent pools and the same source-trained finite detector. Measure both oracle-predicate and detected-predicate conditions, hidden and supplied sentence boundaries, and mark every oracle. Evaluate marker target P/R/F1, predicate non-root edge P/R/F1, typed edges, ROOT P/R/F1 and unsupported/unknown coverage. The primary gate for each variant is fresh-source oracle predicates with hidden boundaries: at least five points of non-root F1 above nearest-previous, ROOT F1 no more than five points below iteration 4's typed control, and ROOT recall at least 80%. Also report paired stream-cluster intervals and detected/hidden results. No hyperparameter selection on fresh confirmation. Only variants passing that gate may be evaluated on the preserved target excerpts, which are explicitly already-inspected diagnostics, not fresh author confirmation. No dictionary optimization.

## Outcome

**Explicit marker attachments improve clause linking and pass the fresh-source point-estimate gate, but transfer remains inconsistent.** Both variants proceed to the preserved target diagnostics. They recover actual non-root links instead of collapsing to all ROOT; neither beats the simple nearest-previous baseline on all three target authors. No dictionary search is justified by this result.

Source fitting remains **8,117 tokens** and **1,385 parent-choice groups**. The marker classifier is fitted on **1,162 occurrences** of **41 source-derived marker spellings**, including NULL/non-marker uses. Inspected development has 2,101 tokens; fresh source confirmation has **2,223 tokens in 197 sentences grouped into 66 streams**, with **371 gold finite predicates, 214 gold ROOT assignments and 157 non-root links**. The first 400, next 100 and following 100 retained sentences per source author are disjoint. Cross-author groups are excluded exactly as in earlier iterations.

### Fresh-source confirmation

Primary results use **gold predicate positions with sentence boundaries hidden**, isolating linking. These are oracle diagnostics, not surface-only recovery scores.

| Model | Non-root precision | Non-root recall | Non-root F1 | ROOT F1 | Gold-ROOT recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Iteration-4 typed control | 52.11% | 23.57% | 32.46% | 77.58% | 89.72% |
| Explicit marker attachments | **59.78%** | 35.03% | **44.18%** | **80.59%** | **89.25%** |
| Markers + parent interactions | 56.31% | **36.94%** | **44.62%** | 79.05% | 85.51% |
| Nearest-previous baseline | — | — | **36.04%** | — | — |

Marker-only improves edge F1 by **11.72 points over the typed control** and **8.14 points over nearest-previous**; interactions improve by **12.16 and 8.58 points**, respectively. Both meet the frozen five-point baseline-gain requirement and ROOT safeguards. Marker-only retains slightly better ROOT decisions, while extra interactions recover three additional correct links with more false links. The 0.44-point difference between the variants is too small to support a preference based on this confirmation set.

The bootstrap intervals remain broad: the paired edge-F1 gain over nearest-previous is **−2.90 to +18.90 points** for marker-only and **−3.36 to +19.92 points** for interactions. These are 1,000 seeded stream-cluster resamples, not independent author-level confidence bounds. Thus the engineering point-estimate gate passes, but the experiment does not establish a statistically secure or general improvement.

With **detected predicates and hidden boundaries**, edge F1 is **24.30% for the typed control, 33.33% for marker-only and 35.29% for interactions**, versus **30.62% nearest-previous**. The stronger oracle improvements shrink once missed and extra predicate positions enter inference.

The marker attachment model itself obtains **70.62% precision, 65.79% recall and 68.12% F1** on fresh confirmation with gold predicates and hidden boundaries: 125 of 190 gold marker-to-predicate attachments are correct. The source-derived vocabulary covers **187/190** reference markers; the remaining errors therefore mostly concern target choice or NULL decisions, rather than vocabulary absence. With detected predicates, marker F1 falls to **60.57%**.

### Transfer to the preserved target excerpts

These are the same already-inspected 601 target tokens used in iterations 3–4, evaluated only after the fresh-source gate passes. They are not a fresh author-level confirmation sample. The finite detector is unchanged.

| Author | Nearest-previous edge F1 | Marker-only edge F1 | Marker + interactions edge F1 |
| --- | ---: | ---: | ---: |
| Cicero | **38.30%** | 29.41% | 30.30% |
| Sallust | 19.05% | **40.00%** | **40.00%** |
| Suetonius | **37.04%** | 14.29% | 14.29% |

All values above use **detected predicates and hidden boundaries**. On Sallust both variants find two correct links and make no false non-root links, but recover only **2/8** gold links; the resulting 100% precision is based on two predictions and is not a confidence guarantee. On Cicero, marker-only recovers **5/22** gold links with 12 predictions, and interactions recover the same five with 11 predictions. On Suetonius each recovers only **1/11**, with three predictions. Link precision/recall and gold-ROOT performance are retained in the raw target results; an aggregate F1 alone would conceal this low support.

Supplying **gold predicate positions while keeping boundaries hidden** raises target edge F1 to:

| Author | Marker-only | Markers + interactions | Oracle nearest-previous baseline |
| --- | ---: | ---: | ---: |
| Cicero | 36.84% | 44.44% | **52.83%** |
| Sallust | 50.00% | **61.54%** | 16.67% |
| Suetonius | 26.67% | 25.00% | **46.67%** |

Thus finite-predicate errors matter, but do not explain the whole transfer failure. Even with oracle positions, Cicero and Suetonius remain below the matched simple baseline. This is not a broadly validated linker or a restored grammatical structure.

Marker-to-predicate F1 on targets with gold predicates is **61.90% Cicero, 60.00% Sallust and 60.00% Suetonius**. With detected predicates it falls to **41.03%, 42.11% and 42.11%**. Missing predicate endpoints further reduce the candidate ceiling; the saved attachment alternatives and NULL decisions make these failures inspectable. Parent-interaction features do not consistently improve on the simpler marker signal.

## What the model now does

[The marker module](../src/voynich_smt/marker_structure.py) predicts a single target finite predicate or NULL for each candidate marker occurrence. Its vocabulary is learned from admitted source annotations, rather than from target words or general word frequency. Features describe marker classes, independent morphological alternatives, neighboring morphology, direction/distance, intervening predicates and target mood. Candidate spellings include ambiguous uses of `cum`, `quod`, relative forms and finite `licet`; the occurrence classifier must choose scope or NULL. Vocabulary membership alone is not a grammar score or an asserted marker role.

A token selected as a finite predicate is forced to NULL in the marker model, preventing it from simultaneously contributing marker evidence. Candidate targets respect supplied boundaries only in the labeled boundary-oracle condition. Every marker has one hard predicted attachment; alternatives are logged but never counted as additional clause rewards. Duplicate identical evidence does not increase feature mass. Two distinct markers can legitimately attach to one predicate, but the parent features use capped existence flags, not an additive marker-count reward.

The marker-only parent model augments the old typed conditional features with the classes and position of markers explicitly assigned to that child. The interaction variant additionally considers markers assigned to the candidate parent, markers lying between the child and parent, intervening markers assigned to a third predicate, and combinations of child direction, marker class and subjunctive alternatives. Both choose an acyclic typed predicate forest with ROOT as a scored choice. Neither imposes a rigid Latin constituent order or a predetermined number of roots.

Source parent training uses the marker model's **predicted attachments on source fitting text**, rather than gold marker heads. Those predictions are in-sample, not out-of-fold; this can make the parent training conditions optimistic. The independent fresh-source and target results expose the resulting exposure/transfer limits. Marker decisions are fixed before parent inference, so a later parent choice cannot repair a mistaken marker scope. Joint marker/parent inference and globally consistent morphological readings remain future work.

The operational marker labels are intentionally narrow: `cc`/`mark` must directly govern a finite predicate, while a relative pronoun is anchored to its nearest finite ancestor. Nominal coordination, markers of nonfinite clauses, many enclitic/transcription cases and markers absent from the source vocabulary remain outside that target. Some source-derived spellings are annotation/transcription artifacts; they are preserved for audit rather than silently curated using confirmation data. Relative-pronoun agreement and the true syntactic attachment of its antecedent are not recovered here.

The module provides **predicate skeletons and marker scope**, not subject/object/modifier dependency reconstruction, normalized grammaticality probabilities or exact lexical recovery. Nearby-word token anchors remain the older baseline. The finite detector, broad morphology adapter and dictionary optimizer are unchanged. Source labels are used for source fitting and evaluation only; target morphology/dependencies never enter normal inference. Gold predicates/boundaries are explicitly labeled diagnostic inputs.

## Bounded inference and abstentions

There are **six source forest abstentions**, all from the same unusually difficult fresh-confirmation stream in hidden-boundary mode: control, marker-only and interactions, each with oracle or detected predicates. The two-second solver limit is reached; no optimal forest is claimed. The affected gold predicates, edges and tokens remain in metric denominators, with zero recovered structure for those trials, including the matched baseline. No target forest abstains. This prevents selective omission of the difficult block, but also means reported ROOT/edge scores include a computational limitation as well as model error. Marker predictions are a separate completed classification stage and remain evaluable in that block.

## Reproduction and verification

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_markers_iteration5
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_markers_iteration5_validate
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/unit/test_marker_structure.py tests/unit/test_parent_ranking.py tests/unit/test_predicate_structure.py
```

The runner refuses to overwrite `experiments/results/grammar-restoration/iteration5-v2/`. It stores the frozen split/gate manifest, source-only marker vocabulary, fitted marker/parent weights, complete source and target hypotheses, single-target marker witnesses and alternatives, typed forest candidates, oracle labels, all metrics, fresh gate decisions and saved morphology for replay. The original `iteration5/` run is retained; v2 adds the finite-predicate/marker role exclusion and removes a dead reporting expression. That consistency correction was made before inspecting the first run's confirmation outcomes and was not selected to improve a measured score.

**Nineteen relevant tests pass**, including six new tests for unique marker scope, conditional normalization, boundary restrictions, predicate/marker exclusion, duplicate-evidence invariance, complete forest coverage, invalid inputs and witness checks. The validator independently refits all **three new source models** and replays **1,680 forests and marker predictions: 1,584 source conditions and 96 target conditions**. It verifies source vocabulary derivation, exact three-way split locations, disjoint IDs, hard marker consistency, typed witness validity, acyclicity, completed optimum scores or explicit abstentions, ROOT/non-root/marker metrics, source gates and permitted target-model evaluation. It also reconstructs the paired confirmation bootstrap.

The principal v2 benchmark took approximately **93.55 seconds**, excluding tests, validation/refits and reporting; peak memory was not measured. Reproduction can vary at the solver time limit, so preserve abstentions and investigate differences rather than changing an old run's score. Source provenance and Latin-period/style limitations remain those of the preceding PROIEL/Perseus reports. Fresh source confirmation is not a previously unseen author, genre or edition.

## Decision and next step

Retain the explicit marker predictor and the simpler marker-only model as interpretable prototypes. The new mechanism improves over the old typed control on fresh source and supplies usable links on one target author, but **there is no consistent three-author advantage over nearest-previous**. Extra parent interactions are not clearly worth their complexity yet. Do not promote this into dictionary optimization or claim grammatical restoration.

The next defensible experiment is **construction-diverse source supervision and marker-scope error analysis**, especially Cicero/Suetonius indirect-speech, relative, copular and nonfinite constructions that the finite-only skeleton compresses poorly. Separate missing predicate endpoints from incorrect marker scope and incorrect parent choice. Use out-of-fold marker predictions for parent fitting, and compare a narrowly scoped joint marker/parent repair against the current hard two-stage pipeline. Freeze a revised design before fresh author-level confirmation; the current target excerpts and both source validation slices are now inspected development/regression data.
