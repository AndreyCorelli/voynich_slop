# Tests

The word-dictionary pipeline and its focused test commands are documented in
[surface word mapping](../docs/word_mapping.md). It tests corpus barriers,
ambiguous morphology, n-gram probabilities, incremental/full equivalence,
seeded annealing, checkpoint resume and matched word-control invariants.

Run `uv run pytest -q`. `unit/` validates alphabets, encoders, prefix-freeness, and
generator capacity. `integration/` exercises solver SAT/UNSAT cases, independent
encoder round trips, boundaries, tokenization, and partial symbolic plaintext.
Hidden-recovery tests exercise dictionary membership, symbolic word lengths,
public-input serialization, timeout reporting, all five representations, and
independent verification. A tiny exhaustive Python encoder oracle checks SAT/UNSAT
outcomes without relying on Z3 to validate its own constraints.
Prefix-graph, finite-domain, unused-letter completion, and staged-configuration
tests cover the broader synthetic validation milestone. The current suite has
300 passing tests.
Null tests cover ownership, insertion boundaries, occurrence and run budgets, and
independent round trips. Optimization is checked against exhaustive tiny encoder
oracles, including unused alphabet mappings. CLI tests cover generation, replay,
sweeps, saved comparisons, input validation, and inconclusive exit codes.

Corpus tests cover source tampering, IVTFF annotations and uncertain boundaries,
Latin offsets and conventions, seeded exact sampling, control invariants, and CLI
ingestion and overwrite protection.

Selection tests compare one- and two-letter cycles against exhaustive independent
oracles, including non-lexical code orders, reset policies, symbolic token counts,
nulls, and optimization. Frontier tests cover paired samples, monotonic bounds,
checkpoint resume, UNKNOWN gates, prior-witness feasibility, and source gaps.

Sample-scaling tests verify uninterrupted clean spans, nested prefixes, fixed
non-ciphertext request fields, safe checkpoint resume, and preserved UNKNOWN cases.

UNSAT diagnostics test exact toy prefix/suffix boundaries, timeouts without false
minimality, checkpoint reuse, observation reduction, latent-word cycle counters,
mask validation and agreement with an independent exhaustive masked-model oracle.

Length-three diagnostics test synthetic gate enforcement, separation of hidden
inputs from truth, fixed hypotheses across formula retries and verified suffix
progression to the prefix. Dictionary formula tests prove flat/trie equivalence
with terminal lengths and padding, compare cyclic outcomes, and reject unsupported
null/optimization combinations. The masked oracle covers both encodings.

Guided recovery tests cover exact and rotated pins, unused alphabet entries,
unvisited homophones, unchanged global counters, release to a verified full-text
fit and conservative conditional evidence. An exhaustive tiny-key oracle checks
all pin subsets and rotations, including re-solving returned cores. Runner tests
check wrapped replay, unchanged models, resume and UNKNOWN without false exclusions.
