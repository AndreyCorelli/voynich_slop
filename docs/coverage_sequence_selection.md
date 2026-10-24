# Coverage-controlled sequence-ranking pilot

The preceding projected-Latin pilot could not isolate sequence ranking because
no continuation word used only generating codewords observed in training.
This new fixed protocol guarantees that coverage, retaining the exact frozen
reference vocabulary and smoothed score from the earlier experiment.

## Construction

The reference remains the first half of cached `caesar-latin-v2.json`; evaluation
uses only its second half, projected onto the same twelve short words. The
first sixteen projected evaluation tokens were used previously and are skipped.
Starting there, select the earliest training prefix of 4–32 words in which every
letter in the next four projected words occurs at least twice. The second block
starts immediately after the first block's continuation. This deterministic
rule produces training lengths 20 and 16; each continuation has four words.

This is **coverage-conditioned control construction**: continuation letter
identities enter the eligibility rule, but neither reference-score tuning nor
key selection. It is not a blind natural-passage generalization test. Training
choices alternate the two homophones per letter; continuation choices are free
seeded draws. All generating codes have length two. Alternation guarantees both
homophones for each continuation letter have appeared in training. Hidden
recovery permits free H2/L1–3 and does not receive plaintext, choices, key or
coverage-derived constraints. We are not testing an enforced cycle model.

Key seeds are 707/808, continuation-choice seeds 909/1010 and paired typewise
shuffle seeds 1111/1212. Reference scores, seeds, eligibility rule, three-key
cap and five-second per-attempt budget are saved before construction and fitting.
No score, seed or budget is adjusted after results. The controls remain filtered
same-author word sequences rather than intact Latin or full-vocabulary tests.

## Recorded results

| Case | Training words | Fitted keys | First-key exact words | Ranked-key exact words | Ranked-key dictionary hits |
| --- | --- | --- | --- | --- | --- |
| Synthetic block 1 | 20 | 2 SAT; third UNKNOWN | 4/4 | 4/4 | 4/4 |
| Synthetic block 2 | 16 | 3 SAT | 1/4 | 1/4 | 2/4 |
| Paired shuffle 1 | 20 | UNSAT | Not evaluated | Not evaluated | Not evaluated |
| Paired shuffle 2 | 16 | UNSAT | Not evaluated | Not evaluated | Not evaluated |

Every returned key fully decodes all four continuation words. In block 1, both
keys recover all four exactly. In block 2, the three exact scores are 1/4, 0/4,
1/4, and each produces two dictionary hits. Training-only sequence ranking
selects the first key in both blocks: **no improvement over the first SAT key**.

Block 1 has two previously seen ciphertext words and two novel dictionary hits;
block 2 has one previously seen ciphertext word and one novel dictionary hit.
Total scores therefore include repetition. A dictionary hit need not be the
true word; exact matches above use generating plaintext only after selection.

All eight continuation words pass the independent generating-code coverage
check, and the generating keys decode each continuation perfectly. Coverage
removes one known obstacle but does not guarantee correct ownership recovery.
The true block-2 training score (-2.291) exceeds all three recovered scores;
the corresponding useful explanation was not found in the capped sample.
This cannot establish that the score would select the generating key among
all solutions.

The five SAT fits take 0.86–1.33 seconds each. Block 1's third attempt is UNKNOWN
at 5.02 seconds; it does not exhaust the remaining explanations. The shuffles
are proved UNSAT within 0.68 seconds under the finite dictionary/model. This
positive/negative fitting separation is a result for these two controls, not
an estimated general discrimination rate or a manuscript-language conclusion.

Compared with the preceding pilot, training length, passages and generating
choice schedules also changed. Improved decoding cannot be attributed solely
to coverage. The first-key versus ranked-key comparison within each new case
is matched; neither shows a ranking benefit.

## Implementation, artifacts and validation

The earlier protocol/results are preserved. New implementation:
`benchmarks/coverage_sequence_selection.py`. Protocol, source/code identities,
requests, truth, coverage proof, recovered keys, predictions and independent
validation are in `experiments/results/coverage-sequence-selection/`.
Completed cases are checkpointed and skipped on rerun. Reuse checks reference
and implementation identities. An interruption repeats only the incomplete case.

Nine focused tests passed. Independent validation reproduces coverage,
generating encoding/decoding, fit verification, ownership exclusions, scores,
selection and predictions. UNKNOWN remains explicitly recorded.

```sh
.venv/bin/python -m benchmarks.coverage_sequence_selection --run
.venv/bin/python -m pytest -q tests/integration/test_coverage_sequence_selection.py \
  tests/integration/test_corpus_sequence_selection.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/coverage-sequence-selection/validate.py
```

This pilot supplies working covered positives and rejected paired shuffles,
but no evidence yet that post-hoc sequence reranking improves predictions.
Before scaling, distinguish a poor candidate set from a poor ranking rule:
a small fixed diagnostic with the generating ownership explanation explicitly
included in the candidate pool can check ranking capacity. Such a truth-assisted
check must remain separate from hidden-key recovery and cannot count as blind
recovery success. Do not increase this run's cap or tune on its continuation.
