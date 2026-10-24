# Can available proxies distinguish grammatical Latin from corruption?

Run: 2026-10-12. **No reliability established for the tested weighted combinations.** This isolates sentence scoring from cipher search: no optimizer over dictionaries is involved.

## Protocol

300 annotated source sentences produced 1,125 originals, grammatical controls and deliberate corruptions. Whole works/authors were separated: 425 fitting cases, 263 calibration cases, 437 test cases from 107 source sentences. Test contains 276 positives and 161 corruptions. Caesar was excluded from this sentence dataset; statistical scorers retained their earlier disjoint 39,346-token Caesar training corpus.

Gold dependencies identify where to edit, but scorers receive only normalized word sequences. Negatives change one real surface form while retaining the dictionary lexeme and other inflection features: subject–verb number, adjective agreement, or governed preposition case. Ambiguous forms retaining the old feature are rejected. Adjective gender and number corruptions appear only in testing. Positive controls substitute a different noun with matching case/number/gender, or swap an adjacent adjective and its noun. Semantically odd substitutions remain positive to separate syntax from meaning.

Nine available features: two neural whole-word masked scores; word unigram, bigram and trigram likelihood; latent morphological sequence likelihood; adjacent and marginal agreement; dictionary coverage. Features are normalized from fitting data only. Balanced logistic regression fits nonnegative and unrestricted signed weights. Five ridge penalties are compared; calibration alone selects penalty and classification threshold. Selection was saved before test scoring. The calibration-selected single proxy was morphological sequence likelihood.

## Held-out results

| Scorer | Balanced accuracy | Original beats corruption | Valid accepted | Corrupt rejected |
|---|---:|---:|---:|---:|
| nonnegative_combination | 57.7% | 81.4% | 90.6% | 24.8% |
| signed_combination | 57.6% | 80.1% | 89.1% | 26.1% |
| neural_mean_piece | 52.3% | 86.3% | 85.9% | 18.6% |
| neural_piece_sum | 49.2% | 86.3% | 62.3% | 36.0% |
| word_unigram | 49.6% | 49.7% | 83.7% | 15.5% |
| word_bigram | 51.4% | 58.4% | 58.7% | 44.1% |
| word_trigram | 51.4% | 58.4% | 52.5% | 50.3% |
| morphological_sequence | 53.1% | 75.8% | 40.9% | 65.2% |
| adjacent_agreement | 53.8% | 32.3% | 46.0% | 61.5% |
| marginal_agreement | 57.1% | 36.6% | 92.4% | 21.7% |
| morphology_coverage | 50.0% | 0.0% | 93.8% | 6.2% |

Balanced accuracy averages valid acceptance and corrupt rejection, so an always-valid classifier gets 50%. Pair accuracy compares each corrupted sentence directly with its own original; ties fail. These are different tasks. A scorer can detect a small deterioration within a pair while failing to provide a portable grammaticality threshold across different sentences.

Nonnegative combination: balanced-accuracy 95% interval **54.8–60.8%**, pair-ranking interval **74.6–87.7%**. Signed combination: **54.7–60.7%** and **73.9–86.3%**. Intervals use 1,000 sentence-cluster bootstrap resamples, retaining correlated variants together. Neither combination improves the observed neural pair-ranking rate of 139/161 (86.3%); this is a descriptive comparison, not a significance claim.

## Error families

| Test family | Cases | Nonnegative correct | Signed correct |
|---|---:|---:|---:|
| adjective_case | 40 | 45.0% | 47.5% |
| adjective_gender | 17 | 35.3% | 35.3% |
| adjective_number | 10 | 60.0% | 60.0% |
| lexical_control | 105 | 90.5% | 91.4% |
| order_control | 64 | 90.6% | 87.5% |
| original | 107 | 90.7% | 87.9% |
| preposition_case | 44 | 11.4% | 13.6% |
| subject_number | 50 | 10.0% | 10.0% |

The nonnegative combination accepted 45/50 subject-number errors and 39/44 preposition-case errors. It also rejected 10/105 morphology-preserving noun substitutions and 6/64 local order controls. This is not a dependable grammar discriminator. On 112 corrupted pairs whose edited lemma was absent from fitting corruptions, its pair accuracy was 83.9%; the main problem is not eliminated by this lexical holdout.

## Selected weights

Coefficients below act on fitting-standardized features. Intercept and thresholds are in the same linear-score units.

| Feature | Nonnegative | Signed |
|---|---:|---:|
| neural_mean_piece | 0.00000 | 0.04244 |
| neural_piece_sum | 0.00000 | -0.05274 |
| word_unigram | 0.00000 | 0.01741 |
| word_bigram | 0.00000 | -0.00119 |
| word_trigram | 0.00000 | -0.04220 |
| morphological_sequence | 0.20078 | 0.18583 |
| adjacent_agreement | 0.00000 | 0.00344 |
| marginal_agreement | 0.28135 | 0.26773 |
| morphology_coverage | 0.18237 | 0.18332 |

nonnegative_combination: intercept 0.01555, threshold -0.18945, ridge penalty 0.001.

signed_combination: intercept 0.01512, threshold -0.19944, ridge penalty 0.01.

## Interpretation and limits

The available proxies contain some sensitivity to local damage, but weighting them does not establish reliable sentence grammaticality. The absolute sentence scores mix grammatical evidence with lexical familiarity, context and analysis ambiguity. The experiment does not isolate which of those causes dominates. It does show that longer cipher search cannot repair this discriminator itself.

This does **not** rule out all weighted objectives, nonlinear combinations, pairwise-trained objectives or explicit dependency inference. Both tested combinations were trained for absolute classification. A pairwise loss is a reasonable separate next experiment, evaluated on newly reserved works and mutation families; a grammar-aware representation may be needed for stronger gains.

Labels are automatically generated violations of the original annotated dependency, not expert-certified proofs that every alternative Latin parse is impossible. Positive noun substitutions preserve intended morphology but may change selectional meaning; local swaps are narrow word-order controls. Annotation errors, poetic ellipsis and alternate parses remain possible. Test families with only 10 or 17 cases cannot support broad reliability claims. Neural pretraining exposure to these classical works is unknown; author separation applies to combination fitting/calibration, not guaranteed model pretraining separation. Lowercasing, u/v normalization and punctuation removal constrain the scope to the current pipeline representation.

The frozen reliability gate required at least 95% balanced and pair accuracy, at least 90% correctness in every family, at least 95% acceptance of each valid-control family, and at least 90% lower bootstrap bounds. Both combinations fail by large margins.

## Artifacts and reproduction

[Sentence examples](../experiments/results/latin-sentence-proxy-calibration/examples.md), [complete report](../experiments/results/latin-sentence-proxy-calibration/report.json), [weights and thresholds](../experiments/results/latin-sentence-proxy-calibration/selection.json), [mutation audit](../experiments/results/latin-sentence-proxy-calibration/dataset-audit.json). Manifests freeze inputs, resources and source hashes; raw features and every test prediction are saved.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_proxy_cases
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_proxy_combination
PYTHONPATH=src:. .venv/bin/python -m benchmarks.latin_sentence_proxy_combination --validate
```

Generation/scoring refuse an existing or changed frozen protocol; use `--validate` to replay the existing scoring run. Validation recomputes all nine features, fitting, calibration, predictions and bootstrap results. Full replay passed: all features, selected weights/thresholds and the complete downstream report reproduced, with raw-feature tolerance 1e-6. Independent audits passed for source separation, single edits, retained lexemes/other inflections and held-out corruption families. Focused unit/related tests: 16 passed.

## Sources and attribution

Sentences and annotations: [Universal Dependencies Latin Perseus](https://universaldependencies.org/treebanks/la_perseus/), pinned [release r2.17](https://github.com/UniversalDependencies/UD_Latin-Perseus/tree/r2.17). Corpus license: CC BY-NC-SA 2.5; its original README and LICENSE are retained under `data/latin-grammar-benchmark/perseus-r2.17/`, and the license is copied with derived artifacts. Original annotator attribution is in that README.

Mutation rules correspond to [Latin agreement](https://dcc.dickinson.edu/grammar/latin/agreement) and [preposition case government](https://www.nationalarchives.gov.uk/latin/stage-1-latin/resources/stage-1-latin-grammar-resource/prepositions/).
