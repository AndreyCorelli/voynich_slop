# Neighbor-quality diagnostic for neural proposals

This oracle-controlled development diagnostic tests whether a true word rises
in rank as its neighboring decoding improves. It follows the
[candidate-pool calibration](word_mapping_pool_size.md); it does not perform
search or measure recovered dictionaries.

## Frozen inputs and controls

Sample 24 ciphertext types from each of the three separate long-context
bundles, using a deterministic hash of the public fixture and type. Sample
selection does not depend on truth, frequency, model scores or earlier success.
Score every occurrence of each sampled type in its original affected segments.
The 72 sampled types have 91 token occurrences.

Each target gets the same training-derived alternative list under every
condition: the 16 most frequent training forms plus 16 seeded uniformly sampled
remaining forms. Append the true word when it is absent. This gives 32 or 33
options and guarantees gold coverage **only for this oracle diagnostic**. It
does not measure rank among all 12,327 training forms or constitute an available
proposal generator.

Create a seeded injective training-vocabulary dictionary with every type
incorrect. For each target, order other ciphertext types by a deterministic
hash, then correct nested prefixes covering 0%, 25%, 50%, 75% or 100% of those
types. These labels describe global neighbor-type correction; actual token
accuracy within scored segments is saved separately and can differ. Add a
sixth condition using the actual n-gram winner from the full-vocabulary,
matched-budget candidate-pool experiment. Truth supplies the controlled
corrections and the target word whose rank is measured.

Synthetic partly corrected dictionaries can contain collisions, and candidate
substitutions can use words assigned elsewhere. This deliberately isolates
context sensitivity; the controls are not valid injective search states or
predictions of constrained optimizer performance. The uniform wrong dictionary
is a different error distribution from the saved n-gram decoding, so both are
reported separately.

## Scores and masking

Replace all occurrences of the target ciphertext type with a candidate form,
then mask **all subword pieces of every such occurrence simultaneously**. Only
the target words' masked log scores are accumulated; all other words remain
visible. Thus a repeated target cannot reveal its spelling through another
occurrence. Candidate subword length remains observable through mask count.

Report both raw summed target log scores and the sum of mean-subword log scores
per target word. The latter is the primary neural metric. Neither is a
normalized probability over variable-length candidate words, and results
remain sensitive to tokenization and length. Model inputs are full affected
segments, with no truncation.

The n-gram comparator scores the entire affected decoded segments for each
candidate, including effects on neighboring n-gram factors. The training-count
baseline is context independent. These are distinct scoring rules: target-only
neural scores are proposal scores, not the previous complete-dictionary neural
objective. A real optimizer would still rescore complete affected segments and
check injectivity before accepting any proposed mapping change.

Ranking uses a 1e-4 tie tolerance. Rank is the average tied rank; top-1, top-5 and
reciprocal-rank credit are expectations under uniform tie breaking. A gold
inclusion in this small list does not imply top-5 inclusion in the full lexicon.
Targets are type weighted, not occurrence weighted, in aggregate metrics.

## Reproduction and checks

```sh
.venv/bin/python -m benchmarks.word_mapping_context_rank
.venv/bin/python -m benchmarks.word_mapping_context_rank --validate
```

The model is loaded strictly offline. Outputs are under
`experiments/results/word-mapping/context-rank/`. Resume requires `--resume` and
rejects changed sources/protocols. Inputs include the validated long-context
foundation and validated candidate-pool experiment. Manifests freeze source
identities, complete probes, code, packages, model files and scoring settings.

Validation independently recomputes every neural/n-gram/frequency score and
reconstructs ranks and the aggregate report. Tests cover simultaneous repeated
target masking, complete multi-subword masking, tie credit, nested corrections,
source/probe identity, resume, protocol rejection and score tamper detection.

This is same-author development analysis. Possible pretrained Caesar exposure
remains unknown; no independent generalization claim is supported. The final
test is untouched.

## Results

The primary word-normalized neural score improves sharply as oracle neighbor
quality increases. It does not provide useful top-ranked gold proposals from
the actual saved decoding in this sample.

| Neighbor context | Neural top-1 | Neural top-5 | N-gram top-1 | N-gram top-5 |
| --- | ---: | ---: | ---: | ---: |
| All incorrect (uniform training dictionary) | 1.39% | 2.78% | 9.72% | 16.67% |
| 25% neighbor types corrected | 1.39% | 4.17% | 13.89% | 29.17% |
| 50% corrected | 8.33% | 20.83% | 23.61% | 34.72% |
| 75% corrected | 15.28% | 29.17% | 27.78% | 41.67% |
| All neighbors correct | 25.00% | 47.22% | 31.94% | 45.83% |
| Actual saved decoding | 0.00% | 2.78% | 5.56% | 11.11% |

With actual saved context, neural top-1 succeeds on **0/72** types and top-5 on
**2/72**, versus n-gram **4/72** and **8/72**. Correct neighbors improve neural
success to **18/72** and **34/72**, versus n-gram **23/72** and **33/72**. The
raw neural score gives the same top-1 counts in every condition, and top-5 of
44.44% with fully correct neighbors versus 47.22% for word normalization.
Training frequency alone has zero top-1 and 1.39% top-5 throughout.

Neural mean reciprocal rank rises from 0.067 with fully corrupted synthetic
context to 0.364 with correct context; actual saved context gives 0.064.
Per-bundle neural top-5 with fully correct neighbors is 62.5%, 54.17% and 25.0%;
with saved context it is 8.33%, 0% and 0%. The small type-balanced sample does
not establish a sharp correction threshold or guarantee similar performance
for a different alternative distribution.

Scoring took about 75.2 seconds in probe scoring calls and 17,940 masked-word
forward examples. This excludes preparation, model loading and independent
validation. The n-gram scores remain higher in top-1 success for every context
condition; these data do not justify replacing its proposal rankings with the
current neural score. Neural top-5 under completely correct neighbors is
slightly better, suggesting a possible late refinement role, not a demonstrated
method for bootstrapping poor decodings.

The practical next step is a cheap bootstrap experiment using independent
morphology/agreement or frequency anchors and coordinated mapping moves.
Measure partial recovery first, then reconsider neural proposals if enough
reliable neighboring context becomes available. Another large run of the same
neural-guided search is not supported by this diagnostic.

All 72 probes and their six context conditions were independently recomputed
and validated, totaling 17,940 neural masked-word jobs. All 119 focused tests
pass. The final test remains unscored.
