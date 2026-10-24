# Shared-key synthetic control with full Latin membership

This is one deliberately small coupling test on the frozen default inventory of
2.55 million generated forms. Three training words (`amare`, `arma`, `mare`) and
one novel held-out word (`area`) use a seeded injective, fixed two-glyph code per
letter. Seed 4901 selects the key without outcome-based resampling. All source
words belong to the inventory; every held-out code occurs in training.

Public assumptions: code boundaries, two-glyph code length and plaintext word
lengths are known. Each distinct observed code has one shared integer plaintext
letter variable, bounded by the full inventory alphabet. Distinct codes map to
distinct letters. Each training word is constrained by exact sparse layered
membership. Training spellings, generating key and held-out word are not supplied
to solving. The first SAT key is frozen before held-out scoring; no alternative
key selection, repair or truth-assisted pruning follows.

The budget is 30 seconds solving and 60 seconds for a fresh worker, with durable
loading/construction/solving/verification checkpoints. This is a single toy
control with four distinct observed codes, not full H1 L1–3 recovery, homophone
selection, hidden segmentation, natural prose or manuscript testing. No shuffled
control was included in this small coupling check.

## Result

**SAT, independently verified**, but **0/3 true training words recovered** and
**0/1 exact held-out words**:

| Training truth | First-key decoding |
| --- | --- |
| amare | euexi |
| arma | exue |
| mare | uexi |

The held-out `area` decodes to `exie`, which is absent from the inventory. The
training decodings are members of the mechanically generated inventory; this
does not establish that they are attested or plausible Latin words.

Loading: 0.008 seconds; construction: 0.995 seconds; solving: 0.646 seconds;
verification: 0.00030 seconds. Total worker: **1.650 seconds**. The independently
checked witness respects every repeated code, shared-key injectivity and exact
training membership. It explains the ciphertext but is not the generating key.

One small test passes, checking consistent repeated-code mapping and held-out
scoring on a tiny inventory. Artifact validation reconstructs the shared-key
training explanation and frozen held-out score. Prior files/results remain
unchanged.

```sh
.venv/bin/python -m benchmarks.latin_layered_cipher --run
.venv/bin/python -m benchmarks.latin_layered_cipher --validate
```

Artifacts: `experiments/results/latin-layered-cipher`.

The computational coupling works in this minimal setting, while predictive
recovery does not. A next calibration should increase independently selected
training diversity and observed alphabet coverage, freeze a novel code-covered
holdout and a matched shuffled control, then score the first key. Increasing
training evidence is a proposal; it has not been implemented here. This result
supports no manuscript-language conclusion and does not estimate a false-fit rate.
