# Why the Latin objective first corrupts a correct dictionary

The first strictly improving corruption in **all ten saved greedy runs** replaces a correct, training-unattested surface form with an unrelated form seen once or twice in training. The gain comes from unigram evidence propagated through smoothing/backoff, rather than an observed matching bigram or trigram. The resulting next-word penalty is smaller than that gain. This diagnoses a specific failure of the earlier Latin objective; it is not a new restoration experiment or a test of the later scalable decoder.

## The 32,004-word example

At proposal 3, seed 101 changes cipher type `v04951_0` from `intulerat` to `perlectam`. This changes one mapping and loses one correct token: accuracy falls from 100% to **99.996875%**. There is no displaced owner or swap. The total objective improves by **1.70474809224 natural-log units**.

The model interpolates bigram and trigram probabilities with equal weights, additive unigram smoothing alpha **0.1**, and backoff strength **1**. Its direct unigram mixture weight is zero, but both conditional models back off to the unigram distribution.

| Affected prediction | Probability before | Probability after | Log-score change |
| --- | ---: | ---: | ---: |
| `intulerat` → `perlectam`, after `populo romano` | 2.35255923e-7 | 2.58781515e-6 | +2.397895273 |
| `ea`, after the changed word | 1.17863218e-3 | 5.89316088e-4 | −0.693147181 |
| `princeps`, with the changed word two positions back | 2.81384536e-6 | 2.81384536e-6 | 0 |
| **Total** | | | **+1.704748092** |

Neither candidate has an observed bigram after `romano` or an observed trigram after `populo romano`. However, `intulerat` has training count zero and `perlectam` has count one. Their smoothed unigram numerators are therefore **0.1 and 1.1**, respectively: the model rewards the substitution by **ln(11)**. At this event, the original probability consists entirely of propagated unigram pseudocount mass; the replacement has that same pseudocount mass plus 2.35255923e-6 from its one observed unigram occurrence.

At the next event, neither word has an observed transition to `ea`. The original predecessor has no outgoing training events; the replacement has one. The conditional denominator changes from **0 + 1 to 1 + 1**, halving the probability of `ea` and costing **ln(2)**. The two-word contexts used for trigram backoff are unobserved on both sides. The third affected event is unchanged because its bigram context is identical and both trigram contexts are unobserved.

Thus the exact explanation is **ln(11) − ln(2) = ln(5.5)**. No observed contextual evidence favors this false phrase. The collapse and decoded-frequency penalties have zero weight in this protocol, morphology adds no score, and injectivity remains satisfied.

## Replication across saved runs

These are the first accepted strict improvements from the perfect dictionary for five nested text sizes and both original seeds. Proposal numbers are specific to each saved seeded trajectory, not an exhaustive ranking of possible moves.

| Words | Seed | Proposal | Mapping changed | Correct tokens lost | Score gain |
| --- | ---: | ---: | --- | ---: | ---: |
| 503 | 101 | 2 | plebi → admittitur | 1 | 1.704748 |
| 503 | 202 | 1 | extremis → onerariam | 1 | 1.704748 |
| 2,022 | 101 | 16 | celtae → exceptans | 1 | 1.704748 |
| 2,022 | 202 | 1 | pisonem → indiligentiae | 1 | 1.704748 |
| 8,024 | 101 | 2 | suspicari → admittitur | 1 | 1.704748 |
| 8,024 | 202 | 2 | traduxisset → integras | 1 | 1.945910 |
| 16,021 | 101 | 2 | caedere → admittitur | 1 | 1.704748 |
| 16,021 | 202 | 1 | pisone → indiligentiae | 3 | 5.114244 |
| 32,004 | 101 | 3 | intulerat → perlectam | 1 | 1.704748 |
| 32,004 | 202 | 1 | perpendiculum → indiligentiae | 1 | 1.704748 |

Nine runs have the same ln(5.5) gain per corrupted occurrence. The `integras` replacement has training count two, giving **ln(21) − ln(3) = ln(7)** instead. All affected observed bigram/trigram numerator counts are zero in these first moves. The nested inputs and recurring replacement words make these dependent observations, not ten independent author-level confirmations.

This identifies inadequate contextual evidence and the smoothing preference for training-attested forms as the immediate mechanism. It does not establish that changing alpha, removing frequency evidence, or another smoothing rule will improve general recovery; those changes require separate checks, including preservation of training-attested words and partially correct dictionaries.

## Reproduction and validation

Run `.venv/bin/python -m benchmarks.word_mapping_first_corruption` using the existing widening and zero-corruption artifacts. The audit reads the saved first-move witnesses; it does not rerun the proposal trajectories. It reconstructs the exact initial and changed dictionaries, checks initial scores against saved scores, verifies token losses and injectivity, and independently rescores the entire text before and after each move. Every affected event's probability decomposition is checked against the production probability function; summed event log-score changes agree with both full rescoring and saved incremental deltas within 1e-7.

The machine-readable output is `experiments/results/word-mapping/first-corruption-audit/report.json`, including input/code hashes, changed mappings, accuracy losses, every affected context, training counts, conditional probabilities, and separate observed-unigram, pseudocount, observed-bigram and observed-trigram probability masses. Those masses add to the probability; their logarithms are not additive objective components. Three parameterized tests check the decomposition across observed/unseen contexts and boundary events, including nonzero direct unigram weights.

Related reports: [zero-corruption experiment](word_mapping_zero_corruption.md), [widening experiment](word_mapping_widening.md).
