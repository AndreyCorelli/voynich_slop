# Repeated-word neural cloze experiment

Pooling repeated occurrences provides some useful proposals with correct function-word anchors. It does not produce a reliable decoding: most gains concern copular or grammatical words, and lexical-content top-10 coverage matches the frequency baseline in a post-hoc sensitivity analysis.

## Protocol

Use the 2,022-word Caesar development passage from the widening study. Select 36 repeated, unanchored ciphertext types solely from public counts: 18 highest-frequency types plus 18 seeded random remaining types occurring at least three times. They account for 235 occurrences. Selection does not use the hidden words, morphological roles or candidate availability.

The candidate bank is the unchanged 100,000-form dictionary. No true word is appended. All candidates tokenize successfully, with one through five subword pieces. The pinned offline `pstroe/roberta-base-latin-cased` model is reused in CPU float32 inference mode, four threads, batch size 16. Its pretraining exposure to Caesar is unknown, so this is a controlled retrieval experiment, not proof of general cipher recovery.

For every occurrence, take a window of at most 12 original words on either side, preserving segment boundaries. Visible words are tokenized normally. Each hidden non-target word becomes one mask. For each candidate piece-count hypothesis, every occurrence of the target in the window becomes that many masks. Target spelling is never placed into the context. Only the center occurrence's candidate labels are scored; pooling then combines every occurrence of the type. Candidate scores are mean log probability per piece and per occurrence, not joint sequence probabilities.

Compare:

- **No anchors:** all surrounding words masked.
- **Function only:** the previous experiment's correct closed-class anchors visible; all other types masked.
- **Decoded context:** every non-target word decoded correctly; every occurrence of the target remains masked. This is an explicitly oracle positive control.
- **Training frequency:** frequencies from the disjoint 39,346-word training split.

The first occurrence alone is also scored to isolate the benefit of pooling. Independently generated morphology defines compatibility, using exactly the previous full-analysis-set criterion. Of the 36 targets, 28 have known content analyses and eight have unknown analyses; 32 exact gold words are in the dictionary. The known-content subset has full gold candidate coverage.

## Retrieval results

The first table filters the bank to candidates with known content analyses, without revealing the target's correct role or features. Counts are over the same 28 known-content types. This filter is an additional favorable assumption; unrestricted rankings are also preserved.

| Ranking | Compatible top 1 | Compatible in top 10 |
|---|---:|---:|
| Training frequency | 1/28 | 7/28 |
| No anchors, pooled | 1/28 | 5/28 |
| Function words, first occurrence | 3/28 | 8/28 |
| Function words, all occurrences | 4/28 | 9/28 |
| Decoded context, all occurrences | 15/28 | 19/28 |

Without the content filter, function-only pooled retrieval places compatible forms in the top 10 for 7/28 types; the frequency and no-anchor baselines obtain 0/28 and 3/28 respectively. These unrestricted rankings can propose function forms already used by anchors, so they are proposal diagnostics rather than valid injective dictionary assignments.

Most improvement is in the frequent half: function-only pooled recall is 7/14 there versus 5/14 for frequency ranking. In the random half, both methods retrieve 2/14; pooling retrieves fewer than the first-occurrence result of 3/14. The sample is small and no independent replication establishes a general advantage.

The function-only top-10 hits are `non`, `esse`, `est`, `ita`, `erat`, `partem`, `facere`, `sunt`, and `tempore`. The previous morphology convention treats adverbs and verbs as content, including grammatical negatives and copular forms. A **post-hoc sensitivity** excludes a fixed list of such glue/copula words. Among the remaining 22 types, pooled cloze and frequency each retrieve 3/22 in the top 10, with three wins and three losses against each other. Fully decoded context retrieves 13/22. This sensitivity is interpretation of the completed experiment, not a changed scorer or a new blinded test.

## Joint proposals

Use the frozen score arrays to enforce the one-to-one fixture's dictionary constraint. Remove every supplied anchor form from the candidate bank, then solve a maximum-weight bipartite assignment for the 36 selected types. Weights multiply pooled mean-piece scores by occurrence count. All selected types receive distinct forms, consistently across their occurrences; other hidden types remain unresolved. This optimizes a fixed cloze proxy, not scores recomputed after filling other words.

| Ranking source | Compatible joint predictions, known types | Compatible joint predictions, lexical sensitivity |
|---|---:|---:|
| Frequency | 1/28 | 0/22 |
| No anchors | 0/28 | 0/22 |
| Function context | 5/28 | 2/22 |
| Fully decoded context | 17/28 | 11/22 |

Thus uniqueness helps a little, but does not rescue the incomplete context. The full-context control indicates that useful predictions depend strongly on already-decoded content. A complete Caesar crack has not been attempted here.

## Verification and artifacts

Full neural replay reproduces every saved candidate score and rank. An independent check uses the model's public full-vocabulary forward pass for one candidate at each of the five piece lengths, across all occurrences of a target. It agrees with the optimized scoring path within 3×10⁻⁷, below the 10⁻⁴ audit tolerance. Joint assignments also replay identically. Unit tests check target-spelling exclusion, masking of repeated types, hypothetical lengths, special-token exclusions, per-piece normalization, and occurrence pooling. The focused suite passes 163 tests.

Artifacts under `experiments/results/word-mapping/repeated-cloze-calibration/` contain frozen protocol/model/source hashes, per-case rankings, complete candidate score arrays, replay validations, paired analyses and joint assignments. See [candidate examples](../experiments/results/word-mapping/repeated-cloze-calibration/examples.md) and [the first 100 words with the actual partial assignment](../experiments/results/word-mapping/repeated-cloze-calibration/partial-first-100.md). Supplied answers, proposed words and unresolved ciphertext are explicitly distinguished.

```sh
.venv/bin/python -m benchmarks.word_mapping_repeated_cloze
.venv/bin/python -m benchmarks.word_mapping_repeated_cloze --validate
.venv/bin/python -m benchmarks.word_mapping_repeated_cloze_analysis
.venv/bin/python -m benchmarks.word_mapping_repeated_cloze_joint
.venv/bin/python -m benchmarks.word_mapping_repeated_cloze_forward_check
```

The main runner supports `--resume`; new generation rejects an existing manifest. The final test remains unscored.

## Implication

This is a modest improvement in proposal quality, not the missing complete solver. Before integrating a large neural search, train or calibrate for the much heavier masking used here, and repeat the test on independently held-out text. Content anchors or grammatical analyses could be studied as controlled intermediate scaffolds, but successes with them must remain distinguished from inferred mappings. Exact content identity also need not be identifiable from function-word context alone.

A subsequent [partial fine-tuning and context-curve experiment](word_mapping_cloze_finetune.md)
lowered training-book validation loss but did not improve retrieval consistently.
The original model remains preferable; its lexical top-10 coverage rises from
3/22 with function-only context to 12/22 when half the content mappings are supplied.
