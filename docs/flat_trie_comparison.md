# Flat versus trie dictionary recovery

This fixed comparison uses the same two preserved 36-type synthetic inputs,
full dictionary, alphabets, H1 prefix-free L1–3 model, free selection and observed
code domains. Training identities, word lengths, key and continuation remain
hidden. Each arm retains the configured five-second solver timeout. Only the
`dictionary_encoding` field changes from `flat` to `trie`.

Trie membership factors shared dictionary prefixes and still constrains exact
word size and inactive padding. The existing formula-equivalence tests, extended
by the flat equality-reuse tests, verify the same membership semantics. This
changes the SMT representation, not vocabulary, cipher freedom or language
assumptions. The flat arm already uses cached equalities and indexed candidate
pruning; the trie arm uses its existing implementation without additional tuning.

Two verified, completed flat records are reused from the equality-reuse benchmark.
Their exact requests, source/code hashes and report provenance are checked before
reuse. Two new trie fits run once, checkpointing per completed arm. Source data,
code hashes and both requests are frozen before fitting. There are no retries,
new seeds, longer timeouts or fixture changes. The protocol commits to stopping
this encoding sweep if both trie fits remain UNKNOWN, rather than adding further
encodings automatically.

First SAT witnesses, if present, are independently verified against the full model
and scored on the unchanged three novel continuation words with the key frozen.
UNKNOWN remains unscored and unresolved. A synthetic UNSAT would contradict the
independently verified generating witness and stops execution. Construction,
solver and wall times are stored separately; configured solver timeouts may
overshoot their nominal duration.

Twenty focused tests pass across matched comparison inputs, saved-flat reuse,
request-only trie fitting, UNKNOWN remaining unscored, checkpoint resume,
dictionary-encoding equivalence and flat AST equality. Actual artifact validation
checks that requests differ only in encoding, cached flat rows are exact copies,
generating/recovered witnesses satisfy the model, oracle lengths are absent,
and frozen scores are reproducible when SAT.

Artifacts: `experiments/results/flat-trie-comparison/`.

```sh
.venv/bin/python -m benchmarks.flat_trie_comparison --validate
```

This is a two-case selected-fixture check, not blind calibration or evidence for
a manuscript language. Flat timings are historical cached measurements, so any
single-run differences include execution-condition variation. Solver timeout
overshoot is not evidence that one encoding solves faster. Judge recovery by
verified SAT and continuation quality; construction cost is a separate outcome.

## Results

| Key | Encoding | Construction seconds | Measured solver seconds | Status |
|---|---|---:|---:|---|
| fixed-two-seed-3101-types-36 | flat | 22.93 | 8.19 | UNKNOWN |
| fixed-two-seed-3101-types-36 | trie | 29.55 | 5.63 | UNKNOWN |
| mixed-one-two-three-seed-3101-types-36 | flat | 26.72 | 9.54 | UNKNOWN |
| mixed-one-two-three-seed-3101-types-36 | trie | 33.09 | 6.37 | UNKNOWN |

All four records are UNKNOWN with reason `timeout`. Neither encoding yields a
verified key or a continuation score in this comparison. Trie construction is
slower on both single-run measurements: 29.55/33.09 seconds versus flat
22.93/26.72 seconds. The shorter trie check durations do not demonstrate improved
search; all checks exhausted their configured timeout. Validation passed for
all four records, and historical flat reports are preserved unchanged.

The protocol's stopping condition is met: do not add another encoding or extend
timeouts on these two fixtures as part of this sweep. Retain flat with indexed
prefix pruning and equality reuse for its lower measured construction cost here.
This is not a universal ranking of encodings.

Recommended next calibration: new simpler synthetic controls with genuinely
varied generating code lengths and a reduced, frozen vocabulary. Use known-word
and hidden-word arms at the same budget, freeze seeds and training/held-out sets
before solving, and require code-covered novel held-out words. This separates
basic mixed-length recovery/identifiability from full-vocabulary search scale.
Review the preserved controls before choosing that protocol to avoid repeating
an equivalent experiment. Nothing in the UNKNOWN outcomes lowers the logical
possibility of the already verified synthetic generating explanations.
