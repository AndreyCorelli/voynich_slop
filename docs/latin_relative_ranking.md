# Relative structural passage ranking

Run: 2026-10-12. **Training relative rankings improves grammatical-control comparisons, especially in the predeclared structural-only arms. No model passes the per-length/per-work reliability gate.**

## What changed

Instead of learning an absolute valid/invalid threshold, learn a candidate score whose differences favor a grammatical candidate over a deliberately damaged candidate for the same source passage. The objective is weighted pairwise logistic loss with ridge regularization. There is no intercept and no centering of differences; fitting-only weighted RMS scales each feature. Consequently, the learned score can evaluate any candidate independently as `sum(weight[i] * candidate_feature[i] / scale[i])`. The original plaintext is needed to curate/evaluate examples, not to score a proposed candidate.

Training pairs include original-versus-corruption and grammar-preserving noun substitution-versus-corruption. Equal fitting mass is assigned to each work, then each width, then each comparison kind. This prevents larger works and more sampled variants from dominating. Signed/nonnegative models are tested with all 19 existing passage features and with eight morphology-only features: morphological sequence, adjacent/marginal agreement, dictionary coverage, and their low-tail rates. These structural-only models contain no neural or lexical-frequency features, but their morphology-sequence model still lexicalizes function words. They are proxies, not dependency parsers.

Five fixed ridge penalties are compared on calibration data. Selection prioritizes grammatical-control ranking, then all-pair ranking, then logistic loss. The calibration-selected model is **all_features_signed**, ridge 0.001. The calibration-selected single feature is marginal agreement. Both are frozen before this run evaluates test pairs. Structural-only arms were declared before evaluation; highlighting their stronger test results is exploratory and does not retroactively change the selected model.

Fitting: 149 pairs from four works. Calibration: 73 pairs from three works. Evaluation: 99 pairs from four works. These reuse the earlier passage dataset and previously examined test authors/mutations. This is an exploratory objective comparison, not a fresh independent test. No new neural scoring or dictionary search is needed because the frozen passage features already exist.

## Results

Numbers are correct strict rankings / comparisons. Ties count as failures. “Control” means a grammatical noun substitution, not the original vocabulary.

| Model | 250 original | 250 control | 1,000 original | 1,000 control | Whole original | Whole control |
|---|---:|---:|---:|---:|---:|---:|
| all_features_signed | 33/34 | 26/29 | 9/10 | 9/10 | 7/8 | 7/8 |
| all_features_nonnegative | 32/34 | 23/29 | 9/10 | 8/10 | 7/8 | 7/8 |
| structural_features_signed | 33/34 | 28/29 | 9/10 | 9/10 | 8/8 | 8/8 |
| structural_features_nonnegative | 33/34 | 28/29 | 9/10 | 9/10 | 7/8 | 8/8 |
| marginal_agreement | 23/34 | 23/29 | 7/10 | 8/10 | 7/8 | 7/8 |
| morphological_sequence | 32/34 | 23/29 | 9/10 | 6/10 | 8/8 | 8/8 |
| neural_mean_piece | 34/34 | 21/29 | 10/10 | 9/10 | 8/8 | 7/8 |

The selected model improves short-passage grammatical-control ranking from neural 21/29 (72.4%) to 26/29 (89.7%), at the cost of one original-versus-corruption failure. Both structural-only models reach 28/29 (96.6%) controls there. The structural-only signed model also gets 8/8 in both whole-work comparisons, but only 9/10 for each kind at 1,000 words. It fails the predeclared >=95% requirement in every length/kind and >=90% in every work.

The structural-only signed arm ranks 95/99 combined comparisons correctly, but those are correlated variants/nested blocks of four works. Treating 99 as independent trials would overstate evidence. Whole works range from 627 to 4,204 words; only two test works supply 1,000-word blocks. Equal changed-token counts between controls and corruptions are guaranteed at whole-work length, not within each local block. Corruptions are sparse and refer to automatically recorded violations under the original annotated parse, not expert proofs that no alternative parse is possible.

No universal probability of grammaticality or absolute anomaly threshold is produced. Pairwise training learns candidate preferences. It can still learn lexical or annotation artifacts; signed weights can also exploit proxy-specific shortcuts. A search optimizer has not yet attacked this fitted score.

## Selected coefficients

Coefficients apply to raw candidate features divided by the fitting-only scale. Means are not subtracted. Complete scales and every arm are saved in selection.json.

| Feature | Selected all-feature signed | Structural-only signed |
|---|---:|---:|
| neural_mean_piece | -0.189208 | 0.000000 |
| neural_piece_sum | 1.339695 | 0.000000 |
| word_unigram | 1.275077 | 0.000000 |
| word_bigram | 0.361860 | 0.000000 |
| word_trigram | 0.100524 | 0.000000 |
| morphological_sequence | 3.657452 | 5.138238 |
| adjacent_agreement | -1.292294 | -1.393773 |
| marginal_agreement | 3.760629 | 4.319424 |
| morphology_coverage | 2.137568 | 3.542934 |
| low_tail_neural_mean_piece | -0.722195 | 0.000000 |
| low_tail_neural_piece_sum | 2.297194 | 0.000000 |
| low_tail_word_unigram | 0.354300 | 0.000000 |
| low_tail_word_bigram | -0.009036 | 0.000000 |
| low_tail_word_trigram | -0.009036 | 0.000000 |
| low_tail_morphological_sequence | 0.000000 | 0.000000 |
| low_tail_adjacent_agreement | 1.253793 | 1.478983 |
| low_tail_marginal_agreement | 0.825225 | 0.764483 |
| low_tail_morphology_coverage | 1.083424 | 1.288247 |
| sentence_acceptance_rate | -0.049604 | 0.000000 |

## Next decision

Relative training is worth continuing; the structural-only arms now provide a concrete promising objective. Freeze them and evaluate new mutation dictionaries and new works before spending a long cipher-search budget. In particular, generate damaging dictionaries that maximize this exact score and retain morphology-preserving vocabulary substitutions as positive controls. These results do not establish recovered sentence structure or successful decryption.

## Artifacts and validation

[Complete rankings](../experiments/results/latin-relative-ranking/report.json), [weights/scales](../experiments/results/latin-relative-ranking/selection.json), [pair examples and failures](../experiments/results/latin-relative-ranking/examples.md), [frozen pair data](../experiments/results/latin-relative-ranking/pairs.json), [replay validation](../experiments/results/latin-relative-ranking/validation.json). Source data, raw score validation and licenses are documented in the [passage audit](latin_passage_proxy_audit.md).

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_relative_ranking
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_relative_ranking --validate
```

A second full fit/calibration/evaluation run reproduced weights, selection and report exactly. Focused tests: 12 passed, including pair-loss direction, signed reversal, score-difference invariance and work/width/kind weighting. No source files or frozen results of earlier benchmarks were changed.

Derived text retains the [UD Latin Perseus r2.17](https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17) CC BY-NC-SA 2.5 license and original attribution README.
