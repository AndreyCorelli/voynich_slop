# Seven matched H2 duplication-layout comparisons

This loop tests whether adjacent duplication makes the previous synthetic H2
calibration unusually easy. Six paired diagnostics use the already inspected
seed-7101 and seed-7102 families at 12, 18 and 24 distinct types. Their validated
adjacent results are copied with raw file hashes rather than refitted. Pair 7
uses a new seed-8101 family at 24 types; both layouts were frozen before either
fit. All fourteen layout inputs were prepared before any new fit.

Within each pair, the plaintext multiset, key, 32,768-form dictionary, alphabet,
holdout plaintext/ciphertext, word-length distribution and global cipher-code
counts are identical. Adjacent layout encrypts `a,a,b,b,...`; two-pass layout
encrypts `a,b,...,a,b,...`. The same generating per-letter alternation changes
code co-occurrence as ordering changes. The solver has no alternation or
plaintext-duplication constraint: it still fits free H<=2 choice using Boolean
word graphs with matching-capacity and joint candidate-support pruning.

Each layout has a first fit, matched shuffle and observed-key exclusion check.
Each worker is capped at 60 seconds with a 30-second Z3 budget. First-key scores
are retained; alternatives are verified, never used to replace those scores.
Seven paired iterations comprise 14 layout cases and 42 fit/exclusion records:
18 records are reused, and 24 are newly generated.

| Pair | Seed / types | Exact first training score, both layouts | Novel holdout, both | Adjacent key | Two-pass key | Positive Z3 seconds, adjacent / two-pass |
|---:|---|---|---|---|---|---|
| 1 | 7101 / 12 | 24/24 | 6/6 | Unique | Unique | 0.0022 / 0.2016 |
| 2 | 7101 / 18 | 36/36 | 6/6 | Unique | Unique | 0.0021 / 0.0019 |
| 3 | 7101 / 24 | 48/48 | 6/6 | Unique | Unique | 0.0019 / 0.0019 |
| 4 | 7102 / 12 | 24/24 | 6/6 | Unique | **Alternative SAT** | 0.0019 / 0.1439 |
| 5 | 7102 / 18 | 36/36 | 6/6 | Unique | Unique | 0.0020 / 0.0020 |
| 6 | 7102 / 24 | 48/48 | 6/6 | Unique | Unique | 0.0019 / 0.0020 |
| 7 | 8101 / 24, fresh | 48/48 | 6/6 | Unique | Unique | 0.0021 / 0.0021 |

Here "unique" means excluding the first observed-code mapping is UNSAT in the
implemented bounded model. All first fits are verified SAT, all 14 matched
shuffles are UNSAT, and 13 of 14 exclusion searches are UNSAT. The remaining
exclusion search is verified SAT. No independent proof certificate is produced.

At 12 types, two-pass layout leaves 89,234 positive candidate rows for seed 7101
and 32,478 for seed 7102, whereas adjacent layout reduces both to 24 (one per
occurrence). This increases propagation/construction/search costs, even where
the observed mapping remains unique. At 18 and 24 types, both layouts reduce to
one candidate per training occurrence. Timings are single runs, and reused
adjacent timings were measured in the earlier loop.

## Verified ambiguity and the richer cases

The seed-7102 two-pass first key happens to recover all training and holdout
words correctly. Nevertheless, its alternative key changes `vs: r -> s` and
`ut: s -> r`, decoding `capros` as `capsor` and `aerque` as `aesque`, each in both
passes. All alternative training words belong to the same frozen dictionary,
and the alternative obeys the same global capacity.

Diagnostic continuation under that alternative yields only 3/6 exact holdouts:
`urenda -> usenda`, `latias -> latiar`, and `coorta -> coosta`; `uiear`, `auita`
and `alluor` remain exact. Only three alternative holdout words belong to the
dictionary. These are diagnostic alternative predictions, not replacement
first-key scores or additional solver constraints. The original first score
remains 6/6. This illustrates why one correct first key alone does not establish
identifiability.

At 18 types, the two-pass exclusion result becomes UNSAT. Checking the discovered
12-type alternative against that richer input shows that new first-pass words
already reject it: for example, `sonis` would decode to `ronis`, which is absent
from both the 32,768 dictionary and the complete 32,846-form length-compatible
inventory. Four other new first-pass words also reject it. The 24-type case adds
another rejection. These checks demonstrate that new word evidence rejects this
specific alternative, without needing to rescore or rerun the first fits.

Two-pass training ciphertext is not nested across type counts: adding words can
also change code choices in the later pass. Its original first-pass prefix is
unchanged, but the whole later input is not a strict superset of the smaller
ciphertext. Consequently, these cases do not prove a universal minimum training
size or a monotonic uniqueness threshold.

The fresh seed-8101 pair exercises all 46 homophones of the full 23-letter
alphabet, recovers 48/48 training occurrences and all six new holdouts under
both layouts, and has unique observed mappings in both cases. Seeds 7101 and
7102 exercise 42 and 44 codes respectively. The fresh pair replicates the
24-type result, not the 12-type ambiguity. Repeated holdout evaluations across
layouts and type levels are not independent new samples.

## Interpretation and next priority

Adjacent duplication can materially improve pruning and can conceal ambiguity
present under a different generating layout. It is therefore an easier positive
control in at least one of these matched cases. The 18/24-type results and fresh
full-alphabet pair show that two-pass layout is also tractable and identifiable
here, so the successful calibration is not limited to adjacent duplication.
The old seed-5101 ambiguity remains stored and is not rescued by these results.

The next useful stress test is **balanced random homophone choice**, rather than
only generating alternation: keep plaintext, key and letterwise code totals
fixed, randomly distribute each letter's two codes across training occurrences,
and compare with a cyclic baseline under the same fitting model and budgets.
Use the complete 32,846-form length-compatible inventory for both arms to close
the remaining 78-form gap, and freeze the complete-inventory cyclic baseline as
well so the choice comparison varies only the selection method. Fresh families
are needed for replication after these adaptive diagnostics. No eighth paired
iteration was run here.

These are assisted synthetic fixed-boundary experiments on generated forms,
not natural prose or manuscript windows. Vocabulary policy, orthography, unknown
boundaries, contractions and natural-text H2 remain uncalibrated. Complete
length-compatible coverage would apply to this finite default inventory, not
all historical Latin.

## Validation and reproduction

Twelve targeted tests pass: layout invariants, nested-generation/novel selection,
unique/ambiguous key exclusion, six compressed-relation equivalence cases and
three existing H2 solver/capacity checks. All 42 records validate. Validators
regenerate the pair inputs, check reused file hashes, reproduce candidate
pruning, verify fitted/alternative training membership and capacity, and retain
first-key scoring. Original benchmark implementations and results are unchanged.

```sh
.venv/bin/python -m benchmarks.latin_h2_layout --run
.venv/bin/python -m benchmarks.latin_h2_layout --validate
.venv/bin/python -m benchmarks.latin_h2_layout_analysis
```

`experiments/results/latin-h2-layout/prepared.json` freezes all pairs and source/
code/reuse hashes. Per-layout directories contain fit/exclusion results and
phase records. `comparison.json` joins both layouts; `validation.json` records
all seven completed comparisons. `alternative-analysis.json` verifies the
alternative continuation and rejects its use on richer training inputs without
additional solver calls. Commands reuse existing frozen results.
