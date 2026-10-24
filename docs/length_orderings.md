# Diversifying public length-vector order

Two optional strategies diversify the shortest-first public length search. They
use only observed ciphertext bounds and vocabulary candidates; no truth is read.
The allowed length domains and cipher model are unchanged.

- `balanced` interleaves a diagonal sweep of per-word length ranks with the
  complete shortest-first product. After the minimum vector, its next suggestion
  increases every word to its next admissible length where available. Later
  diagonal suggestions spread attempts across still-higher ranks. Duplicates are
  skipped, and the underlying shortest-first stream preserves completeness.
- `candidate_rich` ranks each word's lengths by the number of public candidate
  vocabulary entries supporting them, favoring greater support and breaking ties
  by shorter length. Its product is enumerated by total preference rank, with
  lexicographic vector tie-breaking. These counts measure candidate-set population,
  not natural-language probability or word frequency.

Both strategies retain every vector in their finite product. The same public
identity/proper-prefix length filters apply after ordering. SAT requires a verified
full-instance fit. Branch UNSAT rejects that vector; UNKNOWN remains unresolved.
Overall UNSAT still requires exhaustion with every attempted branch proved UNSAT.
A branch/time budget cannot supply that conclusion.

The calibration tries both orderings on the saved seed-7 six- and eight-word
controls with four branches per strategy/case and 30 seconds per solve. These are
the same public inputs, formula and budgets used by the earlier shortest-first
intermediate run. Each strategy starts fresh, and shared vectors are deliberately
rerun. Construction and enumeration add to total wall time. Single-run timing
comparisons are observations, not statistical speedup estimates.

```sh
.venv/bin/python -m benchmarks.length_search \
  --config experiments/configs/length-search-diverse.json \
  --output experiments/results/length-search-diverse.json \
  --artifacts data/generated/length-search-diverse
```

The report identifies the strategy, candidate-count histograms, public source
hashes, every attempted vector and result, enumeration exhaustion and total time.
Branch wrappers can be replayed with the segmentation-diagnostic runner; replay
checks the recorded conditional branch rather than repeating enumeration.
The original shortest-first default and configurations remain unchanged.

Tests establish completeness and uniqueness for both streams on small products,
verify the candidate-support preference, retain public length relations and check
UNSAT/UNKNOWN classification under each strategy.

## Recorded result

| Words | Ordering | Branch outcomes | Total time |
|---:|---|---|---:|
| 6 | balanced | UNSAT, UNKNOWN, UNKNOWN, UNKNOWN | 116.34s |
| 6 | candidate_rich | UNSAT, UNKNOWN, UNKNOWN, UNKNOWN | 119.22s |
| 8 | balanced | UNSAT, UNKNOWN, UNKNOWN, UNKNOWN | 122.50s |
| 8 | candidate_rich | UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN | 127.19s |

Neither alternative ordering found a verified fit in either control. All
four searches ended UNKNOWN without exhausting their admissible vectors. Across
16 branches, three were proved UNSAT and thirteen timed out. The earlier
shortest-first intermediate runs likewise found no fit in four branches each.
This bounded comparison shows no recovery improvement; it does not reject the
full models, timed-out vectors or either ordering at a larger budget.

The default stays shortest-first; alternatives remain available for experimentation.
All 410 tests pass. A distinct next optimization would restrict observed codeword
choices to publicly observed substrings, reducing key-domain search rather than
reordering only length vectors.
