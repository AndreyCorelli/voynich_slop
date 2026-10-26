# Iteration 241: matched strict-core word-order controls

The real Jerome text yields a six-word fully POS-pure strict core; the largest such core across 19 shuffled controls has three words. None matches the real result: the finite upper-tail estimate is **(1 + 0) / 20 = 0.05**. This is encouraging, targeted same-corpus evidence, with coarse resolution and an extensive preceding research history; it is not fresh confirmation or a probability that the group is correct.

## Frozen comparison

We used the first 19 previously fixed within-sentence shuffles, seeds 24000–24018, preserving sentence word multisets, punctuation, positions and global word frequencies. Every trial, including an unshuffled replay, ran the same 31 initialization seeds and 31 sentence-deletion partitions used in iterations 235–238. Strict cores require presence and co-membership throughout these partitions; this is an intersection of 62 partitions, not 961 initialization/deletion combinations. All memberships were frozen before reference POS evaluation, and the real memberships exactly reproduce iteration 238.

The primary statistic is the largest non-singleton core whose members all have the same one-hot global reference POS profile, maximizing over **every output core and every POS class** in both real and shuffled texts. No pure core scores zero. Reference annotations evaluate the output; they do not construct it or assign an inferred class name.

| Outcome | Real text | 19 shuffled controls |
|---|---:|---:|
| Largest fully POS-pure core | 6 | Maximum 3 |
| Trials with a pure non-singleton core | 1 | 1 |
| Trials with no non-singleton output | 0 | 5 |
| Trials matching or exceeding real statistic | — | 0 |

Only shuffle 24011 produces a fully pure non-singleton core, of size three. All 19 control outputs, including the five empty outputs, remain in the denominator. The real core covers 337 tokens (1.12% of the text), and all six words are VERB in the reference annotations.

## Interpretation and audit

Unlike graph availability, which iteration 240 showed is abundant after order shuffling, the matched full selection pilot favors the real text on this particular purity-and-size statistic. The test does not establish general performance across authors, inferred verb labels, exact nuclei, or a usable Voynich key. Stability alone remains insufficient: the previously identified wrong Aquinas pair also survives perturbation.

The independent reviewer passed 640 graph reconstructions, 1,240 Lloyd replays, 40 independent eigenspace geometry checks, all 20 complete core intersections, metric reconstruction and 58 frozen-input/output hash checks. Machine-readable results, frozen selections and audit are in `experiments/results/grammar-restoration/iteration241/`.

## Next frozen proposal

Extend the identical comparison to the remaining 180 existing Jerome shuffle seeds, 24019–24198, retaining the frozen real result and first 19 controls. Report all 199 controls with the same statistic and no threshold, core or seed selection. This increases negative-control resolution; it does not create an independent author validation set. Other authors and a deployable anonymous grammatical constraint remain separate questions.
