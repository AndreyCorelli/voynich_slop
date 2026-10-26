# Iteration 243: strict-core order controls across the remaining authors

**Aquinas adds a second, weaker positive finding; the method remains selective.** Real Aquinas has two fully reference-POS-pure verb pairs, versus no pure non-singleton core in any of its 19 shuffled controls (finite upper tail 0.05). Caesar and Cicero retain mixed pairs, and Dante retains no non-singleton core. Together with the stronger Jerome result, this supports preserving small anonymous grammatical groups as potential decoder inputs, without claiming reliable whole-text or cross-author POS restoration.

## Frozen protocol

All four remaining admitted datasets—Aquinas, Caesar, Cicero and already consumed Dante development data—were included. Each used the first 19 previously fixed within-sentence order shuffles, seeds 24000–24018, plus an unshuffled replay. The extraction rule is unchanged: the same graph eligibility, corrected spectral embedding, K=17, 31 initialization runs, 31 ten-percent sentence-deletion runs and strict intersection requiring word survival throughout. Each real result exactly reproduces iteration 238.

All 80 anonymous outputs were frozen before reading cached reference POS for evaluation. The primary statistic is unchanged: the largest non-singleton core whose global word profiles are one-hot on the same POS class, maximizing over every core and every class; absence scores zero. The finite tail is (1 + controls scoring at least real) / 20. All authors, empty outputs and zero scores are included. No class name is inferred by extraction, and no raw annotations, reserves or sealed Seneca gold were consumed.

## Results

| Author | Real non-singleton core sizes | Largest pure real core | Largest pure control core | Controls scoring at least real | Finite tail | Empty control outputs |
|---|---|---:|---:|---:|---:|---:|
| Aquinas | 3, 2, 2, 2, 2 | 2 | 0 | 0/19 | 0.05 | 11/19 |
| Caesar | 2 | 0 | 0 | 19/19 | 1.00 | 19/19 |
| Cicero | 2 | 0 | 0 | 19/19 | 1.00 | 18/19 |
| Dante | None | 0 | 0 | 19/19 | 1.00 | 19/19 |

Every initial graph is clusterable; two deletion graphs in Caesar control 24009 (deletion seeds 23728 and 23730) are unclusterable and therefore yield no strict core, as required by the frozen rule. No trial is excluded. Aquinas has two pure VERB pairs, an almost-pure ADV-dominant triple, an ADP-dominant pair and the previously identified incompatible PRON/NOUN pair. The primary statistic counts only completely pure groups; it is not tuned to include near-pure ones. All Aquinas cores together cover 985/30,000 tokens (3.28%), with 79.31% core-average and 84.40% pair-weighted POS-profile compatibility. These figures include the wrong pair.

Caesar's pair has 52.75% compatibility, Cicero's 42.82%; neither passes the fully pure criterion. Dante's compatibility is undefined because output is empty. Their lack of pure shuffled output does not validate their real mixed or empty output: their primary scores tie every control.

For context, the separate [Jerome experiment](grammar_full_core_null_iteration242.md) has one six-word fully reference-VERB core covering 1.12% of tokens, exceeding all 199 controls (largest pure control three; finite tail 0.005). The control counts differ: Jerome has 199, each author here has 19. They must not be pooled into a common discovery probability.

## Interpretation and next check

Preserve **two texts with small, anonymously recovered, reference-verified pure verb groups**, with stronger evidence for Jerome. This is not a shared exact-word nucleus: neither lexical identities nor the label VERB were recovered. Gold purity evaluates groups after extraction; it cannot identify which Aquinas groups to trust at inference. The stable wrong pair remains an obstacle to treating every output as a hard constraint.

This is reused-development, targeted evidence with coarse 19-control resolution, author dependence and extensive preceding research; there is no multiplicity-adjusted or fresh-transfer claim. Three remaining datasets do not provide a fully pure output, so a universal grammatical restoration claim would be unsupported.

The next proposed check is to extend the unchanged Aquinas comparison to its remaining 180 already fixed shuffles, reusing these real/first-19 outputs byte for byte. This is explicitly a selected-positive follow-up, not independent confirmation; all Caesar/Cicero/Dante failures remain in the record. If the gap survives, separate-passage replication and a way to rank or name groups without target gold become the practical bottlenecks before decoder use.

## Independent audit

Passed: 2,560 graph reconstructions, 4,958 independent Lloyd replays, 160 SciPy evd eigenspace geometry checks, all 80 full core intersections, complete profile/metric/tail reconstruction and 321 frozen-artifact hash checks. All four real memberships reproduce iteration 238 exactly. The final manifest freezes this report, both new runners and the full result directory.

Artifacts: `experiments/results/grammar-restoration/iteration243/`; runner: `benchmarks/grammar_full_core_authors_iteration243.py`; reviewer: `benchmarks/grammar_full_core_authors_iteration243_review.py`.
