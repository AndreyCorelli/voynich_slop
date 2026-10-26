# Iteration 250: diffusion yields limited cross-half grammatical recurrence

**HIGHLIGHT: Aquinas now has shared strict cores in3/19 random sentence splits, versus0/19 before.** Two splits recover the same completely reference-AUX pair, covering1,252/30,000 tokens (4.17%) by global word frequency. A third yields a different nearly pure ADP-dominant triple. This is the first cross-half recurrence in this branch, but it is sparse, selected after extensive development and not yet tested against matched order controls.

The gain is not universal: Caesar, Cicero, Jerome and Dante still have zero shared non-singleton cores across all19 splits. Diffusion improves some full-text/half-text outputs without establishing reliable group confidence, POS naming or exact word recovery.

## Only the representation changed

Replace equal-weight truncated spectral modes with all eigenvectors weighted `exp(-lambda/2)` and row-normalized, fixed diffusion time1. Every initial and deletion graph recomputes this representation. Graph eligibility>=17 nodes, frequency>=5, two shared frames, K=17,31 initialization seeds,31 ten-percent sentence-deletion samples and strict intersection are unchanged.

All five full texts and190 saved random halves were included. Initial and deletion graphs match the old half pipeline exactly. Every one of195 anonymous outputs and95 cross-half intersections was frozen before cached POS evaluation. All mixed, empty and unclusterable cases remain; no diffusion time, seed, author or purity threshold is tuned.

## Recurrence and half-text yield

| Author | Old→new halves with non-singleton output /38 | Old→new shared-core splits /19 | New fully pure shared splits /19 | Original full-text pairs recovered in both halves |
|---|---|---|---:|---:|
| Aquinas |19→34|0→3|2|1/133|
| Caesar |0→0|0→0|0|0/19|
| Cicero |0→0|0→0|0|0/19|
| Jerome |0→19|0→0|0|0/285|
| Dante |0→0|0→0|0|Undefined (no original pairs)|

The shared AUX pair appears at split seeds24603 and24611; these are the same two opaque word identities, not four recovered words. It is absent as a pair from the new full-text strict cores, showing that strict output is not monotonic in sample size. It was also not an original iteration238 pair. No AUX label or spelling was inferred by extraction.

Split24612 recovers a different three-word group, with global reference counts ADP205; ADP187/SCONJ1; ADP870/ADV2. Its pair-average compatibility is99.49%, and global coverage1,265 tokens (4.22%). It is not completely pure, contains none of the shared AUX pair, and includes the one original pair recovered in both halves. The nearly pure triple is retained in reporting without changing the frozen fully pure criterion.

These split outputs come from overlapping resamplings of one admitted corpus. Two appearances of a pair are not independent passage replications or a measured confidence probability. Most splits still yield no shared group.

## Full-text outputs: broader but imperfect

| Author | Old→new non-singleton core counts | New core sizes | New core-average POS compatibility | New fully pure groups, reference descriptions |
|---|---|---|---:|---|
| Aquinas |5→3|2,2,2|66.67%|VERB pair; NOUN pair|
| Caesar |1→2|2,2|26.38%|None|
| Cicero |1→3|2,2,2|80.94%|CCONJ pair; ADP pair|
| Jerome |1→10|2,3,2,11,10,3,2,2,3,2|80.06%|PRON pair; VERB triple; NOUN pair; ADP pair; VERB pair|
| Dante |0→1|2|0.00%|None|

Full-text covered tokens are389/229/1,405/8,470/113 for Aquinas/Caesar/Cicero/Jerome/Dante respectively. Jerome's coverage grows to28.23%, but the larger groups are not completely pure and there is still no cross-half group. Aquinas retains an incompatible pair, and Dante's new pair has zero profile compatibility. More output is therefore not automatically better grammatical recovery. These class names describe reference evaluation after extraction, not named-POS predictions.

## What to preserve

Fixed diffusion genuinely repairs collapsed geometry and produces a limited downstream recurrence gain, so it is a promising algorithm modification worth keeping in the proposal track. The weak/false outputs and poor cross-author recurrence remain explicit. No exact nuclei, four-text word intersection, general POS accuracy or Voynich decipherment is established.

## Next proposed control

Run a targeted **matched full-selection order-control pilot for Aquinas** using the first19 already fixed within-sentence shuffle seeds24000–24018. For each shuffled corpus replay all19 existing sentence splits, both halves, all initialization/deletion runs and cross-half extraction with the same diffusion pipeline. The primary statistic is the largest fully reference-POS-pure non-singleton shared core over **all19 splits, every output core and all POS classes**, zero if absent; the actual value is2. This includes the same opportunity to select a favorable split in real and null data.

Reuse real iteration250 outputs byte for byte, freeze every control output before cached POS scoring, retain all zeros and classes, and use finite tail(1+controls>=real)/20. Secondary yield and compatibility stay descriptive. This is a selected-positive, coarse same-corpus pilot; no universal or fresh-author claim. It tests whether the limited recurrence exceeds what the same extraction can produce after word-order destruction before treating the groups as decoder inputs.

## Independent audit and artifacts

Passed 4,845 graph reconstructions, 8,095 independent Lloyd replays, 264 independent normalized matrix-exponential geometry checks, all five full-text and190 half-text strict outputs, all95 cross-half intersections, complete global/local profile metrics, original-pair retention and443 hash checks. Prior frozen inputs remain unchanged. The final manifest additionally freezes the summary, both runners and this report.

Artifacts: `experiments/results/grammar-restoration/iteration250/`; runner: `benchmarks/grammar_diffusion_cores_iteration250.py`; reviewer: `benchmarks/grammar_diffusion_cores_iteration250_review.py`. No new raw annotations, reserves or sealed Seneca gold were consumed; Dante remains previously consumed development.
