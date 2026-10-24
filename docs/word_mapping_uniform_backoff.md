# Uniform-backoff Latin objective experiment

**Removing the identified unigram advantage rejects all ten original first corruptions, but does not preserve the correct dictionary.** The full perfect-start experiment instead retains fewer correct tokens than the original objective at four of five tested sizes under greedy ascent and all five under annealing. This is a diagnostic of the earlier Latin optimizer, not a blind restoration benchmark or an experiment with the later scalable decoder.

## Controlled change

Replace the unigram distribution used for n-gram backoff with a uniform distribution over the existing predictive vocabulary (surface forms plus EOS and OOV). Retain observed bigram/trigram counts, context-count denominators, backoff strength, interpolation weights, vocabulary, morphology, proposal families, seeds and search schedule. This is an experimental model; the production/default model is unchanged.

The original formulas were:

```text
p1(c) = (count(c) + alpha) / (total + alpha * vocabulary_size)
p2(c | b) = (count(b,c) + strength * p1(c)) / (count(b) + strength)
p3(c | a,b) = (count(a,b,c) + strength * p2(c | b)) / (count(a,b) + strength)
P = 0.5 * p2 + 0.5 * p3
```

Only `p1(c)` changes, to `1 / vocabulary_size`. This eliminates the training-membership advantage in fallback probability while retaining a normalized conditional model. It also changes smoothing mass on observed transitions and removes unigram frequency evidence throughout the fallback distribution, including EOS; it is not a claim that useful unigram evidence can be selectively removed without side effects. An unseen trigram can still back off to actual observed bigram evidence.

## Same ten original corruption moves

Rescore the saved original first strictly improving moves from their exact correct dictionaries. All ten now have negative score changes. The usual per-occurrence gain of **ln(11) − ln(2) = +1.704748** becomes **−ln(2) = −0.693147**: the unigram reward disappears and the next-word penalty remains. The three-occurrence `pisone` move becomes **−2.079442**, and the twice-training-attested `integras` replacement becomes **−1.098612**.

This passes the targeted regression check, but does not imply other corruptions have been removed.

## Full perfect-start experiment

Repeat all **20 runs**, five nested sizes × two seeds × greedy/annealing, each with **20,000 proposals**, for **400,000 proposals** total. Every run starts with the exact correct dictionary; greedy accepts only strict score increases. Report the mean token accuracy of the best dictionary selected by that run's own objective, as in the original diagnostic. Scores from different objectives are not directly compared.

| Words | Original greedy | Uniform greedy | Original annealing | Uniform annealing |
| --- | ---: | ---: | ---: | ---: |
| 503 | 39.86% | 45.73% | 27.14% | 15.61% |
| 2,022 | 51.88% | 51.09% | 42.26% | 26.78% |
| 8,024 | 66.10% | 62.44% | 57.54% | 45.77% |
| 16,021 | 75.25% | 67.60% | 65.12% | 50.47% |
| 32,004 | 82.80% | 73.35% | 69.58% | 58.25% |

All ten fresh greedy trajectories still find strictly improving errors from truth. For example, seed 101 on 32,004 words now first departs at proposal 4, swapping `tuerentur` and `audacia`, losing three correct tokens and gaining **ln(4) = 1.386294**. Two affected predictions gain ln(4) each and one loses ln(4). Their observed bigram/trigram numerators are zero: exchanging a predecessor with three outgoing training events for one with none changes the backoff denominator from four to one. Thus an unseen predecessor can be rewarded for offering less negative evidence against an unseen transition. Removing the word-frequency advantage exposes this separate context-denominator effect.

The 503-word greedy result improves, but the longer greedy runs and every annealing cohort worsen. All selected final scores exceed the corresponding perfect-start score under the modified objective. Uniform fallback therefore fixes the targeted ten moves without fixing preservation of the correct dictionary. It should remain an experimental ablation, rather than replace the default objective.

## Artifacts and verification

Implementation: [uniform-backoff model](../src/voynich_smt/word_mapping/uniform_backoff.py) and [experiment runner](../benchmarks/word_mapping_uniform_backoff.py). Run:

```sh
.venv/bin/python -m benchmarks.word_mapping_uniform_backoff
.venv/bin/python -m benchmarks.word_mapping_uniform_backoff_validate
```

The runner requires the original local widening and zero-corruption artifacts, refuses to overwrite an existing experiment, and stores its outputs in `experiments/results/word-mapping/uniform-backoff-perfect-start-v1/`. Inputs, model identities, code hashes, original-move checks, all final keys, traces, first departures and per-run comparisons are recorded. The validator independently checks saved final current/best scores and recovery, strict-improvement witnesses, all ten original-move deltas, baseline accuracy comparisons, proposal counts and hashes. Intermediate snapshots also receive full-score and recovery checks during execution. This validates the saved outcomes; the separate validator does not replay all proposal trajectories.

**15 focused tests pass**, covering normalized fallback over observed/unseen contexts and EOS/OOV, retained observed-context evidence, incremental/full-score agreement, probability attribution and the existing oracle/widening machinery. All **20 runs / 400,000 proposals** completed and passed independent output validation. No blind-start decoding, new-author validation, or default change was performed.

Earlier reports: [first-corruption breakdown](word_mapping_first_corruption.md), [original perfect-start experiment](word_mapping_zero_corruption.md).
