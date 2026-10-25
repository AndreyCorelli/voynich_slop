# Iteration 167: admitting rare forms barely improves case-relation coverage

Lowering the occurrence floor from5 to2 does not materially solve coverage. It adds one case-comparable Jerome pair, agreeing in both shared frames, but adds no primary Cicero pairs. The preserved72.22% Cicero conditional agreement is unchanged. Repeated two-sided contexts, rather than the frequency cutoff alone, are the present bottleneck.

The frozen experiment changes only word-type eligibility. Both floors are evaluated on the exact four original streams and16 count-preserving shuffles. Primary support remains two distinct shared frames; secondary one-frame results are retained. No POS, case, purity or catalogue membership selects candidates or edges. Descriptors were frozen before case scoring and all scores before aggregate/null comparisons. The same recognized cases, missing-label handling and edge/frame weighting from166 apply.

| Dataset | Eligible types, floor5 → floor2 | Primary edges, floor5 → floor2 | Case-comparable edges, floor5 → floor2 | Floor2 primary case agreement |
|---|---|---|---|---|
| Caesar | 41 → 197 | 0 → 1 | 0 → 0 | Unscored |
| Jerome | 27 → 126 | 0 → 1 | 0 → 1 | 100% on one edge/two occurrence pairs |
| Cicero | 588 → 1903 | 52 → 52 | 18 → 18 | 72.22% |
| Palladius | 15 → 79 | 0 → 0 | 0 → 0 | Unscored |

The new Jerome edge connects urceorum and calicum, each observed twice. Its two case comparisons agree; these word names are evaluation disclosures, not inferred Latin identities. All16 floor2 Jerome shuffles have no case-comparable primary edges, so there is no nonempty null-precision distribution against which to claim an accuracy victory. One correct pair is not reliable cross-author validation.

Caesar's new pair connects quis (two occurrences) with que (48), but has no comparisons where both cached cases are recognized. It is unscored rather than a case match. Palladius gains no primary edge.

Cicero's complete primary graph is identical at both floors. The added2–4-occurrence types contribute zero primary edges, not merely zero correct ones. It retains48 comparable frames,73 comparable occurrence pairs,60 matches and21 involved types. Its conditional macro agreement remains72.22%, pooled82.19%, and10/18 covered edges have no conflicts. The floor2 null maximum remains50% (mean27.19%,16 nonempty nulls), versus floor5 mean24.06%/maximum50%.

The involved-type fraction in Cicero decreases3.57%→1.10% solely because the eligible pool expands588→1903; no original case relations are lost. This illustrates why counts and denominators must accompany coverage percentages. All edge/frame/occurrence applicability denominators and secondary one-frame results remain in the artifacts. No favorable floor or author arm is adopted.

The old floor5 descriptors and all166 metrics replay exactly for every original/null view. The floor2 graph is decomposed into old pairs (both counts>=5) and new pairs (at least one count2–4), including nulls. Thus the incremental outcome is explicit and does not rely on comparing changed denominators alone.

The original conditional morphological finding is preserved, with only a tiny additional short-text example. It is not named-case recovery, automatic detection of case-bearing positions, general POS inference or lexical nuclei. All texts remain reused development material; no annotations, reserved material, sealed works or fitted models were added.

Next proposed step: inventory additional already cached annotated passages, then freeze nonoverlapping streams and replicate the original floor5/two-frame case rule before further support tuning. Candidate pools include cached background annotations and source-fit sentences, with author/development exposure stated explicitly and sentence-ID/exact-sequence overlap excluded. Keep floor2 as the fixed comparison, both with the same shuffle controls. A replication with more contextual opportunities would distinguish a broader grammatical cue from a small repeated-formula effect in the present Cicero passage.

Independent verification established descriptor completeness by total frame-pair incidence counts plus exact context intersections, checked all136 view/floor combinations, directly enumerated48,160 occurrence pairs, verified44,887 edge records and272 metric groups, and replayed every old-floor reference, new/old decomposition and null contrast. No fitting or production changes occurred. Artifacts and manifest: `experiments/results/grammar-restoration/iteration167/`.
