# Known-training-plaintext diagnostic after public length search

Revealing the training words makes all four preserved successful midpoint cases
verified SAT in 0.03–0.04 solver seconds, and each frozen key predicts all three
novel held-out words exactly. Their hidden-word fits predicted 0, 0, 0 and 1 words.

| Case | Hidden exact words | Known-plaintext exact words | Known-plaintext solver time |
|---|---:|---:|---:|
| Length two / 3101 | 0/3 | 3/3 | 0.038 s |
| Length two / 3102 | 0/3 | 3/3 | 0.030 s |
| Mixed / 3101 | 0/3 | 3/3 | 0.031 s |
| Mixed / 3102 | 1/3 | 3/3 | 0.030 s |

This is a separately preserved oracle diagnostic on the four outcome-selected SAT
cases from the [new-key calibration](public_length_calibration.md). The two
length-three UNKNOWN cases were outside the approved scope. These results are
conditional on the selected cases, not an estimate over the entire six-case suite.

Only the 18 training plaintext words, including their inherent token counts,
are supplied. The generating key, individual code lengths, segmentation,
generation profile and continuation are hidden from the solver. Requests retain
the same alphabets, training ciphertext, H1 prefix-free L1–3 bounds, free
selection, observed code domains and five-second budget. Dictionary word search
is removed because training identities are known. The original full Latin
dictionary remains in independent witness verification and frozen-key scoring.

Preparation freezes the four IDs, revealed training plaintexts, input hashes and
implementation hashes. Each case runs once; completed cases are checkpointed and
skipped on resume. The generating witness is checked before fitting. Recovered
plaintext must equal the revealed words. Only verified SAT keys are scored on
the unchanged continuation. All three held-out plaintext/ciphertext types are
absent from training and their generating letters occur in training.

The same ciphertext and model can therefore produce predictive keys quickly
when word identities are given. Word uncertainty—both lengths and identities—
is a major obstacle on these engineered fixtures. The hidden fits used public
length proposals; revealing identities also supplies correct lengths, so this
comparison does not isolate identity uncertainty alone. In particular the mixed
cases' initial public vectors differ from the generating lengths. We have not
proved uniqueness of observed key mappings or excluded equally valid known-word
fits with different predictions. The result is not hidden recovery, evidence for
Latin in Voynich, or an available manuscript plaintext crib.

Ten focused tests pass, including solver-input isolation, matched request/budget
checks, UNKNOWN remaining unscored, resume without extra fits, changed-source
rejection, full witness validation and independent frozen continuation scoring.
Saved artifact validation confirms all four cases without fitting again.

```sh
.venv/bin/python -m benchmarks.public_length_known_plaintext --validate
```

Artifacts: `experiments/results/public-length-known-plaintext/`.

A bounded next diagnostic would test whether these correct predictions are forced
by the known training words: require at least one held-out letter's recovered
code to differ from its generating code, while still supplying only training
plaintext. SAT would demonstrate residual key ambiguity; UNSAT would certify
those held-out mappings under this oracle model. This checks uniqueness directly
without another vocabulary expansion or timeout increase. Generating-code
exclusions would make it a truth-assisted diagnostic, never a hidden fit.
