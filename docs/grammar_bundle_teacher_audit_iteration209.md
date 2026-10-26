# Iteration209: the failed head mostly contains centers outside the Case test

**The main head failure is Case applicability, rather than weak agreement among Case-bearing words.** Of the12 unsupported full-model top-five centers across Aquinas, Cicero and Jerome,11 have zero recognized Case annotations at every occurrence. They cannot produce recognized Case matches in this test. This diagnoses a mismatch between the count-driven ranker and its Case-based teacher; it does not establish that these words are ungrammatical or useless for decipherment.

## Frozen diagnostic

All305 conservative205 centers and all207 rankings/teacher labels remain unchanged. Use cached201 Case/POS references and205 observed/null statistics only, after checking207/208 manifests. Reconstruct Cartesian comparison weights exactly as in205, then report degree-normalized observed/expected recognized-both coverage, recognized Case equality, surplus, and weighted mean `e*(1-e)` where `e` is the word×POS-profile expected equality for a comparison. The last quantity measures term-level match variability, **not the variance of a bundle sum**: comparisons share observations. Also record center global/queried Case coverage, possible recognized/variable matches under the profiles, unchanged robust statistic and tails, and sampled null standard deviation/range.

All centers are reported before descriptive summaries of supported centers, unsupported centers and each fixed ranking's unsupported top-five. No fitted predictor, raw text, new annotation, reserved labels, threshold, bin search or inference filter is introduced. Recognized Case is the same cached inventory as earlier experiments; missing Case may reflect an uninflected word class or annotation practice, not necessarily an annotation error.

## Main findings

| Author | Unsupported full12 top-five centers | Zero Case at all center occurrences | No possible recognized Case comparison | Supported centers |
|---|---:|---:|---:|---:|
| Aquinas |4|4|4|7|
| Caesar |5|3|3|0|
| Cicero |4|4|4|3|
| Jerome |4|3|3|3|

For every zero-Case center above, observed/expected Case equality, surplus, robust statistic and sampled null variation are exactly zero; raw and adjusted tails are1. Thus many leading errors are structurally outside this teacher's scope, rather than near misses in its significance calibration. Across all four authors,14/17 unsupported full-model head centers have no possible recognized Case comparison.

The remaining Jerome head center has mean surplus .02609 and robust statistic .25, but adjusted tail .8 (the four-center head mean tail is .95). It has Case information and some positive contextual association, but does not pass the frozen corrected test. Caesar's two remaining head centers also have usable profile variation; there are still no supported Caesar centers anywhere in the teacher. An applicability gate cannot create missing teacher positives.

Supported centers have mean global Case coverage92.28% Aquinas,98.84% Cicero and100% Jerome; queried coverage93.35%,100%,100%. Their mean degree-normalized surplus is .20590,.28348,.27852 respectively. These are gold-reference properties, not inferred grammatical labels or word identities.

## Whole-graph context and controls

| Author | Eligible centers | Zero global center Case | No possible recognized comparison | No possible variable match | Sampled zero robust null range |
|---|---:|---:|---:|---:|---:|
| Aquinas |136|53|58|65|65|
| Caesar |23|12|14|15|15|
| Cicero |34|19|20|22|22|
| Jerome |112|47|50|76|76|

No possible variable match means every queried term has profile expected equality0 or1. This is stronger than merely observing zero variance in199 sampled nulls. Here the two counts coincide, but the definitions remain distinct. Across all centers,131/305 have no recognized center Case,142/305 have no possible recognized comparison, and178/305 have no variable matching opportunity. The remaining36 invariant centers can have recognized comparisons while their profiles leave no context-specific matching variation to detect.

The pattern survives the predeclared controls: all four Aquinas unsupported heads lack possible recognized comparisons for every ranking; all Cicero unsupported heads do too (four or five depending on tied selection). Jerome has three such centers for count4, four for frequency and two for degree; Caesar has three, five and two respectively. Missing applicability is therefore not unique to the full model's entropy features.

## Verification and next step

Independent rational reconstruction verifies305 centers and11367 weighted comparison terms, cached observed sums, robust statistics, all raw/adjusted tails, null variability,28 groups and32 hashes. All pass. Artifacts: `experiments/results/grammar-restoration/iteration209/`. Existing grammatical evidence is preserved; no additional POS, named cases or exact nuclei have been restored.

Next run an explicitly oracle applicability diagnostic on the unchanged rankings: retain centers with at least one recognized global Case occurrence, then recompute tied top3/top5 and supported-center rank intervals for every author/model. This is not an annotation-free algorithm. It tests whether perfectly identifying Case-bearing centers would actually fix the head before investing in a source-trained applicability gate. If useful, separately freeze an anonymous applicability predictor and test it on held-out authors; no target gold may enter that deployed gate. Useful non-Case grammatical structure remains a separate research target, not a negative label implied by this audit.
