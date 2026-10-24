# Independent vocabulary coverage audit

Neither new frozen passage fits the one-unknown-occurrence model, even with all
eligible first-half vocabulary. The full prefix has 3,442 Latin types and 1,962
Swabian types; the later passages still miss six and four training occurrences.
No Z3 runs were performed. Four tests and 24-row artifact validation pass.

| Dictionary selection | Latin missing / 24 | Swabian missing / 24 |
|---|---:|---:|
| Corpus order, 256 | 17 | 10 |
| Corpus order, 512 | 15 | 8 |
| Corpus order, 1,024 | 12 | 8 |
| Corpus order, 2,048 | 6 | Unavailable |
| Frequency, 256 | 12 | 8 |
| Frequency, 512 | 11 | 7 |
| Frequency, 1,024 | 9 | 7 |
| Frequency, 2,048 | 8 | Unavailable |
| Entire eligible prefix | 6 | 4 |

Requested 4,096-word dictionaries are unavailable in both prefixes and are
recorded as such, without enlarging the source portion. The Swabian 2,048-word
size is also unavailable. Frequency selection improves small-vocabulary coverage,
but does not dominate corpus order at every size on these fixed passages.
Full-prefix results coincide across rankings because they contain the same words.

Latin forms absent from the entire vocabulary-building half are `silvestris`,
`introrsus`, `perspici`, `continebant`, `paucae`, `stationes`. Swabian forms are
`zebelyben`, `widerkomen`, `ruowet`, `belybt`. Increasing a dictionary within this
same source portion cannot add unseen spellings. This diagnoses exact-form
coverage; it does not by itself establish why each form is absent or justify a
new historical normalization.

## Broader fixed-grid check

The audit also uses every eligible 24-word block on a nonoverlapping grid anchored
at the second-half midpoint. Invalid blocks are rejected whole without shifting
or skipping records inside a block. This gives 393 Latin blocks (34 rejected)
and 207 Swabian blocks (169 rejected). These eligibility restrictions, especially
the Swabian exclusions, limit generalization to the full manuscripts/corpora.

| Inventory | Latin admitted with ≤1 unknown | Swabian admitted with ≤1 unknown |
|---|---:|---:|
| Corpus order, 256/512/1,024 | 0/393 | 0/207 |
| Corpus order, 2,048 | 0/393 | Unavailable |
| Frequency, 256/512 | 0/393 | 0/207 |
| Frequency, 1,024 | 0/393 | 4/207 |
| Frequency, 2,048 | 0/393 | Unavailable |
| Entire eligible prefix | 5/393 (1.3%) | 11/207 (5.3%) |

Even full-prefix inventories leave median missing counts of seven Latin and five
Swabian occurrences per eligible 24-word block. Admission also checks the public
dictionary-derived maximum word length, so ≤1 missing alone is not enough if an
unknown word exceeds that bound. These descriptive rates are not cipher success
rates or a statistically independent sample; frozen passages can overlap grid
blocks and same-source blocks remain correlated.

## Frozen methodology and reproduction

First-half eligible source records determine both rankings without target-word
reservation: original first-occurrence order, or descending prefix frequency
with lexical tuple ties. The existing corrected source inventory, alphabet and
normalization remain fixed assistance. Vocabulary sizes 256, 512, 1,024, 2,048,
4,096 and full-prefix ceiling were frozen before coverage scoring. No passage,
word, ranking or size is selected using a solver result or held-out accuracy.
This is an earlier/later split within one source per language, not independent
external language coverage or a matched comparison of language difficulty.

```sh
.venv/bin/python -m benchmarks.independent_vocabulary_coverage --run
.venv/bin/python -m benchmarks.independent_vocabulary_coverage --validate
```

Artifacts: `experiments/results/independent-vocabulary-coverage/` saves protocol,
source/code hashes, ranked words with counts and record provenance, frozen target
passages, eligible/rejected grid blocks, exact missing-count histograms and
validation. Validation reconstructs rankings, provenance, grid and all coverage
rows. Tests check prefix isolation, deterministic ranking/nesting, occurrence and
public-length admission, and whole-block rejection at barriers.

The useful next direction is an independently built vocabulary that covers more
exact forms, possibly a separately specified morphological expansion, then a new
coverage audit before recovery. It is premature to spend longer solver budgets on
these excluded generating explanations or to weaken the unknown-word allowance
to rescue them. No manuscript-language conclusion follows.
