# Weaker frequency pressure: experimental screen

The source model can assign a higher score to a poor decoding than to a feasible
reference with almost all covered words correct. One possible contributor is
its strong penalty for content words absent or rare in the small training corpus.

This experiment scores complete injective dictionaries with

`S_alpha = S_LM + (alpha - 1) * sum_tokens log q(decoded_word)`.

Here `q` is the existing unigram backoff distribution. EOS is excluded from the
adjustment. At alpha 1 this is the original objective; smaller alpha reduces
frequency pressure while preserving the original residual context contribution.
This is an **unnormalized heuristic score**, not a new normalized language model.
The retrieval probabilities, inventory, training corpus, initialization, annealing,
and candidate limits stay the same. The objective has its own resource identity,
so checkpoints cannot silently resume under a different weight.

The predeclared screen uses alpha .75, .5, and .25 on the previously inspected
35,000-token Wells prefix, seeds 3 and 5, with 4,000 proposals per chain. Its
baseline is the existing identical-cap strategy screen. Development mean literal
token accuracy selects the weight; ties prefer the weight nearer 1. The selected
weight is checked on the previously inspected Hound prefix, seed 7, against its
existing identical-cap baseline. Neither work supplies fresh blind confirmation.
Truth is used for evaluation and development selection, never as search input.
Evaluation-only near-correct reference scores are recorded separately.

Run with `.venv/bin/python -m benchmarks.scalable_english_tempering`.
Artifacts: `experiments/results/scalable-english/frequency-tempering-v1/`.
Defaults remain unchanged. Grammar and semantic recovery are not measured.

## Results

All seven chains completed 4,000 proposals, with independent full-score checks
on current and archived dictionaries. Existing controls were reused; the summary
asserts their protocols match exactly apart from the objective identity.

| Frequency weight | Wells seed 3 | Wells seed 5 | Wells mean |
|---|---:|---:|---:|
| 1.00, original | 33.49% | 19.67% | 26.58% |
| 0.75 | 29.62% | 23.03% | 26.33% |
| 0.50 | 29.82% | 29.15% | 29.49% |
| 0.25 | 31.30% | 18.29% | 24.80% |

The selected .50 weight gains 2.90 percentage points on the development mean,
but the source-score-selected restart falls from 33.49% to 29.82%. On Hound,
seed 7, it drops from **35.32% to 28.32%**, a loss of 7.00 points. The evidence
does not support promoting this objective. The previous roughly 35% result
remains a result on a particular work and run, not a general recovery estimate.

Scoring the evaluation-only near-correct feasible reference reveals a useful
separation between scoring and search. On Wells the reference still scores below
the best recovered key at every tested weight: gaps are approximately -22,457,
-13,633, and -5,719 for .75, .50, and .25 respectively (original gap -33,427).
On Hound at .50 the reference instead scores **1,505 above** the recovered key
(original gap -12,696). Thus weakening frequency pressure can fix this one
reference comparison without improving the dictionary that search actually finds.
These differences are within-objective comparisons; raw scores across different
weights are not directly comparable. The reference is neither an upper bound nor
an inference output, and its missing words are replaced by distinct untrained
inventory forms. It is never supplied to search.

The original normalized probabilities still generate candidates, which may limit
search under the modified objective. Fixed annealing temperatures also do not
represent identical exploration under changed score deltas. These are possible
follow-ups, not established explanations. Aggressive reduction could also reward
implausible rare words; this screen does not isolate that effect.

The new Wells chains took about 251–267 seconds per two-chain setting, compared
with 208 seconds for the stored control; Hound took 95 seconds versus 80 seconds.
Total new search time was about 14.6 minutes, excluding loading and evaluation.
Timing comparisons are approximate because controls ran earlier.

Implementation: `scalable/tempered.py` wraps a bigram without changing retrieval,
adds a bounded adjustment cache, and serializes its alpha and objective hash.
`incremental.py` applies the same token adjustment to aggregated events;
`trigram.load_model` detects and verifies saved objective metadata. This experiment
supports bigram tempering only. The standard bigram and trigram paths retain their
previous behavior. Unit checks cover formula, chunking, all tiny-model moves,
save/load, and exact checkpoint continuation; all **120 relevant tests pass**.

Machine-readable paired results and protocol checks are in
`experiments/results/scalable-english/frequency-tempering-v1/summary.json`.
The experimental implementation is retained; **no defaults change**.
