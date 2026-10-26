# Iteration 182 — transfer survives unseen-pair evaluation, not a novel-vocabulary test

**Preserve the positive overlap check:** on114 exact word pairs absent from source training, the frozen rich model retains applicability AUC.8283 and NLL.4556 versus.6331/.5970 for frequency/support. Eight of the nine case-comparable relations in the original global top10 are unseen training pairs. This rules out dependence solely on repeated exact supervised pair identities, while leaving same-author and vocabulary generalization limits.

## Frozen audit

No models, features or probabilities change. Map source/target salted opaque IDs to a common audit hash using only WORD fields from already-cached annotations; verify exact word-stream hashes and perform no extra normalization. Words are used only for overlap evaluation, never inference features or selection. Freeze all overlap rows and masks before consuming case outcomes.

Primary: unseen exact unordered pair relative to the52 supervised source candidate pairs. Disjoint overlap strata: seen pair; new pair with both endpoints represented in source training; exactly one endpoint absent from the supervised graph; both endpoints absent. Separately measure endpoint membership in the **entire source passage vocabulary**, which is broader than its53 supervised endpoints. Keep all sparse, empty and one-class strata.

Evaluate all three frozen180 arms. Intersect the original global threshold/top10/top20 lists with each stratum as the primary shortlist audit; separately show fixed within-stratum top10/top20 rerankings with exact ties. Do not substitute a reranked list for the original global selection.

## Applicability classification by supervised overlap

| Target stratum | Pairs | Case-applicable | Rich AUC | Control AUC | Rich NLL | Control NLL | Rich Brier | Control Brier |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| All | 126 | 36 | .8417 | .6265 | .4411 | .5958 | .1416 | .2043 |
| Seen exact pair | 12 | 2 | 1.0000 | .6500 | .3034 | .5849 | .0795 | .1997 |
| **Unseen exact pair (primary)** | **114** | **34** | **.8283** | **.6331** | **.4556** | **.5970** | **.1482** | **.2047** |
| New pair, both training endpoints | 30 | 3 | .9877 | .7531 | .2955 | .4102 | .0810 | .1182 |
| Exactly one unseen training endpoint | 64 | 25 | .8021 | .5364 | .5174 | .6864 | .1742 | .2465 |
| Both unseen training endpoints | 20 | 6 | .7619 | .6071 | .4981 | .5908 | .1656 | .2008 |

“Control” means the same frozen source-trained frequency/support-only model. The main disjoint strata sum12+30+64+20=126; unseen-pair comprises the last three. “Unseen training endpoint” means absent from labeled source graph endpoints, not necessarily absent from the source text. Small cells, especially30 pairs with only3 positives, are descriptive and not fresh tests selected for significance.

## Original global top10, intersected with strata

| Stratum | Original top10 pairs retained | Case-comparable | Case-involved types | Conditional case agreement |
|---|---:|---:|---:|---:|
| All | 10 | 9 | 11 | 82.87% |
| Seen exact pair | 1 | 1 | 2 | 95.83% |
| **Unseen exact pair** | **9** | **8** | **10** | **81.25%** |
| New pair, both training endpoints | 1 | 1 | 2 | 100.00% |
| Exactly one unseen training endpoint | 7 | 6 | 8 | 75.00% |
| Both unseen training endpoints | 1 | 1 | 2 | 100.00% |

The100% cells each contain one case-comparable pair and are not high-confidence generalization estimates. Type counts can overlap across rows. Fixed within-unseen-pair reranking yields9/10 applicable pairs,11 types and82.10% conditional agreement, but is a different shortlist from the original9-pair intersection. Within-both-unseen-training-endpoints top10 has only4/10 comparable pairs,6 types and65.63% conditional agreement; thus original high applicability should not be extrapolated across every small stratum.

## Whole-passage vocabulary overlap is extensive

**125/126 target pairs have both words present somewhere in the source passage**, one pair has only one source-vocabulary word, and none has two wholly unseen words. The single partly novel-vocabulary pair is case-applicable but receives rich-model probability below.5, is absent from its original top10, and has0% conditional case agreement; one positive example cannot support an AUC. The zero-source-vocabulary-overlap stratum is empty and explicitly retained.

Consequently this is not an evaluation on a substantially novel vocabulary, despite no word-identity features. It demonstrates transfer of anonymous contextual signals to new pair combinations and some endpoints without supervised source examples. Source passage vocabulary exposure and source **label** exposure are different; no labels for all source words were supplied to fitting.

## Interpretation and next audit

Exact supervised pair repetition does not explain the principal180/181 transfer result. A restricted same-author source-trained applicability interface remains worth preserving as a possible input to a different decipherment method. It still does not assign named cases, restore general POS, recover syntactic links or identify lexical nuclei. All target labels are audit references; none change the frozen model or its selection rules.

Both passages are reused Cicero development data. Their high lexical overlap, correlated pair endpoints and small source sample remain material limitations, and genuine different-author/novel-vocabulary validation is still required. No deployment, hard equality constraint or Voynich success is claimed.

Next proposed audit: omit each source graph endpoint type in turn, deleting all its incident labeled training pairs, and refit the unchanged rich/control pipelines on the remaining source data. Freeze all omissions before target scoring, preserve every low-data/one-class outcome, and report target loss/AUC/shortlist coverage ranges. This tests whether one source word's labeled neighborhood drives the apparent transfer, a failure mode seen in earlier research, without tuning against target labels.

## Verification

Independent reconstruction used exact cached word-pair identities to verify both word streams, cross-salt maps, all126 overlap records and all disjoint masks. Frozen-prediction classification/calibration,135 shortlist metric groups, within-stratum tie decisions and exact180 global baselines passed. Input/stratum hashes passed. The broader test suite was not rerun for this reference-only audit; no new annotations, reserves or sealed data were used.

Runner: `benchmarks/grammar_case_overlap_iteration182.py`; reviewer: `benchmarks/grammar_case_overlap_iteration182_review.py`. Frozen design, audit identity hashes, vocabularies, overlap rows, strata, selected intersections/rerankings, full summaries, audit and verification manifest: `experiments/results/grammar-restoration/iteration182/`.
