# Longer-range conditional prediction: synthetic calibration

The seven-stage experiment asks whether a predictor can detect dependencies at word distances 2–8 after controlling for position and the immediate predecessor. This is a synthetic control test, not a manuscript experiment or a historical mechanism comparison.

## Frozen design

Synthetic words have three letters drawn from `abcd`. Every final letter is sampled independently; the initial letter can copy a previous final letter. This prevents an adjacent final-letter chain from producing a misleading distant signal. The middle letter is independent. Cases are independent order, local-only dependence, dependence at lag 2, 4 or 8, and a mixture of local and lag-4 dependence. Strong copying dose is 0.8; weak dose is 0.25. Mixed cases allocate half the dose to each mechanism.

Each case has 128 training blocks and 256 independent evaluation blocks of 32 words. Only word indices 8–31 are scored, so all seven lag features are available. Blocks reset context. Position is controlled by early/late half-block bins. These are ideal conditions with a small alphabet and balanced, abundant contexts; they do not estimate sensitivity on EVA or historical prose.

The baseline predicts the current initial letter from position and the immediately preceding final letter. Counts back off through position to a globally smoothed distribution, with fixed strength 20. Seven separate extensions condition additionally on one final letter at distances 2–8 and back off to the baseline. The primary extended predictor is the arithmetic mean of these seven **probability distributions**, with no selected best lag. Per-lag gains are diagnostics only. Gains are bits per scored initial-letter event, not full-spelling bits per character.

For each case, three refitted controls permute each lag feature separately within position/immediate-final groups, independently in training and evaluation. Current targets and baseline features remain unchanged, and each conditional feature marginal is preserved. These are conditional feature controls, not necessarily coherent reordered texts. They remove target/lag association conditional on the baseline but also alter relationships between distant features. No permutation p-value or significance threshold is claimed.

Primary contrast is active mixture gain minus the mean refitted-control gain. All sources here are synthetic; no cached corpus, encoder, Z3 solver or manuscript text is used.

## Seven stages

1. Freeze model, lags, smoothing, generators and seeds.
2. Strong controls with seed 36001.
3. Independent replication with seed 36002.
4. Independent replication with seed 36003.
5. Weak controls with seed 36001 and a bijective alphabet-relabeling check.
6. Three matched refitted feature controls per case.
7. Assess separation and limitations; no model or lag selection.

Plans precede scoring and record prepared/preceding-result digests. Twenty-four active cases and 72 refitted controls are saved, with six additional alphabet-relabeled score checks.

## Results

Matched-null excess, bits per scored initial-letter event:

| Control | Strong: range over three seeds | Weak: one seed |
|---|---:|---:|
| Independent | −0.000326 to 0.000963 | −0.000337 |
| Local only | −0.000227 to 0.001442 | 0.001541 |
| Planted lag 2 | 0.289409 to 0.290373 | 0.029646 |
| Planted lag 4 | 0.285891 to 0.287417 | 0.030044 |
| Planted lag 8 | 0.284938 to 0.293717 | 0.030837 |
| Local + lag 4 | 0.093487 to 0.100221 | 0.007903 |

The frozen predictor separates the planted distant effects from independent and local-only controls in these runs. Weak mixed dependence has the smallest positive effect but remains above the tested negatives. This establishes that the implementation responds to its intended signal under idealized conditions. It does not establish a false-positive rate, statistical power across realistic vocabularies, or a mechanism classifier. A longer-range signal in real text could also arise from topic, layout, common latent state, repeated templates or an explicit generator.

## Verification and reproduction

Two focused tests check normalized predictive distributions and conditional-null invariants. Independent validation reconstructs counts using tuple keys and checks every stored baseline, per-lag and mixture loss, all aggregate contrasts, baseline invariance under the nulls, alphabet relabeling, plans and summaries. The synthetic generator itself is reused; no claim of independent generator replication is made.

```sh
.venv/bin/python -m benchmarks.long_range_calibration --run
.venv/bin/python -m benchmarks.long_range_validation
.venv/bin/python -m pytest -q tests/integration/test_long_range_calibration.py
```

Results: `experiments/results/long-range-calibration/`. Benchmark code is hashed in `prepared.json`; further changes require a new module/output directory.

## Next priority

Before applying the statistic to the manuscript, test realistic controls: a 26-symbol alphabet, uneven word frequencies and lengths, real line boundaries, fewer training words, and local-only generators that have shared latent states or vocabulary restrictions. Use a single frozen lag-mixture predictor and train-only smoothing choices, with planted longer-range positives of comparable strength. These checks address sparsity and confounding that this ideal calibration deliberately avoids. Apply to manuscript data only after that calibration gives a useful comparison.

Validation passed: 5,640,192 independently reconstructed target-probability/loss checks across active cases, refitted controls and relabeled replicas. In every planted and mixed case, the diagnostic strongest lag was the planted lag, including the weak cases. This diagnostic was not used to select the primary mixture. Both focused tests passed.
