# Latin follow-up without target-specific information

These experiments keep the same frozen Latin corpus, full 2,557,237-form
inventory, Caesar cipher, normalization, score, and evaluation rules. They add
no topic matching, guessed word list, target vocabulary filtering, original
boundaries, or anchors to inference. Existing language-model counts are reused;
this is not a claim that the system has no statistical prior at all. Latin and
the whole-word substitution channel remain hypotheses of the synthetic benchmark.

Truth is used after inference only, to evaluate outputs and recorded candidate
traces. Its diagnostic use does not supply search with the correct candidates.

## Baseline candidate audit

Each 4,000-proposal baseline visited roughly 2,450–2,480 of 5,663 types. All 19
types with >=100 public occurrences were visited in every run. The correct forms
were offered for 15–18 of those frequent types per run; 14–16 reached active
candidate lists, yet only 1–5 ever became correct during a trajectory. Offers
include both direct assignments and the implied second assignment of a swap.
This shows that missing frequent-word candidates alone cannot explain the
failure. It does not prove that frequent-word search or scoring is adequate.

Content-word support is much poorer: only 69–115 of 5,663 types had a correct
form offered in a baseline run. Of the total, 843 are absent from the inventory
and cannot be recovered. The detailed categories distinguish unavailable forms,
never offered forms, active candidates not selected, rejected proposals, and
correct assignments subsequently displaced. These flags describe search
exposure across time, not simultaneous recovery or calibrated probabilities.

The trace audit is checked against saved final keys, archived keys, and counts.
Accepted moves that lose a correct assignment receive independent full-stream
score-delta checks.

## Experiments fixed before their results

1. **More search:** increase the cap from 4,000 to 20,000 proposals, seeds 3/5/7,
   separately for random and frequency initialization. All other settings stay
   fixed, including the 600-second per-chain allowance. These are fresh runs
   with a longer annealing horizon, not extensions of cooled checkpoints.
   Proposal count and cooling duration change together.
2. **Observed/full-inventory proposal mixture:** at the original 4,000-proposal
   cap, draw random pool candidates and exploration proposals with probability
   .5 uniformly from training-observed forms and .5 uniformly from the entire
   inventory. Every form remains eligible, with a positive uniform probability.
   The score, other retrieval mechanisms, dictionary and training remain fixed.
   The mixture weight is fixed before evaluation and not tuned using truth.

Nearly 99% of this inventory was unseen in the small training corpus. The mixture
addresses random proposals spending almost all their effort on forms without
learned contexts. It introduces no new resource or cipher-specific fact; it
changes how existing model evidence is sampled. Uniform full-inventory sampling
remains the default. A zero mixture preserves its previous RNG sequence exactly;
checkpoints bind the mixture configuration and continue deterministically.

Both experiments retain the unanimous-three-run/public-count>=100 primary anchor
rule. All six seeds/initializer combinations are retained; no favorable seed is
selected using truth. Source-score-selected keys and per-seed literal results
are reported separately from consensus precision and coverage.

The proposal-mixture experiment can overlap the budget experiment. Elapsed times
therefore are not controlled speed comparisons. Every run reports completion and
actual proposal count; a timed-out run cannot be compared as an equal-cap result.

## Artifacts and reproduction

```sh
.venv/bin/python -m benchmarks.scalable_latin_search_budget
.venv/bin/python -m benchmarks.scalable_latin_proposal_mix
```

Both require the original `experiments/results/scalable-latin-caesar/v1/`
resources and fixture and create exclusive sibling directories:
`search-budget-v1/` and `proposal-mix-v1/`. Designs are written before inference.
Each contains full search artifacts, anchor metrics, fixed original/restored
excerpts, candidate audits, validation reports and a summary. The budget directory
also contains the original six-run support audit.

The original [Caesar report](scalable_latin_caesar.md) documents input provenance,
normalization, overlap checks and coverage limitations. No new model was trained.

## Coordinated-move check

The baseline evaluation-only corrective audit checks each of the 19 frequent
types in every saved score-selected key. Every available wrong assignment has a
negative full-score delta when corrected by a feasible single replacement or
swap: 18/18, 18/18, 14/14 in random runs and 17/17, 16/16, 17/17 in frequency
runs. All deltas are independently verified by rescoring the full stream.
These oracle diagnostic moves are never applied to the solver or treated as
inference results. Swap signs include the displaced owner's assignment; the
finding establishes a local barrier, not that the complete true dictionary is
necessarily worse than every nearby alternative.

A third, exploratory experiment therefore tests the existing bounded three-word
cycle mechanism on 10% of proposal steps, at the original 4,000-step cap and
seeds/initializers. It uses current candidate lists and model scores only. No
correct words or anchors are supplied. The .1 setting was fixed before its
results. It is a development diagnostic on the same work, not independent
confirmation. Invoke:

```sh
.venv/bin/python -m benchmarks.scalable_latin_proposal_mix joint
```

Outputs are under `joint-moves-v1/`. Candidate-support traces exclude unselected
internal cycle trials; selected joint moves and their effects are recorded and
validated. Consequently joint support counts are incomplete and must not be
compared as an exhaustive count of all considered corrections.

## Completed results

All 18 new chains completed their declared caps (168,000 proposals in total).
Every saved current/archive key was checked by full scoring, and all trace audits
and correct-assignment displacement validations passed. No input resources or
normalization conventions changed.

| Method | Random-start mean literal | Frequency-start mean literal |
|---|---:|---:|
| Original, 4,000 proposals | 4.21% | 5.49% |
| Longer horizon, 20,000 proposals | 4.26% | 5.48% |
| Observed/full-inventory proposal mixture, 4,000 | 1.19% | 5.50% |
| Three-word cycles, 4,000 | 4.11% | 5.68% |

The corresponding primary unanimous frequent-anchor results are:

| Method | Random: correct / wrong types | Frequency: correct / wrong types | Frequency token precision |
|---|---:|---:|---:|
| Original | 1 / 0 | 2 / 2 | 77.47% |
| 20,000 proposals | 1 / 0 | 2 / 2 | 77.47% |
| Proposal mixture | 0 / 0 | 2 / 3 | 65.19% |
| Three-word cycles | 0 / 0 | 2 / 5 | 48.15% |

For original and longer random runs the only primary anchor is `et`: 479 tokens,
2.34% coverage, one correct type. The frequency runs' two correct primary anchors
remain `in` and `et`, 987 tokens / 4.82% correct coverage. Larger erroneous
unanimous sets are not progress. A zero-anchor set has undefined precision, not
zero errors at meaningful coverage.

The random proposal-mixture regression occurs in all three seeds. Three-word
cycles improve one random run but regress in two; their frequency mean gains
only .19 percentage points, and source-selected recovery falls from 5.11% to
4.88%. Its frequent wrong unanimous mappings are `ad→non`, `cum→est`,
`quod→autem`, `non→de`, `est→quae`. Joint moves were genuinely exercised:
222 cycles were accepted across the three random chains and 814 across the
frequency chains. A failed result is not attributable to the feature being idle.

Longer random search visits 5,212–5,241 of the 5,663 types, versus 2,455–2,479
before. Correct forms offered increase from 69–75 types to 128–140, but frequent
correct forms ever acquired remain 3/1/5 by seed, unchanged from baseline. Thus
broader visitation helps candidate exposure while failing to materially improve
recovery. Content-word candidate starvation remains severe; the full dictionary
is available in principle but only a tiny fraction of correct assignments is
actually considered.

All 100 available wrong frequent assignments in the original six score-selected
keys have negative individually corrective move deltas. This finding, together
with the earlier full-reference comparison, warrants investigating the objective
and coordinated inference. It does not prove an intrinsic Latin limitation or
that a larger global move would also be disfavored. Correct candidates can be
locally expensive inside an otherwise incorrect dictionary.

The new chain wall times sum to 1,584 seconds (26.4 minutes); this is neither
elapsed bundle time nor CPU time because independent experiments overlapped.
Maximum process high-water RSS was approximately 663 MB, including earlier
analysis/load allocations in shared drivers. Resource loading and evaluation
are additional to reported search time.

**Decision:** no default changes. None of these three generic modifications
improves useful anchor recovery reliably. In particular, neither more compute
nor more training-observed random candidates resolves the problem. This is one
previously inspected work with three seeds, so small literal differences should
not be treated as generalization estimates.

The proposal-mixture implementation is retained as an optional config field
`RetrievalConfig.attested_mix`, default 0.0. Checkpoint and protocol compatibility
preserve historical uniform-sampling runs. Distribution/full-support and exact
continuation tests pass, alongside all **126 relevant tests**.

The consolidated machine report is
`experiments/results/scalable-latin-caesar/target-independent-comparison-v1.json`.
All original/restored inspection files, per-run results, public consensus,
private evaluation, trace attribution, and validation artifacts are retained in
the experiment directories described above. The original baseline outputs are
preserved; supplementary corrective audits are separate files.
