# Shrinking the free-selection German conflict

The completed user-run search reduces the conflict from 29 to **25 words**,
original positions **5–29** (`words[4:29]`). The shortest UNSAT suffix ending
at original word 29 has 25 words; its 24-word suffix is independently verified
SAT. All saved SAT witnesses, input hashes and unchanged settings were checked.

| Suffix length | Result | Solver seconds |
|---|---|---:|
| 28 | UNSAT | 58.24 |
| 14 | Verified SAT | 36.22 |
| 21 | Verified SAT | 34.26 |
| 24 | Verified SAT | 73.27 |
| 26 | UNSAT | 125.28 |
| 25 | UNSAT | 34.00 |

The [validation](../experiments/results/german-free-suffix-validation.json)
records all checks. UNSAT is solver-reported, without an independently checked
proof certificate.

Deleting the right endpoint also gives verified SAT: original words 5–28
are certified by restricting the existing 28-word SAT prefix witness, with
no new solver run. That certificate is saved in
[german-free-conflict-right-trim-sat.json](../experiments/results/german-free-conflict-right-trim-sat.json).
Deleting the left endpoint gives the solved SAT suffix, original words 6–29.
Consequently every proper contiguous subinterval of the 25-word conflict
is SAT: each is contained in one of these two SAT intervals. The conflict
is therefore minimal under contiguous trimming, but it may still shrink
by deleting interior words and testing a noncontiguous subsequence.
The subsequent [interior deletion diagnostic](german_word_deletions.md)
removes four duplicate copies by free-selection feasibility equivalence,
leaving a 21-word conflicting subsequence. Further deletions remain unresolved.

The fixed source-143 free-selection H2/L3 model has a minimal excluded prefix
of 29 words. To test whether its first word contributes to the contradiction,
we remove that word and solve the remaining 28 words, `words[1:29]` in
zero-based original-block indices. The dictionary, alphabets, boundaries,
selection and cipher bounds remain unchanged. A new shared key is inferred
for the entire suffix, without fixing the previous witness key.

The first deletion probe returned UNKNOWN in 30.12 seconds under a
30-second budget. The subsequent larger-budget run completed as recorded above.

The checkpoint is
[german-free-suffix.json](../experiments/results/german-free-suffix.json).
Requests for every suffix length 1–28 are prepared under
`data/generated/german-free-suffix/budget-30000ms/`.

The initial SAT lower bound is zero: the existing valid full key certifies
empty-text feasibility, independently checked without solving. This is not
a claim that any nonempty ending-at-word-29 suffix is SAT. The known 28-word
SAT prefix ends before word 29, so it cannot directly certify these suffixes.

## Reproduce or inspect locally

```sh
.venv/bin/python -m benchmarks.german_free_suffix \
  --timeout-ms 1800000 --resume
```

The completed checkpoint returns without rerunning solved inputs. In a fresh
search the larger budget retries the same 28-word suffix first. SAT would show that
the first word is needed when all remaining 28 words are retained. UNSAT
would remove that word from the conflict and begin a binary search for the
shortest UNSAT suffix ending at original word 29. Results are saved after
every solve; UNKNOWN stops the run without moving either bound.

This finds the shortest suffix ending at that word, not a smallest arbitrary
subset. Neither a minimal prefix nor a minimal suffix establishes that every
interior word is necessary.

Each solve has up to 30 minutes plus formula-construction time; no longer run
was started by the assistant. Budgets have separate input folders. Resume
checks source and code hashes, exact suffix requests and same-model settings,
and independently verifies cached SAT witnesses. UNSAT results remain
solver-reported, without independently checked proof certificates.

Focused tests check initial removal, unchanged parameters and word order,
empty-text certificate validity, UNKNOWN preserving bounds, larger-budget
retry, tamper rejection and binary search after a proved reduction.
