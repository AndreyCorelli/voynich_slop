# UNSAT boundary and conflicting observations

The diagnostic runners reuse the exact f3r span, 5,665-entry vocabulary, alphabets,
H2/L2 bounds, prefix-free codebook and text-wide per-letter cycles from
[sample scaling](sample_scaling.md). No new text or dependency is needed.

## What each search establishes

`benchmarks/unsat_boundary.py` maintains a verified SAT lower bound and a proved
UNSAT upper bound on the prefix length. It proves the first UNSAT prefix only
when these bounds are adjacent. UNKNOWN never moves either bound. A completed
report means the scheduled checks finished; it does not imply proven minimality.
The runner checkpoints every attempt and can resume with a different timeout
schedule. Existing resolved outcomes are reused; an unresolved attempt with at
least the requested budget is retained rather than repeated.

It also searches for the shortest contiguous UNSAT suffix ending at the upper
bound. This is a separate minimum, not a minimum arbitrary subset. Removing a
leading block preserves a valid implication: each letter's inferred homophone
order can rotate to match its phase at the new start. Deleting interior words
would change occurrence counters and cannot establish the same claim.

Four comparisons change one setting at the upper bound: free selection, cycles
resetting at word boundaries, H3, and maximum code length 3. Free/H3/L3 widen the
model. Word reset is a different selection rule and is not a superset of text
reset. UNKNOWN in a comparison does not show that the change repairs the fit.

`benchmarks/observation_core.py` removes whole words' **glyph observations** while
keeping every original word as a latent dictionary word, its ciphertext length,
and its place in the cycle. Prefix pruning and repeated-word equalities are
rebuilt using retained observations only. Each dropped observation requires an
UNSAT check. A retained observation is proved necessary only if removing it is
SAT; UNKNOWN leaves necessity unresolved. The resulting core is conditional on
all word lengths and latent context. It is neither a minimum number of words nor
a standalone ciphertext formed by concatenating the retained words.

Masked SAT models are independently verified against retained observations,
all original lengths, dictionary membership, codebook constraints and cycles.
They may generate different glyphs at omitted words. Mask files have an explicit
wrapper and a separate replay command so they cannot be mistaken for ordinary
full-observation solver inputs.

## Reproduction

```sh
uv run python benchmarks/unsat_boundary.py
uv run python benchmarks/unsat_boundary.py --resume --budgets-ms 10000
uv run python benchmarks/observation_core.py --timeout-ms 10000
uv run python benchmarks/observation_core.py \
  --replay data/generated/observation-core/mask-0.json
uv run pytest -q
```

Boundary outputs are checkpointed in `experiments/results/unsat-boundary.json`;
public inputs are in `data/generated/unsat-boundary/inputs/`. Observation reduction
has its own report, `experiments/results/observation-core.json`, and wrapped inputs
in `data/generated/observation-core/`. Every attempt records its result and time
budget. Wrapped inputs retain the full request even when the core run starts
while the boundary report is still being updated.

Regression tests cover an exact toy boundary and suffix, UNKNOWN handling,
completed resume, deletion-minimal observation reduction, preservation of counters
through latent words, index validation and independent exhaustive tiny masked
models. Earlier full-vocabulary synthetic recovery gates remain incomplete;
these diagnostics do not establish manuscript language or a probability for the
broader Latin encryption hypothesis.

## Measured boundary

The current run verifies SAT at 6 words and UNSAT at 23 words. Prefix lengths
7–22 remain UNKNOWN at the attempted budgets; the minimal UNSAT prefix is not
proved. Early midpoint checks received up to 120 seconds, while the subsequent
scan used ten-second checks. One interrupted check is recorded as UNKNOWN too.

The shortest UNSAT suffix ending at word 23 has **11 words**, source records
485–495 (zero-based):

```text
chol daiin cthy schey chor chal chag cham cho qokol chololy
```

Starting one word later yields verified SAT, certifying this contiguous suffix
minimum. It does not certify a shortest UNSAT block elsewhere in the manuscript.

Observation reduction leaves five glyph observations: indices 12, 17, 20, 21,
and 22 of the 23-word prefix, namely `chol chal cho qokol chololy`. Removing the
other 18 observations still gives UNSAT with all 23 word lengths and latent
cycle positions retained. Each of the five remaining deletion trials timed out;
this is a proved reduced conflict, not a proved deletion-minimal core.

## Model comparisons

| Change at the 23-word prefix | Result | Check time |
| --- | --- | ---: |
| Free homophone selection | UNSAT | 8.89 s |
| Cycles reset at each word | UNSAT | 2.91 s |
| Up to three homophones per letter | UNKNOWN | 142.29 s |
| Maximum code length three | UNKNOWN | 62.77 s |

Free selection was retried with a 60-second requested timeout after an initial
ten-second UNKNOWN. H3 and L3 were also retried at 60 seconds. Z3's timeout is
not a hard wall-clock cap for this tactic: actual check and construction times
are recorded separately. H3 exceeded the requested limit substantially.

The free-selection UNSAT excludes this particular vocabulary/H2/L2 model without
requiring the cycling rule. It does not exclude all Latin, longer codes, more
homophones, different glyph units or alternative word boundaries. Word reset
also fails in this bounded model. No relaxation tested here has a verified SAT
repair for the full 23-word prefix.

For an additional interpretation check, the five retained words were solved as
a **new standalone text** with free selection and yielded verified SAT. Its
public input is
`data/generated/unsat-boundary/inputs/free-subset-12-17-20-21-22.json` and result
is in `experiments/results/free-small-conflict.json`. This reinforces the need
to state the original context of the masked contradiction. The SAT model for a
new text does not repair the original 23-word prefix.

The full regression suite passes **311 tests**.
