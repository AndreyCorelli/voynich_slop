# Three-round natural-passage calibration

This run uses the authorization to continue through three experiment-and-analysis
rounds. Older results and inputs remain frozen. The model still assumes public
fixed-two-glyph code boundaries and word lengths, with one injective code per
letter. Exact equality filtering uses ciphertext alone; the full existing
morphology inventory and alphabet are retained. Each fit has a 30-second solver
budget, a 60-second worker limit and durable phase timing records.

## Round 1: additional natural passages

Three new contiguous 24+6 Caesar blocks are selected after the previous frozen
block, using only raw-record eligibility, novel held-out types and training
coverage of held-out letters. They do not overlap each other or the preceding
control. Selection occurs before morphology coverage audits; a failed audit
does not cause passage replacement. Intervening records skipped by structural
eligibility are reported through exact start/end indices. Membership never
enters selection.

Source intervals, zero-based and half-open: **[10392,10422)**,
**[10422,10452)** and **[10453,10483)**. Canonical i/u normalization is unchanged.
Both complete default and broader inventory policies are audited. Every default
arm is NOT_ADMITTED. Broader coverage:

| Passage | Missing training | Missing holdout | Admission |
| --- | --- | --- | --- |
| 1 | None | None | Admitted |
| 2 | conlocarat | None | NOT_ADMITTED |
| 3 | None | auderent | Admitted |

Strict admission requires zero missing training forms. Holdout membership is
reported, not required. No target forms were added and no OOV rescue was used.
Admitted cases use new key seeds 5501/5503 and shuffle seeds 5601/5603.
Shuffles preserve each word's exact equality signature, length and code counts.

| Admitted passage | Positive first key | Training exact | Novel holdout exact | Shuffle |
| --- | --- | --- | --- | --- |
| 1 | SAT, verified; solver 0.450 s | 24/24 | 6/6 | UNSAT, 0.087 s |
| 3 | SAT, verified; solver 1.734 s | 22/24 | 4/6 | UNSAT, 1.491 s |

In passage 3, both training occurrences of `ad` decode as `ah`. Held-out
`cedentes` becomes `cehentes` and `auderent` becomes `auherent`; the other four
holdouts decode correctly. This is a valid inventory-consistent explanation,
not the true key. The first-key score stays **4/6** in its original artifact.
All control candidate counts are nonempty and match their positive counterparts.

```sh
.venv/bin/python -m benchmarks.latin_pattern_natural_replication --run
.venv/bin/python -m benchmarks.latin_pattern_natural_replication --validate
```

Artifacts: `experiments/results/latin-pattern-natural-replication`.

Decision: distinguish genuine key ambiguity from an implementation or scoring
error before choosing a refinement.

## Round 2: alternative-key existence

For each admitted positive, keep all constraints and add one disjunction requiring
at least one observed-code mapping to differ from its frozen first key. This
references the fitted mapping, not the generating truth. There is one existence
query per case, no enumeration or best-scoring-key selection.

| Passage | Second-key query | Interpretation |
| --- | --- | --- |
| 1 | UNSAT, solver 0.365 s | First observed-code key unique within model |
| 3 | SAT, verified; solver 1.633 s | First observed-code key ambiguous |

The alternative passage-3 key happens to recover all six holdouts. It is a
diagnostic witness and does **not** replace or improve the original 4/6 score.
UNSAT is a solver result without an independently checked proof certificate;
uniqueness covers observed codes only, not unobserved alphabet mappings.

```sh
.venv/bin/python -m benchmarks.latin_pattern_natural_ambiguity --run
.venv/bin/python -m benchmarks.latin_pattern_natural_ambiguity --validate
```

Artifacts: `experiments/results/latin-pattern-natural-ambiguity`.

Decision: add fixed adjacent natural context to the ambiguous case, without
ranking keys by a previously inspected holdout or introducing a frequency prior.

## Round 3: fixed preceding context

Add exactly the 24 raw source records immediately preceding passage 3, interval
**[10429,10453)**. The resulting training interval is **[10429,10477)**, 48
contiguous words; the unchanged six-word holdout remains **[10477,10483)**.
This is a refinement of the existing fixture, not another independent sample.
It overlaps earlier replication material and is not aggregated with it as
independent evidence. Prefix eligibility and full training coverage are checked
before fitting. Any failure would block the case, with no shifted retry.

The broader inventory admits all 48 training words. The generating key, inventory,
full alphabet and budgets remain unchanged. All six holdouts remain novel even
with the extra context. The observed training alphabet grows to 20 letters.
A new pattern-preserving shuffle uses seed 5702.

| Arm | Status | Filtering | Construction | Solver |
| --- | --- | --- | --- | --- |
| Extended natural positive | SAT, verified | 2.744 s | 8.709 s | 0.317 s |
| Matched extended shuffle | UNSAT | 2.791 s | 8.816 s | 0.138 s |

The first key now recovers **48/48 training words and 6/6 unchanged novel
holdouts**, including `auderent`, which is absent from the inventory. No holdout
membership or truth constrains fitting. Longer construction buys substantially
more constraining training evidence and shorter solving. The extended key has
not received an additional uniqueness audit.

This holdout was inspected during prior rounds. The improvement is a useful
adaptive diagnostic, **not a fresh independent holdout success estimate**.
Original scores remain unchanged; a new context-length policy needs validation
on previously untested passages.

```sh
.venv/bin/python -m benchmarks.latin_pattern_natural_context --run
.venv/bin/python -m benchmarks.latin_pattern_natural_context --validate
```

Artifacts: `experiments/results/latin-pattern-natural-context`.

## Verification, limits and next priority

All three new artifact validations pass. Ten targeted tests pass, including
contiguous nonoverlapping selection, unique/alternative-key existence, preserving
the original holdout on extension, strict rejection of missing prefix forms,
selected-inventory filtering, exact equality patterns and sparse language
membership. Validation regenerates coverage and inputs, verifies generating and
recovered explanations, reconstructs candidate counts, checks shuffle invariants
and recomputes frozen accuracy scores.

The three-round limit is reached. Natural passage recovery reproduces, but short
blocks can remain ambiguous, and strict morphology coverage can still exclude
true passages. More context resolves this particular observed ambiguity without
changing vocabulary or selecting a different first key by holdout accuracy.
None of this tests manuscript plaintext or demonstrates a general false-fit rate.

Next priority: preregister a small set of **fresh 48+6 natural controls** to test
the context policy without reusing this inspected holdout, retaining explicit
coverage admission and matched pattern-preserving shuffles. Then calibrate
multiple homophones while keeping boundaries public before removing boundary
assumptions. The exact distinct-code/distinct-letter filter is not sound for
multiple homophones and must be changed before that extension.
