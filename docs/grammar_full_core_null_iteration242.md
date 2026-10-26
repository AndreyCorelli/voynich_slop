# Iteration 242: full fixed Jerome order-control comparison

**HIGHLIGHT: the six-word Jerome core exceeds all 199 matched full-pipeline controls.** The largest fully reference-POS-pure strict core has six words in real text and at most three in any within-sentence shuffle. There are zero matches or exceedances; the finite upper-tail estimate is **(1 + 0) / 200 = 0.005**. This strengthens the same-corpus evidence for a small anonymous grammatical group, while preserving its limited coverage and unresolved class naming.

## Unchanged protocol

The iteration extends [the 19-control pilot](grammar_full_core_null_iteration241.md) with the remaining 180 fixed shuffle seeds, 24019–24198. The original real result and first 19 compressed control outputs are reused byte for byte. All 199 control seeds were fixed before this extension; none is selected by outcome.

Each shuffle preserves within-sentence word multisets, global frequencies, lexical positions, punctuation and boundaries. Every trial uses the identical graph eligibility rule, corrected spectral embedding, K=17, 31 initialization runs and 31 ten-percent sentence-deletion partitions. Strict cores intersect these 62 partitions, requiring each member to survive every deletion. All output memberships are frozen before reference POS evaluation, including singletons and empty non-singleton results.

The unchanged primary statistic is the largest non-singleton core whose members all have the same one-hot global reference POS profile, maximizing over every core and every POS class. Absence of a pure core scores zero. This statistic uses gold annotations to evaluate the anonymous extraction; the algorithm itself does not identify the POS name.

## Complete results

| Largest pure non-singleton core | Real text | Number of shuffled controls |
|---|---:|---:|
| None (score 0) | — | 190 |
| 2 words | — | 7 |
| 3 words | — | 2 |
| 4 or more words | 6 words | 0 |

Of 199 controls, **35 produce no non-singleton core at all**; the other 164 are also retained, regardless of purity. The two pure triples occur at seeds 24011 and 24180. The seven pure pairs occur at 24044, 24056, 24082, 24118, 24130, 24181 and 24191. Pure shuffled groups include both VERB and ADP, so small clean groups can arise in the controls.

The real output remains the exact iteration-238 six-word group: 15 pair constraints covering 337/30,000 tokens (**1.12%**). Every member has reference VERB probability one. Its separately measured perturbation robustness remains 30/31 intact at ten-percent deletion and 24/31 at twenty-percent deletion; this extension does not change those measurements.

## What this supports

The result addresses the earlier objection that shuffled text also produces abundant graphs: the full strict selection, scored identically on real and shuffled text, yields a larger completely pure core in the real Jerome sample. Preserve this as a promising potential grammatical input for another decoder. It is an anonymous co-membership constraint, with reference-verified purity on this sample, rather than restored named POS or exact lexical nuclei.

The finite tail is an exploratory, targeted negative-control result, not a posterior correctness probability, a multiplicity-adjusted discovery, independent-author confirmation or a measured general-purpose false-positive rate. The author and hypothesis emerged from extensive reused-development research. Shuffling destroys more than syntax, and fixed sentence bags retain other structure. The wrong but stable Aquinas pair and absent Dante core remain counterexamples to universal confidence. No Voynich application or four-text lexical milestone is established.

## Independent audit and artifacts

The independent reviewer passed **6,400 graph reconstructions**, **12,400 Lloyd replays**, **400 independent eigenspace geometry checks**, all **200 core intersections**, complete profile/metric/finite-tail reconstruction and **240 hash checks**. The real core also reproduces iteration 238 exactly. The first reviewer stopped on SciPy evr eigenvector geometry; the diagnostic found loss of orthogonality in a repeated eigenspace. A separate reviewer retry uses the independent SciPy evd driver with unchanged comparison tolerances; production outputs and clustering are unchanged. Diagnostic records and the failed reviewer are preserved. The final manifest additionally freezes this report, all new runners and all iteration-242 artifacts.

Artifacts: `experiments/results/grammar-restoration/iteration242/`; runner: `benchmarks/grammar_full_core_null_iteration242.py`; successful independent reviewer: `benchmarks/grammar_full_core_null_iteration242_review_retry.py`. No new raw annotations, reserves or sealed Seneca gold were used.

## Next proposed check

Before treating this as a generally useful decoder interface, run the same matched 19-control pilot for **all four remaining admitted author datasets**: Aquinas, Caesar, Cicero and the already consumed Dante development data. Use their existing fixed first 19 shuffles, identical core extraction and largest-pure-core statistic, report every author and zero result, and do not select the best author or relax the rule. This tests the scope of the finding on reused development data; genuinely separate-passage transfer and POS naming remain later requirements.
