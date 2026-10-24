# Word-conditioned reading weights — iteration 71

Weighting candidate readings helps slightly, but **does not make the lexical score useful**. On the same 1,273 frozen iteration-70 pairs, original-word wins rise from 174 (13.67%) to 207 (16.26%). Weighted shuffled context wins 171 (13.43%) and weighted grammatical prior 154 (12.10%). The contextual advantage is only 2.83 percentage points over shuffle and 4.16 over prior; all primary thresholds fail. No dictionary search, historical-corruption phase or nucleus recovery was run.

| Score | Original wins | Wrong candidate wins | Ties |
|---|---:|---:|---:|
| Original union, contextual | 174 | 966 | 133 |
| Weighted readings, contextual | 207 | 1,066 | 0 |
| Weighted readings, shuffled context | 171 | 1,102 | 0 |
| Weighted readings, grammatical prior | 154 | 1,119 | 0 |
| Source word frequency | 27 | 1,246 | 0 |

The strict-win increase comes with more losses: weighting resolves previously tied pairs as well as changing preferences. These are correlated, reused development positions; do not interpret the percentages as a validated improvement in restoration.

## Fixed intervention

Keep the iteration-70 candidate pairs, contextual model, source fold and cached joint analyses unchanged. Estimate each candidate word's coarse POS probability from its source word/POS counts, adding one pseudo-observation distributed according to global source POS frequencies. Unseen words use that global prior. Split a POS probability equally across its distinct joint dictionary readings. Score the expected compatibility under these reading probabilities rather than the union of all compatible labels.

Do **not** renormalize over only dictionary-supported POS: otherwise a lone rare reading could absorb all probability. Unknown dictionary entries still receive zero. The intervention learns word-specific POS probabilities, not word-specific Case/Number probabilities; those remain uniform within POS. The reference-POS candidate sampling, supplied correct surroundings and sentence boundaries of iteration70 are retained privileges. No new target annotations or target-informed hyperparameters are introduced.

The frozen gate requires at least 65% strict wins, ten percentage points over both frequency and weighted prior, and five over weighted shuffle. It fails. A post-result candidate-only control (total supported reading probability, no context) wins 102/1,273; it is descriptive and was not used to select weights.

## What the failure narrows down

Among 727 pairs with distractor `non`, wrong-candidate victories fall from 710 to 664. Its source counts are ADV 430 and ADJ 4: the rare noun reading is strongly downweighted, as intended. But the score still rewards its **ordinary adverb reading** where the masked contextual model gives substantial adverb probability.

For example, for `gallia` versus `non`, original union scores are 0.1441 versus 0.6768; weighted scores are 0.0386 versus 0.4885. The noun reading of `non` receives only 0.000475 probability, so that rare reading is no longer the main explanation. The model assigns enough probability to an adverb at that position to overwhelm the original noun's weighted compatible readings. Dictionary coverage and same-profile ambiguity identified in70 also remain.

This rejects the simple claim that fixing rare alternate readings is sufficient. It does not establish that all word-conditioned analysis models fail: the tested estimator has only word/POS counts and uniform within-POS readings. The next useful diagnostic is to separate **wrong predicted POS** from **wrong Case/Number within the correct POS**, using an explicitly supplied coarse-POS oracle on these fixed pairs. If even oracle POS leaves a weak discrimination ceiling, improve contextual morphology only after checking that limitation. Do not infer new nuclei from these pairwise results.

## Verification

All 1,273 weighted predictions are replayed and the fixed pairs verified unchanged; 1,486 prior manifest input hashes pass. Four new tests cover rare-reading suppression, unseen-word fallback, within-POS weighting and unknown handling; all 14 focused tests pass. The grammar reserve and sealed lexical final test remain unscored.

Artifacts: `experiments/results/grammar-restoration/iteration71/`; code: `benchmarks/grammar_weighted_readings_iteration71.py` and its audit.
