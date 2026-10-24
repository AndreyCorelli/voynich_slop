# Iteration 25: can anonymous grammatical classes be aligned?

With correct anonymous class assignments, the pooled source transition model recovers the exact three-class and eight-class mappings on both fresh corpora. Frequency matching alone fails badly on the eight-class inventory. Through 25% injected class error, the transition model reaches the target-label oracle alignment ceiling. The bounded frequency proxy has a low oracle ceiling, so alignment alone cannot repair its information loss.

This narrows the hypothesis: alignment is tractable under this controlled class channel; obtaining useful classes from ciphertext remains the harder untested step. It does not establish word recovery, relation recovery, or unsupervised POS induction.

## Data and frozen setup

Training reuses the 767 source sentences (8,106 tokens) from earlier experiments. Source UPOS annotations define the known grammatical inventory and source distributions. No target-dependent parameter selection or tuning is performed. All objectives, inventories, noise rates and controls are fixed before target scoring.

| New target material | Scored sentences / tokens | Background sentences / tokens |
|---|---:|---:|
| Jerome | 100 / 871 | 200 / 1,839 |
| Caesar | 100 / 1,901 | 200 / 3,977 |

All new IDs are disjoint from prior grammar manifest/truth declarations and the 200-sentence reservation. Background and query observations jointly estimate target statistics; this is transductive alignment. The scored labels do not enter alignment. The main class channel is nevertheless **privileged**: each target token's true POS class is supplied under an unknown, consistent permutation. Target background observations therefore also contain oracle class information, not merely unlabeled words. The solver receives anonymous integer sequences and a source model, not target tag names, words, keys, or reference dependencies. Sentence boundaries are supplied.

The coarse inventory is nominal / verbal / function-other. The fine inventory has noun, adjective, pronoun-determiner, verb, adverb, adposition, conjunction and other; it merges selected UPOS categories explicitly. Source templates are fitted separately to pooled Jerome/Palladius, Jerome alone and Palladius alone. Pooled is the predeclared primary condition; single-author results are sensitivity checks, not a target-selected model choice.

## Exact objectives and controls

For the hidden true-class inventories, all 6 or 40,320 bijections are enumerated:

- **Frequency:** average source unigram log score under the candidate mapping.
- **Transition:** source conditional bigram log scores plus sentence-start and sentence-end log factors, normalized by event count. This is a composite sequence score, not a complete generative Latin grammar.
- **Joint:** an equal mixture of the normalized frequency and transition scores.

All source distributions use fixed .5 pseudocounts. Exact score ties yield set-valued mappings and abstention on ambiguous states. No candidate-order tie-break determines predicted labels. The correct key is present in the search space, so an outscored correct key is an objective/distribution failure, not candidate retrieval or optimizer failure.

Controls include 100 randomly sampled alignments, independently shuffled target contexts with unigram counts preserved, a fresh permutation key, and independently injected per-token class errors at rates 10%, 25% and 50%. Replacement chooses a different class uniformly before anonymization; the noisy token assignments are identical under rekeying. This is an idealized noise channel, not an empirically fitted model of our previous classifier errors. Source templates are not adjusted for the injected noise rate.

## Clean-class result

Percentages are class-label balanced accuracy over scored tokens. For a clean bijective channel, they also equal the fraction of semantic classes assigned correctly when all classes occur.

| Pooled source objective | Coarse Jerome | Coarse Caesar | Fine Jerome | Fine Caesar |
|---|---:|---:|---:|---:|
| Frequency | 100 | 100 | 25.0 | 37.5 |
| Transition | **100** | **100** | **100** | **100** |
| Joint | **100** | **100** | **100** | **100** |
| Oracle alignment | 100 | 100 | 100 | 100 |

The fine frequency mapping preserves only 2/8 classes on Jerome and 3/8 on Caesar. Its token accuracy is 10.2%/54.0%, illustrating why class-balanced and token accuracy must be distinguished. The correct key is strictly outscored in both cases; transition scoring instead makes it the unique optimum. Evaluation saves changed class mappings, correct-key and selected-key scores, and their unigram/transition/boundary components.

The 100 random fine alignments average 14.1% balanced accuracy; their theoretical expectation is 12.5%. They are random baselines on the same test data, not additional corpus samples.

With shuffled target context, fine transition accuracy falls to 50.0% on Jerome and 62.5% on Caesar, while frequency results remain unchanged. The coarse Caesar mapping survives this shuffle, so the control does not imply every successful alignment requires order. It does demonstrate that ordered transitions supply useful information for the fine primary task.

## Noise separates alignment from class quality

| Injected class error | Fine Jerome: transition / oracle | Fine Caesar: transition / oracle |
|---|---:|---:|
| 0% | 100 / 100 | 100 / 100 |
| 10% | 91.8 / 91.8 | 91.4 / 91.4 |
| 25% | 78.0 / 78.0 | 76.2 / 76.2 |
| 50% | 17.1 / 52.0 | 52.9 / 52.9 |

Every pooled coarse and fine transition condition through 25% error reaches the target-label oracle balanced-accuracy ceiling. It is recovering the class-name alignment, **not correcting individual erroneous class assignments**. Actual sampled balanced error can differ from the nominal token corruption rate.

At 50% error, the Jerome fine transition model selects a wrong key even though a much better alignment is available. The exact-search audit exposes this directly. A clean source template with an unmodeled corruption channel is a possible explanation; this experiment does not establish an irreducible information limit or test a noise-aware objective.

## Source-domain sensitivity

Clean fine transition accuracy with source templates:

| Source template | Jerome | Caesar |
|---|---:|---:|
| Pooled, primary | 100% | 100% |
| Jerome only | 100% | 75% |
| Palladius only | 50% | 75% |

Consequently the positive pooled result does not justify a universal alignment claim. Source-domain coverage matters even when the target classes themselves are perfect. The pooled template was declared before evaluation, rather than chosen by inspecting target scores.

## A bounded real frequency proxy

The second channel uses no target POS information to form its groups: the seven most frequent word types each receive a group, and every remaining type enters an eighth group. Ties use first occurrence rather than word spelling. These groups are anonymously renamed. All 3^8 many-to-one maps onto the coarse inventory are enumerated.

This is deliberately a small exact-search proxy. It **is not** iteration 24's richer word-rank/ending-rank class-pair representation, and its ceiling must not be used as the ceiling of that earlier representation.

Ordinary sequence likelihood can collapse multiple groups onto a frequent source class. We therefore also compare aggregate-distribution fits: negative Jensen–Shannon divergence of mapped unigram counts, and a fixed joint objective adding mapped bigram and boundary distributions. Target tags appear only in the label-aware oracle ceiling and evaluation. Oracle token accuracy and oracle balanced accuracy are optimized separately; one mapping need not optimize both.

| Coarse balanced accuracy | Jerome | Caesar |
|---|---:|---:|
| Frequency-distribution fit | 42.4% | 38.3% |
| Joint distribution fit | 45.3% | 40.5% |
| Ordinary sequence score | 43.8% | 33.3% |
| Label-aware oracle map | **54.2%** | **47.4%** |

The oracle token-accuracy ceilings are 60.5%/59.6%. Much of the vocabulary is mixed into the final group, so information has already been lost. No mapping can recover distinctions absent from this representation. The inferred joint alignment leaves an additional gap, but improving it cannot turn this proxy into high-quality grammatical classes. The real-proxy result is consequently not a contradiction of the perfect-class alignment result.

## Revised conclusion

This experiment passes the narrow alignment upper-bound test: source transitions can identify the names of good anonymous classes, including on a new author, when the inventory and class assignment are supplied. Frequency-only alignment is insufficient for the fine inventory. Robustness is limited by source-domain shift and severe class noise.

The next concrete task is **latent class induction**, with the successful transition model serving as a controlled prior. A useful small experiment would keep source transitions fixed and infer soft per-token classes from repeated anonymous word types and ending groups, without a plaintext dictionary or supplied POS classes. Compare oracle class emissions, learned emissions and shuffled/repetition-destroyed emissions. Allow syncretism rather than enforcing one tag per word type, and test for state collapse. This would move beyond the privileged channel here. The new corpora are now inspected; future evaluation needs another declared slice, while preserving the reserved 200.

## Artifacts and validation

Artifacts are in `experiments/results/grammar-restoration/iteration25/`: fixed source templates, fresh datasets, anonymous observations and separately stored truth/keys, exact alignment predictions, evaluation and score-component audits. No dependency parsing or grammatical-skeleton recovery was rerun.

Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_class_alignment_iteration25_validate`. The validator checks fresh/source/holdout disjointness, source tags, source-only template fits, generation of anonymous observations and oracle bounds. It independently recomputes **1,851,156 mapping/objective scores** across 36 problems using a second formulation, checks optimal sets and abstentions, verifies rekey-equivariant semantic predictions, and exhaustively verifies oracle token ceilings. Tests cover symmetric states, missing classes, noisy rekeying, frequency-invariant shuffles, many-to-one collapse, mixed-class ceilings and absence of target labels from alignment. The relevant regression suite passes **286 tests**. The reserved 200 sentences remain unscored and previous artifacts are unchanged.
