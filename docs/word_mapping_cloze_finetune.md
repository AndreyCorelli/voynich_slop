# Repeated-word masking fine-tuning and context curve

A 200-update partial fine-tuning pilot lowered held-out masking loss but did not produce a useful retrieval improvement. With function-word anchors alone, lexical compatible top-10 retrieval increased from 3/22 to 4/22, while top-1 fell from 2/22 to zero. With half the other content mappings supplied, top-10 fell from 12/22 to 7/22. Keep the original model for further experiments.

## Setup

The original pinned Latin RoBERTa assets remain intact. The final two encoder blocks and LM-head dense/layer-normalization layers were trained: 14,767,872 of 124,697,433 parameters. Embeddings, the tied vocabulary decoder, decoder bias and lower encoder blocks were frozen. Training used CPU, seed 731, AdamW, a maximum learning rate of 2e-5, warmup and decay, gradient clipping, normal training dropout, 200 batches of eight examples, and a 12-word radius.

Only the existing disjoint training books were used: Gallic V–VII and Civil III. A deterministic whole-segment split assigned 34,975 tokens to training and 4,371 to validation. Targets were sampled uniformly from known lexical content types, excluding the copula/glue list frozen before this experiment. Every occurrence of a target in its window was masked. Other unknown words occupied one mask; function words and a random fraction of local content types were visible. Fractions were 0%, 10%, 25% and 50%. Original target pieces served as labels; examples were weighted equally despite different piece counts. Training used the correct target piece count, while retrieval tested every candidate piece-count hypothesis.

The checkpoint was selected solely by mean per-example piece cross entropy on 128 fixed examples from the training-book validation split, including the unchanged model as a step-zero option. Validation loss fell from 10.0375 to 9.0334; step 200 was selected. No development retrieval metric selected the checkpoint.

## Retrieval results

The curve reused the previously explored 36 repeated development types in the 2,022-word excerpt, with the same 100,000-form dictionary. Of these, 28 have known content morphology and 22 remain after excluding grammatical glue. Results below use these 22 lexical types and candidates with known content morphology. Compatibility is the existing strict morphological oracle, including exact identity; it does not establish grammatical sentences or recovered meaning.

Function mappings were supplied correctly. For each target, a seeded nested ordering of the other unanchored types selected the content scaffold. The target was excluded before selection and remained hidden in all its occurrences, even at 100%. Correct visible forms were removed from candidate rankings to reserve those mappings; the same restriction applied to frequency and both neural models. All target occurrences were pooled.

| Other content mappings supplied | Original top-1 | Tuned top-1 | Original top-10 | Tuned top-10 | Frequency top-10 |
|---|---:|---:|---:|---:|---:|
| 0% | 2/22 | 0/22 | 3/22 | 4/22 | 3/22 |
| 10% | 2/22 | 0/22 | 4/22 | 4/22 | 3/22 |
| 25% | 3/22 | 3/22 | 6/22 | 5/22 | 3/22 |
| 50% | 8/22 | 4/22 | 12/22 | 7/22 | 3/22 |
| 100% | 12/22 | 10/22 | 14/22 | 12/22 | 7/22 |

These are counts of types with a compatible candidate at the indicated rank, not token accuracy or a complete dictionary assignment. The 100% control still hides the evaluated target. Its frequency result also benefits from removing forms reserved by the supplied mappings. This candidate restriction explains differences from the earlier unrestricted decoded-context control.

For all 28 known content types, function-only compatible top-10 retrieval fell from 9/28 to 4/28 after tuning. The small lexical top-10 gain therefore accompanied a substantial loss on grammatical glue. At 50% context the corresponding counts were 18/28 and 11/28.

## Interpretation

The context curve supports using this model once substantial content context is already correct. It does not show a reliable way to bootstrap that context. Lower masking loss did not translate into better dictionary retrieval: the loss uses correct piece length and original spelling, whereas retrieval compares all lengths and permits morphological alternatives. Training also sampled local scaffolds rather than a globally shared cipher mapping.

This is a small partial-fine-tuning pilot on 1,600 sampled examples, not evidence that all fine-tuning approaches fail. The evaluation sample is small and previously explored. Pretraining exposure to Caesar is unknown, and the reserved final test remains unscored. Oracle content mappings are supplied answers; their benefits cannot be counted as search recovery. Per-target scaffolds vary, so the curve is not a single simultaneous global solution.

A further model experiment should address unknown-type identity and train against candidate-ranking errors across repeated occurrences, rather than simply extend this run. All non-target unknown types currently look identical to the network. A longer optimization search using this tuned scorer is not supported by these results.

## Artifacts and verification

Artifacts live in `experiments/results/word-mapping/cloze-finetune-calibration/`: the protocol, exact sampled training/validation examples, loss history, selected model, candidate score arrays, per-type rankings and summary report. The implementation is isolated from the frozen earlier benchmarks. The focused test suite passes 85 tests, including scaffold nesting, target exclusion and equal example weighting. Independent validation checks the segment split and masked labels, and compares optimized candidate scores with the model's public full-forward outputs at all five piece lengths and context fractions. Full neural replay checks score arrays within 1e-6 and reproduces every saved case and report.

```sh
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_cloze_finetune
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_cloze_finetune --evaluate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_cloze_finetune --validate
PYTHONPATH=src:. .venv/bin/python -m benchmarks.word_mapping_cloze_finetune_check
```

Training rejects an existing completed run. Evaluation resumes saved cases; validation recomputes every neural score. The original model is retained, and the tuned model is stored separately.

The subsequent [repeat-aware input experiment](word_mapping_repeat_identity.md)
implements anonymous hidden-type embeddings and matched training, including
repetition-enriched sampling. It finds no reliable identity-specific retrieval
gain under broken-identity and fresh-permutation controls.
