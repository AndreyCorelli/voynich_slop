# Iteration 113: literal loss of extra-context evidence

This source-only challenge distinguishes removing a candidate from the repair catalogue (iteration110) from removing its actual occurrences. Both frozen long-context policies,109 and111, are tested without recalibration or author evaluation.

The source calibration input has829 sentences/10917 tokens. Its first100 sentences are protected exactly. For each of the16 candidate types, all occurrences in the remaining729 sentences are deleted before applying each global corruption. All64 cross-class errors and three clean/same-class controls are retained for every deletion:1072 cases. Candidate eligibility is recomputed from the resulting text; the original true pair remains the reference even when an endpoint disappears entirely. Both policies use their existing full-volume branch.

This is a synthetic deletion diagnostic. It changes token adjacency, contextual evidence, occurrence counts, and eligibility together. Sentence slots remain829, the same bootstrap sentence weights are used across all conditions, and no sentence becomes empty. Nominal sentence count therefore remains constant, but token evidence does not. It is not an isolated causal estimate of any one mechanism or a guarantee for natural missing-word inputs.

The removed type becomes entirely absent for `ac`, `ex`, and `sine`. Three more types (`atque`, `c`, `per`) retain some occurrences but fall below the existing five-occurrence/three-sentence support gate. The other10 remain supported. Between four and231 tokens are deleted, depending on type; the protected query stays unchanged. No new grammar labels, PP evaluation, reserved data, sealed lexical test, or policy fitting is used.

The complete-input baseline uses the stored iteration102 features and bootstrap results. The matched catalogue-only comparison uses iteration110, evaluated under the same two policies. These comparisons distinguish unchanged observed context with a smaller candidate catalogue from literal text deletion with a potentially still-eligible candidate.

## Result: strict policy is selective, but zero-error behavior does not survive

| Literal-loss stratum | Cases | 109 correct / wrong | 111 correct / wrong |
|---|---:|---:|---:|
| All errors |1024|914 /8|667 /1|
| True pair supported |976|914 /0|667 /0|
| True pair unsupported |48|0 /8|0 /1|
| True endpoint literally absent (subset) |24|0 /4|0 /1|
| Clean/same-class controls |48|0 /0|0 /0|

Observed call precision is99.13% for109 and99.85% for111, but pooled precision hides the unsupported-case failures. The strict rule's wrong call is `remove sine`, corruption `sine/sed`, recommendation `ac/sed`: the absent endpoint cannot be repaired and the rule instead picks a plausible rival. Its gain.8390, gap.2623, and bootstrap rank stability.5430 pass all three frozen guards. Bootstrap uncertainty does not rule out systematic fallback errors. No cutoff is changed to fit this example.

The source complete-input baseline remains10964/0 and11148/0 over64 errors. Catalogue-only omissions gave109896/16 and111674/0 over1024 errors. Literal loss is not uniformly harder: it retains the deleted type as a repair candidate when sufficient occurrences survive in the protected prefix. This explains why comparing pooled hit totals alone is misleading; support and literal-absence strata are reported separately.

The earlier positive grammatical restorations on Caesar and Jerome remain preserved. This new source-only finding limits their generalization: omission-aware calibration is helpful but does not certify abstention when evidence actually vanishes. No new grammatical restoration or lexical recovery is claimed here.

Next hypothesis: compare a swap against an explicit one-anchor-error/unknown-partner alternative, rather than requiring the optimizer to explain suspicious evidence with a supported two-anchor swap. Test that model comparison on source data with frozen coverage and unsupported-case guards; do not add a `sine` exception or select stricter thresholds from this counterexample. Simply raising stability after seeing this result would not establish a general solution.

Relative to matched catalogue-only omissions,111 changes120 actions:63 previous correct repairs are lost,56 are gained, and one new wrong call appears. Thus neither candidate-pool omission nor nominal context volume adequately predicts all decisions under literal evidence loss.

Verification:25 focused tests pass. The audit verifies2177 frozen input hashes, reconstructs all16 deletion views and their unchanged prefixes, replays1072 rankings/2144 blind actions, recomputes67000 bootstrap columns and their occurrence counts/support, and independently reruns1000 clean-case pair classifier totals. Detailed strata, all nine wrong actions across policies, and matched comparisons are preserved in `experiments/results/grammar-restoration/iteration113/`.
