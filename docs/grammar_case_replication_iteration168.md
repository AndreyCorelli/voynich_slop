# Iteration 168: conditional case signal replicates in another Cicero passage

**Preserve the replication:** the fixed primary rule gives70.41% conditional case agreement in a second, nonoverlapping Cicero passage, above all16 shuffle controls (maximum55.56%). The preceding passage scored72.22% with a50% null maximum. This strengthens the evidence for a narrow morphological compatibility signal, while remaining same-author, reused-development evidence rather than general restoration.

The replication set was frozen from four available cached pools, with original candidate order and no outcome-based selection. Background authors were identified using source/sentence-ID headers only; POS and case came exclusively from existing annotation caches. Reserved IDs, all previous sentence IDs, and normalized word-sequence duplicates against every prior original/joined sentence and across new pools were excluded before graph construction. Case labels played no part in selection.

| Frozen pool | Candidate → retained sentences | Retained tokens | Rejected duplicate sequences |
|---|---|---|---|
| Background Jerome | 377 → 372 | 3,283 | 5 |
| Background Palladius | 390 → 390 | 4,806 | 0 |
| Source-fit Cicero | 2,375 → 2,365 | 30,581 | 10 |
| Source-fit Palladius | 96 → 96 | 1,271 | 0 |

All are previously used development/source annotations; no fresh author holdout is claimed. The rule itself fits no labels or parameters. Sentence-level nonoverlap does not imply different vocabulary, frame templates or statistically independent edges. No new annotations, reserved features or sealed works were used.

Primary inference remains occurrence floor5 and at least two distinct shared two-sided frames; floor2 and one-frame support remain fixed controls. Models, word meanings, anchors and POS do not construct edges. The same seven recognized cases, pair/frame/edge weighting and16 word-shuffle seeds16400–16415 are retained. Selections/streams were frozen before descriptors, descriptors before case scores, and scores before aggregate/null comparisons.

| Primary result | Earlier Cicero passage | New Cicero passage |
|---|---|---|
| Tokens | 20,136 | 30,581 |
| All inferred edges | 52 | 126 |
| Case-comparable edges | 18 (34.62%) | 36 (28.57%) |
| Comparable frames | 48/124 | 83/310 |
| Comparable occurrence pairs | 73/187 | 118/459 |
| Edge/frame-macro case agreement | 72.22% | 70.41% |
| Pooled occurrence agreement | 60/73 (82.19%) | 89/118 (75.42%) |
| Conflict-free covered edges | 10/18 | 18/36 |
| Supported types involved in case comparisons | 21/588 (3.57%) | 33/857 (3.85%) |
| Null primary mean / maximum | 24.06% / 50.00% | 29.24% / 55.56% |

All16 new Cicero nulls contain case-comparable edges, and none reaches the actual70.41%. These are descriptive controls, not a formal independence/significance claim. Pooled agreement remains secondary; no favorable metric is promoted. Half of the covered new edges have at least one conflict, so a strong average does not identify a reliable subset automatically.

Background Jerome has one primary edge without paired recognized cases. Both Palladius pools have no primary edges. These remain unscored, not perfect case predictions or counterevidence with adequate coverage. At floor2, background Jerome adds one case-comparable edge with2/2 agreement, but two of four nonempty nulls also achieve100%, so it is not a persuasive replication.

At floor2, new Cicero has130 edges/38 case-comparable edges,69.33% macro agreement and91/122 (74.59%) pooled agreement. The extra coverage is small and agreement slightly lower; no floor is selected after evaluation. Every secondary result and applicability denominator remains in the artifacts.

The meaningful outcome is a replicated conditional relation in two sizable same-author passages. It is a possible input to a morphological decoder when candidate analyses carry case, without requiring exact lexical nuclei first. It does not identify which unknown tokens bear case, name their cases, validate a universal70% prior, or establish a successful decoder. Cases are available only for evaluation here; they never select inferred edges.

Next proposed robustness audit: freeze removal of each inferred endpoint type and each distinct shared frame, separately in the two Cicero graphs, with matched null removals. Reapply two-frame support after frame deletion and report all remaining case agreement/coverage and empty outcomes. This tests whether a few words or repeated templates dominate both results, before adding model complexity or treating the relation as a decoder constraint. No favorable removal may be adopted as a filter.

Independent verification reconstructed header provenance, every candidate/retained/rejected sentence and global normalized deduplication, checked zero prior sentence-ID/sequence overlap and reserve overlap, established complete descriptors, and directly replayed110,051 edge records,123,568 Cartesian pairs and272 metric groups across136 view/floor combinations. No fitting or production changes occurred. Artifacts and manifest: `experiments/results/grammar-restoration/iteration168/`.
