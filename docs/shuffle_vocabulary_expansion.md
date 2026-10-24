# Identical randomized controls at 256 words

Expanding only the dictionary changes the twelve preserved shuffle outcomes
from twelve UNSAT at 64 words to **one verified SAT, two UNSAT and nine UNKNOWN**
at 256 words. The SAT key completely decodes none of its three novel shuffled
held-out words, so it yields zero dictionary-compatible continuation words.

| Positive fixture | Shuffle 4401 at 256 | Shuffle 4402 at 256 | Saved positive at 256 |
|---|---|---|---|
| Length two / 4301 | UNKNOWN | SAT | UNKNOWN |
| Length two / 4302 | UNKNOWN | UNKNOWN | SAT, 0/3 exact |
| Lengths one/two / 4301 | UNSAT | UNKNOWN | SAT, 3/3 exact |
| Lengths one/two / 4302 | UNKNOWN | UNKNOWN | SAT, 0/3 exact |
| Lengths one/two/three / 4301 | UNKNOWN | UNSAT | UNKNOWN |
| Lengths one/two/three / 4302 | UNKNOWN | UNKNOWN | SAT, 1/3 exact |

The randomized SAT fit takes 2.05 solver seconds. UNSAT checks take 0.41 and
3.03 seconds; UNKNOWN checks consume about five seconds. UNKNOWN is unresolved,
not evidence of rejection or acceptance. Nine unresolved cases prevent a useful
estimate of control acceptance frequency. The controls were not assumed impossible;
verified SAT establishes bounded dictionary compatibility for that shuffled input.

## Fixed dictionary-only intervention

All shuffled training and held-out ciphertexts, shuffle seeds, construction
metadata and paired positive keys are exactly those from
[64-word shuffled controls](varied_length_shuffle_controls.md). The only changed
request field is the dictionary, replaced by the already frozen 256-word corpus
ladder. Alphabets, word boundaries, H1 prefix-free L1–3 bounds, free selection,
flat membership, observed domains and five-second configured timeout remain
unchanged. Training identities, key, word lengths and continuation remain hidden
from the solver. No new random draws, seeds, retries or longer timeouts occur.

The 64-word controls preserved word lengths, every word's glyph multiset and the
complete repetition partition; using identical ciphertext preserves those facts
here. Six 256-word positive rows and twelve 64-word control rows are reused after
hash/request checks, not fitted again. Sources, previous reports and model code
are hashed in the new protocol. Completed fits checkpoint and skip on resume.

Only verified SAT keys are scored, with the key frozen and the same shuffled
continuation held out. Controls have no known generating plaintext, so their
metric is complete decoding and dictionary compatibility, not exact accuracy.
The lone SAT control has zero fully decoded words and zero dictionary words;
partial prefix decoding is not counted as prediction success.

## Interpretation

The larger vocabulary admits at least one randomized training explanation that
was impossible in the 64-word model. Training SAT alone is therefore insufficient
to identify a predictive generating explanation. The frozen continuation rejects
this returned control key. However, two true-positive first keys at 256 words
also predict zero correct/dictionary words. A poor first-key holdout score is not
by itself a reliable negative classifier: correct predictive positive keys are
still constructively known to exist.

The suite now exhibits both unresolved search and wrong first-key identification.
This does not establish a language, grammatical plaintext, population false-fit
rate or manuscript conclusion. Twelve correlated randomizations of six keys over
one engineered word inventory cover only this shuffle family. The two UNSATs are
solver-reported, without independently checked proof certificates.

Five focused tests pass, checking dictionary-only changes, identical seeds and
holdout, cached pair matching, public-training-request inputs, unscored UNKNOWN,
checkpoint reuse and the original shuffle invariants. Actual artifact validation
checks the exact preserved control/positive records, unchanged requests apart
from dictionary, recovered SAT witness and independent frozen continuation score.

Artifacts: `experiments/results/shuffle-vocabulary-expansion/`.

```sh
.venv/bin/python -m benchmarks.shuffle_vocabulary_expansion --validate
```

Further dictionary expansion is not the priority now. Keep the 64-word suite as
a tractable recovery/discrimination control and preserve the 256-word cases as
ambiguity/search failures. Any next method should be judged on both true-positive
frozen prediction and randomized-control outcomes, rather than SAT alone. Review
prior ranking experiments before trying another score: earlier priors did not
consistently rescue first-key prediction, and these training sequences are
engineered repetitions rather than natural prose.
