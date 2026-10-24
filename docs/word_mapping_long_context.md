# More observations and local objective diagnostics

This calibration tests the two prerequisites identified after the frequency-prior
experiment: more training-disjoint natural observations, and an evaluation-only
audit of whether truth is a local optimum of the score.

```sh
.venv/bin/python -m benchmarks.word_mapping_long_context
.venv/bin/python -m benchmarks.word_mapping_long_context --validate
```

Output: `experiments/results/word-mapping/long-context-calibration/`.
`--resume` continues identical searches; `--prepare-only` builds the foundation.
The runner uses cached source files and never downloads implicitly.

## Data and scope

Training uses Caesar's *Gallic War* V–VII and *Civil War* I–III, downloaded from
[The Latin Library's Caesar collection](https://www.thelatinlibrary.com/caesar/).
HTML navigation, headings and footer are excluded. Numbered prose chapters are
checked for continuity; sentence punctuation and paragraph boundaries are
preserved. Raw downloads, extracted text and normalized streams have checksums.
Normalization matches the existing scoring conventions.

Training contains 56,646 words and supplies 12,327 candidates. Development comes
from the earlier Gutenberg *Gallic War* I–IV source. The original final-test
positions are excluded and never scored. No development forms augment candidates.
One upstream morphology lookup (`qu`) raises a missing `PACK`-table error; its
surface stays in candidates with no analyses and a recorded annotation failure.
Other unexpected morphology errors still fail preparation.

Of 18,359 eligible development words, 1,093 words in 90 complete scored segments
are fully covered by training candidates. This is approximately 6% admission,
so the calibration is strongly coverage-screened. Three chronological thirds
of the original source supply disjoint bundles of 195, 393 and 505 words. The
pooled case uses all 1,093 words with one shared dictionary. No rejected gap is
joined and no segment is repeated to inflate length. Abbreviation punctuation
can split linguistic sentences; these are scored-segment bundles, not contiguous
passages. More tokens increase observations per dictionary, not n-gram order.

All four cases use the same training resources. The pooled case overlaps the
three bundles and is not an independent replicate. This is same-author,
disjoint-book calibration rather than cross-author or manuscript validation.
Changes from the earlier 120-word experiment include both training resources
and candidate vocabulary, so those older results are not a controlled length
comparison with this experiment.

## Searches and diagnostics

One-to-one fixtures activate every observed ciphertext type. Baseline mixture,
trigram and injective-mixture searches use three seeds, two restarts and paired
budgets of 10,000 and 50,000 mutations per restart. All candidates remain
reachable. The four cases total 72 searches and 4.32 million search evaluations.

Separately, evaluation constructs the true dictionary and exhaustively scores
every single-type replacement into every other frozen candidate and every pair
swap. It reports unconstrained and injectivity-preserving replacements separately,
as well as counts of improving, tied and worsening neighbors. The top examples
include affected n-gram terms before and after the change. Their deltas are checked
against independent full scoring. Oracle mappings never enter search inputs,
initialization, proposals, candidate selection or budgets.

A feasible improving neighbor is a direct local objective counterexample. No
improving neighbor would establish only local optimality in this neighborhood,
not global identifiability. Token recurrence and per-type diagnostics distinguish
singleton words from words with repeated observations. Exhaustive reconstruction
and saved-search validation are available through `--validate`.

All 101 focused tests pass, including an exhaustive small-domain neighborhood
comparison against full scoring, unchanged evaluation inputs, missing-candidate
rejection, HTML extraction boundaries, recorded morphology failures and a
foundation reconstruction/tampering check with the test split unchanged.

## Completed results

All 72 searches completed: 4,320,000 mutation evaluations. The eight exhaustive
audits scored 35,828,536 distinct replacement/swap neighbors across cases and
profiles. Injective replacement counts are a classified subset of replacements,
not additional evaluations. The pooled case and separate cases share observations,
so these counts do not represent independent samples.
Independent validation rebuilt the foundation, validated every saved search,
and exhaustively reconstructed all eight neighborhood reports with exact agreement.

Mean exact token recovery across three seeds at 50,000 mutations per restart:

| Case | Words | Baseline mixture | Trigram | Injective mixture |
| --- | ---: | ---: | ---: | ---: |
| Bundle 1 | 195 | 0.171% | 0.000% | 0.000% |
| Bundle 2 | 393 | 5.004% | 4.071% | 5.259% |
| Bundle 3 | 505 | 0.660% | 0.462% | 0.462% |
| Pooled | 1,093 | 3.934% | 4.422% | 4.514% |

Across all searches, 36 archived an incorrect complete dictionary above truth
and 36 stayed below truth. At the larger budget, 33 of 36 searches produced a
counterexample. The remaining three were pooled injective runs. Their search
shortfall does not establish a sound objective: the local audit directly finds
feasible higher-scoring dictionaries near truth in that same setting.

Number of true ciphertext-type assignments with at least one improving
injectivity-preserving single replacement, with all other assignments correct:

| Case | Types | Mixture | Trigram |
| --- | ---: | ---: | ---: |
| Bundle 1 | 163 | 139 (85.3%) | 141 (86.5%) |
| Bundle 2 | 283 | 229 (80.9%) | 229 (80.9%) |
| Bundle 3 | 353 | 295 (83.6%) | 300 (85.0%) |
| Pooled | 629 | 514 (81.7%) | 519 (82.5%) |

The pooled mixture also has 9,102 improving pair swaps. Among its 448 singleton
types, 418 (93.3%) have an improving injective replacement; among 181 repeated
types, 96 (53.0%) do. Repetition helps some words, but many entries remain
misranked even with repeated observations. This is descriptive evidence within
this cohort, not a causal or generalization result.

An illustrative bundle-1 counterexample replaces both occurrences of `eorum`
with the unused form `eius`, gaining 23.27 log-likelihood units. Its largest gains
include the contexts `ab eorum castris` and `eorum fuga`. This preserves the
one-to-one constraint and changes only one dictionary entry. The saved examples
expose each affected prediction term for inspection.

More observations and trigram scoring did not make this objective reliable for
exact dictionary recovery. A faster optimizer alone would still pursue these
wrong alternatives. The next scoring experiment should test longer-context
evidence, with uncertainty for poorly observed entries, against these frozen
local counterexamples before allocating another broad search. No recovery,
manuscript-inference or final-test gate has been passed.
