# Paired randomized controls at 64-word vocabulary

All twelve fixed randomized controls return UNSAT in 0.24–0.63 solver seconds.
Their six paired positives remain verified SAT with 17/18 exact novel predictions
from the preserved 64-word ladder. There are no UNKNOWN controls or unavailable
shuffle cases. This suite distinguishes the generated encrypted inputs from
these particular randomized alternatives under the same bounded model.

| Generating profile / seed | Paired positive | Shuffle seed 4401 | Shuffle seed 4402 |
|---|---|---|---|
| Length two / 4301 | SAT, 3/3 exact | UNSAT | UNSAT |
| Length two / 4302 | SAT, 3/3 exact | UNSAT | UNSAT |
| Lengths one/two / 4301 | SAT, 3/3 exact | UNSAT | UNSAT |
| Lengths one/two / 4302 | SAT, 3/3 exact | UNSAT | UNSAT |
| Lengths one/two/three / 4301 | SAT, 2/3 exact | UNSAT | UNSAT |
| Lengths one/two/three / 4302 | SAT, 3/3 exact | UNSAT | UNSAT |

## Construction and protocol

The existing deterministic typewise within-word glyph shuffler is reused. It
shuffles each distinct ciphertext spelling once and assigns that shuffled spelling
to every occurrence of its type. Controls preserve word boundaries, the complete
length sequence, every word's glyph multiset, global glyph counts and the exact
repetition partition. They do not preserve codeword boundaries, prefix relations
or adjacent-glyph statistics. Each changes 8–12 of the twelve distinct full
training-plus-held-out types; training changes in every control.

Seeds 4401 and 4402 were fixed before fitting for all six positives. The generator
rejects colliding word types and completely unchanged draws within its existing
1,000-draw cap. Unavailable cases would be recorded without new seed selection.
No generating-key compatibility, solver outcome or continuation score enters
construction. The concatenated training/held-out ciphertext is shuffled together
solely to preserve its full repetition partition and novel holdout types. Recovery
receives only the changed training request; neither held-out glyphs nor plaintext
or true code lengths enter the solver. This control-construction access to held-out
ciphertext is explicit; it is not an independently generated continuation sample.

Six existing 64-word positives are reused after request/hash checks. For each
control only the ciphertext field changes: dictionary, alphabets, H1 prefix-free
L1–3 bounds, free selection, flat encoding, observed code domains and configured
five-second solver timeout remain the same. All twelve controls and hashes were
frozen before solving. First SAT keys would be independently verified and scored
on the randomized novel continuation with the key frozen. Such a score would
measure dictionary compatibility, not accuracy against a generating control
plaintext. All controls are UNSAT here, so none has a continuation score.

A post-solve public-domain audit finds all controls individually length-feasible,
with nonempty candidates after public prefix arc consistency. Their rejection is
therefore not explained simply by empty per-word length domains or that public
candidate-graph pruning. These checks were not used to select or regenerate
controls. Randomized controls were not assumed to be impossible; their solver
outcomes were measured. UNSAT applies to each bounded changed input, not to its
original positive or to a manuscript hypothesis.

## Validation and limits

Three focused tests pass, covering frozen seeds and structural invariants,
ciphertext-only request changes, training-only solver inputs, unscored UNKNOWN,
checkpoint reuse and bounded construction failure without extra seeds. Actual
artifact validation regenerates every control, verifies invariants, matches request
hashes and checks witness/scoring paths when applicable. UNSAT is solver-reported;
no independent proof certificates were produced or checked.

Artifacts: `experiments/results/varied-length-shuffle-controls/`, including
`public-domain-audit.json` computed after fitting.

```sh
.venv/bin/python -m benchmarks.varied_length_shuffle_controls --validate
```

Twelve correlated shuffles of six keys over one engineered word inventory do not
establish a population false-positive rate, a p-value, uniqueness of positive
keys or a manuscript language. The unchanged 2/3 positive prediction illustrates
that rejecting randomizations and identifying the correct explanation are
separate properties. This shuffle family also destroys local codeword structure,
so harder structure-preserving controls could behave differently.

The next bounded comparison should reuse these exact randomized ciphertexts with
the already frozen 256-word dictionaries, changing only dictionary size. That
would test whether the observed loss of predictive quality at 256 words coincides
with greater acceptance of these same controls. Do not choose new shuffles based
on the current rejection results; preserve these seeds and inputs.
