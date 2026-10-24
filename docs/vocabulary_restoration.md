# Vocabulary restoration diagnostic

The corrected 5,655-entry model is UNSAT for the 23-word prefix. The original
5,665-entry model has a verified SAT witness. This diagnostic restores selected
removed entries while preserving the ciphertext, alphabets, H2/L3 bounds,
prefix-freeness, text-wide phase-zero cycles, word boundaries and observed domains.
Public requests contain no key, segmentation or plaintext-length hints.

| Variant | Added entries | Purpose |
|---|---|---|
| restore-i | i | Test the single-letter vocabulary gap |
| restore-iv | iv | Test the removed Roman numeral alone |
| restore-i-iv | i, iv | Test both entries together |
| restore-i-iv-iulius | i, iv, iulius | Include the removed proper name as well |
| restore-by-of | by, of | Test English footer words without the Latin additions |
| restore-old-witness-words | by, iv, of | Independently recheck the old witness in a minimally expanded vocabulary |

These descriptions identify plausible word categories, not a complete Latin
lexicon. No general grammatical language claim follows from dictionary membership.
Original source ordering is retained when entries are restored.

Each fresh attempt has a 30-second solver budget. UNKNOWN is inconclusive,
particularly since the corrected baseline needed 210 seconds for UNSAT. The final
variant needs no fresh search: a complete independently checked existing witness
is sufficient to establish SAT. Its stored result retains the original witness's
historical solver timing; the row's method and wall time identify reuse clearly.
This is a sufficient three-entry restoration, not a proved minimal one.

Run or resume the diagnostic:

```sh
.venv/bin/python -m benchmarks.vocabulary_restoration --resume
```

To regenerate inputs without running the solver:

```sh
.venv/bin/python -m benchmarks.vocabulary_restoration --prepare-only --resume
```

Inputs: `data/generated/vocabulary-restoration/inputs/`.
Report: `experiments/results/vocabulary-restoration.json`.
The report is checkpointed after every attempt. Resume checks the configuration
and the hashes of both source inputs and the witness.

A targeted 30-minute retry for restoring plausible Latin entries only:

```sh
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/vocabulary-restoration/inputs/restore-i-iv-iulius.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/restore-i-iv-iulius-30min.json
```

This long run is prepared, not launched. Its purpose is to separate the effect
of missing Latin/numeral/name entries from admitting the English words `by/of`.

## Recorded results

| Added entries | Status | Fresh solver time |
|---|---|---:|
| i | UNKNOWN | 30.08s |
| iv | UNKNOWN | 30.08s |
| i, iv | UNKNOWN | 30.07s |
| i, iv, iulius | UNKNOWN | 30.07s |
| by, of | UNKNOWN | 30.08s |
| by, iv, of | SAT | Existing witness; no fresh solve |

All five fresh searches returned UNKNOWN at the 30-second budget. No tested
subset was proved UNSAT, and necessity of any particular removed entry remains
unresolved. Restoring `by/iv/of` is sufficient by independent witness validation;
it is not claimed minimal. The Latin/numeral/name restoration is the next
long-run target. All 424 tests pass.

## Long-run Latin-entry restoration result

The user-run `restore-i-iv-iulius` retry returned **UNSAT in 273.64 solver
seconds**. The saved request matches the prepared variant except for the
1,800,000 ms timeout. Its vocabulary has 5,658 entries: the corrected corpus
plus exactly `i`, `iv`, and `iulius`. Provenance and request checks are recorded
in `experiments/results/restore-i-iv-iulius-validation.json`; no independent
UNSAT proof certificate was checked.

This rules out that fixed expanded vocabulary under the same 23-word H2/L3
model. By vocabulary inclusion, it also rules out the `restore-i`, `restore-iv`
and `restore-i-iv` models, although their original short-run records remain
UNKNOWN. These are logical consequences of the larger model's UNSAT result,
not new solver runs.

The previous witness proves that adding `by` and `of` to the Latin-entry
restoration is sufficient for SAT, because `iv` is already restored. Whether
one English word alone is sufficient is unresolved. Other removed footer
entries also remain untested in this comparison, so this does not establish
that English entries are necessary for every extension of the corrected
vocabulary, or that the manuscript could not encode Latin outside it.

Next, add `by` alone and `of` alone to the `i/iv/iulius` variant. This holds the
Latin/numeral/name additions fixed and isolates the two English-word effects.


The [separate English-word diagnostic](english_word_restoration.md) implements
this comparison, retaining `i/iv/iulius` in all three variants.
