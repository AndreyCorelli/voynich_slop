# Iteration 251: matched order controls support the limited Aquinas recurrence

**HIGHLIGHT: the real Aquinas text produces shared grammatical groups, while none of19 matched word-order controls produces any shared non-singleton core.** Every control repeats all19 sentence splits and the complete diffusion/stability pipeline. The largest fully reference-POS-pure shared core is2 in real text and0 in every control, with finite upper tail **(1+0)/20 = 0.05**.

This is encouraging evidence for a potential anonymous grammatical decoder input. It remains a coarse, targeted, reused-corpus pilot after extensive development; it does not establish group correctness probabilities, independent passage transfer, named POS or exact word recovery.

## Matched selection opportunity

Use fixed within-sentence word-ID shuffle seeds24000–24018, preserving each sentence's word multiset, punctuation, stream positions and global frequencies. For every shuffled corpus, repeat every existing split24600–24618 and both halves, applying the unchanged time-one diffusion representation, graph rules, K=17,31 initializations,31 sentence-deletion partitions and strict cross-half intersection.

The primary statistic maximizes over **all19 splits, every output core and every POS class**. A pure group means all words have the same one-hot global reference POS profile. No pure shared group scores zero. A control AUX, VERB or other class pair would count equally as a tie; no AUX-only filter is introduced after observing the real pair.

The38 real half outputs are reused byte for byte from iteration250. All760 real/control half outputs and380 cross-half intersections are frozen before cached POS scoring. No control, split, zero output or mixed group is dropped.

## Complete result

| Outcome | Real text | 19 controls |
|---|---:|---:|
| Largest fully pure shared core over all splits/classes |2|0 in every control|
| Corpus trials with any shared non-singleton output |1|0/19|
| Split trials with shared non-singleton output |3/19|0/361|
| Split trials with fully pure shared output |2/19|0/361|
| Corpus trials scoring at least the real primary statistic |—|0/19|

Every initial half-graph is clusterable, including all722 control halves. Empty control output therefore does not arise from the initial eligibility cutoff. It reflects the complete extraction/strict-recurrence procedure; the result does not assign the cause to any single stage.

The control-level denominator is19, not361: the primary maximizes over the19 correlated split trials within each control. The finite tail is not a posterior correctness probability, a general false-positive rate or multiplicity-adjusted confirmation.

## Potential decoder input to preserve

The real text's three outputs comprise **two distinct anonymous groups**, spanning five word types and2,517/30,000 tokens (8.39%) by global frequency. The same two-word group appears at splits24603 and24611 and is fully AUX in the reference, covering1,252 tokens (4.17%). A disjoint three-word group at24612 is ADP-dominant, with99.49% pair-average compatibility, covering1,265 tokens (4.22%). No class name or word spelling is inferred by extraction.

The selection rule itself is anonymous shared strict co-membership; reference POS evaluates it afterward. The matched pilot now supports preserving this rule as a promising selective grammatical interface. However, discovery recurrence remains only two of19 splits for one group and one of19 for the other. The pair is not a strict core in the new full-text output, and four other datasets still show no cross-half recurrence. Known false full-text groups remain in the broader experiment record.

These observations support further testing, not immediate hard constraints for Voynich. The four-text exact-word nucleus milestone and named-POS restoration remain unmet. No raw annotations, reserved passages or sealed Seneca gold were used; Dante's earlier results remain consumed development.

## Next proposed validation

Freeze **both unique real shared groups**, retaining the ADP-dominant triple as well as the pure pair without a gold-purity filter. Run the same extraction on19 previously unused random complete-sentence balanced splits, seeds25200–25218, with no membership updates or parameter changes. Report each fixed group's endpoint survival and intact co-membership in both halves, all within-group pair retention, all new shared outputs and empty cases.

The primary diagnostic is each fixed group's joint recovery count across all19 new splits, reported separately for both groups without choosing a winner or a success threshold afterward. This tests whether the discovery recurs beyond its selection seeds before paying for180 more order controls or attempting naming/decoder integration. It is new resampling of the same corpus, not fresh text or independent author validation.

## Independent audit

Passed 24,320 graph reconstructions, 47,120 independent Lloyd replays, 1,520 independent matrix-exponential geometry checks, all380 cross-half intersections, full shuffle/sentence-bag reconstruction, all reference metrics, primary selection and finite-tail reconstruction, 38 byte-identical real-half checks and999 hashes.

The first reviewer stopped because its inherited comparator applied exact equality to lists containing two oracle-purity values differing by about1e-16. The diagnostic and failed reviewer are preserved. The successful retry applies the existing1e-8 scalar tolerance recursively, with no experimental-output or primary-score changes. The final manifest freezes both reviewer versions, the diagnostic, this report, the runner and all result artifacts.

Artifacts: `experiments/results/grammar-restoration/iteration251/`; runner: `benchmarks/grammar_diffusion_controls_iteration251.py`; successful reviewer: `benchmarks/grammar_diffusion_controls_iteration251_review_retry.py`.
