# Contextual profile likelihood ratios — iteration 75

**Better than the tested posterior-overlap scores, but insufficient for lexical search.** The primary ratio score prefers the original in333/1273pairs (26.16%), versus207 (16.26%) for iteration71. Its shuffled-context control wins283 (22.23%): only3.93percentage points separate real from shuffled context. The65%primary gate and required5point shuffle margin fail. No historical first-corruption phase, search or nuclei were measured.

| Score | Original wins | Wrong candidate wins | Ties |
|---|---:|---:|---:|
| Ratio with candidate word/POS weights, context | 333 | 940 | 0 |
| Same, shuffled context | 283 | 990 | 0 |
| Same, grammatical prior | 114 | 1,159 | 0 |
| Context-only normalized ratio, context | 499 | 645 | 129 |
| Same, shuffled context | 475 | 668 | 130 |
| Same, grammatical prior | 0 | 233 | 1,040 |
| Iteration71 weighted posterior compatibility | 207 | 1,066 | 0 |
| Source word frequency | 27 | 1,246 | 0 |

## Frozen intervention

Reuse the1273pairs, iteration70context model, iteration71word/POS reading weights and iteration73normalized distributions over joint POS/Case/Number profiles. No fitting or tuning occurs. For profile a and context c, compute posterior/source-prior ratio q(a|c)/pi(a), then average over each candidate reading distribution and its existing word/POS weight.

Equivalently, each reading contributes its compatible posterior mass divided by its compatible source-prior mass. This removes the unconditional prevalence of that reading's features. Joint analyses remain intact; unresolved features are integrated over source-supported profiles. Unknown entries and unsupported readings remain zero. The primary score retains the candidate's total supported reading weight, making that lexical prior explicit.

The secondary context-only score divides by total supported reading weight. With the grammatical prior as query, every supported candidate then scores1; unknown/unsupported candidates score0. Its prior-arm233losses and1040ties reflect this resource-support asymmetry rather than grammatical evidence. This secondary arm was declared before evaluation and is not promoted after the primary failure.

The primary gate requires at least65%strict wins, ten points above both frequency and matching prior, and five above matching shuffle. It fails. No gold POS is supplied to these inference arms; reference-POS pair construction, content selection, correct surrounding plaintext and sentence boundaries remain privileges inherited from70. Repeated development positions are not fresh confirmation.

## Interpretation

Removing source-profile prevalence helps transfer some of iteration74's predictive signal into candidate rankings. However, the context-only version's39.20%strict wins versus37.31%shuffle shows only a1.89point order advantage. It also loses645pairs and ties129; it cannot support a general lexical recovery claim. Neither version is adopted.

Preserve iteration74's stronger direct-prediction finding separately. This result does not undo that finding, and predictive grammatical information still does not establish exact word identity. Dictionary gaps, candidate ambiguity, imperfect context prediction and the deliberately frequent distractors remain relevant limitations.

A possible next check is **selective recovery potential**, calibrated on source-only held-out candidate pairs before inspecting target outcomes: can a fixed confidence/abstention policy retain a useful number of word types at high exact precision beyond frequency and shuffled controls? Require support by multiple contexts where available and report coverage by type and token. Do not choose a threshold on these reused Caesar outcomes or interpret isolated high margins as nuclei. This proposal is untested; the current failed score does not authorize dictionary search.

## Verification

Independent compatible-mass summation replays all1273predictions and pair identities; evaluation checks pass. Audit verifies1530prior input hashes. Four new tests cover prior neutrality, exact profile ratios, unresolved readings and unsupported/unknown candidates; all30focused tests pass. The grammar reserve and sealed lexical final test remain unscored.

Artifacts: `experiments/results/grammar-restoration/iteration75/`; runner and audit: `benchmarks/grammar_likelihood_ratio_iteration75*.py`.
