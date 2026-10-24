# Seven complete-inventory H2 homophone-choice comparisons

Seven paired comparisons test cyclic versus balanced random **training** choice
with the complete default length-compatible dictionary. Six adaptive pairs use
the already inspected seed-7101/7102 families at 12, 18 and 24 types. Pair 7 is a
fresh seed-9101 family at 24 types, with new sampling, key, shuffle and holdout
seeds. All fourteen inputs were frozen before fitting; no case was replaced.

Both arms use all **32,846** default-inventory forms of length 3–6. The dictionary
is the exact length subset of the cached complete default inventory, verified
against its hashed source. This closes the previous 78-form gap, so all cyclic
baselines were refitted; no 32,768-form result was reused. Known two-glyph
boundaries make plaintext lengths public, so excluding other lengths does not
exclude any admissible training word in these cases. This is complete coverage
of a finite inventory for these lengths, not of all historical Latin.

Training words appear in two passes. Cyclic generation alternates each letter's
two codes across its occurrences. Balanced random generation independently
shuffles each letter's equally sized code bags and assigns them across the same
training positions. Within a pair, word order, plaintext, key, complete
dictionary, alphabet, exact global code histogram, and holdout plaintext/cipher
are identical. Only training code assignment changes. Both homophones of each
trained letter remain observed.

Holdout code choices remain fixed from cyclic generation to isolate the training
choice comparison; this is not a wholly random end-to-end selection experiment.
Fit constraints still permit free choice up to H=2, with no imposed cycle or
balance rule. The unchanged Boolean word graph, capacity matching and joint
candidate semijoins are used. First keys are scored; separate exclusion searches
check observed-key uniqueness. Each fit/check has 30 seconds of Z3 search and a
60-second worker cap. Alternatives never replace first-key scores.

| Pair | Seed / types | Cyclic exact training / holdout | Cyclic key | Random exact training / holdout | Random key | Z3 seconds, cyclic / random |
|---:|---|---|---|---|---|---|
| 1 | 7101 / 12 | 24/24, 6/6 | Unique | 24/24, 6/6 | Unique | 0.2549 / 0.1724 |
| 2 | 7101 / 18 | 36/36, 6/6 | Unique | 36/36, 6/6 | Unique | 0.0019 / 0.0019 |
| 3 | 7101 / 24 | 48/48, 6/6 | Unique | 48/48, 6/6 | Unique | 0.0019 / 0.0019 |
| 4 | 7102 / 12 | **20/24, 3/6** | **Alternative exists** | 24/24, 6/6 | Unique | 0.1455 / 0.2375 |
| 5 | 7102 / 18 | 36/36, 6/6 | Unique | 36/36, 6/6 | Unique | 0.0020 / 0.0020 |
| 6 | 7102 / 24 | 48/48, 6/6 | Unique | 48/48, 6/6 | Unique | 0.0020 / 0.0020 |
| 7 | 9101 / 24, fresh | 48/48, 6/6 | Unique | 48/48, 6/6 | Unique | 0.0020 / 0.0020 |

All fourteen first fits are verified SAT. All fourteen matched shuffles are
UNSAT. Thirteen exclusion searches are UNSAT, establishing uniqueness of their
observed mappings within this bounded model. The remaining cyclic case has two
verified keys; its known generating key supplies an alternative witness without
a redundant exclusion fit. No proof certificate is independently checked.

At 18/24 types, propagation leaves one candidate per occurrence. At 12 types,
cyclic versus random candidate rows are 91,174 versus 29,500 for seed 7101 and
32,562 versus 44,865 for seed 7102. Random choice does not universally reduce
candidate count or search time. Positive propagation spans approximately
0.97–3.98 seconds; all fits/checks resolve within the existing budgets. Timings
are single runs, not performance distributions.

## Why the cyclic alias fails under random assignment

In the seed-7102 twelve-type cyclic case, the first key returns the previously
verified `r/s` alias (`vs: r -> s`, `ut: s -> r`), scoring 20/24 training and 3/6
holdouts. The generating key also satisfies the same training constraints.
This is the same known ambiguity; the earlier subset-dictionary fit happened to
return the correct key first. Changing the dictionary can change solver model
ordering, so the differing first score does not establish newly introduced
ambiguity. Both original scores remain stored, with no key-selection rescue.

Applying this cyclic alias to the matched random training produces `azuseo`
instead of `azureo` and `abrume` instead of `absume`, each in both passes. Those
four occurrences are outside the complete dictionary, excluding the alias.
The wrong key's aggregate decoded letter histogram is identical across the two
choice methods, because cipher-code totals are fixed. Its failure here depends
on word-level code arrangement, not a change in monogram counts. No frequency
prior was added to the solver.

`alias-analysis.json` verifies dictionary closure, the discovered alias and these
cross-case rejections. It makes no new solver calls and does not alter first
scores. The random case's separate UNSAT exclusion establishes observed-key
uniqueness under its training constraints.

## What is now calibrated

Complete default-inventory membership at public plaintext lengths 3–6 is
tractable and recovers uniquely on these generated H2 fixtures beyond only
cyclic choices. All seven balanced-random cases recover correctly and uniquely;
the fresh pair also succeeds under both methods. The 18/24-type settings are
identifiable here, while the twelve-type cyclic counterexample remains visible.
This does not establish a universal training threshold: changing training size
also changes generated code associations, and random schedules are not nested.

Sampling from 512 forms and greedy initial letter coverage remain features of
fixture generation, though the fitted dictionary no longer retains a special
sampling pool or omits other eligible forms. Samples are synthetic Latin forms,
not natural prose. Repeated holdout scores across levels and methods are not
independent new samples; only seed 9101 contributes six newly uninspected
holdout words in this loop. Seed 7101 observes 42 codes/21 letters, seed 7102
44/22, and seed 9101 42/21. Uniqueness covers those observed maps, not unused
full-key assignments. Selection is balanced and two-pass training is duplicated;
unbalanced choice, unequal homophone capacities, longer/shorter words, variable
code boundaries and manuscript statistics remain outside this result.

The next most useful step is **natural-text H2 calibration**, using independently
frozen source passages, fresh continuation holdouts and complete length-relevant
inventories. Preserve first-key scoring, uniqueness checks and explicit lexical
coverage failures rather than adding missing truth words. This tests natural
word lengths and repetitions after the synthetic model/solver calibration;
further manuscript-language inference should wait for that result. Seven paired
iterations are complete here; no eighth was run.

## Validation and reproduction

Thirteen targeted tests pass: balanced counts/inverse decoding/fixed holdouts,
odd-count rejection, nested-generation selection, unique/ambiguous key exclusion,
six compressed-relation equivalence cases and three existing H2 solver/capacity
checks. All 42 newly generated fit/exclusion records validate. The paired
validator recomputes random assignment and frozen inventory construction,
checks equal truth/keys/holdouts/code histograms, reproduces pruning, verifies
training membership and capacity, and retains first-key scores.

```sh
.venv/bin/python -m benchmarks.latin_h2_choice --run
.venv/bin/python -m benchmarks.latin_h2_choice --validate
.venv/bin/python -m benchmarks.latin_h2_choice_analysis
```

Artifacts under `experiments/results/latin-h2-choice` include the complete
`inventory`, frozen `prepared.json`, per-arm results/phases and reports,
`comparison.json`, `validation.json` and `alias-analysis.json`. Existing frozen
benchmark implementations and prior results were unchanged. Commands reuse
saved results instead of refitting or selecting among keys.
