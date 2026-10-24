# Oracle morphology and inferred grammar: lexical recovery test

Correct morphological information substantially narrows the candidate dictionary, but the tested local grammar predictors do not recover that benefit. With supplied function-word mappings, training-frequency ranking finds the original word in the top ten for 3/22 lexical types. Restricting candidates to those sharing a complete analysis with the original raises this to 17/22. Inferred grammar leaves frequency retrieval at 3/22 or worse. This supports investigating grammatical constraints, but does not establish a decoder or a successful method for inferring them.

## Oracle diagnostic

The experiment reuses the previously explored 36 repeated development types in the 2,022-word Caesar excerpt and the 100,000-form dictionary. Of these, 28 have known content morphology and 22 remain after excluding the frozen copula/glue list. Function mappings are supplied correctly. Candidate forms already reserved by those mappings are excluded. The unfiltered known-content pool contains 96,823 forms.

The model scores are the unchanged base model's saved function-only predictions, pooled across every occurrence. Candidate selection uses the original word's dictionary analysis set; it does not supply its spelling to the scorer, add its form to the dictionary, or change the neural predictions. Each analysis retains its joint features, so case and number from different alternatives cannot be combined into an invented analysis.

Exact lexical identity is the primary result. Morphological compatibility is supplementary: an oracle filter can make that metric high by construction. Unknown gold morphology remains unknown and is excluded from the known-lexical denominator.

| Supplied information | Median candidate pool | Neural exact top-1 | Neural exact top-10 | Frequency exact top-1 | Frequency exact top-10 |
|---|---:|---:|---:|---:|---:|
| None | 96,823 | 2/22 | 3/22 | 0/22 | 3/22 |
| POS alternatives | 7,247 | 2/22 | 4/22 | 0/22 | 3/22 |
| POS, case and number alternatives | 1,970 | 2/22 | 5/22 | 2/22 | 9/22 |
| Any shared full analysis | 565.5 | 4/22 | 8/22 | 4/22 | 17/22 |
| Identical complete ambiguity profile | 48.5 | 9/22 | 14/22 | 15/22 | 20/22 |

A full analysis includes POS, its available morphological features and enclitic. The intersection filter keeps a candidate if at least one of its analyses matches one of the original's analyses. It does not require equality of the whole ambiguity profile. Uniform random ordering within the full-analysis pools would recover approximately 0.83 of the 22 original words in the top ten, versus the frequency baseline's 17. Pools range from 38 to 1,662 candidates, and all 22 originals remain eligible.

The identical-profile control is stronger and less realistic: a word's entire dictionary ambiguity pattern can act as a lexical fingerprint. Its pools range from one to 463 words, and chance top-ten recovery already reaches an expected 8.41/22. Morphological compatibility reaches 22/22 by construction in that control. It must not be presented as successful grammatical inference.

These supplied analyses are dictionary possibilities for the original surface form, not context-disambiguated token tags, dependency links or grammatical roles. The test establishes the value of restricting candidates by morphology; it does not test a full syntactic parser or neighbouring agreement constraints.

## Hiding the grammar

Two small context classifiers were trained from scratch on the disjoint training books, Gallic V–VII and Civil III. The existing whole-segment split contains 34,975 training and 4,371 validation tokens. Known lexical tokens produce 20,416 training examples and 2,534 validation examples. No development answer is used for training or checkpoint selection.

Inputs contain 17 relative positions: supplied function-word spellings, boundaries, anonymous hidden words and a distinct marker for occurrences of the hidden target. Unknown spelling, target length and lemma identity are absent. The function vocabulary has 404 forms from the training split. Positional embeddings are summed into a 64-dimensional hidden layer and predict a grammatical-analysis distribution.

One classifier predicts 628 complete dictionary analysis states. The other predicts 43 joint POS/case/number states. Training labels admit every dictionary analysis for the original word; loss rewards probability assigned to any admissible analysis. This is weak supervision, not a corpus of correct token parses. Training samples word types uniformly through inverse-frequency weighting and runs 1,000 batches of 64. Checkpoints are selected by ambiguity-aware loss on training-book validation segments; the full model selects step 600 and the coarse model step 700.

Validation plausible-analysis top-1 reaches 5.27% for full states and 23.18% for coarse states, weighted equally across types. On the 22 lexical development types, the predicted top analysis belongs to the original's possible analyses for only 2/22 full-state types and 3/22 coarse-state types. Context-free training analysis priors reach 0/22 and 4/22 respectively. These counts do not measure contextually correct syntactic roles.

Candidate grammar scores average the log probability mass of their allowed analyses across occurrences, permitting different occurrences of a type to use different analyses. Fixed weights one and three combine those scores with the unchanged neural or frequency ranking. A hard-filter condition instead retains candidates admitting the highest mean-probability analysis. Neither weights nor checkpoint are selected by development retrieval.

| Grammar source, weight one | Neural exact top-1 | Neural exact top-10 | Frequency exact top-1 | Frequency exact top-10 |
|---|---:|---:|---:|---:|
| None | 2/22 | 3/22 | 0/22 | 3/22 |
| Inferred full states | 2/22 | 4/22 | 0/22 | 3/22 |
| Context-free full-state prior | 2/22 | 4/22 | 0/22 | 2/22 |
| Inferred POS/case/number | 2/22 | 3/22 | 0/22 | 2/22 |
| Context-free POS/case/number prior | 2/22 | 3/22 | 0/22 | 2/22 |

The full model's one-type neural top-ten gain is matched by the context-free prior, so it does not demonstrate a context-inference benefit. Weight three generally worsens recovery. Hard inferred filtering reaches only 2/22 exact top-ten for both rankers with full states; coarse hard filtering reaches 1/22 for neural and zero for frequency. Committing to an incorrect grammatical tag excludes the original word.

Coarse-run supplementary compatibility uses projected profiles and is not directly comparable with strict full-profile compatibility. Only exact identity is compared across these runs.

## What this changes

Morphology is useful information: even case/number alternatives considerably improve frequency-ranked proposals when supplied correctly. The inference gap is substantial. A local classifier using function-word context does not recover enough of that information, and stronger commitment to its guesses harms retrieval.

This makes joint inference with explicit agreement and preposition–case constraints a more concrete next experiment than another long search under the existing objective. Such a system would retain several grammatical hypotheses and test relationships between unknown words rather than assign each type one local classifier prediction. That system is not implemented here, and these results do not guarantee that it will work.

The sample is small and previously explored, only one training seed is used, and pretrained exposure to Caesar remains unknown for the reused neural scores. This is synthetic word substitution on Caesar's Latin text, not a letter-shift cipher. Exact lexical recovery is stricter than the user's tolerated morphological substitutions; the separate compatibility controls prevent mistaking oracle filtering for inferred recovery. The final test remains unscored.

## Verification and artifacts

The focused suite passes 95 tests, including preservation of correlated analyses, empty-profile handling, full-feature/enclitic preservation, hidden-spelling exclusion and ambiguity-aware loss. Oracle replay regenerates all filters, candidate rankings and reports. Predictor replay regenerates context predictions, soft/hard rankings and reports using the selected model files; it does not retrain the models. Frozen manifests record source/model/score hashes and input examples. Earlier experiments and models remain intact.

Artifacts are under `experiments/results/word-mapping/grammar-oracle-calibration/`, `grammar-inference-calibration/` and `grammar-inference-coarse-calibration/`.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_grammar_oracle
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_grammar_oracle --validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_grammar_inference
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_grammar_inference --validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_grammar_inference_coarse
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_grammar_inference_coarse --validate
```

Generation rejects an existing manifest. Replays verify saved protocols and selected model hashes before regenerating results.
