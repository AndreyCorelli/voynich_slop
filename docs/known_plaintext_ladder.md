# Plaintext-revealed recovery diagnostic

The same saved Latin synthetic prefixes (5, 10, 15 words) were rerun with their
training plaintext revealed. The generating key, homophone choices, code lengths
and segmentation were **not** supplied. Full alphabets, free H2/L1–3 bounds,
prefix-free codes, observed-code domains and ten-second solver budgets match
the hidden-word ladder. Each known plaintext is checked unchanged in the
returned SAT witness, and the encoder is independently verified.

| Training words | Hidden-word fit, 10 seconds | Plaintext-revealed fit | Solver seconds | Correct continuation words / 22 |
| --- | --- | --- | --- | --- |
| 5 | UNKNOWN | Verified SAT | 0.38 | 3 |
| 10 | UNKNOWN | Verified SAT | 0.62 | 10 |
| 15 | UNKNOWN | Verified SAT | 0.83 | 10 |

All recovered keys are frozen before scoring the same original continuation,
words 31–52. The scored continuation is not moved to the next words after each
short prefix. Complete-decode, dictionary-membership and exact generating-word
counts coincide at 3, 10 and 10 respectively; partial decodes are excluded.

## What this isolates

Plaintext-revealed recovery removes dictionary/word-sequence search and fixes
input word lengths as part of that revelation. It still searches the encoder
and homophone choices. The substantial timing difference points to hidden-word
search and its associated ambiguity as the main bottleneck **on these cases**,
not a general proof about every solver workload. It does not count as successful
hidden-plaintext calibration, so the six-case comparative matrix remains deferred.

The generating truth was then used **only for post-fit diagnostics**. The
continuation has respectively 3, 10 and 10 words composed entirely of generating
codewords that appeared in each training prefix. These are exactly the words
the recovered keys decode correctly. Thus the frozen-key failures here coincide
with encountering unobserved homophone forms, even after some corresponding
plaintext letters have been observed.

By contrast, the numbers of continuation words whose plaintext letters all
appeared in training are 4, 15 and 18. Letter coverage is therefore insufficient
when each letter can have multiple codewords. A SAT training explanation need
not discover codewords that never appeared in training. No post-fit codeword
coverage information was passed to the solver or used to select new cases.

These measurements distinguish two problems that previously looked alike:
hidden dictionary search prevents obtaining a key within the short budget;
limited training codeword coverage can prevent even an otherwise useful key
from predicting every future word. Requiring perfect continuation coverage
from very short training blocks is a stringent gate, and these prefixes do
not demonstrate that the model itself lacks predictive structure.

## Scope and next distinct diagnostic

This three-case diagnostic is complete. No longer budget is needed for these
known-plaintext prefixes. Before changing the cipher mechanism or returning
to Voynich, the next useful bounded calibration would measure hidden recovery
with a **predefined smaller distractor vocabulary** and explicitly report
generating-codeword coverage. That would vary the language search dimension
while keeping the encoder fixed. Any such simplified success must be labeled
as a reduced-vocabulary calibration, not full-vocabulary success.

The [fixed reduced-vocabulary diagnostic](reduced_vocabulary_calibration.md)
is now complete: one 64-entry five-word fit returned verified SAT but decoded
none of the continuation, while the remaining eight short fits were UNKNOWN.
It has not supplied the missing hidden-word predictive calibration.

## Reproduction

```sh
.venv/bin/python -m benchmarks.known_plaintext_ladder
.venv/bin/python -m pytest -q \
  tests/integration/test_known_plaintext_ladder.py \
  tests/integration/test_synthetic_size_ladder.py
```

Four focused tests pass, including positional known-plaintext preservation,
matched request hashes, frozen-key scoring, fixed continuation and UNKNOWN
handling in the hidden ladder. Existing diagnostic results prevent accidental
overwrite. Reports and post-fit codeword coverage validation are saved in
`experiments/results/predictive-calibration/known-plaintext-ladder-10000ms.json`
and `known-plaintext-ladder-validation.json`. Only three short solver attempts
were made; no Voynich or long fits.
