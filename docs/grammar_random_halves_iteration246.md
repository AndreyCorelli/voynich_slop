# Iteration 246: random sentence mixing does not rescue half-text strict cores

**The disjoint-half failure persists under random sentence mixing.** Across19 fixed balanced random splits for each of five datasets, none of95 split pairs produces a shared non-singleton strict core. No original full-text core pair is recovered in both halves: zero out of456 original-pair/split opportunities. These are overlapping reused-corpus trials, not456 independent observations.

This makes chronological passage composition an insufficient explanation of iteration245's failure. Reduced-volume evidence and the strict extraction pipeline remain the immediate bottleneck; this test does not distinguish graph sparsity from clustering and deletion instability.

## Frozen comparison

For each admitted dataset and seeds24600–24618, select floor(N/2) complete lexical sentence groups with `Random(seed).sample` from first-occurrence order; the complement forms the other half. Retain original stream positions and boundaries, masking the other half without bridging. This matches the chronological split's sentence counts, though token counts can differ.

The extractor is unchanged: word frequency>=5, two shared frames, corrected spectral embedding, K=17, 31 initializations and31 ten-percent sentence deletions, with unanimous strict membership and endpoint survival. Initial graphs below17 nodes stay unclusterable. Every one of190 half outputs and95 cross-half intersections was frozen before cached reference-POS evaluation. Full-stream profiles are primary, within-half profiles secondary. No seed, author or criterion is selected for reporting, and no raw annotations, reserves or sealed Seneca data were opened.

## All-author outcomes

| Author | Clusterable halves /38 | Halves with non-singleton output /38 | Halves with fully pure output /38 | Initial graph node range | Shared-core splits /19 | Original pairs retained across both halves |
|---|---:|---:|---:|---|---:|---:|
| Aquinas |38|19|9|70–99|0|0/133|
| Caesar |7|0|0|4–21|0|0/19|
| Cicero |34|0|0|12–30|0|0/19|
| Jerome |38|0|0|35–66|0|0/285|
| Dante |28|0|0|9–30|0|Undefined (no original pairs)|

Overall145/190 initial graphs are clusterable;45 are explicitly unclusterable. All are included. Aquinas retains small half-specific pairs, including fully pure reference-profile outputs in9 halves, but never a shared pair. These half-output descriptions have no new matched order controls and do not establish independent repeatability or inferred class names.

Jerome's initial graphs are clusterable in every half but strict non-singleton output is absent in all38. Thus initial graph availability alone cannot explain the loss. Across11 original-pair/split cases in Jerome and one in Aquinas, both original endpoints survive strict extraction in both halves, but they are not co-assigned in both. That statistic measures strict endpoint survival, not initial graph presence. Caesar/Cicero/Dante have no such original-pair case.

The [chronological halves](grammar_disjoint_cores_iteration245.md) also had zero shared cores across every dataset; random mixing supplies no rescue. The prior full-text [Jerome](grammar_full_core_null_iteration242.md) and [Aquinas](grammar_full_core_null_iteration244.md) order-control signals remain valid at their original scope. They do not yet establish reproducible small-text inputs, reliable POS names, exact nuclei or a Voynich decryption.

## Next proposed diagnostic: locate the attrition stage

Use the frozen half outputs to trace every original full-text strict-core pair through four separately reported conditions: both endpoints in the initial graph, co-assignment in all31 initializations, both endpoints surviving every deletion graph, and co-assignment in all31 deletion partitions. Report both marginal failures and cumulative attrition, since endpoint survival and clustering instability can overlap. Include all five datasets, all19 splits and both halves, with missing/unclusterable cases explicitly failing rather than disappearing.

Reconstruct these flags directly from saved partitions, compare their conjunction with stored strict-core membership, and independently audit the counts. This is a post-hoc mechanism diagnostic, not another success test; it introduces no threshold change or new raw data. It will indicate whether a future modification should address sparse graph support or unstable partition consensus before we relax any rule.

## Audit and artifacts

The independent audit passed 4,685 graph reconstructions, 7,785 Lloyd replays, 254 independent SciPy evd geometry checks, all 285 strict/cross-half intersection checks, random split/masking/disjointness reconstruction, global/local profile metrics, original-pair retention and 225 hash checks. Unclusterable initial and deletion outputs are verified explicitly. The final manifest additionally freezes the aggregate summary, both runners and this report.

Artifacts: `experiments/results/grammar-restoration/iteration246/`; runner: `benchmarks/grammar_random_halves_iteration246.py`; reviewer: `benchmarks/grammar_random_halves_iteration246_review.py`.
