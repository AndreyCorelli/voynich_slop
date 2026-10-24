# Fixed-key synthetic recovery size ladder

The unresolved 30-word Latin synthetic calibration was reduced to fitting
prefixes of 5, 10 and 15 words, with one ten-second solver attempt each. The
generating key, original synthetic ciphertext, full 5,655-word dictionary,
alphabets, free selection, H2/L1–3 bounds and observed-code domains are unchanged.
Generating witnesses for each shortened prefix were independently checked.

| Fitting words | Result | Solver seconds | Continuation |
| --- | --- | --- | --- |
| 5 | UNKNOWN | 10.07 | Not evaluated |
| 10 | UNKNOWN | 10.11 | Not evaluated |
| 15 | UNKNOWN | 10.14 | Not evaluated |

The ladder has not located a practical recovery scale **within ten seconds**.
It does not prove that the smaller cases would also time out at 30 minutes,
nor that they lack solutions. All three are known-solvable. No recovered key
exists, so no prediction failure or score is inferred.

Had any fit returned verified SAT, its recovered key would have been frozen
and evaluated on the same original continuation, source words 31–52. Words
between the shortened fitting prefix and source word 30 would not have been
fitted or scored. That design keeps the continuation constant while varying
training size; it is not an immediate-following-window test for every size.

This fixed ladder is complete. The six-case Voynich/comparative benchmark
remains deferred. Do not increase budgets repeatedly or tune additional cipher
mechanisms in response to these results. A distinct diagnostic next step is
to reveal the known training plaintext while keeping the encoder hidden, so
that a short matched recovery test can separate hidden-word search cost from
cipher-key search cost. That test was not performed here.

The subsequent [plaintext-revealed diagnostic](known_plaintext_ladder.md)
returns verified SAT for all three prefixes in under a second each. It also
shows continuation failures coinciding with unseen generating homophones;
the hidden-word calibration remains unresolved.

## Reproduction and validation

```sh
.venv/bin/python -m benchmarks.synthetic_size_ladder
.venv/bin/python -m pytest -q \
  tests/integration/test_synthetic_size_ladder.py \
  tests/integration/test_frozen_key_holdout.py
```

The existing ladder report prevents accidental overwrite or repeat. Results
and validation are under `experiments/results/predictive-calibration/` as
`size-ladder-10000ms.json` and `size-ladder-validation.json`. Hashes bind the
original manifest and effective requests. Six focused tests pass, including
unchanged prefix/model constraints, UNKNOWN handling, repeat protection and
fixed-key continuation scoring using a valid synthetic witness in the test.
Only three short solver attempts were made; no long run or Voynich fit.
