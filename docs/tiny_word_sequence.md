# Toy word-sequence selection

The preceding six-key diagnostic found both useless and useful predictions from
identical training observations. This experiment adds a training adjacency rule:
only `ab → ac`, `ac → ba`, `ba → ca`, and `ca → ab` are allowed.
These pairs are derived from four declared toy phrases, saved in the protocol
before fitting. The whole four-word training sentence is absent from those
phrases. No continuation score enters filtering, exclusions or stopping.

**This is an engineered toy grammar, chosen after the fixture was known.**
Separate reference phrases do not constitute independently collected evidence.
This checks implementation and illustrates what a strong sequence prior can do;
it is not blind language calibration or evidence for a Voynich hypothesis.

## Recorded result

Of the six saved dictionary-compatible explanations, explanations 1–5 fail the
training pair rule; explanation 6 passes. A fresh constrained search finds a
verified SAT explanation in 0.018 seconds. Its frozen key decodes all four
continuation words to the exact generating words (also four dictionary hits).
After blocking its used symbol/code ownership facts, the next search proves
UNSAT in 0.022 seconds. No timeout or longer search was needed.

This exhaustion is relative to the used-ownership blocking rule: it excludes
supersets, code-slot permutations and keys differing only in unused mappings.
It does **not** prove a unique complete key or that every unused-key completion
would predict identically. Predictions here describe the single returned key.

The generating training sequence satisfies the rule. The continuation is
scored using the ordinary dictionary and frozen key; its word pairs are not
required to satisfy the training rule. The true generating key remains a
positive control, not an input to recovery.

## Implementation and checks

The internal finite hidden-dictionary solver now accepts an optional set of
word pairs. Every consecutive recovered word pair must belong to that set.
An empty allowed set makes a multiword request UNSAT. Unsupported recovery
modes and words outside the dictionary are rejected. The Python verifier checks
the sequence constraint independently of the SMT encoding.

The experiment has a fixed six-explanation cap and five-second per-fit budget.
It freezes all fits before evaluating continuation. Protocol, source/request
hashes, saved-key audit, complete fits and predictions are in
`experiments/results/tiny-word-sequence/`. Existing output prevents overwrite.
Nine focused tests passed for word-pair enforcement, validation, protocol
protection, key ambiguity and frozen-key scoring.

```sh
.venv/bin/python -m benchmarks.tiny_word_sequence
.venv/bin/python -m pytest -q tests/integration/test_tiny_word_sequence.py \
  tests/integration/test_tiny_key_ambiguity.py \
  tests/integration/test_frozen_key_holdout.py
```

## Next useful check

Use a genuinely separate corpus to define a smoothed word-sequence score, freeze
it before generating new synthetic controls, and compare training-only key
selection against dictionary-only selection on fresh continuations. Include
shuffled negatives and a small fixed budget. Strict observed-bigram membership
will reject many legitimate unseen pairs in sparse historical corpora, so this
toy allowlist should not be transferred unchanged to Latin or German.
