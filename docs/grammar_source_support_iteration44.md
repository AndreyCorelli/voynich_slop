# Iteration 44: expanded source support and stricter context tests

**Additional source support is available, but it does not rescue the occurrence-context model.** The audit increases the ambiguous-predicate support from 29 examples/six verbs to 261 examples/38 verbs in a different, author-separated source pool. On sentence-held-out evaluation, lexical counts reach79.1% accuracy versus77.0% for context; the context model also has worse log loss. On predicate holdout with shared sentences removed from training, accuracy falls from67.8% to64.0%.

## Source selection and audit

Before parsing token annotations, freeze the following selection: use cached PROIEL train/dev/test files, accept only **Cicero and Palladius**, and exclude the reserved200 and **every previously declared sentence ID**, including old source/background IDs as well as queries. Author/source and sentence-ID metadata are checked before token rows. This excludes all Jerome/Caesar material, not merely their query IDs. Keep the previous3–60-token, normalized-singleword, no-multiword-row restrictions and the same simple contiguous prepositional-construction extractor.

These are newly declared source sentences, not additions to the old Jerome/Palladius training pool. The changed author composition means the experiment is not a controlled estimate of the effect of data quantity alone. Cached official dataset splits are pooled as a source resource; the new evaluations use explicitly declared source folds rather than claiming an untouched official test split.

| Source author | Eligible unused sentences | Accusative *in* examples | Ablative *in* examples | Total examples |
|---|---:|---:|---:|---:|
| Cicero | 3,916 | 254 | 593 | 847 |
| Palladius | 154 | 5 | 27 | 32 |
| Total | **4,070** | **259** | **620** | **879** |

Of879 examples,762 have an identified verbal-ancestor lemma. The remaining117 remain in sentence/author evaluation, with a global lexical fallback and bias-only occurrence context; predicate evaluation excludes them.

There are **38 source predicate lemmas with both cases**, totaling261 examples (105 accusative,156 ablative). Thirteen lemmas have at least two examples of each case. Examples include *facio*15Acc/11Abl, *fio*7/9, *mitto*4/4, *sum*3/18, and *uenio*25/1. Many predicates still have a very small minority-case count.

A fitting gate was frozen before the annotation audit: at least100 examples belonging to mixed-case predicates and at least10 such predicates. The new pool passes. No prior query outcomes enter the gate or the new model fitting.

## Fixed model and evaluation

Reuse iteration43's feature extraction and model without tuning:

- Entire target nominal subtree excluded; no target lexical or agreement morphology, Case features anywhere, Number/Gender, or target nominal dependency relation.
- Other occurrence-specific child/parent context and selected verbal morphology remain available under oracle topology/POS/lemma/morphology.
- Ridge1 logistic residual over a mass4 predicate-count prior. Training offsets leave the entire current sentence out. Feature document frequency must be at least2 in each training fold.
- Controls: unchanged lexical counts, bias-only calibration, and occurrence context with a global rather than lemma-specific prior.

All data, rules and source audit are frozen before model fits; predictions are frozen before evaluation. There is no selection among model settings or reuse of the17/41 target query outcomes. No dependency recovery, sentence parsing, ciphertext recovery or practical morphology induction is evaluated.

Run five sentence-grouped folds, five lemma-grouped predicate folds, and leave-source-author-out checks. Predicate folds exclude every training case label for held-out predicate lemmas. The initial predicate folds can contain different predicates from the same sentence on both sides; they are therefore treated as exploratory. After that overlap was identified, a separately declared stricter check removes **all test sentences** from training as well. This is an additional conservative validation, not a tuned replacement model or independent new dataset.

## Sentence-held-out results

| Estimator | All879 accuracy | All879 balanced accuracy | All879 log loss | Mixed261 accuracy | Mixed261 log loss |
|---|---:|---:|---:|---:|---:|
| Lemma counts | **79.1%** | **67.0%** | 0.4806 | 64.8% | **0.6475** |
| Bias calibration | 78.8% | 66.0% | **0.4789** | 64.8% | 0.6531 |
| Context + lemma | 77.0% | 66.4% | 0.5096 | **66.7%** | 0.7095 |
| Context + global prior | 68.6% | 54.0% | 0.6329 | 64.8% | 0.7163 |

Context adds five net correct decisions within the mixed-predicate cohort, but loses18 net correct decisions overall. Its probability estimates are worse in both cohorts. The small ambiguous-cohort accuracy increase is not a consistent scoring improvement.

Ten thousand paired sentence-cluster bootstrap draws, conditional on the fitted folds, give context-minus-lemma accuracy intervals of [-4.08,0] points overall and [-2.60,+6.46] points on mixed predicates. Log-loss reduction intervals are **[-0.0537,-0.0060]** overall and **[-0.1224,-0.0062]** on mixed predicates: the measured probability-quality change is negative. These are within-source checks, not estimates of performance on the reserved target texts.

The mixed cohort is identified from all audited source labels. A training fold may lack one case for a lemma that belongs to this cohort; the cohort label is used only for evaluation, not as a model feature.

## Unseen-predicate checks

| Estimator | Initial predicate-fold accuracy | Initial log loss | Sentence-purged predicate accuracy | Purged log loss |
|---|---:|---:|---:|---:|
| Lemma counts / unseen-lemma fallback | **67.8%** | 0.6474 | **67.8%** | 0.6486 |
| Bias calibration | **67.8%** | **0.6422** | **67.8%** | **0.6421** |
| Context + lemma | 64.4% | 0.6691 | 64.0% | 0.6696 |
| Context + global prior | 64.2% | 0.6786 | 63.6% | 0.6801 |

All762 linked examples are evaluated once in each predicate-fold variant. The stricter variant has neither predicate-label nor sentence overlap between train and test. Initial folds share17–23 sentences across different predicates; the stricter check reduces that to zero without changing the negative conclusion.

In the purged mixed261 subset, lemma accuracy59.8% falls to57.9% with context, and log loss worsens from0.7293 to0.7870. Overall purged balanced accuracy is50.0% for the lexical fallback and49.1% for context. Thus the result is not merely a misleading majority-class accuracy comparison.

No context representation is derived from held-out data. The occurrence features of each test example are extracted using that example's oracle annotation inputs, while vocabulary, weights and lexical statistics use training folds only. Holding a lemma out removes its case labels, not every mention of it as another example's non-target context word.

## Source-author transfer

| Training author → held-out author | Train/test examples | Lemma accuracy | Context accuracy | Lemma/context log loss |
|---|---:|---:|---:|---:|
| Palladius → Cicero | 32 / 847 | 70.0% | 69.8% | 0.6582 / 0.7273 |
| Cicero → Palladius | 847 / 32 | 84.4% | 75.0% | 0.4616 / 0.5009 |

Both directions worsen, but the source-author imbalance is severe. In particular, training on only32 Palladius examples is a limited transfer test. Report the directions separately; a pooled number would mostly describe that weakly supported model on Cicero. These authors are part of the new source audit, not the original Jerome/Caesar query evaluation.

## Implication

A lack of any available ambiguous-case data is no longer sufficient to explain the failure: substantially more support exists and the fixed model still underperforms on held sentences and unseen predicates. This does not prove that occurrence semantics is uninformative, or that this source pool is large enough for every possible model. It does show that adding these generic context features to lemma-count scoring has not earned a place in the grammatical objective.

Retain lemma-conditioned case statistics as a useful local diagnostic. Do not promote the current occurrence model or the aggregate-profile model from iteration42. Further work needs a sharper, falsifiable feature hypothesis or source-only model-selection protocol; repeatedly revisiting the same17/41 query cases would not provide new evidence. These results still concern local case interpretation, not restored grammatical structure.

## Verification and artifacts

359 regression tests pass. The validator reconstructs all51 fitted source models, replays13,128 probabilities, and verifies879 context extractions are unchanged after globally corrupting Case/Number/Gender. It verifies all4,070 source IDs are disjoint from prior declaration **keys and values** and the reserved set; only permitted authors occur; sentence/author folds are disjoint; and the purged predicate check has zero sentence and predicate overlap. All148 frozen-input/declaration hash checks pass. Prior query predictions are not computed; the reserved200 remain unscored.

Run `python -m benchmarks.grammar_source_support_iteration44 prepare`, then `python -m benchmarks.grammar_source_support_iteration44`; the stricter check is `python -m benchmarks.grammar_source_support_iteration44_purged`, and replay is `python -m benchmarks.grammar_source_support_iteration44_validate`. Preparation/fitting refuse overwrite. Artifacts are under `experiments/results/grammar-restoration/iteration44/`, including the pre-audit selection, source annotation truth, audit, case-free features, folds/models, frozen predictions, metrics/intervals, stricter predicate-holdout records and validation. Previous artifacts and the shared todo remain unchanged.
