# Boundary and relation oracle diagnostics

## Fixed diagnostic plan

Freeze iteration 7 weights, gold predicate positions and complete gold marker evidence. Evaluate the gold-marker-trained parent model as primary and the out-of-fold-marker-trained model as a replication. Exclude the failed exploratory contrast model. Reuse development and confirmation passages, explicitly as previously inspected source material; this is not fresh confirmation or author transfer.

Cross two candidate restrictions: gold sentence boundaries (remove cross-sentence parent choices) and gold predicate relation labels (retain only ROOT, coordination or subordination choices matching that predicate's reference label). Include unrestricted, boundaries-only, roles-only and both-oracle conditions. The role oracle reveals which predicates are ROOT; ROOT accuracy in that condition is supplied information, not a recovery result. Report non-root parent accuracy and the number of non-root children with more than one possible parent after masking, alongside edge/typed-edge F1 and exact reference-score gaps.

Keep all retained logits unchanged, including original feature geometry and marker attachments. Boundaries restrict parent choices only; do not recompute marker predictions or inject reference parent identities. Recompute conditional probabilities over the retained candidate set. Use exact integer maximum-spanning arborescences with a super-root for all conditions, including a new unrestricted baseline, so oracle gains do not include changes in solver completion. Preserve the original iteration 7 abstention figures separately and compare scores for every originally completed baseline. Do not overwrite iteration 7 results.

Inspect up to twenty residual wrong-parent choices from the primary model under both oracles, selecting the first ten in stream/child order per source author from development only. If an author has fewer than ten, inspect all available without replenishing from confirmation. Include normalized sentence text, predicate positions, marker evidence, parent candidates/margins and the original UD dependency path. Distinguish an annotation-derived reference from an independently verified linguistic analysis; record uncertainties rather than silently relabeling examples.

Validate retained candidate sets and unchanged logits, reference feasibility, acyclic selected witnesses, exact selected/reference scores and monotonicity of the reference score gap under nested restrictions. Cross-check the new solver on the twenty reviewed conditions against the existing Z3 solver with an adapter that masks candidates. No model fitting, new target evaluation or dictionary search.

## Results

All 1,056 conditions complete under the exact forest solver. The primary model is the frozen gold-marker-trained model; every condition also supplies the same gold predicate positions and iteration 7 reference marker attachments. “Confirmation” below is the previously inspected iteration 7 cohort: 66 streams, 2,123 tokens, 158 non-root reference edges. It is not a new confirmation claim.

| Restriction | Non-root edge F1 | Non-root parents correct | Correct among children with >1 possible non-root parent | Reference strictly outscored / 66 |
|---|---:|---:|---:|---:|
| Unrestricted | 44.37% | 63/158 (39.87%) | 63/158 (39.87%) | 50 |
| Gold sentence boundaries | 51.49% | 69/158 (43.67%) | 44/120 (36.67%) | 44 |
| Gold relation labels | 62.66% | 99/158 (62.66%) | 99/158 (62.66%) | 29 |
| Both | 71.52% | 113/158 (71.52%) | 75/120 (62.50%) | 23 |

Gold boundaries remove 25 selected cross-sentence parent links in the unrestricted primary condition, but net correct non-root links increase by only six. Thus the F1 gain partly reflects fewer false attachments, rather than many more correct parents. Gold roles help more, but supply ROOT identity: their ROOT F1 is 100% by construction, and edge F1 equals non-root parent accuracy because exactly the correct number of non-root edges is supplied. Of the 113 correct edges with both oracles, 38 have only one permissible non-root parent; the 75/120 result describes the remaining ambiguous cases. Neither restriction supplies which parent to choose when several remain.

The out-of-fold-trained replication gives 43.54%, 49.04%, 62.66% and 71.52% F1 respectively, with the same 75/120 ambiguous-parent accuracy under both oracles. On development, primary F1 is 54.62%, 61.61%, 78.36% and 86.57%; both-oracle ambiguous-parent accuracy is 65/83 (78.31%). The considerable development/confirmation difference remains under ideal supplied information.

These are changes in feasible choices, not improvements from a learned boundary or role model. They show headroom for separating grouping/role decisions from parent choice, while also leaving substantial errors once both are supplied. The reference forest remains strictly beaten in 23/66 confirmation streams under both oracles.

### Baseline and completion accounting

The new unrestricted score optimum matches every originally completed baseline. Two old primary/replication confirmation baselines abstained under the time-limited solver; this diagnostic solves them exactly and recalculates *all four conditions* with the same solver. Consequently 44.37% is the appropriate primary baseline here, rather than iteration 7's abstention-inclusive 45.09%. The old artifacts and denominators are preserved. No observed oracle gain includes switching only one condition to a solver with better completion. Tied optimum witnesses may differ; score comparisons are exact integer comparisons at the original 1e-6 scale.

### Residual review: a concrete projection problem

The deterministic development review contains seventeen cases: all seven available Jerome residuals and the first ten of eleven Palladius residuals, across eleven streams. This is a qualitative review of original text and UD paths, not independent expert adjudication. Full normalized sentences, candidate logits/margins, marker evidence, dependency paths and notes are saved in [review.json](../experiments/results/grammar-restoration/iteration8/review.json).

The remaining errors include an intervening parenthetical (one), intervening relative clauses (three), nesting errors (five), coordination level errors (four), and one each involving relative scope, coordinated subordinates, sibling subordinates and a questionable projected reference. These small, selected counts describe the reviewed cases only.

Two examples illustrate distinct failure types:

- **13263, `dederit`:** the reference parent is `perdet`, but the model chooses intervening `dico` (“amen dico uobis”). The original UD annotation marks `dico` as parataxis under `perdet`. Correct role and sentence membership do not distinguish the parenthetical from the main predicate. The chosen-parent advantage is 1.481 score units.
- **13305, `sunt`:** the text contains `factae fuissent uirtutes quae factae sunt ... mansissent`. Our reference says `sunt → mansissent`; the model chooses `sunt → fuissent`. The raw UD path goes from `sunt` to relative participle `factae`, then `uirtutes`, then the outer participle `factae`, then `mansissent`. The finite auxiliary `fuissent` is a **child branch** of the outer participle, so the nearest-finite-*ancestor* rule cannot encounter it. At the level of clause complexes, the chosen `fuissent` is a plausible governor. Treating this automatically as a grammatical model error would be misleading.

The same mismatch affects the marker oracle. In 13305, relative `quae` is routed to `mansissent` instead of the finite representative of its local relative predicate, `sunt`. The `si` marker on outer `factae` is omitted entirely because its immediate head is nonfinite. Thus “gold markers” in iterations 5–8 mean **the current mechanically projected reference markers**, not a guarantee of complete and linguistically correct clause-complex markers. The observed score failures remain valid relative to that frozen reference, but cannot all be attributed to poor grammar scoring.

A mechanical audit across the already inspected cohorts finds:

| Projection audit | Development | Confirmation |
|---|---:|---:|
| Verbal heads with one finite auxiliary child | 23 | 28 |
| Existing marker targets whose ancestor path skips such a local auxiliary | 4 | 8 |
| Direct `mark`/`cc` omitted on such verbal heads | 8 | 7 |

These counts identify a concrete extraction mechanism, not a revised gold standard or a measured restoration improvement. The audit does not cover every copular, elliptical or multi-auxiliary construction.

### Next step

Repair and test **predicate-complex projection before another scoring experiment**: give a participle/nonfinite verbal head and its finite auxiliary a shared clause representative, then derive marker scopes and inter-clause parents through those representatives. Preserve unresolved/multiple-auxiliary cases explicitly. Use the cited sentences as regression cases, audit source-only reference changes, and refit/evaluate under a separately labeled reference version. Old and revised metrics must not be compared as if their targets were identical.

After that correction, the oracle gains justify testing a separate ROOT/relation classifier and a boundary/grouping model. They do not yet show those decisions can be learned reliably from the available evidence. No dictionary search was run.

### Reproduction and verification

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_boundary_role_iteration8
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_boundary_role_iteration8_review
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_boundary_role_iteration8_validate
```

The benchmark preserves existing outputs and takes under one second, excluding manual review and validation. The [validator](../experiments/results/grammar-restoration/iteration8/validation.json) reconstructs frozen candidate logits, verifies exact masks and unchanged evidence, checks selected/reference scores, checks reference-gap monotonicity under nested restrictions, and independently matches Z3 optima for all four conditions in the eleven reviewed streams (44 checks). Existing outputs remain unchanged. Input, implementation and result hashes are saved alongside the report.

Thirty-four focused tests pass, including new checks that role masks retain wrong-parent alternatives, boundary masks remove only cross-sentence parents, logits are unchanged and cycle constraints survive the oracle masks. Paired stream-bootstrap intervals (2,000 draws, seed 1729) for primary confirmation edge-F1 gains over the recomputed unrestricted baseline are +7.13 points [3.99, 11.08] for boundaries, +18.29 [10.48, 26.95] for roles and +27.15 [19.02, 36.99] for both. These describe oracle restrictions on inspected same-author passages; they do not estimate the gain of a learned restoration system.
