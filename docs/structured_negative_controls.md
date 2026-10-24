# Local-structure controls for ordinary recovery

This calibration strengthens the within-word glyph shuffles used previously.
It preserves local ciphertext structure while corrupting the saved synthetic
fixtures. Ordinary finite dictionary recovery remains the baseline; statistical
guidance is paused. No new Voynich fits, seed searches or budget changes.

## Fixed construction

Source fixtures are the four covered Latin/Swabian letter/mixed positives from
`guided-model-calibration/prepared.json`. Each is replayed unchanged as a paired
positive and transformed by two predefined rules:

- **Pair chunks:** shuffle aligned two-glyph blocks inside each word type.
  This preserves aligned pair counts and the generating length-two codewords,
  but can change overlapping bigrams at chunk boundaries and word endpoints.
- **Bigrams:** randomly traverse the word's directed bigram multigraph to obtain
  another Euler trail. This preserves overlapping bigram counts and endpoints;
  it does not necessarily preserve aligned codewords or longer substrings.

Both preserve word-length sequences, per-word glyph counts and the exact word
repetition partition. Every occurrence of a word type receives the same
transformation. Collision-free type mappings prevent accidental new repetitions.
Construction runs on combined training and continuation ciphertext with seed
1818, at most 128 draws. Unchanged or colliding draws are rejected. No draw is
selected using the generating key, language score, SAT result or continuation
performance. Some word types may remain unchanged; change counts are reported.

Controls are **structural corruptions**, not guaranteed model-impossible
negatives. Their status under the shared-key model is the question being tested.
Generating-key compatibility is inspected only after construction; it does not
filter controls. In this run all seven constructed controls fail whole-block
dictionary compatibility under the generating key, which alone would not rule
out another fitting key.

The Latin letter bigram construction produces no changed collision-free draw
within the fixed cap. It is recorded as unavailable, not counted as an UNSAT
result or proof that no alternative exists. No source or rule was substituted.

Each constructible case and paired positive receives one ordinary recovery fit
with a five-second timeout, observed codeword domains, its generating profile's
dictionary/alphabet and free H2/L1–3 prefix-free model. No key enumeration,
contraction expansion beyond the existing rule, or statistical objective is
introduced. Frozen SAT keys are evaluated on the transformed continuation.

## Recorded results

| Source fixture | Unchanged positive | Pair-chunk control | Bigram control |
| --- | --- | --- | --- |
| Latin letters | Verified SAT | UNSAT | Construction unavailable |
| Latin mixed | Verified SAT | UNSAT | UNSAT |
| Swabian letters | Verified SAT | UNSAT | UNSAT |
| Swabian mixed | Verified SAT | UNSAT | UNSAT |

All four positives fit and all seven constructible corruptions are proved
UNSAT under their respective bounded models. No timeout. The eleven fits total
13.33 seconds, individually 0.72–2.09 seconds.

The bigram controls alter only two Latin-mixed training words, one Swabian-letter
training word and one Swabian-mixed training word. The latter two controls are
rejected despite such small changes and preservation of all per-word bigram
counts, endpoints, lengths and repetitions. All seven negative inputs pass
individual word-length feasibility and have nonempty prefix-pruned candidate
graphs. Their rejection therefore goes beyond those preliminary filters.

Pair-chunk controls remain fully decodable under the generating keys, because
every aligned codeword is retained. However, many reordered plaintext words
fall outside the vocabulary. Rejecting these cases requires more than the mere
presence of complete known codewords.

Paired-positive first-key continuation predictions are:

| Source fixture | Exact words | Novel exact words |
| --- | --- | --- |
| Latin letters | 3/4 | 1 |
| Latin mixed | 4/4 | 2 |
| Swabian letters | 4/4 | 2 |
| Swabian mixed | 4/4 | 3 |

These predictions include previously seen ciphertext words. Positive SAT and
negative UNSAT separation does not imply reliable decipherment of unseen words.
No continuation scores exist for UNSAT controls; they are not assigned zero.

## Interpretation and limitations

The bounded cipher-plus-dictionary models can distinguish these four known
ciphertexts from seven corruptions preserving substantially more local structure
than simple glyph shuffles. This supports using ordinary recovery as a calibrated
baseline for this small test suite.

It does not supply a statistical false-positive rate: there is one fixed draw
per control/source, short related fixtures, a twelve-spelling vocabulary per
language and engineered generating-code coverage. Rejection can depend heavily
on that restrictive vocabulary. These are projected short-word streams, not
intact prose, full historical vocabularies, independently sampled authors or
Voynich controls. No language preference or manuscript conclusion follows.

Do not tune more corruption seeds until one becomes SAT. Keep the fixtures as
regression/calibration evidence. The next breadth check should compare a simpler
cipher baseline with the bounded expansion/mixed models under fixed matching
controls, rather than deepen statistical guidance or add cipher freedoms.

## Artifacts and verification

`benchmarks/structured_negative_controls.py` prepares and runs the suite.
Protocol, identities, complete requests, generating-key diagnostics, construction
invariants, fit results and independent validation are saved under
`experiments/results/structured-negative-controls/`. Earlier results are unchanged.
Preparation rejects source/code identity changes. Completed cases are skipped;
interrupted cases repeat from their start.

Eleven focused tests pass, covering preserved bigram/chunk structure, deterministic
repetition handling, unavailable construction, positive verification, feasible
score-search regression and frozen prediction scoring. Independent validation
reconstructs all controls and the unavailable draw, verifies SAT fits and
predictions, and checks generating-key diagnostics and necessary filters. UNSAT
statuses are the recorded solver proofs; validation does not rerun those solves.

```sh
.venv/bin/python -m benchmarks.structured_negative_controls --run
.venv/bin/python -m pytest -q tests/integration/test_structured_negative_controls.py \
  tests/integration/test_feasible_sequence_search.py \
  tests/integration/test_frozen_key_holdout.py
PYTHONPATH=.:src .venv/bin/python experiments/results/structured-negative-controls/validate.py
```
