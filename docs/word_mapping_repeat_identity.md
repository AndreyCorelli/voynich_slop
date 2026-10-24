# Repeat-aware inputs: matched training and ablations

A local repeat-aware input representation is implemented and tested against matched collapsed-mask training. It does not show a consistent retrieval advantage. This is a test of one small adapter design, not a rejection of all models that represent repeated words.

## Representation

Each unknown word type in a 25-word window receives one of 32 anonymous identifiers. Repeated occurrences share an identifier; different types receive different identifiers. A learned 768-dimensional identifier embedding is added to the pretrained word embedding at every masked piece. Visible words, padding and boundary tokens receive a fixed zero identifier embedding. Anonymous assignments are randomized per training example and per evaluation window. Hidden spellings never enter input token IDs or identifier embeddings.

The evaluated target remains masked at every occurrence in its window. Candidate scoring still tests every hypothesized subword length, scores all 100,000 dictionary forms, and pools predictions across every occurrence in the excerpt. Target spelling is used only for training labels and evaluation. Identifiers describe local equality; they do not provide memory across distant windows or optimize a shared dictionary across the whole passage.

Two training arms start from the same pinned Latin model and use identical text inputs, masks, target labels, sampling and dropout seeds. The repeat-aware arm adds anonymous type embeddings. The collapsed arm assigns zero embeddings to every hidden word. The added embedding table has 25,344 parameters. Both arms train the upper two encoder blocks and LM-head dense/layer-normalization layers; pretrained vocabulary embeddings, lower encoder parameters and the tied decoder remain frozen.

## Training

The disjoint corpus and whole-segment split are the same as in the [previous fine-tuning pilot](word_mapping_cloze_finetune.md): Gallic V–VII and Civil III, 34,975 training tokens and 4,371 validation tokens. Each arm receives 3,200 examples over 400 updates, batch size eight, learning rate up to 2e-5, warmup/decay and clipping. Checkpoints are selected by 128 fixed training-book validation examples, including step zero, before development retrieval.

The initial ordinary sampler exposed an important limitation: only 4/3,200 training examples repeated the target in its window, and 193 repeated another hidden type. Its repeat-aware top-10 lexical results were 1/22, 3/22 and 6/22 at 0%, 25% and 50% supplied content, versus 2/22, 3/22 and 6/22 for collapsed training.

A second, separately retained experiment uses a balanced sampler: one third repeated hidden targets, one third other repeated hidden types, one third ordinary lexical targets. A repeated-other witness remains hidden when additional context is supplied. Both arms receive the same scaffold. This produced 1,076 repeated-target and 1,264 repeated-other training windows; validation contained 43 and 51 respectively. Categories can overlap in actual repetition. This intentional enrichment changes the training distribution; validation losses cannot be compared directly with the ordinary sampler.

In the enriched run, validation loss fell from 9.5563 to 8.2487 for repeat-aware training and from 9.5734 to 8.2115 for collapsed training. Both selected update 400. Loss reduction alone is not evidence of dictionary recovery.

## Development retrieval

The benchmark reuses the previously explored 36 repeated types in the 2,022-word Caesar excerpt. There are 28 known content types and 22 lexical types after the frozen copula/glue exclusion. All tables below use strict morphological compatibility, content candidates and these 22 lexical types. This is synthetic word substitution on Caesar's Latin text, not a letter-shift cipher.

Correct function mappings are supplied throughout. Additional content fractions select a seeded nested set of other unanchored types, excluding the evaluated target before selection. Supplied word forms are reserved and removed from candidate rankings. These oracle mappings are answers given to the model, not inferred recovery.

| Other content supplied | Original model top-10 | Enriched collapsed top-10 | Enriched repeat-aware top-10 | Broken-identity top-10 |
|---|---:|---:|---:|---:|
| 0% | 3/22 | 4/22 | 4/22 | 4/22 |
| 25% | 6/22 | 7/22 | 8/22 (7/22 under new permutations) | 7/22 |
| 50% | 12/22 | 11/22 | 11/22 | 11/22 |

The matched models also tie on compatible top-1 at all three levels: 2/22, 3/22 and 7/22. At 50%, exact top-10 is 8/22 for repeat-aware inputs versus 9/22 for collapsed and broken inputs. The original model reaches 8/22 compatible top-1 at that level.

The broken control uses the trained repeat-aware model but randomizes identities independently for each hidden occurrence, keeping an individual word's hypothesized pieces together. It preserves the marginal embedding signal while destroying reliable cross-occurrence equality. Accidental identifier collisions remain possible. The identical aggregate results at 0% and 50% provide no evidence that the model is using repetition to improve retrieval there.

At 25% content, the default repeat-aware identifiers yielded 8/22, but two fresh identifier permutations both yielded 7/22, matching collapsed training and broken identities. Top-1 stayed 3/22 in all conditions. Thus the one-type top-10 advantage is sensitive to anonymous numbering and does not establish a robust repetition benefit. These permutation seeds change inputs to the same trained model; they are not independent training seeds. The extra ablation stores 108 complete candidate arrays and per-type rankings under the enriched run’s `ablation/` directory.

## Verification and limits

The focused unit suite passes 90 tests. Tests cover identity equality, distinction between hidden types, preservation of the ordinary mask inputs, zero embeddings for visible/padded tokens, target exclusion, randomization, renaming of anonymous relations and matching of the enriched samples. Independent validation regenerates every training/validation example, verifies identical text inputs across arms and confirms that only the intended pretrained parameters changed. It regenerates all 288 saved case rankings per main experiment, replays eight complete candidate-score arrays, and compares 15 candidate scores against the model's public full-forward outputs. This is sampled neural replay plus complete ranking regeneration, not full neural replay of every case.

Original models, prior experiments and their frozen source files remain unchanged. The ordinary and enriched runs are stored separately under `experiments/results/word-mapping/repeat-identity-calibration/` and `experiments/results/word-mapping/repeat-identity-enriched-calibration/`, with manifests, sampled examples, selected models/adapters, full candidate arrays, per-type results and independent validation reports.

The excerpt has been explored before, only one training seed is used, and pretrained exposure to Caesar is unknown. Morphological compatibility does not establish sentence grammar or meaning. The reserved final test is unscored. This experiment does not implement joint dictionary optimization or candidate-ranking training.

A longer search with this adapter is not supported by the results. If continuing, the next separate experiment should train directly to distinguish correct shared mappings from plausible wrong alternatives across multiple occurrences, with controlled corruption tests before search integration. Merely supplying identifiers and continuing masked-word training has not yielded a reliable bootstrap decoder here.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_repeat_identity
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_repeat_identity_enriched
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_repeat_identity_check --ordinary
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_repeat_identity_check
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_repeat_identity_ablation
```

Main generation rejects an existing run. `--evaluate` resumes saved retrieval cases; `--validate` recomputes every main neural score and compares cases and reports. The enriched runner also checks its sampling manifest. The independent checker provides the more limited replay coverage described above.
