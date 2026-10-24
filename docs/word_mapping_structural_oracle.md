# Morphology-tolerant oracle diagnostic

The proposed relaxation is feasible as an evaluation baseline. On the 32,004-token development passage, a globally consistent, injective dictionary changes 41.14% of tokens and receives zero morphology error. This is an explicit plaintext-derived oracle, not an objective usable for blind decoding.

## Definition

For each form, retain the full set of Whitaker part-of-speech, inflection-feature and enclitic signatures, dropping lemma identity. Content substitutions receive zero error only when these signature sets are identical. Any form with a preposition, conjunction, pronoun, numeral, interjection or unsupported POS analysis is fixed to its original spelling. Unknown unchanged forms are compatible; unknown substitutions remain unresolved, never automatically correct. The permissive alternative accepts any shared signature.

These are morphology constraints, not a syntactic parser. They do not check dependencies, verb argument structure, auxiliary status, selectional preferences or meaning. Cached analyses are ambiguous and can be wrong; grammatical gender is conservatively held fixed. The rule can therefore reject valid paraphrases and accept invalid sentences. “Zero error” means zero error under this definition only.

## Controlled results

Whole dictionaries are changed consistently across every occurrence, preserving injectivity. Content words with identical complete profiles are rotated within groups. Broken controls swap content words with disjoint profiles, or rotate fixed function-word forms. All five nested development passages are tested; no final test is scored.

| Words | Changed tokens under compatible swaps | Morphology error |
|---:|---:|---:|
| 503 | 24.85% | 0% |
| 2,022 | 30.17% | 0% |
| 8,024 | 36.28% | 0% |
| 16,021 | 38.91% | 0% |
| 32,004 | 41.14% | 0% |

At the largest width, 3,025 content types can be rotated. The broken-feature control produces 48.22% token error and the changed-function-word control 29.30%. Examples of morphology-preserving replacements include `discessisset → misisset` and `reduxit → putauit`; compatibility does not imply preserved meaning or argument structure.

## Earlier search results under the relaxed measure

Reevaluate all 20 perfect-start search winners from the zero-corruption experiment, without running new searches. At 32,004 tokens, greedy winners average 82.80% exact accuracy, 82.85% strict-profile compatibility, 5.35% definite error and 11.80% unresolved substitutions. Allowing any shared analysis lowers definite error only to 5.25%. Annealing winners have 9.85% definite error and 20.49% unresolved substitutions under the strict rule.

Thus exact-match accuracy was too narrow as the sole success measure. However, those earlier winners are not simply equivalent content-word dictionaries under this relaxation. Missing morphology prevents a complete verdict on their grammatical quality.

## Reproduction and next step

Run `.venv/bin/python -m benchmarks.word_mapping_structural_oracle`. The report in `experiments/results/word-mapping/structural-oracle-calibration/report.json` records code/input hashes, compatible dictionaries, controls and retrospective evaluations. Deterministic replay produces an identical report. Two unit tests check ambiguity, unknown handling, function-word protection, token weighting and enclitics.

Next, build a scorer that infers grammatical structure without plaintext and evaluate it against this oracle. A search that optimizes the plaintext-derived oracle would only demonstrate engineering correctness. Before a long blind run, require the independent scorer to prefer compatible dictionaries over broken controls. A dependency-aware version is needed to address the user's stronger claim that the sentence's composition is correct.
