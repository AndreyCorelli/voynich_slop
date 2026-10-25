# Iteration 133: sparse PP selections are a precision filter on immediate-preposition proximity

The source result contains class-assignment information: actual classes beat all sixteen tested shuffled assignments on all-token PP F1. However, Jerome does not beat every shuffle, Caesar remains unrecovered, and **every actual PP selection is also selected by the immediate-left-ADP rule**. The learned PP model raises precision by rejecting some of that simple rule's selections, at a substantial coverage cost. Preserve that narrower conditional success, not a claim of richer phrase recovery.

## Frozen controls

Use exactly iteration 132's five-anchor inputs, inferred classes, original PP model, and 0.80 PP cutoff across source and all four author views. The author scoring positions remain their original 100 sentences. Controls are unknown target classes, all ADP, all CCONJ, and sixteen type-consistent permutations of the actual hard classes with seeds 13300–13315. IDs are sorted before permutation; one assignment applies to every occurrence of a type.

Permutations preserve type-class counts, not token-weighted class mass. Thus word frequency can contribute to differences between null runs. They are correlated controls, not independent texts or a formal significance test. In expanded Caesar every type is CCONJ, so all permutations are identical and provide no nontrivial null variation.

Two simple controls select a token when an ADP tag appears in the previous one or two positions in the same sentence. These rules use the same inferred and supplied tags, no gold POS filtering, and no lexical information beyond the frozen inputs. Their binary output is evaluated at 0.5; this encodes a fixed rule, not a fitted probability cutoff. Both rules are computed for every assignment, including nulls, and all fixed cohorts are retained.

Assignments are frozen before new scores, and scores before metrics. Actual PP scores reproduce iteration 132. There is no fitting, threshold/budget/author selection, new annotation, reserve access, sealed lexical evaluation, default change, or lexical nucleus recovery. All results remain development reuse with supplied mappings/catalogue/segmentation.

## Type-shuffle challenge

| Context | Actual PP F1 | Mean shuffled F1 | Maximum shuffled F1 | Null runs at least actual F1 |
|---|---:|---:|---:|---:|
| Source | **0.2157** | 0.1008 | 0.2071 | **0/16** |
| Jerome original | 0.4419 | 0.3078 | 0.5000 | 2/16 |
| Jerome expanded | 0.4048 | 0.2171 | 0.4419 | 1/16 |
| Caesar original | 0.0125 | 0.0211 | 0.2022 | 6/16 |
| Caesar expanded | 0 | 0 | 0 | 16/16, identical assignments |

Source actual selections are 95 correct / nine wrong, compared with mean shuffled counts of 45.38 correct / 61 wrong. The source fixed originally unmapped cohort is less decisive: actual F1 0.1794 versus mean 0.0977, with two null runs at least as good. Jerome's actual assignments beat the mean but not all nulls in either all-token or originally unmapped comparisons. Saved rank fractions are descriptive, not p-values or guarantees.

Assigning every target ADP produces source 163/153, Jerome 20/28 in both views, and Caesar 33/27 in both views. All-CCONJ and unknown arms select nothing. The observed source/Jerome precision is therefore not reproduced by indiscriminately asserting prepositions.

## Proximity challenge

Each cell gives correct / wrong selections using the actual inferred classes.

| Context | Learned PP model | Immediately follows ADP | ADP within previous two positions |
|---|---:|---:|---:|
| Source | **95/9** | 229/67 | 287/281 |
| Jerome original | **19/1** | 32/9 | 35/39 |
| Jerome expanded | **17/1** | 28/5 | 30/30 |
| Caesar original | 1/0 | 6/0 | 6/6 |
| Caesar expanded | 0/0 | 0/0 | 0/0 |

All learned selections, both correct and false, are contained within the immediate-left-ADP selections. Relative to that rule, the PP model adds **zero new correct and zero new false selections** in every context. It discards source 134 correct selections while removing 58 errors; Jerome original discards thirteen correct while removing eight errors; expanded discards eleven correct while removing four errors. Caesar original loses five correct and removes no errors.

The source precision rises from 77.36% for adjacency to 91.35% for the PP filter; Jerome rises from 78.05% to 95% original and 84.85% to 94.44% expanded. However, adjacency has higher F1: source 0.4268 versus 0.2157; Jerome 0.5981 versus 0.4419 original and 0.5657 versus 0.4048 expanded. Thus the model supplies a precision/coverage tradeoff over simple proximity, not demonstrated new structural reach.

## Meaning for the high-level goal

Selective PP membership can still be useful to another decoder even when its mechanism is simple. But the present evidence should be described as partial class information plus filtering of tokens immediately following predicted prepositions. It is not full phrase reconstruction, dependency recovery, reliable cross-author grammar, or a discovered plaintext nucleus.

Before another PP scoring variation, a fresh class-inference direction is to use repeated opaque-neighbor patterns. The current classifier masks almost all contextual word identities and mainly sees unknown tags outside the five supplied anchors; opaque IDs group occurrences for pooling but are not contextual identity features. A source-only, strict type-held-out test of identity-invariant neighbor frequency/repetition summaries could ask whether cipher-observable distributional evidence helps beyond those five anchors. Freeze its features, calibration, and controls before source/author evaluation, retain the sixteen-type exclusion, and do not assume that it will solve Caesar. This is a proposed experiment, not a finding.

## Verification

Independent review verifies eighteen frozen input hashes, all eighty type-permutation constructions and preserved class counts, recomputes all one hundred complete PP vectors, independently checks 1,200 confusion groups, reconstructs sentence-local proximity outputs, and replays shuffle summaries and paired losses. Actual scores reproduce iteration 132 and reserved IDs are absent. Nine focused tests pass. Artifacts are in `experiments/results/grammar-restoration/iteration133/`.
