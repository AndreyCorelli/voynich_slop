# Broader hidden-plaintext validation

The broader synthetic gate now passes on the configured fixture: 24 plaintext
symbols, 35 Latin vocabulary entries, up to two homophones per symbol, code
lengths 1–3, preserved word boundaries, and prefix-free decoding. Plaintext,
plaintext word lengths, key, segmentation, and choices are hidden.

All nine 10/25/50-word cases across seeds 7/17/1729 returned verified SAT within
the ten-second solver budget. Their ciphertext checksums match the nine cases
that timed out in the previous array-based benchmark. This improves search without
changing the allowed cipher family or supplied language model.

## Dictionary propagation

Candidate words are filtered by public length bounds. If two ciphertext words
share at least K times the maximum code length in leading tokens, prefix-free
decoding guarantees at least K equal leading plaintext tokens. If a complete
ciphertext word is a strict prefix of another, its plaintext must be a strict
prefix of the other's plaintext. Arc consistency removes unsupported vocabulary
candidates. Z3 also receives these prefix consequences explicitly.

The inferences use ciphertext and public constraints only, and make no deductions
from partial suffixes. They apply to the current prefix-free, boundary-preserving
model without nulls. Revisit them when adding nulls or context.

## Prefix intervals and unused-code completion

A code of length ell identifies an aligned interval of width `c ** (L - ell)`
among the `c ** L` leaves of a prefix tree, where c is ciphertext alphabet size
and L is maximum code length. Codes are prefix-free exactly when their intervals
are disjoint. With alphabet x/y and maximum length two:

| Code | Maximum-depth leaves | Interval |
| --- | --- | --- |
| x | xx, xy | [0, 2) |
| yx | yx | [2, 3) |
| yy | yy | [3, 4) |

Unobserved letters need one unused maximum-depth leaf each. The solver reserves
that capacity, and Python assigns their codes after solving. Every configured
letter still receives a legal code and contributes to reported capacity. Tests
check both exact-capacity completion and insufficient-capacity UNSAT cases.

Constructive completion preserves existence of an explanation while removing
arbitrary placements of unused codes from search. It does not enumerate equivalent
keys or establish minimum complexity. Revisit unused-code length normalization
before adding complexity optimization.

## Finite-domain search

The new default `finite` representation uses interval codebooks, bounded scalar
code selections, and explicit local substring transitions. It removes symbolic
array lookups from encoding constraints. All integer variables have explicit
finite ranges; Z3's `qffd` tactic compiles them for finite-domain/SAT search.

Segmentation stays symbolic. Python enumerates individual substring edges, not
complete segmentation paths. Code selections are linked only to the letters
allowed by dictionary candidates at that position.

Representations `ite`, `array`, `interval`, and `chunk` remain available for
comparison. `interval` uses observed prefix windows; `chunk` adds local substring
matching while retaining array selection. Neither alone passed the broader
ten-word pilot within ten seconds. Finite scalar selection and the SAT backend
made the larger difference in these experiments.

## Staged workloads

[staged-recovery.json](../experiments/configs/staged-recovery.json) specifies
alphabets, bounds, vocabulary widths, seeds, sizes, timeout, and representation.
Inputs are validated before generation. Stage identifiers must be unique and
safe for filenames; generator capacity and dictionary/alphabet compatibility are
checked. Each hidden solve reloads a public JSON request; ground truth stays
separate. Checkpointed reports distinguish experiment completion from validation
success and include public-request checksums.

Changing vocabulary width also changes the generated plaintext sample. These
are workload measurements, not a controlled estimate of vocabulary size alone.
Plaintext and key generation each use the reported seed in separate generators;
occurrence choices use seed + 1.

The alphabet `abcdefghiklmnopqrstuvxyz` has **24** symbols: u and v remain
distinct. Earlier documentation called it 23; saved inputs and capacity counts
already contained the correct definition. Unobserved letters stay in the encoder.

## Measurements

Python 3.14.4, Z3 4.16.0, macOS arm64. Times measure solver checking; construction
is recorded separately. Single runs are observations, not performance guarantees.

Standalone broader gate, H ≤ 2, code lengths 1–3, 35-word vocabulary:

| Words | Seed 7 | Seed 17 | Seed 1729 |
| --- | ---: | ---: | ---: |
| 10 | 2.023 s | 1.264 s | 1.603 s |
| 25 | 3.902 s | 1.267 s | 2.770 s |
| 50 | 2.546 s | 2.261 s | 2.689 s |

All nine explanations passed independent dictionary membership, bounds,
prefix-freeness, exact encoding, decoding, and segmentation checks. Eight matched
the original plaintext; the ninth was another valid vocabulary explanation.
Original-key or plaintext uniqueness is not claimed.

The staged matrix has 54/54 verified SAT results: three seeds, three sample sizes
(5/10/25), and six stages. Each stage passed its validation check.

| Stage | Vocabulary | Verified SAT | Solver time range |
| --- | ---: | ---: | --- |
| Monoalphabetic | 35 | 9/9 | 0.027–0.164 s |
| Length-one homophonic, H ≤ 2 | 35 | 9/9 | 0.206–0.433 s |
| Verbose, H ≤ 1, length 1–3 | 35 | 9/9 | 0.230–0.806 s |
| Verbose, H ≤ 2, length 1–3 | 5 | 9/9 | 0.088–0.227 s |
| Verbose, H ≤ 2, length 1–3 | 15 | 9/9 | 0.277–0.928 s |
| Verbose, H ≤ 2, length 1–3 | 35 | 9/9 | 0.791–3.797 s |

Prefix filters removed 664 candidate occurrences across the staged runs. Neither
final matrix had UNKNOWN or UNSAT outcomes. Earlier pilots and the interval
baseline retain their timeouts in separate result files.

197 tests pass. They cover all five representations, including a Python oracle comparing 36
tiny ciphertexts per representation against independently enumerated encoders and
dictionary plaintexts. Additional tests cover prefix inference, incomplete
prefixes, atomic tokens, unused-code completion, unary alphabets, and configuration
validation.

## Reproduction

```sh
uv run pytest -q
uv run python benchmarks/staged_recovery.py \
  --output experiments/results/staged-finite.json \
  --artifact-dir data/generated/staged-finite
uv run python benchmarks/hidden_recovery.py --representation finite \
  --profiles latin-hidden \
  --output experiments/results/finite-full-gate.json \
  --artifact-dir data/generated/finite-full-gate
```

Replay a broader 50-word case without loading its original plaintext or key:

```sh
uv run python benchmarks/hidden_recovery.py \
  --request data/generated/finite-full-gate/inputs/latin-hidden-seed7-words50.json \
  --output experiments/results/finite-replay.json
```

No new dependencies or external corpora were needed. This gate validates a bounded
family and a small finite vocabulary, not unrestricted Latin or Voynich recovery.
The next milestone can add bounded nulls, explicit complexity objectives, and a
full CLI, followed by corpus acquisition and controls.
