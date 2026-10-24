# Paper-fidelity audit: iterative EM

Reference: [Ravi and Knight (2011), Sections 2–2.3](https://aclanthology.org/P11-1002.pdf).
This is a method implementation with development diagnostics, not an exact
published-result reproduction. Bayesian mathematical contracts remain pending.

| Choice | Published description | Current implementation |
| --- | --- | --- |
| Alignment | Word substitution preserves order | Same |
| Channel | P(cipher word given plaintext word) | Same; source rows normalize |
| Excluded types | Collapse into UNKNOWN | Same; a modeled context symbol |
| Expansion | Experimental sizes 100 through 350, increments of 50 | Library defaults match; natural pilot deliberately uses 10/20/30 |
| Confidence | Strict probability above 0.5, then fixed to one | Same direction and strict threshold |
| Reciprocal exclusion | Describes deleting other destinations for that plaintext row | Only that row is constrained; collisions allowed |
| LM | Statistical word n-gram model | Additive-smoothed bigram reference; exact smoothing match unverified |
| Boundary handling | Segmented expressions/sentences | Heuristic punctuation/paragraph segmentation; not gold boundaries |
| UNKNOWN freezing | Not explicitly resolved in the paper | Exclude UNKNOWN rows and destinations because aggregate identity changes |
| Unfixed initialization | Insufficient implementation detail | Fresh seeded positive random rows at each stage |
| EM stopping | Insufficient implementation detail | Configurable updates and absolute corpus-likelihood tolerance |
| Final decoding | Viterbi with cubed channel probability | Exponent 3 |
| Data | Temporal expressions and Transtac | Different Gutenberg works; no numerical comparability claim |
| Scoring | Exact token recovery | Whole-stream token recovery, coverage ceiling and consistency diagnostics |

Likelihood monotonicity is checked only within a stage. Different stages change
both the LM and collapsed ciphertext, so their likelihoods are not directly
comparable. A probabilistic channel and token Viterbi decoder do not impose the
injective dictionary constraint planned for the type-consistent extension.

Before claiming closer reproduction: verify source-model construction against
available original resources/code, resolve initialization and UNKNOWN details,
obtain the original datasets if available, and run the published vocabulary
schedule at a measured feasible budget. Until then report every deviation.
