# Restoring the full block with a surviving vocabulary

The East Franconian source-133 vocabulary is tested on the full original
30-word contiguous block, restoring all words removed during conflict
reduction. Source 133 was chosen because it gave the fastest of the four
verified SAT results on the 19-word subset (207.03 seconds).

The full 2,425-word vocabulary, plaintext alphabet, free-selection H2/L3
bounds, ciphertext alphabet and other settings are held fixed. One shared
newly inferred key must explain all 30 words; no subset witness key or
plaintext is given to the solver. Preparation checks that the full block
contains the independently verified 19-word subset at its exact original
positions. Relative to the earlier source-143 full-block request, only the
vocabulary, plaintext alphabet and timeout differ.

The initial 30-second probe returned UNKNOWN in 30.12 seconds. The user-run
longer retry returned **independently verified SAT in 349.69 seconds** on all
30 consecutive words. The same ciphertext is UNSAT with source 143 and SAT
with source 133 under the same free-selection cipher rules: the full-block
exclusion, as well as the smaller conflict, is vocabulary-dependent.

The [longer replay](../experiments/results/german-133-full-30-30min.json) and
[independent validation](../experiments/results/german-133-full-30-30min-validation.json)
check the input hash, unchanged parameters, complete dictionary membership,
key bounds and prefix-freeness, and exact encoding/decoding round trips.
The recovered witness has 80 plaintext letters, mean 2.67 per word:

```text
wye abe aue ist nie abe k wan an zw ware abe im ab kam abe al al an ab wo aber k an aue nucz abe aus got gabe
```

This is a dictionary fit, not demonstrated grammatical prose.
The subsequent [short-form audit](german_short_form_audit.md) finds that the
witness's two `k` tokens derive from unexplained `k x k` prayer sequences.
A separate input excluding `k` and `x`, while retaining attested `o`, is
returned UNSAT in 5.55 seconds. The original source-133 full-block fit
therefore requires at least one of those unexplained entries.

Artifacts:

- [Preparation](../experiments/results/german-vocabulary-full-block-preparation.json)
  records the source, input hash, verified subset provenance and original positions.
- [Short replay](../experiments/results/german-133-full-30-30sec.json)
  records the effective request, result and solver statistics.
- [Validation](../experiments/results/german-133-full-30-validation.json)
  checks request hashes and unchanged full-block/cipher settings.

Reproduce preparation and run the longer attempt locally:

```sh
.venv/bin/python -m benchmarks.german_full_block
.venv/bin/python -m benchmarks.observed_codes \
  --replay data/generated/german-vocabulary-robustness/full-block/133-words-30.json \
  --timeout-ms 1800000 \
  --replay-output experiments/results/german-133-full-30-30min.json
```

The longer user-run attempt above has completed. The preparation script supports the other
three surviving vocabularies with `--source`, but they have not been tested
on this full block here. Its 11 focused checks passed across full-block
preparation and robustness setup, covering restored subset order, unchanged
parameters, public-input separation and invalid source/budget rejection.

A verified SAT would extend dictionary compatibility to the full block,
without establishing grammatical German or manuscript language. UNSAT would
exclude that full block for source 133 while preserving the existing subset
SAT. UNKNOWN leaves full-block feasibility unresolved.
