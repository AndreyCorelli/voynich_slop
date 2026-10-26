# Iteration 245: strict cores fail to recur in disjoint sentence halves

**The strong small-deletion result does not extend to this disjoint-half test.** None of the five admitted datasets yields a shared non-singleton strict core across its two sentence halves. None of the original 24 strict-core pairs is recovered in both halves. Preserve the earlier full-data Jerome/Aquinas order-control results, but do not describe their groups as independently reproducible passage-level decoder inputs.

## Frozen test

Complete lexical sentence groups were ordered by first occurrence in the cached stream; the first floor(N/2) groups form half zero and the remainder half one. This is sentence-count halving, not exact token halving. Positions outside a half are masked without bridging boundaries. Each half independently rebuilds the graph and applies the unchanged frequency minimum five, two-shared-frame rule, corrected spectral embedding, K=17, 31 initializations and 31 ten-percent sentence deletions. An initial graph with fewer than17 nodes remains explicitly unclusterable; no criterion is relaxed.

All ten anonymous outputs and their cross-half intersections were frozen before POS evaluation. Shared groups require survival and strict co-membership in both halves; they are not restricted to the original full-text cores. Original-pair retention separately requires both endpoints and co-membership in both halves; missing endpoints count as failure. Full-stream global POS profiles are the primary evaluation consistent with earlier experiments; within-half profiles are a secondary description. All datasets and empty outputs are included.

## Results

| Author | Half token counts | Graph nodes, halves 0/1 | Non-singleton core sizes, halves 0/1 | Shared non-singleton cores | Original pairs retained in both |
|---|---|---|---|---:|---:|
| Aquinas | 15,578 / 14,422 | 62 / 94 | 2 / 2 | 0 | 0/7 |
| Caesar | 13,237 / 14,149 | 16 / 12 | Unclusterable / Unclusterable | 0 | 0/1 |
| Cicero | 15,928 / 14,072 | 22 / 27 | None / None | 0 | 0/1 |
| Jerome | 15,817 / 14,183 | 66 / 60 | 2 / None | 0 | 0/15 |
| Dante | 13,058 / 13,025 | 21 / 26 | None / None | 0 | Undefined (no original pairs) |

Aquinas's two halves each yield one different pair, with global POS-profile compatibility99.47% and99.24% (within-half98.90% and99.77%). Neither pair is fully pure under the frozen global criterion, and they produce no shared pair. Jerome's first-half pair is fully ADP in the reference, but the second half has no non-singleton core; this is not recurrence of the six-word full-text VERB core. Reference descriptions do not assign inferred class names.

Only one original Jerome pair has both endpoints surviving strict extraction in both halves, and it is not co-assigned in both. No original pair in the other datasets has both endpoints in both strict outputs. This endpoint statistic concerns strict-core survival, not merely initial graph presence.

## Interpretation

The previous order-control evidence still supports full-sample anonymous grammatical grouping: Jerome's six-word core exceeds all199 shuffled controls, while Aquinas's largest pure pair ties2/199. However, small-deletion robustness uses heavily overlapping data, and halving the admitted text removes enough graph support or stable co-membership to eliminate cross-half recovery here. The current experiment changes sample volume and passage composition together, so it cannot attribute failure solely to topic change, frequency loss, repeated-frame scarcity or clustering instability.

This is a material coverage/reproducibility bottleneck, not proof that the full-text groups are spurious. The half-specific high-compatibility pairs remain descriptive findings without matched half-specific controls or repeatability. No restored exact nuclei, inferred POS names, general-purpose grammatical accuracy or Voynich key is established. Dante remains consumed development, not fresh validation; no raw annotations or reserves were opened.

## Next proposed diagnostic

Use19 fixed random complete-sentence balanced bipartitions, seeds24600–24618, for all five admitted datasets, keeping the exact extractor and half sizes unchanged. Freeze all190 half outputs and95 cross-half intersections before profile evaluation. Report every split's graph availability, empty/unclusterable outputs, shared core sizes/compatibility and original-pair retention, without selecting a favorable seed or loosening thresholds.

Compare the chronological result with this distribution descriptively: recovery under interleaved random halves would implicate passage composition, whereas similarly empty random halves would point toward sample/support loss at this volume. These are overlapping reused-corpus stress tests, not independent confirmations or a formal fresh-text success rate. This tests the immediate cause before changing the algorithm.

## Independent audit

Passed 258 graph reconstructions, 454 Lloyd replays, 14 independent SciPy evd geometry checks and all 15 strict/cross-half intersections, plus split/mask/no-overlap verification, local/global scalar profile metrics, original-pair retention and 234 hash checks. Unclusterable initial/deletion graphs are explicitly verified rather than dropped. The final manifest freezes both runners, this report and all iteration artifacts.

Artifacts: `experiments/results/grammar-restoration/iteration245/`; runner: `benchmarks/grammar_disjoint_cores_iteration245.py`; reviewer: `benchmarks/grammar_disjoint_cores_iteration245_review.py`.
