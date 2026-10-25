# Iteration 181 — transfer gain survives source-label permutation controls

**Highlight the strengthened diagnostic:** the frozen rich applicability model trained on actual source labels beats all199 shuffled-source fits on target NLL, Brier loss, AUC and top10 joint yield. One shuffled fit ties actual9/10 top10 case applicability. The frequency/support-only pipeline does not show comparable separation, supporting the relevance of the admitted anonymous context features under this test.

## Frozen experiment

Reuse exact180 features, source-only scaling, ordinary logistic objective, fixed ridge strength.1, optimizer,19 rich/3 control columns, thresholds and tie policy. Generate199 source-label permutations with seeds18100–18298, preserving18 positives among52 source pairs. Use the same label assignment for both arms. Copy actual-label fits from180 as frozen originals; do not choose a new model or refit a winner from target outcomes.

Freeze all source label vectors before fitting, all models before target prediction, and all target probabilities before target evaluation. Primary: lower target NLL of the rich model against shuffled-source fits. Secondary: Brier, AUC, top10 applicability, joint yield, case-type diversity, and paired rich-versus-control gains under each same label assignment. Keep every threshold/top10/top20 list, empty selection and calibration bin. Corrected tails are descriptive `(1 + as-or-more-extreme)/200`, not formal fresh-validation significance: labels of edges sharing endpoints are correlated, and the target is reused same-author development data.

## Rich model versus its shuffled-source fits

| Target metric | Actual-source fit | Shuffled-source mean | Best shuffled-source result | Nulls as good or better /199 | Descriptive tail |
|---|---:|---:|---:|---:|---:|
| NLL (primary, lower) | .4411 | .6821 | .5019 | 0 | .005 |
| Brier (lower) | .1416 | .2364 | .1687 | 0 | .005 |
| AUC (higher) | .8417 | .4834 | .7781 | 0 | .005 |
| Top10 applicability | 90.00% | 24.97% | 90.00% | 1 | .010 |
| Top10 joint yield | 74.58% | 18.42% | 72.22% | 0 | .005 |
| Top10 case-involved types | 11 | 4.23 | 13 | 4 | .025 |

Actual top10 conditional case agreement remains82.87%; this was not the primary permutation endpoint and is not an inferred named-case accuracy. Joint yield retains its diagnostic definition: mean frame-conditioned agreement over **all selected pairs**, with inapplicable pairs contributing zero. It does not mean74.58% of tokens or word identities are restored.

## Frequency/support control and paired gains

The actual-label frequency/support model's NLL.5958 is matched/exceeded in the favorable lower direction by45/199 shuffled fits (tail.230); Brier by50, AUC by51, top10 applicability by54 and joint yield by61. This simple-feature control provides a weaker actual-source-label signal.

| Paired actual-label improvement from rich contexts | Actual improvement | Best same-label shuffled improvement | Nulls as good or better /199 | Descriptive tail |
|---|---:|---:|---:|---:|
| NLL reduction | .1547 | .1111 | 0 | .005 |
| Brier reduction | .0626 | .0448 | 0 | .005 |
| AUC increase | .2151 | .3886 | 8 | .045 |
| Top10 applicability increase | 50 percentage points | 70 percentage points | 10 | .055 |
| Top10 joint-yield increase | 47.36 percentage points | 60 percentage points | 5 | .030 |
| Top10 case-type increase | 4 types | 9 types | 39 | .200 |

These paired contrasts prevent overstating every individual gain as equally robust. Loss improvement is the clearest separation; shortlist applicability improvement over the control has a.055 descriptive tail and diversity improvement does not strongly separate. All values and both full null families remain in the artifacts, including unfavorable results.

## Interpretation and limits

Actual source applicability labels carry a context-feature relationship that transfers to the other passage better than the tested random source assignments. This strengthens180's potential supervised source-language interface to morphological compatibility; it does not require target POS/case labels at inference or exact word mappings as input features. Nothing here restores named cases, general POS, syntactic links, Latin identities or nuclei.

The source has only52 correlated pair examples, both passages are Cicero and were used during development, and the graph restricts the candidate universe. Raw calibration remains imperfect as documented180. Permuting source labels breaks their endpoint dependence, so the descriptive tail is not a formal calibrated probability of generalization. This diagnostic does not establish performance on another author, unseen vocabulary, or Voynich.

Next proposed audit: use existing cached word references only to measure source/target overlap of exact unordered word pairs and endpoints, then report the frozen180 model's target performance separately for unseen pairs and unseen endpoints, with all sparse/empty strata retained. No word identities become inference features and no model is retuned. This checks whether the apparent transfer depends heavily on repeated lexical relations before attempting stronger generalization claims.

## Verification

Independent replay checked199 label assignments and positive inventories, independently solved all400 source models by Newton iterations (398 null plus2 originals), verified gradients below1e-6, every target prediction, classification/calibration score and1,200 list metric groups. Exact180 original models, predictions and summaries matched, and all scalar scores, paired gains and tail directions passed. Frozen label/model/prediction hashes passed. The broader test suite was not rerun for this reference-only diagnostic; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_source_labels_iteration181.py`; reviewer: `benchmarks/grammar_case_source_labels_iteration181_review.py`. Frozen design,199 permutations, full models/predictions/selections/summaries, scalar metrics, contrasts, audit and verification manifest: `experiments/results/grammar-restoration/iteration181/`.
