# Iteration 45: which revealed facts resolve a construction?

**Boundary information propagates; predicate revelation mostly removes an unconstrained variable.** Among869 initially ambiguous examples whose reference survives, supplying the correct boundary resolves270 additional nominal-head choices and131 case choices. Supplying the predicate resolves **no other field**, even though it makes422 complete tuples unique. A wrong predicate produces the same kind of false certainty. The distinction between genuine propagation and directly supplying a missing answer is essential.

## What is tested

Reuse iteration44's879 source *in* constructions from Cicero/Palladius. No prior Jerome/Caesar query or reserved sentence is scored. The experiment has no fitted objective, likelihood ranking, or optimizer: it enumerates compatible alternatives.

A hypothesis has four fields:

1. Phrase boundary: left/right endpoints.
2. Nominal head to which *in* attaches.
3. Head case: accusative or ablative.
4. First verbal ancestor token, or a single `None` category for no verbal ancestor.

This is a **four-field PP construction schema**, not a complete sentence parse. The null category does not identify the actual nonverbal governor, and modifier attachments are assumed by the compatibility schema rather than independently recovered.

Generate nominal-head candidates within8 tokens of the known *in* anchor; all anchor-containing intervals of length2–8; both cases; and every VERB/AUX in the sentence plus `None`. Cross these domains with the head inside the phrase and the predicate outside it. Oracle domain augmentation guarantees that correct field values are available without marking the correct combination. In this dataset, **no augmentation was needed**: all reference heads, boundaries and predicates already occur in the raw domains.

The grammar filter admits only nominal/adjectival/DET/NUM phrase material besides the anchor. It requires an existential morphology witness: head case; agreement of ADJ/DET in case/number/gender; other nominals may share the head case or have genitive case. Missing morphological features are wildcards. No reference dependency edges or token-specific reference morphology are read during filtering.

The morphology dictionary is an explicit **oracle word-type lattice**: all observed Case/Number/Gender tuples per normalized word/POS across the4070 iteration44 source sentences, including analyzed sentences. POS, anchor, token identities and sentence boundaries are also privileged. This excludes retrieval failure as intended, but does not establish a practical morphology channel for ciphertext.

Run two arms:

- **Oracle word-type morphology:** use its observed case/number/gender tuples.
- **Hidden case:** mask Case in those tuples, retaining exactly the same number/gender information. Both head cases are therefore symmetric under the implemented rules.

Predicate identity has **no semantic, valency or lexical-government compatibility constraint**. It is constrained only to lie outside the phrase. Since the phrase template excludes verbs, predicate choices factor out completely. Thus predicate revelation results characterize this rule set, not the intrinsic linguistic value of knowing a predicate.

## Candidate pruning and reference survival

| Stage | Oracle word-type morphology | Hidden case |
|---|---:|---:|
| Raw geometry-compatible tuples | 423,850 | 423,850 |
| POS-compatible tuples | 59,480 | 59,480 |
| Morphology-compatible tuples | **11,816** | **48,934** |
| Reference constructions surviving | **875/879** | **877/879** |
| Unique and correct with no facts revealed | **6/879** | **0/879** |

The large reduction in alternatives is not the same as recovery: most constructions remain ambiguous, and some correct constructions are eliminated. Empty sets are failures, not unique solutions.

## Single-fact propagation

For the primary oracle-morphology arm, restrict this table to the869 examples that retain their reference but have more than one baseline hypothesis. “Newly resolved” means an **unrevealed** field becomes uniquely correct when it was not uniquely correct before.

| Correct fact revealed | Median remaining tuples | Newly resolved boundary | Newly resolved nominal head | Newly resolved case | Newly resolved predicate |
|---|---:|---:|---:|---:|---:|
| None | 8 | — | — | — | — |
| Boundary | 5 | supplied | **270** | **131** | 0 |
| Nominal head | 6 | **66** | supplied | **130** | 0 |
| Case | 7 | **73** | **95** | supplied | 0 |
| Predicate | 2 | **0** | **0** | **0** | supplied |

Boundary revelation resolves additional heads in31.1% and cases in15.1% of this cohort. Head revelation resolves more cases but fewer boundaries than boundary revelation. These are conditional dependencies in this lattice, not a cost-normalized ranking of acquisition strategies: a boundary supplies two endpoints, a case supplies one binary value, and domain sizes differ.

In the hidden-case arm, boundary revelation newly resolves459 heads among877 reference-surviving ambiguous examples. It resolves no case. Revealing case resolves no other field: it only selects one of two symmetric copies. This symmetry is built into the masked model, not evidence that real Latin or ciphertext inherently lacks all case information.

## Complete-tuple uniqueness

| Revealed facts | Oracle morphology: uniquely correct /869 initially ambiguous | Hidden case: uniquely correct /877 initially ambiguous |
|---|---:|---:|
| None | 0 | 0 |
| Boundary | 8 | 0 |
| Head | 2 | 0 |
| Case | 4 | 6 |
| Predicate | 422 | 0 |
| Boundary + predicate | **799** | **0** |
| Head + predicate | 487 | 0 |
| Case + predicate | 517 | 288 |
| Boundary + case + predicate | 851 | 854 |
| All four fields | 869 | 877 |

The all-four row is tautological given reference survival and is only an integrity check. The predicate-only row is also easy to misread: it often completes a tuple because the phrase analysis was already unique and predicate choice was the only remaining free factor. It does not infer another fact.

With oracle morphology, minimum numbers of revealed fields needed for a unique correct tuple are: zero for6 examples, one for432, two for407, three for30; four references have already been pruned and cannot be recovered. With case hidden: one for6, two for297, three for560, four for14; two references are pruned. Multiple inclusion-minimal fact sets may exist for one construction; their overlapping counts are saved separately.

Even with correct boundaries and predicates,70 reference-surviving oracle-morphology constructions remain ambiguous. Their remaining alternatives are indistinguishable **to this constraint system**, not proved indistinguishable under all possible linguistic evidence.

## Consistency does not validate supplied facts

For each example/arm/field with an alternative, sample one incorrect field value uniformly from its raw domain, using fixed seed45001. Condition this audit on the baseline retaining the reference. These are incorrect treebank facts; surviving alternatives are not certified grammatical readings.

| Wrong fact supplied | Oracle morphology: nonempty / probes | Unique wrong tuples | Hidden case: nonempty / probes |
|---|---:|---:|---:|
| Boundary | 47/875 | 1 | 101/877 |
| Nominal head | 115/846 | 1 | 200/848 |
| Case | 183/875 | 4 | 877/877 |
| Predicate | **855/855** | **422** | **857/857** |

Every tested wrong predicate remains compatible, because no rule links that choice to the phrase. With oracle morphology,422 wrong-predicate probes even yield a unique wrong tuple. This is a model-identifiability failure, not an optimizer or smoothing failure. High consistency or uniqueness cannot establish correctness when the constraint graph leaves a relation disconnected.

These counts use one probe per available field, not all alternatives. No alternative means no probe, hence unequal denominators.

## Hard constraints also make concrete errors

The oracle-morphology arm rejects four references; the hidden-case arm rejects two. The failure audit identifies a specific assumption behind these losses: **every ADJ/DET is treated as an agreeing modifier**.

Examples include *in illius potestate*, *in istius potestate*, and *in istorum sella curuli*: the genitive determiner/possessor need not agree with the ablative head. Another retained reference span contains *in turma inauratarum*, whose genitive plural adjective does not satisfy the imposed head-agreement rule. These are treebank reference counterexamples to the implemented schema, not demonstrations that their readings are ungrammatical.

The correct candidate was available before filtering. Hard filtering removed it. Revealing every reference fact cannot recover a candidate already rejected by the grammar. The primary results preserve these failures; no rule is silently relaxed after evaluation.

## Wider domains

A16-token head window and maximum span were declared before enumeration as a sensitivity check. Oracle-morphology survivors remain exactly11,816. Hidden-case survivors grow to50,498, but the reported median counts and unique-recovery counts for the single-fact and principal combined interventions remain unchanged on the **same primary ambiguous cohorts**. Exact per-intervention comparisons are saved. This limits concern that the principal result is only an8-token-window artifact; it does not remove the template/POS/morphology assumptions.

## What to pursue

The useful hypothesis is now more specific: **boundaries can connect ambiguous local analyses, while a governor label helps only if some constraint connects it to those analyses.** Boundary estimation is therefore a justified local target under this morphology channel. The matrix does not justify claiming predicate information is linguistically unhelpful; the implemented PP grammar simply cannot use it for propagation.

Before another decoder, add explicit internal-role alternatives for agreeing modifiers versus genitive possessors and test that correct readings survive. For relation recovery, choose a construction with a genuine cross-token constraint—such as finite subject–predicate person/number agreement—and repeat the intervention test. That would test actual governor–dependent propagation rather than removing a free label. Any such experiment should preserve candidate-survival and wrong-fact checks alongside uniqueness.

No full grammatical structure, practical morphology, or ciphertext translation has been restored here.

## Verification and artifacts

365 regression tests pass. The validator replays56,256 primary/wide intervention summaries, checks all1,758 predicate-factorization cases and879 hidden-case symmetries, verifies monotonicity under adding facts and expanding candidate domains, reconstructs the oracle dictionary and lattices, and confirms candidate filtering ignores reference edges and token-specific morphology. All11 frozen-input hash checks pass. The reserved200 remain unscored; no prior target queries are evaluated.

Run `python -m benchmarks.grammar_construction_interventions_iteration45` (refuses overwrite), then `python -m benchmarks.grammar_construction_interventions_iteration45_validate`. Core code is `src/voynich_smt/construction_interventions.py`. Artifacts under `experiments/results/grammar-restoration/iteration45/` include the declaration, oracle morphology, candidate lattices, all16 interventions, wrong-fact probes, minimal-revelation sets, wider-domain comparison, reference-pruning audit and validation. Previous artifacts and the shared todo remain unchanged.
