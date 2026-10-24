# Small-vocabulary varied-length calibration

All twelve fixed-budget fits reach verified SAT quickly. Known-word recovery
predicts all three novel held-out words on each of six cases. Hidden-word recovery
predicts 3/3 on five cases and 2/3 on one mixed-length case: 17/18 exact held-out
occurrences across its six first-key predictions.

| Generating profile | Seed | Known-word solver seconds | Known-word exact held-out | Hidden-word solver seconds | Hidden-word exact training | Hidden-word exact held-out |
|---|---:|---:|---:|---:|---:|---:|
| Length two | 4301 | 0.038 | 3/3 | 0.224 | 14/18 | 3/3 |
| Length two | 4302 | 0.029 | 3/3 | 0.216 | 18/18 | 3/3 |
| Lengths one/two | 4301 | 0.027 | 3/3 | 0.200 | 18/18 | 3/3 |
| Lengths one/two | 4302 | 0.028 | 3/3 | 0.208 | 14/18 | 3/3 |
| Lengths one/two/three | 4301 | 0.028 | 3/3 | 0.164 | 10/18 | 2/3 |
| Lengths one/two/three | 4302 | 0.028 | 3/3 | 0.162 | 18/18 | 3/3 |

Construction takes 0.10–0.17 seconds per fit. No timeouts or synthetic UNSATs
occurred. The single hidden-word miss decodes generating `in` as `mn`, which is
not in the fixed dictionary; `a` and `eo` decode correctly. Training identity
ambiguity persists even in several cases that predict the continuation correctly.
First-key success does not establish unique keys or forced predictions.

## Frozen protocol

The experiment reuses the existing twelve-spelling letter-only Latin inventory,
18 training occurrences (nine distinct types, each repeated twice), and three
novel held-out types (`in`, `a`, `eo`). Its plaintext alphabet has only the 14
letters in this inventory; the ciphertext alphabet is the same six glyphs
`uvwxyz`. All held-out generating letters occur in training, so every held-out
H1 code is observed there. Both plaintext and ciphertext held-out types are
absent from training, though their plaintext spellings remain dictionary members.

Six new generating keys use seeds 4301/4302 under three profiles: fixed length two,
mixed lengths one/two, and mixed lengths one/two/three. Mixed keys allocate two
length-one leaves, then length-two and length-three leaves on disjoint branches
of the prefix tree. Actual training codes are checked to use every requested
length, without resampling. Keys and all inputs were saved before any solve.

Both recovery arms permit H1 prefix-free L1–3 codes, free selection and observed
code domains, with a configured five-second solver timeout. The known-word arm
receives training plaintext only, with key, individual code lengths, segmentation
and continuation hidden; dictionary word search is removed. The hidden-word arm
receives only the public request, retaining full search within the twelve-word
dictionary. No oracle lengths, generating profile, statistical objective, public
length schedule or continuation constraints are passed to either arm. First
verified keys are frozen before scoring. Construction is separate from solver
time; no retries or extra seed selection occur. Completed arms checkpoint.

## Why this is a new check

The earlier reduced novel-word controls generated length-two keys, even though
recovery allowed lengths one through three. Their “mixed” profiles referred to
plaintext contractions, not varied generating code lengths. The newer varied-code
suite used the full 5,655-word dictionary and 24-letter alphabet. This experiment
combines a genuinely varied generating code with the reduced, fixed vocabulary
and known/hidden training-word arms. It reuses words to keep the comparison
interpretable, but uses new keys and does not rerun the old fixtures.

Seven focused tests pass. They cover deterministic keys, distinct prefix-free
codes, generating length sets, matched arm requests/budgets, plaintext-only
known-arm inputs, request-only hidden-arm inputs, unscored UNKNOWN and resume
without repeated fits. Actual artifact validation checks code/source hashes,
synthetic and recovered witnesses, generating length coverage, novel/code-covered
holdout, fixed known words and independently recomputed continuation scores.

Artifacts: `experiments/results/small-varied-length-controls/`.

```sh
.venv/bin/python -m benchmarks.small_varied_length_controls --validate
```

## Interpretation and next check

Basic varied-length recovery is tractable on this engineered small vocabulary;
full-vocabulary timeouts are not explained by an inability to handle varied code
lengths alone. However, vocabulary and plaintext alphabet are both smaller than
in the full-scale suite, keys differ, and the training text is engineered rather
than intact prose. This does not isolate the source of full-scale difficulty.
No scrambled controls were included, so it measures positive recoverability,
not specificity against accidental fits or evidence for a manuscript language.

The next useful one-variable comparison would preserve these keys, alphabets,
training ciphertext and held-out words, and grow only the dictionary using a
frozen corpus rule. Added words must use the same 14-letter alphabet. Review prior
vocabulary-scaling protocols before choosing sizes to avoid repeating equivalent
checks. Score verified frozen keys as well as SAT throughput: fast recovery and
predictive identification are distinct, as the 2/3 mixed-case result demonstrates.
