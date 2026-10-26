# Iteration 252: the fixed AUX pair recurs once; the triple does not validate intact

**The fixed two-word group recurs in1/19 unused splits, while the fixed three-word group recurs in0/19.** This is a limited replication of the reference-AUX pair beyond its two discovery splits, not dependable recovery. The triple's failure remains explicit; its successful two-word subset is not substituted for the frozen candidate.

## Frozen validation

Before generating new outputs, freeze both unique anonymous shared groups from iteration250, with no gold-purity filter. G1 is the two-word group found in discovery splits24603/24611; G2 is the three-word group from24612. Their AUX/ADP descriptions come from cached evaluation, not inferred names.

Use19 unused balanced complete-sentence split seeds25200–25218. Keep the time-one diffusion representation, graph/frequency/frame criteria, K=17,31 initializations,31 deletion samples and strict-core extraction unchanged. A fixed group is intact when all its members survive and are co-assigned in a strict core in each half; that core may contain additional words. Candidate memberships never change. All38 half outputs and19 cross-half intersections are frozen before reference evaluation, and every failure is retained.

## Fixed-candidate results

| Candidate | Discovery recovery /19 splits | Unused-split recovery /19 | All members in both initial graphs /19 | All members survive strict extraction in both /19 | Intact individual halves /38 | Pair recoveries across both halves |
|---|---:|---:|---:|---:|---:|---:|
| G1: two-word, reference AUX |2|1|19|18|13|1/19|
| G2: three-word, ADP-dominant |1|0|16|0|10|2/57|

G1 recurs at split25201. Its initial endpoint presence is complete in every split, and strict endpoint survival succeeds in18/19. Therefore the rare joint recovery cannot be explained primarily by missing initial endpoints; co-membership is unstable even when the two types survive. Diffusion repairs proximity but hard partition/stability filtering still limits recurrence.

G2 never recurs intact. It has all members in both initial graphs in16/19 splits, but none retains all members in both strict outputs. A fixed pair within G2 survives at25207 and25218, yielding2 of57 possible fixed within-group pair/split recoveries. These are the same two-word subset, not two different pairs. They do not count as successful recovery of the original triple.

## What the unchanged anonymous rule outputs

There are shared non-singleton outputs in3/19 new splits, the same yield as discovery: the G1 pair once and the same G2 subset twice. Their reference pair compatibility is100%,99.77%,99.77%; only G1 is fully pure under the unchanged global-profile criterion. This preserves a selective grammatical signal on new resampling seeds, while the fixed-candidate result is weaker than broad reproducibility.

The reference profiles and text are reused; these are not fresh passages or new correctness labels. The earlier matched-control pilot on discovery splits remains encouraging at its original scope, but does not convert1/19 validation recovery into high confidence or validate every new subset. No output is named or translated by extraction. No exact nuclei, cross-author common-word intersection or Voynich key is recovered. Raw annotations, reserves and sealed Seneca gold remain untouched.

## Next proposed change: local relations instead of whole partitions

Test deterministic **mutual nearest-neighbor pairs** in the fixed diffusion geometry, replacing only global k-means/co-assignment. Keep the graph, eligibility>=17 nodes and deletion samples unchanged. A pair must be mutual nearest neighbors in the initial graph and all31 deletion graphs of a half, with missing/ineligible cases failing; cross-half output requires the pair in both halves. Include every nearest-distance tie within the existing1e-10 tolerance, exclude self, and do not merge pairs into transitive classes.

Use all five full datasets and the190 existing246 halves, plus the38 saved Aquinas252 halves as an explicitly reused diagnostic comparison. Freeze every anonymous pair before reference scoring; report all authors, empty outputs, coverage, all-pair POS compatibility and both fixed groups' pair retention. No neighbor-count, diffusion-time or confidence-threshold search. This tests whether a local, seed-free relation can preserve useful affinity without unstable whole-graph partitioning. Any gain still needs matched order controls and cannot fix missing endpoints or infer POS names by itself.

## Audit and artifacts

Independent audit passed inventory reconstruction of both frozen candidates, all19 unused random splits, 1,216 graph reconstructions, 2,356 independent Lloyd replays, 76 matrix-exponential geometry checks, all19 cross-half intersections, all38 fixed-group/split records, complete profiles/summary counts and1052 hashes. Candidate identity and both fixed failure denominators are preserved.

The initial reviewer completed the split/partition replay but stopped on a missing tags argument in its final reference-summary call. Its code and failure record are preserved; a separate retry supplies the already fixed inventory. Experimental outputs and criteria are unchanged. The final manifest freezes the runner, both reviewer versions, this report and all outputs.

Artifacts: `experiments/results/grammar-restoration/iteration252/`; runner: `benchmarks/grammar_fixed_groups_iteration252.py`; successful reviewer: `benchmarks/grammar_fixed_groups_iteration252_review_retry.py`.
