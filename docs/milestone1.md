# Milestone 1 evaluation

Implemented one shared bounded integer representation for three cipher families.
Each plaintext symbol has between one and H active code slots, each with bounded
length and glyph IDs. Unused slots are zeroed. Active homophones have canonical
lexical ordering to remove permutations. Every pair of active codes differs before
either code ends, establishing global prefix-freeness and unique decoding.

Per-occurrence plaintext IDs, homophone choices, and cumulative word offsets are
symbolic. Ciphertext is an immutable Z3 integer array. Selected code glyphs must
equal observed glyphs at symbolic offsets; the final offset equals word length.
No segmentation list is enumerated in Python. This representation has not yet been
compared against string/sequence or bit-vector formulations.

The solver allocates at least one code to every configured plaintext alphabet
member, including unobserved members. These entries consume capacity and can make
a model UNSAT. Use an explicit alphabet and report it; do not silently shrink it.
Pairwise prefix constraints grow quadratically with available codebook slots.

## Recorded benchmark

Command: `uv run python benchmarks/recovery.py --seed 1729 --timeout-ms 10000`.
Environment: Python 3.14.4, Z3 4.16.0, macOS arm64. A single run on a hand-authored
fixture with vocabulary `amo amor ora oro mora`, four plaintext symbols, and eight
ciphertext symbols. Each larger sample extends the same seeded 50-word sequence.
Keys and occurrence choices are hidden; plaintext is supplied to the solver.

| Family | 10 words | 25 words | 50 words |
| --- | ---: | ---: | ---: |
| Monoalphabetic | 0.002 s | 0.003 s | 0.005 s |
| Homophonic, H ≤ 2 | 0.024 s | 0.068 s | 0.184 s |
| Verbose, H ≤ 2, length 1–3 | 0.102 s | 0.283 s | 0.600 s |

All nine results were SAT and independently verified in both directions.
Times measure solver checking only. At 50 words, construction took approximately
0.062, 0.090, and 0.164 seconds respectively. The verbose instance had 596 symbolic
integer variables, 1,750 asserted constraints, and eight active recovered codes.
Measurements are observations, not performance guarantees or statistical estimates.
Detailed results are generated in `experiments/results/milestone1.json` and excluded
from version control; rerun the command to reproduce inputs and record local times.

37 tests cover seeded round trips, impossible mappings, prefix collisions,
homophone and code-length bounds, one token, repeated tokens and words, empty text,
atomic multi-character glyphs, invalid input, and partially symbolic plaintext.

## Limits and next milestone

The small four-symbol fixture establishes basic correctness and tractability.
It cannot establish full-alphabet performance or hidden-plaintext recovery.
UNKNOWN is recorded with the solver's reason; it is never interpreted as UNSAT.
No optimality or key uniqueness is claimed. The seed makes generated samples
reproducible; equivalent recovered models may vary between Z3 versions.

Next, benchmark a full Latin alphabet and multiple seeds, then add a short explicit
dictionary model with symbolic plaintext. Validate recovery with plaintext, key,
choices, and segmentation all hidden. Add bounded nulls, optimization, validated
experiment configurations, and a CLI as milestone 2. Defer conclusions about
Voynich until hidden-plaintext synthetic recovery is reliable. Prefix-free codes
remain an explicit restriction; relaxing it requires a separate decoding model.
