# Distinct training types with correct lengths supplied

This fixed experiment keeps one length-two key and one mixed-length key from
the earlier suite (seed 3101), the full Latin dictionary, alphabets, H1 L1–3 model,
observed code domains and three held-out words. It compares 9, 18 and 36 distinct
training types. Each type appears twice, so the inputs have 18, 36 and 72 words.
The two nine-type results are reused without fitting again. Four new fits receive
five solver seconds each and the correct training word lengths; identities,
key and individual code lengths remain hidden.

Selection retains the original nine types in their original order, then takes
the first new eligible distinct words from the normalized Caesar corpus in record
order. Added words must belong to the fixed full dictionary, must not be excluded
by normalization, and must differ from all three held-out types (`in`, `a`, `eo`).
There is no length, frequency or outcome filter. The 18-type set is a prefix of
the 36-type set. Each addition records its corpus index. This is an engineered
training sequence with added corpus words, not an intact Latin passage.

All inputs, keys, type lists, lengths, provenance and hashes were frozen before
solving. Generating keys independently verify every synthetic positive and its
unchanged continuation. Nested training sets increase distinct word types, total
words, plaintext letters, observed mappings and ciphertext length together; the
experiment does not isolate a pure diversity effect. It tests additional useful
training evidence rather than repeated occurrences of the same H1 words.

Completed fits checkpoint and resume without extra solves. UNSAT would contradict
a verified generating witness and stops the experiment; UNKNOWN is unscored and
does not establish impossibility. Each verified first SAT key is frozen before
scoring. Solver budgets exclude construction, which remains saved separately in
recovery capacity metadata. No retries, budget increases or selection by held-out
prediction are allowed.

Four focused tests pass. They cover deterministic corpus ordering, holdout and
normalization exclusions, dictionary eligibility, nested selections, insufficient
input rejection, unchanged solver requests, length-only information, UNKNOWN
remaining unscored and checkpoint reuse. Artifact validation reconstructs the
selection and checks witnesses, fixed lengths and frozen-key scoring.

Artifacts: `experiments/results/training-diversity/`.

```sh
.venv/bin/python -m benchmarks.training_diversity --run
.venv/bin/python -m benchmarks.training_diversity --validate
```

## Results

| Key | Distinct types | Status | Solver seconds | Construction seconds | Exact training words | Exact novel words |
|---|---:|---|---:|---:|---:|---:|
| Length two | 9 (reused) | SAT | 0.88 | See baseline | 2/18 | 0/3 |
| Length two | 18 | UNKNOWN | 5.03 | 28.38 | Unscored | Unscored |
| Length two | 36 | SAT | 4.06 | 91.04 | 72/72 | 3/3 |
| Mixed | 9 (reused) | SAT | 0.69 | See baseline | 2/18 | 0/3 |
| Mixed | 18 | SAT | 1.98 | 35.81 | 36/36 | 3/3 |
| Mixed | 36 | SAT | 3.82 | 98.43 | 72/72 | 3/3 |

All three new SAT fits recover every training occurrence exactly and predict the
three unchanged novel words exactly. The length-two 18-type timeout remains
unresolved; the 36-type SAT result demonstrates that solver outcome need not
improve monotonically with input size. First-witness success does not prove all
compatible explanations have the same training words or held-out mappings.

Additional distinct corpus words overcome the poor first-key predictions on
these two fixed keys when correct word lengths are provided. This supports
training diversity as a useful direction, without demonstrating general recovery:
only two keys, one nested text inventory and three short held-out words are tested.
There are no scrambled controls, no blind text samples, no dictionary changes,
and no full manuscript fits in this comparison.

The five-second solver limit is not a five-second wall-clock limit. Four new fits
used about 14.89 solver seconds and 253.65 construction seconds in total, in
addition to validation and preparation. Construction is the dominant scaling
cost and must be included when planning further experiments.

Next, remove the correct-length oracle on the two 36-type positives, keeping
these inputs and budgets fixed. This would test whether the richer evidence
also works in hidden recovery. Preserve the length-only successes as controls;
UNKNOWN without the oracle would indicate a remaining search/performance issue,
not the absence of a correct predictive explanation.
