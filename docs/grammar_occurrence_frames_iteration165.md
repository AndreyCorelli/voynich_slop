# Iteration 165: contextual POS does not explain the shared-frame failures

Scoring actual occurrence POS only slightly improves the long-text result: Cicero's primary edge/frame-macro agreement is50.64%, compared with48.08% global modal-type agreement in164. Only25/52 edges have no conflicting occurrence pairs. The three short texts still have no primary edges. Modal-reference ambiguity therefore does not explain most of the failure, and the frame graph is not a reliable same-POS constraint.

The exact164 opaque streams, permutations and edges were retained. All types with>=5 occurrences are eligible; primary support is two distinct shared frames, secondary one. No POS, anchors or names select edges, and no labels select a successful subset afterward. No new annotations, reserved material or sealed works were used.

Before label scoring, descriptors froze every edge's shared frames and matching occurrence positions. Within an edge/frame, every Cartesian pair of occurrences of the two distinct middle-word types is compared for exact cached UD POS equality. Pairs are averaged within frame, frames equally within edge, and edges equally for the primary metric. Pooled occurrence agreement and the fraction of entirely conflict-free edges are fixed secondary metrics. Labels travel with their original token through the existing word-shuffle permutations; they are not replaced by type-modal POS.

| Dataset | Primary edges | Edge/frame-macro agreement | Pooled occurrence agreement | Entirely conflict-free edges | Supported type coverage |
|---|---|---|---|---|---|
| Caesar | 0 | Unscored | Unscored | 0 | 0/41 |
| Jerome | 0 | Unscored | Unscored | 0 | 0/27 |
| Cicero | 52 | 50.64% | 117/187 (62.57%) | 25/52 (48.08%) | 53/588 (9.01%) |
| Palladius | 0 | Unscored | Unscored | 0 | 0/15 |

The primary Cicero value exceeds all16 nonempty shuffle controls (mean14.03%, maximum25.00%). There is grammatical association, but it is neither high agreement nor broad coverage. Pooled62.57% weights frequent/repeated occurrence pairs more heavily; it is not promoted over the predeclared50.64% primary result. Conflict-free edges cannot be identified at inference using their evaluation labels, so25 correct-looking edges are not a validated selectable output.

| Dataset | One-frame secondary edges | Edge/frame-macro agreement | Pooled agreement | Conflict-free edges |
|---|---|---|---|---|
| Caesar | 1 | 100% | 1/1 | 1/1 |
| Jerome | 2 | 100% | 10/10 | 2/2 |
| Cicero | 863 | 24.49% | 328/1104 (29.71%) | 210/863 |
| Palladius | 1 | 0% | 0/1 | 0/1 |

The short-text perfect secondary values remain tiny cases, not evidence for relaxing support after seeing outcomes. Empty results remain unscored, not perfect. Comparisons share word types, frames and contexts and are not independent replications.

This closes one reference diagnostic without adding a restoration method. Current evidence does not support hard POS-equality constraints from these frames. It leaves open whether a different grammatical relation is more appropriate: nouns, pronouns and adjectives may substitute in the same slot while sharing case rather than POS.

Next proposed diagnostic: keep the same frozen frames/supports and compare actual occurrence case where both members have an explicit unambiguous cached case. Missing case must never count as agreement. Freeze recognized case labels and the same pair/frame/edge weighting; report applicability among every original edge/frame/pair, not only agreement on the case-bearing subset. Use the same label-carrying shuffles. This is explicitly conditional morphological consistency, not automatic identification of case-bearing words, named case recovery or a license to select edges with gold labels. It tests a different possible grammatical input while preserving the POS failure.

Independent verification reconstructed all descriptors from opaque positions, enumerated Cartesian occurrence pairs directly rather than using POS-count products, checked all68 views and136 metric groups, and replayed every contrast/empty outcome. No fitting or production model changes occurred. Artifacts and manifest: `experiments/results/grammar-restoration/iteration165/`.
