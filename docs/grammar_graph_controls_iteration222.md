# Iteration222: actual graph benefits are conditional, not universal

The real graph outperforms degree-preserving rewiring for some applicability metrics, notably Cicero ranking and Caesar/Cicero NLL. However Jerome's real-graph NLL is worse than global averaging and every sampled rewire, and no top-five support yield improves. Preserve relationship information as a potential grammatical input; do not adopt universal propagation or claim reliable extraction.

## Frozen controls

Reuse221 original seeds,546 nodes,305 established centers and the same half-self/half-neighbor step. Compare identity, actual graph, half-self/half-author-global-mean shrinkage, and199 rewired graphs per author, seeds22200–22398. Rewire undirected edges by double-edge swaps, preserving every node degree and rejecting duplicates, loops and non-four-distinct-vertex swaps. Target10E accepted swaps with a100E attempt cap, record all attempts, no retry selection. The same rewires serve both baseline and balanced models.

Freeze graphs before labels and all score vectors before metrics. Recompute fixed.5 gates/207 support ordering and products/tied top3/top5. Source models and seed features remain frozen on the original graph; only propagation adjacency is rewired, isolating this update rather than rebuilding an entire predictor. No fits, strengths, thresholds, new annotations, raw text, reserves or author-specific winners.

The rewiring ensemble is a finite algorithmic control, not a guarantee of uniform sampling or full mixing. It preserves degrees but not components, original frequency mixing or semantic relations. Directional tails below are descriptive among many metrics and reused development authors, without multiplicity-adjusted inference or independent confirmation claims.

## Established-center balanced results

AUC tail counts rewires at least as high; NLL tail counts rewires at least as low, using `(1+count)/200`.

| Author | Original AUC | Real graph AUC | Rewire mean AUC | AUC tail | Real graph NLL | Global-mean NLL | Rewire mean NLL | NLL tail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Aquinas |.5694|.5810|.5619|.185|.6602|.6706|.6729|.030|
| Caesar |.7955|.8485|.7435|.065|.6531|.7018|.7074|.005|
| Cicero |.7789|.8596|.7463|.010|.5926|.6388|.6432|.005|
| Jerome |.6173|.6219|.5950|.165|.8897|.7908|.8087|1.000|

Global-mean shrinkage leaves AUC unchanged because it is a positive affine transformation within an author. Real relations therefore can alter ordering, especially Cicero; generic shrinkage alone cannot account for that ranking gain. For NLL, however, Jerome benefits much more from generic shrinkage than actual neighbors. Its real-graph NLL is worse than the maximum sampled rewire NLL. All-node metrics are separately retained and do not necessarily agree with center-only results.

Baseline also gives mixed results: Cicero center AUC tail.045, Caesar.095, Aquinas.375, Jerome.100. Caesar and Cicero baseline NLL beat every rewire(.005 tails), but Jerome NLL again has tail1.000. This is not a universally successful graph update.

## Supported-center consequences

Balanced actual propagation retains12/13 supported centers versus original/global-mean11/13, but Cicero's extra retained center is not unusually strong against rewiring: retention tail.210. Its hard top5 remains2/5, with directional tail.985 for equal-or-better rewire hits. Aquinas/Jerome hard top5 remain1/5 and Caesar0. Thus improved applicability ranking has not become a precise grammatical shortlist, and retention alone cannot justify adoption.

The finite controls confirm that the graph contains relationship-specific information useful in some contexts while also preserving harmful score biases in others. No named POS/cases, Latin nuclei or Voynich plaintext is recovered. Existing aggregate grammar evidence and controlled relevance-retention gains remain valid distinct findings.

## Audit and next direction

Independent deterministic replay verifies all796 rewired graphs, degrees, uniqueness, swap logs, synchronous/global scores and1616 scalar metric groups, plus all summary tails and30 hashes. Artifacts: `experiments/results/grammar-restoration/iteration222/`.

Next test a different grammatical output from these relations: soft POS compatibility, including non-Case words rather than treating them as useless negatives. On the same graph, use cached global word-POS profiles to measure endpoint POS-profile agreement, with the fixed frequency-stratified profile-permutation control. Retain all POS tags and all authors; report both-Case, mixed and neither-Case edge groups descriptively without selecting a winner. This is a reference diagnostic of potential pairwise constraints, not POS inference. It checks whether the relationship signal offers a useful grammatical output even when applicability propagation fails, before committing to another node-classification variant.
