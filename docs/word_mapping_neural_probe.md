# Longer-context Latin model scorer probe

The longer-context model corrects many of the strongest saved n-gram
counterexamples, but still misranks a substantial minority. This probe evaluates
the scorer without changing candidate vocabulary, running searches or scoring
the final test.

## Model and reproduction

Install optional inference dependencies and explicitly download the pinned model:

```sh
uv sync --extra word-mapping --extra word-mapping-neural
HF_HOME=.cache/huggingface HF_HUB_DISABLE_IMPLICIT_TOKEN=1 HF_HUB_DISABLE_XET=1 \
  .venv/bin/python -m benchmarks.word_mapping_neural_model
.venv/bin/python -m benchmarks.word_mapping_neural_probe
.venv/bin/python -m benchmarks.word_mapping_neural_probe --validate
```

Inference is offline and uses a safetensors copy under `data/models/latin-roberta/`.
The download command is separate and refuses to overwrite an installed snapshot.
Partial downloads can be continued by rerunning that command. Probe `--resume`
skips completed rows with identical model assets, inputs, code and configuration.

The model is Phillip Ströbel's
[Latin RoBERTa](https://huggingface.co/pstroe/roberta-base-latin-cased), pinned to
revision `0f5e1a95f76fafac3002f8349fa5c6e41129ed6f`. Its model card describes
pretraining on Latin CC100 text. Caesar exposure is unknown and plausible;
this is a scorer probe, not a clean held-out generalization result. No fine-tuning
uses these passages. The original final-test split is never loaded by this runner.

The published `tokenizer_config.json` contains a tokenizer backend dump rather
than a standard Transformers configuration. The installer reconstructs a standard
fast RoBERTa tokenizer from its published vocabulary and merges, with prefix
spaces and BOS/EOS tokens. The original files and adapted inference files are
retained and checksummed. The architecture uses built-in Transformers code;
remote model code is disabled. Conversion uses the restricted weights-only loader.

Saved dependencies include PyTorch 2.14.1, Transformers 4.57.6, tokenizers 0.22.2
and safetensors 0.8.0. The experiment uses CPU float32, four threads and batches
of sixteen masked words. Model files, package versions, source code and probe
selection identities are recorded in the manifest.

## Scores and controlled context comparison

The approach follows the general idea of
[masked-language-model scoring](https://arxiv.org/abs/1910.14659), with a
whole-word masking variation. Every subword belonging to a target surface word
is masked simultaneously. This prevents other pieces of the same word from
revealing its spelling. The model predicts each original piece from the masked
context; piece log probabilities are summed for that word.

Two fixed aggregation rules are reported:

- **Word-masked sum:** sum every piece log probability over all surface words.
- **Word-normalized sum:** average piece log probabilities within each surface
  word, then sum those word means.

Both are heuristic masked scores, not normalized joint sentence probabilities.
The second reduces direct subword-count penalties, but neither eliminates all
tokenization bias. Each pair reports its subword-count change. BOS/EOS and pad
tokens are never prediction targets. Unknown tokens or overlong segments fail
instead of being silently scored or truncated.

The same model and aggregation rules are tested with all words in the scored
segment visible versus only two neighboring words on each side of the target.
Windows respect the existing segment boundaries. This compares longer versus
shorter context within the same neural model; it does not change n-gram order.

All words in every affected segment are rescored, including unchanged words
whose context changes. Unaffected segments cancel exactly because the objective
is additive over segments. Cached identical segments avoid repeated inference.
These are complete dictionary-wide replacements and swaps, not isolated cloze
predictions at just the changed word.

## Frozen probes

The source is the independently validated
[disjoint-book calibration](word_mapping_long_context.md). For each of four
cases and two n-gram profiles, the runner selects up to ten strongest improving
injective replacements and ten strongest improving swaps. Identical dictionaries
selected by both profiles are deduplicated within each case, retaining their
selection provenance. All alternatives preserve the declared one-to-one constraint.

There are 128 distinct probes: 34 from bundle 1, 29 from bundle 2, 31 from bundle 3
and 34 from the pooled case. They comprise 65 replacements and 63 swaps.
Every probe was selected because at least one original n-gram scorer preferred
it over truth. This is a directed error set, not an unbiased sample of possible
mutations. The pooled case overlaps the separate bundles, so results are correlated.

## Results

| Context | Aggregation | Truth preferred | Wrong preferred |
| --- | --- | ---: | ---: |
| Full segment | Word-masked sum | 94/128 (73.4%) | 34/128 |
| Two words each side | Word-masked sum | 85/128 (66.4%) | 43/128 |
| Full segment | Word-normalized sum | 95/128 (74.2%) | 33/128 |
| Two words each side | Word-normalized sum | 83/128 (64.8%) | 45/128 |

No scores tie within the declared tolerance. With word normalization, longer
context fixes sixteen short-context misrankings and introduces four reversals,
for a net improvement of twelve probes. The raw sum fixes eleven and introduces
two, for a net improvement of nine. Context helps under both predeclared rules;
this is descriptive evidence on the selected error set, not a significance claim.

Full-context word-normalized preference by case:

| Case | Truth preferred |
| --- | ---: |
| Bundle 1 | 23/34 |
| Bundle 2 | 25/29 |
| Bundle 3 | 19/31 |
| Pooled | 28/34 |

It prefers truth in 41/65 replacements and 54/63 swaps. One corrected replacement
changes `acriter` to `uenitur` in both `acriter utrimque usque ad uesperum pugnatum
est` and `acriter in eo loco pugnatum est`. The short-window normalized score
favors the wrong mapping by +5.12; full-segment context instead favors truth
with a wrong-minus-truth gap of -12.81. Other substitutions remain misranked,
including plausible alternatives requiring evidence outside the scored segment.

The neural scorer is a promising candidate for a bounded archive-reranking
experiment or shortlist evaluation. These results do not demonstrate dictionary
recovery from a bad initialization or validate replacing the annealing objective.
Thirty-three counterexamples remain under full-context word normalization.
Any search experiment should measure compute as well as mutation counts and
preserve the known pretraining-overlap caveat.

All 128 probe results were independently recomputed and validated offline.
All 105 focused tests pass. Tests verify complete subword masking, score agreement
with ordinary model inference, batch-size agreement, context-window boundaries,
no silent truncation, frozen selection/deduplication, resume and tamper rejection.
