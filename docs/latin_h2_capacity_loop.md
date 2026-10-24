# Seven-iteration H2 capacity and joint-support loop

The prior assisted vocabulary ladder recovered the seed-5101 fixture exactly
through 8,192 forms but left both arms UNKNOWN at 16,384 and 32,768. This loop
keeps its ciphertext, free homophone-choice model, dictionary, first-key scoring
and budgets unchanged: 30 seconds of Z3 search and 60 seconds per worker.
No true-key assignments or homophone-selection cycle constraints are added.

Two sound necessary-condition refinements were tested:

- **Capacity matching:** expand each plaintext letter into two slots and find a
  bipartite matching for observed codes. Test each code/letter edge for support
  in a complete matching, prune unsupported edges, and repeat word-domain
  propagation. This detects saturated groups beyond singleton saturation.
- **Joint word support:** for every pair of training occurrences sharing at
  least two codes, retain only candidates whose assignments to all shared codes
  jointly occur in the other word's candidate list. Alternate these semijoins
  with capacity propagation to a fixed point. This preserves cross-position
  correlations that unary domains discard; it does not require distinct codes
  to represent distinct letters.

Original frozen implementations are unchanged. New helpers and benchmark
wrappers have frozen code hashes. Positive/control arms form one iteration;
remaining inputs within each module are prepared before fitting.

| Iteration | Method and fixture | Vocabulary | Positive | Propagation / solver seconds | Exact train / novel holdout | Shuffle |
|---:|---|---:|---|---|---|---|
| 1 | Matching, 5101 | 8,192 | SAT | 1.102 / 23.474 | 24/24, 3/3 | UNSAT |
| 2 | Matching, 5101 | 16,384 | UNKNOWN | 1.233 / 30.056 | Unevaluated | UNSAT |
| 3 | Matching + semijoin, 5101 | 8,192 | SAT | 2.647 / 0.002 | 24/24, 3/3 | UNSAT |
| 4 | Matching + semijoin, 5101 | 16,384 | SAT | 4.286 / 0.142 | 24/24, 3/3 | UNSAT |
| 5 | Matching + semijoin, 5101 | 32,768 | UNKNOWN | 6.713 / 30.062 | Unevaluated | UNSAT |
| 6 | Replication, 5102 | 16,384 | SAT | 3.407 / 0.464 | 24/24, 3/3 | UNSAT |
| 7 | Replication, 5103 | 16,384 | SAT | 1.312 / 0.002 | 24/24, 3/3 | UNSAT |

Matching does not reduce positive candidate counts in iterations 1–2. It does
detect a contradiction in both shuffles; their Z3 checks become effectively
immediate, though building their remaining word constraints still takes time.
Joint support reduces positive candidate rows from 100,146 to 24 at 8,192 forms
and from 201,730 to 15,430 at 16,384. Construction at 16,384 falls from 8.97 to
0.72 seconds. At 32,768 it reduces 409,558 rows to 224,206, but search remains
unresolved. Rows count training occurrences separately.

Iterations 6–7 replicate the successful 16,384-form setting on the two original
independent synthetic fixtures, seeds 5102 and 5103. Each retains its own whole
512-word generating pool and extends it using the same independently ordered
eligible vocabulary (extension seed 6201). Both inputs are frozen before either
fit. These are independently generated plaintext/key/shuffle fixtures, with
assisted vocabulary coverage and synthetic rather than natural prose. There is
no fixture replacement or addition of individual truth words.

Both replications recover every training occurrence and novel holdout from their
first returned keys; both matched shuffles are UNSAT. Together with seed 5101,
this gives 72/72 training occurrences and 9/9 novel holdouts at 16,384 forms on
three independently generated synthetic fixtures. Positive construction takes
0.72, 2.82 and 0.03 seconds respectively, in addition to propagation and search.
Seed 5102 retains 62,576 candidate rows; seed 5103 reduces to 24. Recovery can
therefore succeed even when propagation does not isolate all words.

Eight targeted tests pass: exhaustive small matching support versus enumeration,
a saturated nonsingleton group, joint-support pruning, preservation of global
solutions under the combined filter, and existing H2 solver/capacity checks.
Every experiment validates frozen metadata, reproduces candidate pruning,
verifies recovered training membership and global capacity, and recomputes the
first-key holdout scores. All seven pairs (14 arm records) are retained with
phase/timing files. Validation records are stored in these directories:

- `experiments/results/latin-h2-matching`
- `experiments/results/latin-h2-semijoin`
- `experiments/results/latin-h2-semijoin-full`
- `experiments/results/latin-h2-semijoin-replication`

```sh
.venv/bin/python -m benchmarks.latin_h2_matching --run
.venv/bin/python -m benchmarks.latin_h2_semijoin --run
.venv/bin/python -m benchmarks.latin_h2_semijoin_full --run
.venv/bin/python -m benchmarks.latin_h2_semijoin_replication --run
```

Each module also supports `--validate`. Existing artifacts are reused rather
than refitted; held-out outcomes never select among alternative keys.

This is a meaningful calibration improvement within the assisted, fixed-boundary
H2 model. It does not calibrate natural Latin, manuscript transcription, hidden
boundaries, contractions or historically realistic selection rules. The shuffled
controls are matched distortions, not a sample of every accidental-fit mechanism.
UNSAT is a bounded-model result without an independent proof certificate;
UNKNOWN remains unresolved and its holdout accuracy unevaluated. These timings
are single runs, not performance distributions or a precise size threshold.

The seven-iteration limit is reached. Next recommendation: compare compressed
word-automaton membership with direct candidate disjunctions **after the same
matching/semijoin pruning**, on the frozen 32,768-word pair, with 16,384 as a
resolved regression case. This isolates representation cost while preserving
admissible keys, budgets and scoring. Earlier layered H2 experiments lacked this
joint pruning, so they do not answer that comparison. Full-vocabulary and natural
H2 calibration remain ahead of manuscript-language inference.
