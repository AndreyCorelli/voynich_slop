# Iteration 142: one anchor-free joint model reaches 71–80% binary class agreement across four texts

**Preserve this development milestone:** one fixed source-trained model combining corrected directional overlap with second-order role similarity gets **Caesar 12/15 (80%), Jerome 12/16 (75%), Gellius 12/15 (80%), and Livy 10/14 (71.43%)**. No supplied word mappings or sentence boundaries enter inference. Its AUC exceeds all sixteen frequency-preserving word-shuffle controls in each text, and NLL is below the balanced prior in all four.

This is a candidate grammatical input for a later decipherment algorithm, not general POS tagging or a lexical nucleus. Function-word candidate membership remains supplied, references are modal type classes, raw Gellius `c` remains ambiguous, and the four texts have been reused during method development. This is not fresh confirmation or a guarantee of reliable Voynich restoration.

## Small frozen model and matched controls

The primary is an **uncalibrated two-feature logistic classifier**, with bias plus corrected left/right neighbor overlap and second-order neighbor-role cosine. Both features use only opaque ID equality, counts, and word order. All inputs, including source training context, are concatenated word streams without supplied sentence boundaries.

Training uses the same thirteen noncatalogue types, strict exclusion of all sixteen target types' labels, three type-held-out source folds, class-balanced loss, and regularization. Feature standardization uses each training fold only. Unlabeled graphs/statistics include other types' occurrences but not their class labels. All models are frozen before target features.

Matched single-feature controls use the same concatenated source stream and training protocol. This removes the old difference between sentence-aware overlap training and sentence-free role training. No large supervised feature bundle is introduced.

Raw probabilities are primary by predeclared design, not chosen after target results. Secondary arms apply the thirteen-type out-of-fold scalar calibration either unconditionally or subject to a source-only feasible-domain check. Every model/offset/guard is frozen before target features. The guard rejects a shift if logit extrema over corrected-overlap bounds [−1, 1] and role bounds [0, 1] make one class impossible. Passing this necessary check does not guarantee good calibration on actual texts.

All four exact full streams remain unchanged. The same sixteen frequency-preserving global shuffles per text as iteration 141 provide matched nulls. Class predictions are frozen before source-modal references and metrics. No new annotations, reserve features, sealed works, PP inference, defaults, or exact word mappings are added. All present candidate types remain included; occurrence support is metadata, not a primary filter.

## Primary results and matched raw controls

| Text | Corrected overlap only | Role similarity only | **Joint primary** | Joint balanced accuracy | Joint NLL |
|---|---:|---:|---:|---:|---:|
| Caesar | 11/15 | 11/15 | **12/15 (80%)** | 78.57% | **0.4731** |
| Jerome | 10/16 | 11/16 | **12/16 (75%)** | 75% | **0.6669** |
| Gellius | 11/15 | 12/15 | **12/15 (80%)** | 80.36% | **0.5068** |
| Livy | 9/14 | 9/14 | **10/14 (71.43%)** | 70.83% | **0.6274** |

The majority all-ADP prior gets eight types correct per text; the balanced prior has NLL 0.6931. The joint model improves hard agreement over both matched raw single-feature models in three texts and ties the role model on Gellius. This does not mean it is best on every metric: Caesar's old calibrated overlap model remains 13/15, and Gellius's role-only ranking remains stronger.

The joint class-confusion counts are:

| Text | ADP correct / available | CCONJ correct / available |
|---|---:|---:|
| Caesar | 8/8 | 4/7 |
| Jerome | 7/8 | 5/8 |
| Gellius | 6/8 | 6/7 |
| Livy | 6/8 | 4/6 |

This is useful discrimination across both classes, rather than a majority-class result. It is binary type classification among given function-word candidates, not token-level POS accuracy across nouns, verbs, and other categories.

## Word-order controls

| Text | Joint AUC | Maximum null AUC | Null AUC at least actual |
|---|---:|---:|---:|
| Caesar | **0.9821** | 0.6071 | 0/16 |
| Jerome | **0.7031** | 0.6250 | 0/16 |
| Gellius | **0.8929** | 0.6071 | 0/16 |
| Livy | **0.6875** | 0.6458 | 0/16 |

Counts and candidate sets are identical in the nulls. These finite correlated controls support an order-sensitive signal, not formal significance or a generalization guarantee. The texts have different lengths and segmentation provenance; no token-matched robustness of this new joint model has yet been established.

## Errors and reference compatibility

The joint model's errors are Caesar `atque`, `que`, `sed`; Jerome `c`, `que`, `sed`, `sine`; Gellius `ad`, `per`, `sed`; Livy `a`, `sed`, `sine`, `uel`. **`sed` is wrong in all four texts**: retain this systematic failure rather than adding a word-specific exception.

Raw Gellius `c` may represent initials instead of the source catalogue's treebank conjunction component. It remains in the primary as specified. As a secondary compatibility check using the pre-existing fourteen-type common set from iteration 139, reference agreement is Caesar **12/14**, Jerome **12/14**, Gellius **11/14**, and Livy **10/14**. This set was defined by full-text presence before this model, not chosen from its errors; it does not remove candidate-set privileges or validate raw token POS labels.

The plaintext names above are attached for assessment only. The model does not infer those identities and has not produced the shared exact-word nuclei required by the lexical goal.

## Calibration guard: useful but insufficient

The source-only guard rejects the role-only calibration because it makes CCONJ unavoidable across [0, 1], reproducing iteration 141's diagnosis. It accepts the corrected and joint offsets because both classes remain mathematically possible somewhere in their feature domains.

Nevertheless, the accepted joint offset **1.6894** damages results to **7/15, 7/16, 7/15, and 6/14**, respectively. A domain check prevents the strongest impossible-boundary failure but cannot ensure transfer to actual feature distributions. These failures remain reported; no calibrated model is chosen per author. The positive primary result is the unshifted model selected in the frozen design.

## Implication and next check

This is the closest current result to a broadly reusable grammatical clue: a simple anchor-free, sentence-free model reaches approximately 71–80% binary type agreement across four development texts. It merits preservation independently of whether the original lexical decoder can use it. Candidate discovery, fresh confirmation, selective reliability, and exact lexical identifiability remain separate unresolved problems.

Next freeze this primary model and check additional **already inspected** Latin works, such as the earlier Apuleius, Curtius, and Suetonius development streams, without opening the remaining sealed works or changing the model. Report all present types and reference/normalization caveats, and use fixed word-shuffle controls. This would challenge adaptive reuse of the present four texts before treating the result as a dependable decipherment component.

## Verification

Independent review verifies 26 frozen input hashes, retrains twelve models, replays 39 out-of-fold probabilities, recomputes 1,020 paired target feature records using separate combinatorial-overlap and dictionary-graph implementations, checks 3,060 model probabilities and 816 metric groups, and reconstructs all 68 transformations. An independent interval calculation verifies every domain guard. Strict training-type exclusion is checked. Eighteen focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration142/`.
