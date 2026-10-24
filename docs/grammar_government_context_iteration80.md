# Government and clause proxies for nominative eligibility — iteration 80

**Modest nominative signal; no reliable grammatical-restoration improvement.** Adding government/marker/carrier proxies raises nominal-nominative F1 from24.45%for79's direct model to25.28%for geometry and25.50%with readable marker identities. Probability loss improves slightly. However, subject-role F1 after soft transfer remains about20.5%, below the original local23.66%; none of the source-calibrated high-precision policies qualifies. Neither new arm is adopted.

| Model | Nominative F1 | Nominative Brier | Nominative NLL | Subject-role F1 |
|---|---:|---:|---:|---:|
| Original local70role/profile posterior | 24.79% | .08498 | .30348 | 23.66% |
| Frozen79direct baseline | 24.45% | .08419 | .30123 | 20.63% |
| Government/marker/carrier geometry | 25.28% | .08325 | .29653 | 20.36% |
| Geometry plus readable marker identities | 25.50% | .08306 | .29607 | 20.48% |
| Geometry, shuffled tuples | 20.10% | .08669 | .32269 | 18.86% |
| Readable identities, shuffled tuples | 22.34% | .08649 | .32176 | 17.22% |

The identity arm improves only0.22percentage points over geometry. Most of the modest improvement does not require marker identity. These reused development comparisons do not establish independent or statistically robust restoration gains.

## Features and access

Keep the masked±2POSandflank features of79. Add the nearest predicted ADP, CCONJ/SCONJmarker and finite-carrier candidate within8positions on each side. Encode distance buckets1/2/3–4/5–8, intervening nominal/marker counts capped at2, and finite-confidence buckets at0.5/0.9. The identity arm additionally encodes the nearest predicted ADP/marker's readable word with its distance bucket. No center word, center POS, center finiteness, content-word identity or reference target grammar enters these features.

Finite probabilities come from the frozen49expanded morphology model at candidate-derived VERB/AUXpositions; other POS receive zero finite probability. That model uses readable neighboring forms/suffixes and source supervision. Nearest finite candidates are **proxies**, not recovered governing predicates or clause boundaries. Nearest ADPs are likewise not verified governors.

Correct neighboring candidate words and sentence boundaries are supplied, as in the preceding diagnostics. Readable marker identities are an additional explicit input privilege, **not established cipher-side anchors**. The geometry arm still uses predicted POS and finite probabilities derived from readable candidate words. No blind Voynich grammatical-restoration claim follows.

Matched shuffle controls jointly permute word/POS/finite-probability tuples; the permutation reproduces the saved baseline shuffle. This preserves per-sentence feature inventories while disrupting order and proximity. It is one saved permutation per sentence, not a comprehensive permutation test.

## Fixed fit/calibration and grammatical tasks

Train both new binary logistic models on the same21,023source-fit content positions, retaining79's minimum feature count3andL2=.001. The source49calibration split remains disjoint:829sentences/7,034positions. Freeze models before calibration and source-selected policies before target predictions. No target-informed model/threshold selection occurs.

Evaluate the same1,273target content positions (123explicit nominal nominatives;107nsubjroles). The nominative task is NOUN/PROPN/ADJwith annotated Case=Nom; absent Case does not count as explicitly nominative. It is not identical to subjecthood. The subject arm softly replaces nominal-nominative profile mass with the learned probability while preserving within-group role uncertainty. It predicts token role, not predicate attachment, and excludes pronoun subjects outside the content cohort.

Policies retain the fixed0.01threshold grid, source-F1 selection and secondary90%precision requirement with at least20predictions across10types. No arm has a qualifying high-precision policy for either task. Small F1/probability-loss changes therefore do not establish solid partial restoration.

## Interpretation and next decision

Preserve the weak government/marker-proximity signal as an ablation, not a default. The Case-oracle finding of78–79still identifies useful information, but neither local POS windows nor these nearest-cue summaries infer it reliably enough for role restoration. Adding readable marker identities has not materially closed that gap.

Before another feature expansion, the next bounded diagnostic should ask whether **actual governor/phrase membership**, rather than proximity, could resolve the remaining Case errors. Declare a source-only controlled oracle for government membership, compare it with the existing nearest-cue features, and measure whether it adds Case discrimination beyond POS and source priors. Do not infer a governing relation from proximity or apply a hard case rule to every nearby nominal. Any target-label use would require an explicitly frozen oracle phase on already declared material; reserve data stays closed. This diagnostic is proposed, not run.

## Verification

Both learned fit objectives and gradients pass optimality checks; gradients have maximum absolute components3.23e−7and1.09e−6. Calibration and target predictions replay with numeric tolerances. Frozen79baseline and shuffled predictions reproduce exactly within those tolerances. Replacing all target center POS/Case/role annotations leaves inference scores unchanged, confirming annotations select/evaluate rows rather than supply features.

Audit verifies1,594prior input hashes. Five new tests cover center masking, geometry identity independence, marker identity restrictions, nearest finite thresholds and radius bounds; all52focused tests pass. No new target annotation queries, grammar reserve, sealed lexical final test or dictionary search is used.

Artifacts: `experiments/results/grammar-restoration/iteration80/`; implementation: `src/voynich_smt/government_context.py`; runner/audit: `benchmarks/grammar_government_context_iteration80*.py`.
