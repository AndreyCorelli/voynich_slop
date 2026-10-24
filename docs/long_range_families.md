# Longer-range specificity across mechanism families

The frozen pooled estimator detects mapped distant dependencies, but its separation from stronger template controls fails. This closes its use as a direct-copy or historical-mechanism discriminator. It remains a measure of conditional predictive association.

## Frozen protocol

Reuse the estimator selected previously on training-only calibration: pooled/fine strength 10, extension weight 0.75, fixed seven-lag probability mixture. No smoothing, lag, model or decision-threshold selection occurs here. Training has 32 blocks (1,024 words, 512 eligible events); evaluation has 89 blocks (2,848 words, 1,424 eligible events). Synthetic words use 26 letters with uneven emissions and three/four-letter lengths. Blocks contain two artificial 16-word lines; distances 2–8 never cross a line boundary.

Seven preset generator types:

- Independent uneven emissions.
- Mapped local copying with probability 0.6.
- Mapped lag-4 or lag-8 copying with probability 0.6.
- Weak mapped lag-4 copying with probability 0.25.
- Persistent hidden-state emissions, switching with probability 0.02 per word and resetting at line starts. Two states favor different alphabet halves, with leakage weight 0.2.
- A four-phase noisy template. A random phase offset is chosen per line; final-letter preferences follow `aein` and initial-letter preferences follow `rtos`, each with probability 0.7. Other emissions follow the uneven background. Template generation uses current phase, not a predecessor lookup.

Mapped copying uses a seed-specific shuffled alphabet bijection shared between training and evaluation. This is a new mapping rule relative to identity-copy calibration; it is not a learned cipher/decryption key. A random permutation can retain fixed points, so not every copied event necessarily changes its character.

Baseline features remain scored-line position bin, current word length and immediate predecessor final letter. Current length is supplied publicly. Each fixture has three refitted conditional feature controls: distant features are independently permuted within baseline groups, leaving targets and baseline features unchanged. Such controls need not correspond to coherent texts and do not supply a claimed permutation p-value.

## Seven stages

1. Freeze estimator, selection record, new families, three seeds and three null streams.
2. Score all seven families with seed 39001.
3. Replicate with seed 39002.
4. Replicate with seed 39003.
5. Expose true current state or template phase in baseline features for the two confound families, across all three seeds.
6. Score matched refitted controls for all 27 active cases.
7. Evaluate the predeclared descriptive criterion: minimum weak mapped excess must exceed the largest independent/local/state/template control excess. Failure stops mechanism-discriminator interpretation and further estimator tuning.

Prepared code/selection hashes and preceding-result digests are recorded. Plans are saved before scoring. The criterion is a descriptive range comparison, not a fitted threshold or a significance/power estimate. Oracle state/phase is diagnostic information unavailable for manuscript scoring.

## Results

Matched-null excess, bits per eligible initial-letter event, ranges across three seeds:

| Generator | Excess range |
|---|---:|
| Independent | −0.013437 to 0.006592 |
| Mapped local | −0.004701 to 0.003570 |
| Strong mapped lag 4 | 0.476069 to 0.537273 |
| Strong mapped lag 8 | 0.495691 to 0.544890 |
| Weak mapped lag 4 | 0.131452 to 0.139929 |
| Persistent hidden state | 0.071044 to 0.078807 |
| Noisy template | 0.291554 to 0.308852 |

The criterion fails: minimum weak mapped excess **0.131452** is below maximum control excess **0.308852**. Template gains exceed weak mapped gains on every tested seed. Persistent hidden states also produce substantial gains despite having no explicit distant-copy operation.

With oracle current-state information, state excess falls to −0.007564 to −0.000249. With oracle current-phase information, template excess falls to −0.012058 to 0.020627. Most of these effects disappear when the common generating variable is exposed to the baseline. This is a diagnostic comparison with different baseline conditioning and smoothing contexts, not a quantitative causal decomposition.

A template has genuine distant association, so this is **not a failure to detect statistical dependence**. It is a failure to attribute that dependence to a direct distant-copy operation. All these generators produce real predictable associations beyond the original baseline. The tested statistic cannot distinguish their mechanism from its sign or magnitude alone. Strong mapped positives remain larger than templates in these fixtures, but no universal magnitude boundary follows.

## Assessment

Stop tuning this estimator and stop presenting longer-range gains as a manuscript-mechanism discriminator. Preserve it for descriptive association measurements, with matched controls and explicit conditioning limitations. Do not infer that Voynich uses templates, hidden states or mapped copying from this synthetic result. No manuscript data, historical corpus, encoder or Z3 solver was scored here.

The next useful move is a step back: compare the remaining hypothesis families and specify what observation each predicts that competing mechanisms cannot readily reproduce. Reuse the completed calibration results as constraints on test choice. Prefer a falsifiable mechanism-specific restriction over another generic local or distant summary statistic. This report does not select a new historical hypothesis or claim that any untested alternative is likely.

## Verification and reproduction

Two tests check mapped-copy traces against the bijection and line boundary, and oracle phase feature construction. Independent validation reconstructs hierarchical probabilities and every feature row, checks mapping operations, unchanged baseline scores under controls, conditional inventories, frozen selection, plans and final criterion. The generator implementation is reused; historical realism is not independently validated.

```sh
.venv/bin/python -m benchmarks.long_range_families --run
.venv/bin/python -m benchmarks.long_range_families_validation
.venv/bin/python -m pytest -q tests/integration/test_long_range_families.py
```

Results: `experiments/results/long-range-families/`. Prepared records hash estimator and new generator code plus the original selection record. Further variants require a separate module/output directory.

Verification passed: both tests, 1,384,128 independently reconstructed probability/loss checks and 17,386 mapped-copy event checks. All saved contrasts and the failed criterion passed the audit.
