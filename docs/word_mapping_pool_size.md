# Training-frequency candidate-pool calibration

This matched-budget diagnostic compares search and contextual ranking under
smaller candidate vocabularies. It follows the [diverse restart experiment](word_mapping_diverse_rerank.md),
which exposed modestly better dictionaries that neither the n-gram winner nor
the neural reranker selected.

## Protocol

Use the three separate long-context development bundles, excluding the overlapping
pooled bundle. Candidate pools contain the top 512, top 2,048 or all 12,327
surface forms by frequency in the independently selected training books. Ties
use the original training catalog's alphabetical order. Restriction preserves
training counts and recomputes lemma counts/groups on the surviving forms; it
never adds true development words. The n-gram model remains fixed across pools.

Every bundle/pool case gets six independent one-restart searches: frequency,
random and lemma-aware initialization with seeds 101 and 202. Each uses 20,000
mutations, activates every observed ciphertext type, enforces injectivity and
retains ten archive entries. Thus 54 searches execute 1,080,000 mutations, with
an identical budget and initialization schedule for every candidate-pool size.

Pool the six archives in each case, deduplicate assignments and select eight
using minimum assignment distance, starting with the best n-gram dictionary.
Score the shortlisted dictionaries using full-segment Latin RoBERTa and the
fixed sum-of-per-word-mean-subword-log-score metric. Break ties by shortlist
order. No truth enters search, candidate restriction, shortlist selection or
neural ranking.

Load truth afterward to report exact token/type recovery, the best possible
accuracy in the shortlist and full archive pool, and candidate coverage. Token
coverage is the exact-recovery ceiling caused by missing candidate words;
accuracy on supported tokens is also recorded. Reduced pool size and reduced
coverage change together, so this is not a pure comparison at constant coverage.
The pools are not oracle difficulty sets containing every true word.

Possible Caesar exposure in neural pretraining remains unknown. These are
same-author development cases, not independent generalization evidence. Final
test text is neither optimized nor scored.

## Reproduction and checks

The model is already installed locally; no network access is needed.

```sh
.venv/bin/python -m benchmarks.word_mapping_pool_size
.venv/bin/python -m benchmarks.word_mapping_pool_size --validate
```

Outputs are in `experiments/results/word-mapping/pool-size-calibration/`.
`--resume` continues interrupted work; protocol/configuration/source/resource
changes reject resume. `--phase search` allows search-only execution, followed
by `--phase rerank --resume`. Validation always includes both phases.

The manifest freezes training/public/model identities, candidate catalogs,
package versions, source code, configurations and scoring settings. The search
report hashes every archive; selection freezes complete pools, origin labels
and rendered shortlists. Validation restores all search checkpoints, recomputes
every archived n-gram objective, reconstructs selection, independently reruns
all neural scores and reconstructs recovery/coverage reports. Stored neural
rows retain their original compute measurements during validation.

## Results

Means are unweighted across the three disjoint development bundles. Accuracy
uses all development tokens, including true words absent from a candidate pool.

| Candidate forms | Candidate token coverage | N-gram recovery | Neural recovery | Shortlist / pool oracle |
| --- | ---: | ---: | ---: | ---: |
| 512 | 59.17% | 0.53% | 2.31% | 3.64% |
| 2,048 | 81.58% | 0.58% | 2.29% | 3.65% |
| 12,327 | 100.00% | 2.03% | 2.28% | 3.31% |

Detailed exact token recovery:

| Bundle | Pool | N-gram | Neural | Pool oracle |
| --- | ---: | ---: | ---: | ---: |
| 1 | 512 | 0.00% | 0.00% | 3.59% |
| 1 | 2,048 | 0.00% | 0.00% | 3.08% |
| 1 | 12,327 | 0.00% | 0.00% | 3.08% |
| 2 | 512 | 0.00% | 5.34% | 5.34% |
| 2 | 2,048 | 0.76% | 6.87% | 6.87% |
| 2 | 12,327 | 5.09% | 5.85% | 5.85% |
| 3 | 512 | 1.58% | 1.58% | 1.98% |
| 3 | 2,048 | 0.99% | 0.00% | 0.99% |
| 3 | 12,327 | 0.99% | 0.99% | 0.99% |

Neural ranking selects the best available candidate for bundle 2 at every pool
size, and always chooses the frequency-101 origin there. It fails to find the
better lemma-aware candidates in bundle 1, and worsens bundle 3 at 2,048 forms
by choosing a lemma-aware dictionary with zero exact recovery. At 512 forms
there is one improvement and no regressions; at 2,048 there is one improvement
and one regression; at full size there is one improvement and no regression.
The shortlist contains the full pool's best-recovery candidate in every case.

All nine pools contain 60 distinct dictionaries. Searching took about 54.6
seconds in search calls. Neural scoring took about 89.2 seconds in scoring calls
and 22,952 actual masked-word examples after segment caching. These exclude
model/resource loading, preparation, evaluation and independent validation.

This demonstrates limited contextual selection value in one bundle, rather
than a recovery breakthrough. Shrinking the candidate pool does not materially
increase average neural recovery: it stays near 2.3%. Reduced candidate
coverage limits the smaller pools, but measured accuracy is far below those
limits; candidate coverage alone does not explain the failure. Even a perfect
pool selector would average only 3.3–3.7% recovery.

The next useful test should diagnose proposal quality directly: measure the
rank of true assignments against training-derived alternatives under fixed
incorrect versus correct neighboring context, on development only. That can
separate candidate-generation weakness from a scorer needing better decoded
context before another long search. These selected three cases do not establish
robust performance, and the final test remains unscored.

All 54 search checkpoints and 540 archived objective scores validate. All 72
neural dictionary scores were independently recomputed and validated; all 116
focused tests pass. Tests cover frequency restriction and restricted lemma
weights, matched budgets, candidate coverage ceilings, supported-token recovery,
checkpoint/resume behavior, protocol rejection and score tamper detection.
