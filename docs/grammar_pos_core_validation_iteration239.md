# Iteration239: selected cores largely survive unused perturbations

**Preserve the validated Jerome grouping:** its fixed six-word core remains fully intact in30/31 unused10%-deletion runs and24/31 runs at20%, with mean unconditional pair retention98.92% and89.03%. No memberships were updated. This strengthens the anonymous grouping's perturbation robustness, not the inference of the verb label or word identities. Coverage remains337/30000 tokens(1.12%) and the five-author strategy still has weak/empty outputs.

## Frozen validation

All238 non-singleton cores are fixed before validation. Use new seeds23900–23930, primary10% and secondary20% sentence-group deletion, same cached stream masking, floor5/two-frame eligibility, corrected spectral embedding,17 clusters and initialization23500. Every graph/partition is frozen before retention scoring. No selection by outcomes, purity reinspection, raw annotation, new labels or reserves. Baseline23500 co-membership is verified for every original pair. These are unused perturbations of the same development texts, not unseen authors or fresh grammatical validation.

## Mean pair retention

Unconditional retention counts missing endpoints as failures; conditional retention uses pairs whose two words remain in the replacement graph. Values are means of replicate ratios.

| Author | Fixed core pairs | 10% unconditional | 10% conditional | 20% unconditional | 20% conditional |
|---|---:|---:|---:|---:|---:|
| Aquinas |7|97.24%|99.08%|91.71%|98.16%|
| Caesar |1|100%|100%|41.94%|48.15%|
| Cicero |1|96.77%|100%|90.32%|100%|
| Jerome |15|98.92%|98.92%|89.03%|92.26%|
| Dante |0|undefined|undefined|undefined|undefined|

Dante remains empty, not100% retained or zero-accuracy output. No graph in310 runs becomes unclusterable, so observed losses are not hidden behind a changed cluster count. At20% Caesar's endpoints survive87.10% on average but co-membership retention falls sharply; this is genuine membership instability beyond missing eligibility.

## Whole-core intactness

| Author | Core count | Intact runs per core,10% | Intact runs per core,20% |
|---|---:|---|---|
| Aquinas |5|29,31,30,31,30|26,31,25,31,29|
| Caesar |1|31|13|
| Cicero |1|30|28|
| Jerome |1|30|24|
| Dante |0|none|none|

Jerome's six endpoints all survive at10%; one run splits its core. At20% all six survive27/31 runs and remain together24/31. Mean pair survival95.70% exceeds unconditional co-membership89.03%, making its residual failure explicit. Unconditional pair-retention range is66.67–100% at10% and26.67–100% at20%; the mean is not a worst-case guarantee.

Aquinas's reference-incompatible PRON/NOUN pair is still intact30/31 and25/31 runs. Caesar and Cicero's weak grammatical pairs can also be highly stable. Thus held-out perturbation stability cannot be interpreted as POS correctness, automatic class naming, or a calibrated probability that a constraint is safe. Keep every fixed core; do not discard the bad ones using gold.

## Meaning for the high-level goal

One small, pure reference-verb group is inferred anonymously and largely survives unused text perturbations. This is a potential soft co-membership input to another decoder, not a recovered Latin dictionary or a common nucleus across four texts. Its purity was already measured in238;239 adds robustness evidence without new grammatical labels. Other retained cores and empty Dante prevent a universal reliable-restoration claim.

## Audit and next control

Independent310 masked-graph/partition replays,30 independently computed eigenspace-geometry samples,310 retention groups, per-core counts, baseline checks and29 hashes pass. Dependency hashes from237's frozen graph/clustering design are also rechecked. Artifacts: `experiments/results/grammar-restoration/iteration239/`.

Next a word-order destruction control: shuffle word identities among lexical positions within each admitted sentence while preserving word frequencies, sentence lengths and punctuation boundaries, with199 fixed seeds in all five authors. First measure whether the unchanged floor5/two-frame graph still has sufficient nodes/edges for the17-group pipeline. If clusterable, run the same single23500 clustering baseline; never relax eligibility for null texts. This tests whether apparent structure can arise from the token inventory and sentence bags alone, before spending on a full consensus pipeline for shuffled controls. It is a graph/pipeline negative control, not a new decipherment or a fresh-author validation.
