# Iteration 244: complete Aquinas strict-core order controls

**Aquinas remains promising, with ties in the larger control set.** Its largest fully reference-POS-pure strict core has two words, equaled by two of 199 matched shuffled controls and exceeded by none. The unchanged finite upper-tail estimate is **(1 + 2) / 200 = 0.015**. This preserves a second, weaker grammatical grouping signal alongside Jerome, without turning either into a general confidence guarantee.

## Frozen extension

This explicitly selected-positive follow-up extends iteration 243's Aquinas pilot to the remaining 180 already fixed seeds, 24019–24198. The real output and first 19 controls are reused byte for byte. All anonymous outputs were frozen before evaluation with cached reference POS. Every trial uses the unchanged graph, corrected spectral embedding, K=17, 31 initializations, 31 ten-percent sentence deletions and strict co-membership intersection requiring survival throughout. This intersects 62 partitions, not 961 combinations.

The primary statistic remains the largest completely pure non-singleton core, maximizing over **all cores and all POS classes**, with zero if absent. Purity means every member's global reference profile is one-hot on the same POS. Consequently, control AUX pairs count as ties with real VERB pairs: there is no switch to a verb-only comparison or to the number of pure cores after seeing the result.

## Complete results

| Largest fully pure non-singleton core | Real text | Shuffled controls |
|---|---:|---:|
| None (score 0) | — | 197 |
| Two words | 2 | 2 |
| More than two words | None | 0 |

Real Aquinas has **two** pure VERB pairs, covering 80 and 197 tokens respectively (277/30,000 = 0.92% together). These are reference descriptions, not inferred POS names or word identities. Both control ties are reference AUX pairs, at seeds **24105 and 24157**. There are **122/199 controls with no non-singleton output**; all remain in the denominator along with the other 77 outputs. Every initial graph is clusterable.

The full real output remains five cores, sizes 3,2,2,2,2, covering 985 tokens (3.28%) with 79.31% core-average and 84.40% pair-weighted POS-profile compatibility. It includes the known wrong PRON/NOUN pair, the almost-pure ADV-dominant triple and the ADP-dominant pair. Gold evaluation cannot be used at inference to retain only the two clean verb pairs.

## Implications and limits

The strongest current small-group evidence remains [Jerome](grammar_full_core_null_iteration242.md): one six-word pure core versus maximum three over 199 controls, finite tail 0.005. Aquinas provides a smaller second signal with two null ties. [Caesar/Cicero mixed outputs and empty Dante](grammar_full_core_authors_iteration243.md) remain unchanged; this follow-up does not erase those failures or establish a universal extractor.

These finite tails are targeted, same-corpus exploratory diagnostics after extensive reused-development research, not independent confirmation, multiplicity-adjusted significance or correctness probabilities. The control preserves sentence bags and word frequencies while disrupting order; it does not isolate syntax alone. Anonymous co-membership is potentially useful as a soft decoder constraint, but named POS, exact nuclei, the four-text lexical milestone and Voynich decipherment remain unresolved.

## Next proposed test: disjoint passage support

Stop increasing this particular control count and test whether the unchanged extraction can recover useful co-membership from **disjoint sentence halves**. Include all five admitted datasets, ordering complete lexical sentence groups by first occurrence and splitting at floor(N/2), masking the other half without bridging boundaries. Recompute each half's graph and full 62-partition strict cores with unchanged frequency/frame thresholds, K and seeds; retain unclusterable and empty outputs without relaxing the rule.

Freeze all half-cores and their cross-half intersections before reference evaluation. Report every half's output, coverage and POS-profile compatibility, plus shared non-singleton groups defined by co-membership in both halves and presence in both. Also report how many original strict-core pairs survive in both halves, treating missing endpoints as failures. This is a within-corpus non-overlap stress test, not a fresh-text validation or a license to select a favorable split. It challenges reliance on heavily overlapping deletion samples before attempting group naming or decoder integration.

## Audit and artifacts

The independent review passed 6,400 graph reconstructions, 12,400 Lloyd replays, 400 SciPy evd eigenspace geometry checks, all 200 complete core intersections, all profile/metric/tail reconstructions and 240 hash checks. It also verifies byte-identical reuse of the real output and first 19 controls, and exact iteration-238 real membership. No experimental outputs or criteria were altered during review.

Artifacts: `experiments/results/grammar-restoration/iteration244/`; runner: `benchmarks/grammar_full_core_null_iteration244.py`; reviewer: `benchmarks/grammar_full_core_null_iteration244_review.py`. The runner's inherited docstring still says Jerome, but its frozen data paths, design, computations and independent reviewer all use Aquinas. No new raw annotations, reserves or sealed Seneca labels were used. The final manifest freezes both runners, this report and all iteration artifacts.
