# Diverse restart pool and neural reranking

This experiment tests whether archive reranking improves when candidates come
from separate initialization basins rather than neighboring states of one run.
It uses the four frozen long-context development bundles. The pooled bundle
overlaps the other three, so aggregate results are descriptive.

## Frozen protocol

For each bundle, pool all 30 entries from each saved injective-mixture archive
(seeds 11, 22 and 33, the 50,000-per-restart budget). Add six fresh independent
single-restart searches: frequency, random and lemma-aware initialization, each
with seeds 101 and 202 and 20,000 mutations. All ciphertext types are active,
all assignments are injective, and each fresh run retains ten candidates.

The 24 new searches total 480,000 mutations. Each bundle's pool has 150 entries.
Select at most 12 unique dictionaries by starting with the highest n-gram score
and repeatedly maximizing minimum assignment distance to already selected
candidates. Distance counts differing ciphertext-type assignments without
occurrence weighting; n-gram score and stable order break ties. No truth enters
pooling, search, distance selection or neural ranking.

Score the 48 shortlisted dictionaries using the same full-segment Latin RoBERTa
word-normalized metric as [the prior reranking experiment](word_mapping_neural_rerank.md).
Compare the pooled n-gram winner with the neural winner. Load truth afterward
for exact token/type recovery and shortlist-oracle evaluation. A separate
post-selection audit measures the entire pool's oracle recovery, per-origin
accuracy and pairwise dictionary distance. An oracle is an evaluation diagnostic,
not an available selection method.

These fresh shorter runs versus saved longer runs are not a matched-budget
initialization comparison. The goal is a bounded, diverse proposal pool.
Possible Caesar exposure in neural pretraining remains unknown. The final test
is untouched. Large dictionary distances do not imply linguistic quality.

Run offline:

```sh
.venv/bin/python -m benchmarks.word_mapping_diverse_candidates
.venv/bin/python -m benchmarks.word_mapping_diverse_candidates --validate
.venv/bin/python -m benchmarks.word_mapping_diverse_rerank
.venv/bin/python -m benchmarks.word_mapping_diverse_rerank --validate
.venv/bin/python -m benchmarks.word_mapping_diverse_audit
```

Both experimental runners support `--resume`; existing outputs require resume
or validation. Source code, resource identities, configurations, model files,
archives and candidate selection are hashed. Search validation restores every
checkpoint and recomputes all archived objectives; neural validation recomputes
all dictionary scores and reconstructs evaluation results. Generation artifacts
are in `experiments/results/word-mapping/diverse-candidates/`; reranking and audit
artifacts are in `experiments/results/word-mapping/diverse-neural-rerank/`.

## Results

| Bundle | N-gram winner | Neural winner | Shortlist / full-pool oracle |
| --- | ---: | ---: | ---: |
| Bundle 1 | 0.000% | 0.000% | 3.077% |
| Bundle 2 | 5.598% | 5.598% | 5.852% |
| Bundle 3 | 0.000% | 0.000% | 1.386% |
| Pooled | 4.666% | 4.666% | 4.849% |
| Mean across cases | 2.566% | 2.566% | 3.791% |

All 600 pooled entries were distinct within their respective bundles. Mean
pairwise type distances in the 12-entry shortlists were 96.89%, 95.25%, 96.32%
and 94.44%. Shortlisting retained each full pool's best recovery. Unlike the
previous narrow shortlists, each diverse shortlist offers a better candidate
than its n-gram winner. Nevertheless the neural scorer chose a saved
frequency-initialized run in every case; only bundle-3 changed dictionary rank,
without changing accuracy.

Fresh random starts were almost entirely wrong. The best fresh lemma-aware
candidate helped bundle-1 (3.077% versus its original zero), while fresh
frequency starts modestly improved bundle-2 and pooled. Neither scorer selected
these improvements. Scoring the 48 dictionaries took about 96.4 seconds in
scoring calls and 23,939 actual masked-word forward examples; these exclude
model loading, candidate generation, evaluation and independent validation.

Candidate diversity alone did not solve recovery. The stronger near-truth
counterexample ranking from the earlier probe does not transfer to choosing
among these badly decoded texts. The pool oracle remains below 6% in every
case, so even a perfect reranker would yield poor absolute recovery.

The next useful diagnostic is a graded difficulty experiment with fixed,
training-derived candidate-pool sizes, comparing n-gram and contextual ranking
from poor initializations. This would identify where context becomes useful
before committing to expensive neural-guided search. No new long run or final
test evaluation is justified by this result alone.

All 24 fresh search checkpoints and 240 archived search scores validate. All 48
neural dictionary scores were independently recomputed and validated. All 114
focused tests pass, including distance selection, deduplication, domain checks,
synthetic recovery, resume, provenance tamper rejection and evaluation-only
pool-oracle auditing.
