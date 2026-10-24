# Tiny multiple-explanation diagnostic

This fixed artificial example tests whether selecting one arbitrary dictionary
SAT witness can obscure a useful predictive explanation. It is not Latin,
German, Voynich or full-vocabulary calibration.

The vocabulary contains eight words over `a/b/c`. Four training words and
four continuation words are encrypted with a fixed globally prefix-free key,
two length-two homophones per letter. Recovery permits free H2/L1–3 encoding,
the whole eight-word vocabulary, and a five-second budget per attempt. The key,
word sequence, choices, segmentation and continuation are hidden during recovery.

All **six generating homophones appear in training**. Thus the continuation
contains no generating codeword absent from the training ciphertext. This
controls the coverage failure identified by the preceding diagnostic.

## Fixed six-explanation results

Every recovered explanation independently reproduces the training ciphertext
and meets dictionary, prefix-free and cipher-bound constraints. Keys are frozen
before decoding the identical four-word continuation.

| Explanation | Fit | Fully decoded | Dictionary hits | Exact generating words |
| --- | --- | --- | --- | --- |
| 1 | Verified SAT | 4/4 | 0/4 | 0/4 |
| 2 | Verified SAT | 4/4 | 2/4 | 2/4 |
| 3 | Verified SAT | 4/4 | 0/4 | 0/4 |
| 4 | Verified SAT | 4/4 | 1/4 | 1/4 |
| 5 | Verified SAT | 4/4 | 2/4 | 2/4 |
| 6 | Verified SAT | 4/4 | 4/4 | 4/4 |

All six fits took under a second combined, with no timeout. The generating key
also decodes all four words correctly. The first recovered explanation has
no dictionary hits, while another compatible explanation predicts every word.
Complete decoding alone does not distinguish these explanations.

This demonstrates that one arbitrary SAT witness can give a misleading account
of predictive potential even when the true homophones are all observed.
It does not establish that the same situation holds for full Latin/German
recovery or that a useful explanation can be selected from training data alone.
The good explanation was identified **by evaluation**; selecting it using this
continuation would consume that continuation as validation, not supply a blind
prediction score.

## What “distinct” means

After each solution, the next solve excludes the conjunction of symbol/code
ownership facts actually used in encoding training words. Changing unused
codewords or permuting homophone slots alone does not evade that block. Supersets
of the same used ownership facts are excluded too. Predictions never affect the
blocking rule, stopping rule, next solver call or fixed six-solution cap.

This is a capped sample of distinct used explanations, not exhaustive or uniform
sampling of all keys. The distribution of six scores is not a probability or
success-rate estimate. Unused recovered codewords can still affect predictions;
the experiment avoids counting explanations whose only distinction is such
unused choices, but does not remove them from each complete returned key.

## Next implication

The next useful question is **how to distinguish compatible explanations using
training information**, such as independently derived word-sequence constraints,
or how to report consensus predictions and uncertainty across a bounded key set.
Do not choose a key by its score on this same continuation and call that
generalization. The full predictive benchmark remains deferred; no additional
keys or seed searches were run beyond the fixed cap.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.tiny_key_ambiguity
.venv/bin/python -m pytest -q \
  tests/integration/test_tiny_key_ambiguity.py \
  tests/integration/test_frozen_key_holdout.py
```

The existing report prevents an accidental rerun/overwrite. Six focused tests
pass, including mapping-signature invariance to unused codes/slot order,
independent fit verification, true-homophone coverage, different predictive
outcomes and partial-decode scoring. Reports, complete keys, predictions,
generating truth and independent validation are saved under
`experiments/results/tiny-key-ambiguity/`. No downloads or long fits.
