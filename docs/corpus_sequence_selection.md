# Corpus-derived training-only key ranking pilot

This pilot replaces the engineered toy pair allowlist with an add-one smoothed
sequence score derived from a separate reference passage. It compares the first
SAT explanation with the highest training-score explanation among three keys.
Continuation scores never enter selection or exclusions.

## Fixed protocol

The cached, normalized Caesar corpus has 20,508 records. Records `[0:10254]`
provide the reference text; evaluation records come exclusively from the second
half. Spelling follows `caesar-latin-v2.json`, with no new normalization.
The twelve most frequent reference words of at most three letters define the
vocabulary: `a ab ad cum eo et ex in non qui se ut`.

Both streams are projected onto that vocabulary: intervening words are removed.
The reference projection has 1,408 tokens. The score combines a smoothed initial
word probability with smoothed conditional bigram probabilities, divided by
sequence length. Unseen pairs have finite probability. No hard pair rejection.

**These are filtered word sequences, not intact Latin prose.** The two halves
are disjoint text from the same author; this is not independent-author or
historical manuscript validation. Vocabulary comes only from the reference.
The score is frozen before evaluation sequence extraction/key generation.

Two fixed, consecutive eight-token evaluation blocks each supply four training
words and four continuation words. Fresh keys use seeds 101/202, free homophone
choices use 303/404. Generating keys have two distinct length-two codes per
letter over six cipher glyphs. Recovery permits H2/L1–3 and observed codeword
domains, hiding the key, plaintext, lengths, choices and segmentation.

Each block also has a typewise within-word shuffled ciphertext control using
seeds 505/606 across all eight words. Lengths, glyph counts and exact word
repetition are preserved. A shuffled control is not guaranteed unencryptable.

Each case permits three explanations with five seconds per attempt. Used
ownership blocks exclude supersets and slot permutations, as in the toy test;
this is a small biased sample, not exhaustive key search. Ties in training
score favor the first key. Selection is fixed before evaluating continuation.

## Results

All twelve fits are independently verified SAT, taking 0.23–0.30 seconds each.
No timeout. Key numbers below start at one.

| Case | Training-selected key | First key dictionary hits | Selected key dictionary hits | Selected key exact words |
| --- | --- | --- | --- | --- |
| Synthetic block 1 | 3 | 0/4 | 0/4 | 0/4 |
| Shuffle block 1 | 2 | 0/4 | 0/4 | Not applicable |
| Synthetic block 2 | 1 | 0/4 | 0/4 | 0/4 |
| Shuffle block 2 | 3 | 0/4 | 0/4 | Not applicable |

Neither selected synthetic key fully decodes a continuation word. The selected
second shuffle key fully decodes two words, neither a dictionary word. All
sampled synthetic keys have zero exact matches and zero dictionary hits.
Training ranking does not demonstrate an improvement or positive/negative
separation in this pilot. Equal dictionary scores of zero are not evidence
that the controls and positives are equivalent.

## Coverage limitation

Post-fit inspection identifies a substantial confound: training observes only
7/28 generating codewords in block 1 and 5/28 in block 2. **No continuation word
in either block consists entirely of generating codewords seen in training.**
The correct generating key independently decodes every continuation word, but
missing training codewords are unconstrained by direct observation. This pilot
therefore cannot cleanly isolate whether the sequence ranker discriminates
useful keys when coverage is adequate.

The true training score is -2.221 in block 1 (above all three sampled keys),
but -2.695 in block 2 (below the highest-scoring wrong explanation, -2.143).
These are post-fit truth diagnostics, not selection criteria. A smoothed corpus
score need not rank a particular true short sequence above every wrong one.
The true generating ownership explanation was absent from both capped samples.

No seed, vocabulary, sample cap or solver budget was adjusted after seeing the
results. No Voynich solve or new corpus download was performed.

## Artifacts and validation

`experiments/results/corpus-sequence-selection/` contains the frozen protocol,
reference counts, source/code hashes, complete requests and generating controls,
all recovered keys, selection indices, continuation predictions and validation.
Independent validation reproduces scores, selection, ownership exclusions,
predictions and generating coverage. Ten focused tests pass.

```sh
.venv/bin/python -m benchmarks.corpus_sequence_selection
.venv/bin/python -m benchmarks.corpus_sequence_selection --run
.venv/bin/python -m pytest -q tests/integration/test_corpus_sequence_selection.py \
  tests/integration/test_tiny_word_sequence.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/corpus-sequence-selection/validate.py
```

Preparation checks source/code identity on reuse. Completed cases are skipped
on rerun; existing results are preserved. Case completion is checkpointed.
An interruption within a case repeats that incomplete case, not completed ones.

The next discriminating experiment should require generating-codeword coverage
before accepting a control, while keeping the reference score independent and
the selection training-only. Prefer a small controlled fixture that supplies
coverage over increasing budgets on these confounded cases. A new frozen
protocol is required; retain this pilot as a negative/limited result.
