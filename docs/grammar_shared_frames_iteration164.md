# Iteration 164: two-sided frames carry signal, but do not reliably equate type POS

The shared-frame relation is not ready as a reliable same-POS constraint. The primary rule yields no edges in the three short texts; in Cicero it produces25 correct pairs out of52 (48.08%), covering53/588 supported types (9.01%). This exceeds every fixed shuffle control but falls well below a dependable grammatical relation.

The design was frozen before edges: all opaque word types with>=5 occurrences are eligible, independent of POS, purity or catalogue membership. A frame is the ordered pair of immediate left/right opaque neighbors in the flat stream. Distinct middle types are connected when they share at least two distinct frames; one-frame support is a fixed secondary comparison. Repeated occurrences of one frame cannot satisfy two-frame support. No learned class boundary, anchors, plaintext names, sentence boundaries or POS enter edge construction.

Each of the four original cached streams is evaluated alongside16 fixed global word permutations (seeds16400–16415), preserving every type/token count. Streams/permutations were frozen before edges, and every original/null edge before reference labels or metrics. Exact modal UD POS per word type is the reference; mixed-POS words remain eligible. No new annotations, reserved material or sealed works were used.

| Dataset | Primary edges | Same modal POS | Supported types covered | Largest nonempty shuffle precision |
|---|---|---|---|---|
| Caesar | 0 | Unscored | 0/41 | No null edges |
| Jerome | 0 | Unscored | 0/27 | No null edges |
| Cicero | 52 | 25/52 (48.08%) | 53/588 | 25.93% |
| Palladius | 0 | Unscored | 0/15 | No null edges |

Empty sets are not perfect predictions. All16 Cicero nulls are nonempty, with mean precision14.36% and33–83 edges; none reaches the original48.08%. That is a real descriptive grammatical association in the long text, not high-precision recovery or four-author replication. Shared word types and overlapping edges are correlated.

| Dataset | Secondary one-frame edges | Same modal POS | Supported type coverage | Nulls at least as precise / nonempty nulls |
|---|---|---|---|---|
| Caesar | 1 | 1/1 | 2/41 | 1/15 |
| Jerome | 2 | 2/2 | 4/27 | 0/16 |
| Cicero | 863 | 202/863 (23.41%) | 363/588 | 0/16 |
| Palladius | 1 | 0/1 | 2/15 | 3/3 |

The tiny perfect short-text results do not justify relaxing the primary rule or claiming reliable coverage. In Cicero, lowering support increases coverage while reducing precision sharply. This is why both predeclared supports and empty outcomes remain explicit.

Cicero's strongest examples include me/te (both modal PRON, eight shared frames), que/c (both CCONJ, five), and quo/quibus (both PRON, four). Counterexamples include quod/ut (modal PRON/SCONJ), ego/est (PRON/AUX), and ego/etiam (PRON/ADV), each with three shared frames. Structural sharing alone does not uniquely determine global word-type POS. Enclitic and modal-reference caveats also remain.

A possible reference mismatch deserves a separate test: the edge is built from particular contexts, but correctness currently compares each word's global modal POS. An ambiguous word can take a different POS in those specific shared contexts. Current results do not show whether that explains many failures; do not relabel them by hand or count them as successes without a frozen occurrence-level check.

Next proposed diagnostic: evaluate the actual cached POS of matched occurrences within each shared frame, keeping the same supported types, two-frame primary rule and one-frame secondary rule. Freeze how repeated occurrences and frames are weighted; report both contextual token-pair agreement and the fraction of edges with no conflicting pairs, plus coverage. Carry each occurrence's POS with its token through the existing shuffle permutations. This tests contextual grammatical interchangeability rather than global type identity, with labels still confined to evaluation. Named POS, lexical identities and broad coverage remain unestablished.

Independent verification reconstructed all edges by direct intersections of per-type frame sets, checked all68 streams/permutations and modal references, and replayed16,747 edge records,136 metric groups and all contrasts. Distinct-frame support and empty outcomes were explicitly verified. No fitting or production model changes occurred; the dedicated audit covers the benchmark. Artifacts and manifest: `experiments/results/grammar-restoration/iteration164/`.
