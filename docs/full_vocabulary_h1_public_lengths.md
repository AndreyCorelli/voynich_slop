# Public midpoint length search

The preserved full-vocabulary Latin H1 positive now yields verified SAT in
2.20 seconds of solver time, using its first publicly proposed length vector.
Construction time is recorded separately in the result. The frozen recovered key
predicts all three novel continuation words exactly. The original unrestricted
fit remains UNKNOWN at five seconds.

The proposal function receives only the recovery request: training ciphertext,
dictionary, alphabets and model bounds. It ranks each admissible plaintext length
by distance from ciphertext length divided by the midpoint of the allowed code
lengths (two for bounds 1–3), breaking ties toward shorter words. Complete ranked
Cartesian enumeration is filtered by public ciphertext prefix/equality relations.
The first three admissible vectors were frozen before fitting. No generating
plaintext, key or continuation enters this function.

Branches retain the full 5,655-word dictionary, 24-letter alphabet, six ciphertext
glyphs, H1, free selection, prefix-free L1–3 codes and observed codeword domains.
A shared 5,000 ms solver budget is reduced after each branch; construction and
schedule generation are outside this solver budget, as in prior experiments.
Solver timeout accounting can slightly overshoot. Search stops at verified SAT,
budget exhaustion or three branches. Unsuccessful searches are UNKNOWN: rejection
of a scheduled vector does not prove global UNSAT.

This heuristic was developed retrospectively after the word-length diagnostic on
a synthetic fixture generated with length-two codes. It is not a blind test and
does not establish that manuscript codes have length two. The public first vector
matches the diagnostic lengths here. Three short predictions do not identify the
true key or resolve training ambiguity. No Voynich result is changed.

Seven focused tests pass. Saved validation checks source/code hashes, regenerates
the public schedule, independently checks the full witness and branch lengths,
and recomputes frozen-key predictions.

Artifacts: `experiments/results/full-vocabulary-h1-public-lengths/`.
The benchmark refuses to overwrite its fixed protocol. To validate without fitting:

```sh
PYTHONPATH=src:. .venv/bin/python experiments/results/full-vocabulary-h1-public-lengths/validate.py
```

Next: freeze this rule and assess it on new synthetic positives with varied
code lengths, alongside the ordinary solver under equal budgets, before returning
to manuscript fits. Keep seeds and cases fixed before any outcomes are inspected.
