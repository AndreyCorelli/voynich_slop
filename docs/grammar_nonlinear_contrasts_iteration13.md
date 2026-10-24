# Nonlinear capacity check and construction audit

## Fixed plan

Keep iteration 12's 131 matched source contrasts, forty matched development contrasts, twenty same-child contrasts, feature vectors (137 rich / two geometry), marker predictions, parent confusions and reference version unchanged. Reuse the existing source cross-fit artifacts; do not regenerate errors or change matching. Fit one tightly constrained nonlinear specification for each feature set: five Newton-boosted binary trees, maximum depth two, minimum leaf size twenty observations, leaf L2 penalty ten, shrinkage 0.2, clipped leaf updates of magnitude at most one. Use joint depth-two split search (including zero-gain first splits), source-only candidate thresholds (all distinct midpoints for <=5 unique values, otherwise source quartiles), fixed deterministic tie-breaking, and no development parameter sweep. Frozen linear classifiers from iteration 12 are controls. Compare fitting and development performance; a negative result for this limited model does not rule out all nonlinear models.

Apply the unchanged iteration 12 diagnostic screen with the nonlinear rich and nonlinear distance models. No classifier score is composed with the decoder, and no confirmation/target inference is performed regardless of the result. Development has been repeatedly inspected; report descriptive paired stream uncertainty and no fresh-generalization claim.

Before fitting, reserve a new cohort by sentence IDs only: first 100 previously undeclared retained sentences per Jerome/Palladius at or beyond author-relative position 700. Check overlap against all prior grammar-restoration manifest/truth artifacts; record hashes and IDs in a separate holdout registry. Do not construct/evaluate model features or predictions for the reserved cohort. This reservation is for later validation, not an extra evaluation of the current model.

Audit all twenty existing same-child development contrasts, including the five distance-controlled cases, rather than selecting failures after observing the nonlinear output. Save normalized text, true/cross-parent positions, original UD paths, projected complex metadata, predicted marker evidence, feature differences and classifier preferences. Assign qualitative construction categories and state what observable evidence could distinguish the alternatives. Separate supplied reference annotations from available token/morphological evidence and from hypotheses requiring a new parser. Do not relabel or fit on the audit. Use this audit to recommend one narrow construction mechanism, not a new full decoder.

Validate the nonlinear implementation against logistic-loss reduction and serialization, source-only splits/thresholds/leaf sizes, deterministic refits, unchanged samples/features/controls, all prediction metrics and the holdout exclusion registry. Preserve earlier outputs.

## Nonlinear result: better point estimates, insufficient evidence to promote

The nonlinear rich model improves over the frozen linear rich model on the same development examples, but fails the predeclared diagnostic screen. It misses the absolute matched-AUROC and matched-preference requirements, and the matched-preference gain over its distance control is below ten points. Same-child accuracy reaches the inclusive threshold. No model was selected by a development sweep, and no new score was added to the decoder.

| Model | Source fitting preference | Development matched AUROC | Development matched preference | Development same-child preference |
|---|---:|---:|---:|---:|
| Frozen linear, distance only | 51.15% | 49.47% | 48.75% | 60.00% |
| Frozen linear, rich | 92.37% | 42.50% | 32.50% | 35.00% |
| Fixed nonlinear, distance only | 50.00% | 50.00% | 50.00% | 50.00% |
| **Fixed nonlinear, rich** | **74.81%** | **57.88%** | **57.50%** | **60.00%** |

The nonlinear model wins 23/40 matched comparisons. On same-child contrasts it wins eleven, ties two and loses seven; 60% awards ties half credit. The five tightly distance-controlled same-child cases score 50%, with ties included. These sample sizes remain too small for a strong generalization claim.

The rich nonlinear model actually uses five depth-two trees with twenty terminal leaves in total. Each leaf has at least twenty training observations; Newton updates use L2=10, clipping at one and shrinkage 0.2. Its source logistic loss decreases monotonically from 0.6931 to 0.6624. The distance-only nonlinear fit remains constant and has no useful split, as expected when almost every source contrast has identical geometry. Joint two-level search is tested on XOR, so zero first-split gain does not automatically prevent a genuine depth-two interaction.

Matched development Brier score improves from 0.3976 for linear rich to 0.2444 for nonlinear rich; log loss improves from 1.3384 to 0.6819. The constant balanced predictor has 0.25 Brier and 0.6931 log loss. Thus the new model is less overconfident on this sample and modestly better than a constant predictor on those point estimates. Probabilities remain conditional on the deliberately balanced, decoder-error-selected sample; they are not calibrated general sentence-membership probabilities.

This is a **capacity/regularization diagnostic**, not a clean attribution to nonlinearity alone: the tree learner also has much stronger capacity restrictions than the 137-feature linear fit. The result is compatible with the earlier model overfitting its source confusions, while leaving room for missing evidence and construction shift. Neither the improvement nor the failed screen proves that all classifiers over these features would behave similarly.

### Uncertainty on reused development

Descriptive paired stream-cluster intervals use the same fixed matching and seed 1729 as iteration 12:

- Nonlinear rich matched preference: **57.50% [32.14%, 80.96%]**.
- Matched preference minus nonlinear distance: **+7.50 points [−17.86, +30.96]**.
- Matched preference minus linear rich: **+25.00 points [0.00, +51.16]**.
- Nonlinear rich same-child preference: **60.00% [36.84%, 81.83%]**.
- Same-child preference minus nonlinear distance: **+10.00 points [−13.16, +31.83]**.
- Same-child preference minus linear rich: **+25.00 points [−10.88, +60.72]**.

The pool bootstrap weights both stream endpoints when positives and negatives come from different streams and holds matching fixed. It omits refitting/matching uncertainty. Development has been inspected repeatedly; these are descriptive intervals, not new author-transfer or fresh-confirmation evidence. The improvement over the poor linear baseline is not enough to establish reliable discrimination over the distance control.

## Construction audit

All twenty same-child contrasts were reviewed, regardless of whether the nonlinear model improved them. The [full audit](../experiments/results/grammar-restoration/iteration13-v2/construction-audit.json) records normalized sentences, reference/cross-parent positions, original UD witness paths, projected complex membership, independent morphology readings, predicted marker scopes, feature-block differences and every model's preference.

Primary qualitative categories are:

| Construction family | Cases |
|---|---:|
| Relative or free-relative | 10 |
| Conditional | 6 |
| Temporal/circumstantial | 3 |
| Causal | 1 |

These categories describe the selected decoder-confusion set, not natural-language frequencies. Several examples combine multiple constructions. The audit does not relabel references, train a rule or provide expert adjudication. No pair has exactly identical rich feature vectors; differing vectors do not establish that they encode the relevant grammatical relation.

### Repeated missing relation: a nominal bridge

Seven of the ten relative cases have an **annotated nominal intermediate** between the relative predicate complex and its projected finite governor. Examples:

- **13249, `est → negabo`:** the relative `qui est in caelis` is associated with `patre`; the raw UD path passes through the locative copular head `caelis` and then `patre`. The copular head is part of the child's own complex, not a candidate antecedent. A useful model must distinguish that internal structure from the external nominal link.
- **160128, `nocent → patieris`:** `quae uitibus nocent` modifies `animalia`, which belongs to the main predicate's nominal material. Direct child/parent verb agreement is not sufficient: the false `crucifigunt` may agree with `nocent` in number while being in another sentence.
- **160198, `excipiatur → accedat`:** relative `quibus` connects to `aluearia` inside the participial material headed by `habens`; the finite governor is `accedat`. The path requires nominal and participial argument structure, not just marker proximity.
- **160209, `possit → debebunt`:** relative `quae` is tied to a measurement phrase (`magnitudine`), with a quantifier/modal bridge before the finite governor. This is more complex than nearest-noun attachment.

Other relative cases are free relatives, parallel/elliptical coordination or arguments without an obvious overt nominal antecedent. In **160182**, several feminine nouns are possible antecedents; UD chooses a path through `parte`, but that is not independent proof of the best linguistic reading. In **13313**, the nominal path in a free-relative/coordination context likewise needs careful interpretation. These cases should remain explicit exceptions or adjudication cases rather than force a convenient rule.

The existing 137 features encode broad morphology existence flags, small endpoint windows, interval means/maxima and marker presence. They do **not** explicitly encode a chosen relative-pronoun analysis, a nominal antecedent, or that nominal's governing predicate. The independent morphology lattice retains more case/gender/number readings than those summaries, but merely finding compatible readings independently would allow contradictory analyses. Any new bridge should commit to compatible analyses within the construction.

### Other recurrent requirements

The conditional and temporal examples often involve a matrix copula or a reported/nonfinite complement: `factum est cum ...`, `feruntur ... ungendae`, `pelli ... dicuntur ... si ...`, and `fugari posse ... si ...`. Several contain an intervening relative or a sibling subordinate clause. This suggests testing explicit complex/span and argument relations rather than interpreting a generic subordinate-marker flag as evidence for a particular parent. These are hypotheses about useful evidence; no new parser was implemented here.

## Next bounded mechanism

Start with **relative pronoun → nominal antecedent → governing predicate** on the simpler nominal-relative cases, before attempting free relatives or elliptical coordination:

1. Retain independent case/gender/number alternatives and choose a consistent relative/antecedent analysis. Gender/number agreement can help; the relative pronoun and antecedent need not share case.
2. Recover the nominal's relation to a finite predicate or supported nonfinite/auxiliary complex using observable morphology and constituent structure. Do not use the audit's UD head chain as an inference feature.
3. Test with at least three finite candidates and plausible wrong governors, so success cannot come from a forced sole-parent choice. Include both subject and object/oblique antecedents.
4. Check a controlled source construction set, then independently labeled natural cases. Keep the newly reserved cohort untouched until the mechanism and decision rules are frozen.

This recommendation follows the repeated annotated relation, not an assertion that agreement alone solves clause attachment. It is a separate next experiment; the current task stops at the nonlinear test and audit.

## Reserved validation cohort

[Holdout registry](../experiments/holdouts/grammar-construction-next.json) reserves **100 Jerome and 100 Palladius sentences**, author-relative retained positions **700–799**. All IDs are disjoint from the 31 earlier grammar-restoration manifest/truth declarations audited before the nonlinear fit, and from the fitting/development groups used here. The registry records exact IDs, retained positions and input hashes.

The corpus is parsed only to enumerate retained sentence IDs. No classifier features, scores or predictions were evaluated for the reserved sentences, and the nonlinear settings were not selected on them. The disjointness claim is scoped to declared grammar-restoration samples, not every unrelated repository experiment. A future study must consult this registry and declare its reference/selection policy before using the cohort.

## Reproduction and validation

```sh
# Initial reservation only; refuses to replace an existing registry.
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_nonlinear_contrasts_iteration13_reserve
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_nonlinear_contrasts_iteration13
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_nonlinear_contrasts_iteration13_audit
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_nonlinear_contrasts_iteration13_validate
```

Fifty-one focused tests pass, including OR/XOR interactions, capacity limits, serialization/refit determinism and inclusive numerical screen thresholds. The [validator](../experiments/results/grammar-restoration/iteration13-v2/validation.json) refits both nonlinear models from unchanged source features, reproduces both frozen linear controls and all logits/metrics, checks source-only threshold candidates and leaf membership, independently checks Newton sums/updates and monotonic training loss, verifies all twenty selected annotated witness paths and checks 200 reserved IDs remain disjoint and unscored. Paired uncertainty and the failed screen reproduce.

Validated outputs are in `iteration13-v2`. The initial `iteration13` run and its runner snapshot are preserved: v2 fixes floating-point handling of an inclusive +10-point threshold (`0.6 - 0.5`) only. Validation confirms **identical models and predictions** across the two runs; no model setting was retuned. Both runs fail the overall screen. [Report](../experiments/results/grammar-restoration/iteration13-v2/report.json) and [diagnostics](../experiments/results/grammar-restoration/iteration13-v2/diagnostics.json) preserve the result. The benchmark took 0.55 seconds. No decoder score composition, confirmation/target inference or dictionary optimization.
