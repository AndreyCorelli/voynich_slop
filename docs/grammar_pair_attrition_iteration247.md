# Iteration 247: support loss dominates Aquinas; partition instability dominates Jerome

**The half-text failure has different immediate causes across authors.** Aquinas loses many originally related endpoints from deletion graphs. Jerome also loses support, but, even when endpoints survive, the old six-word group is not consistently clustered together. Its failure is not a handful of near-unanimous exceptions that a small relaxation would fix.

This is a post-hoc mechanism diagnostic of frozen iteration246 outputs, not a new recovery experiment or an accuracy result. No POS labels, raw texts, reserves or modified clustering thresholds were used.

## What was traced

All24 original iteration238 pairs were followed across19 fixed random splits and both halves: **912 pair-half cases**, or456 pair-split cases. Dante has no original pair and remains explicit with an empty denominator. The diagnostic records graph endpoint presence, initial clusterability, counts of co-assignment across31 initializations, endpoint survival/clusterability/co-assignment across31 deletion graphs and stored strict-core membership.

Deletion stages not executed because the initial graph is unclusterable are explicitly marked unevaluated. They fail the joint recovery rule but are not presented as measured endpoint disappearance. Marginal conditions and cumulative attrition are both retained because failures overlap. The conjunction of initialization unanimity and deletion unanimity reproduces stored strict membership for every case.

## Ordered attrition

Each column below retains only cases passing every preceding column. Counts are pair-half cases, not independent texts, graph counts or correctness rates.

| Author | Original pair-half cases | Both endpoints initially present | Also initially clusterable | Also all31 initializations agree | Also endpoints survive every deletion | Also every deletion clusterable | Also all31 deletion assignments agree |
|---|---:|---:|---:|---:|---:|---:|---:|
| Aquinas |266|159|159|117|26|26|17|
| Caesar |38|11|4|0|0|0|0|
| Cicero |38|9|8|1|0|0|0|
| Jerome |570|388|388|20|3|3|0|
| Dante |No original pairs|—|—|—|—|—|—|

**Aquinas:**117/159 initially present cases are initialization-unanimous. Of these117,91 fail endpoint survival across deletions, leaving26;17 also pass deletion co-assignment. Independently of initialization,31 pair-half cases retain both endpoints through every deletion, of which17 are co-assigned in all31. Thus a small number of real full-text relations survive individually in half texts, but none recurs across both complementary halves. Initial endpoint loss also matters:107/266 cases lack at least one endpoint before clustering.

**Jerome:** only20/388 initially present cases are initialization-unanimous (5.15%). Only3 of those20 retain both endpoints through every deletion, and none survives all deletion assignments. Marginally,80 pair-half cases retain endpoints throughout the deletion graphs, yet **none** is consistently co-assigned. Among those80, deletion co-assignment counts range from1 to18 out of31: none is close to the unanimity boundary. This makes graph availability alone, or a one-failure tolerance, inadequate explanations for recovering the old group at this volume.

**Caesar/Cicero:** graph support, clusterability and initialization disagreement already prevent useful recovery. Sparse data also make many deletion graphs unclusterable. No stage is dropped to manufacture output.

## Cross-half consequences

Both endpoints initially appear in both halves for41/133 Aquinas and144/285 Jerome pair-split cases. Initialization unanimity holds in both halves for27 Aquinas cases but only2 Jerome cases. Endpoint survival through every deletion in both halves holds for just1 Aquinas and11 Jerome cases; deletion co-assignment unanimity holds in both halves for neither author. These are separate marginal conditions, not a cumulative sequence. All original pair-split joint recoveries remain zero, exactly matching iteration246.

The earlier full-text Jerome/Aquinas order-control results remain promising at full volume. This diagnostic explains why they cannot yet be treated as reproducible passage-level grammatical constraints. It neither recovers POS names nor exact words and does not address the four-text nuclei milestone.

## Next proposed diagnostic

Before changing K or relaxing unanimity, inspect the **continuous graph embedding before k-means**. For every original pair, compare its within-graph distance rank in the full text and every saved random half, reporting missing endpoints separately and as worst-case coverage failures. Rank against all unordered node pairs in each graph; preserve every author, seed and pair without selecting a threshold or a favorable group.

This asks whether the old grammatical relations remain close neighbors but are split by hard partitioning, or whether the half-text graph representation itself has lost their proximity. A positive proximity result would motivate a local soft relation; a negative result would push the next modification toward graph support or representation. It is a mechanism diagnostic on selected original pairs, not validation of a new classifier or confidence rule. No new raw annotations or reserves are needed.

## Independent audit and artifacts

Passed record-level reconstruction of all912 pair-half records and456 pair-split records, inspection of8,990 frozen initial/deletion partitions, strict-membership conjunction equivalence, every both-half retention result, all five author summaries and205 hash checks. The previously audited iteration246 manifest is unchanged. The final manifest freezes both runners, this report and all diagnostic artifacts.

Artifacts: `experiments/results/grammar-restoration/iteration247/`; runner: `benchmarks/grammar_pair_attrition_iteration247.py`; reviewer: `benchmarks/grammar_pair_attrition_iteration247_review.py`.
