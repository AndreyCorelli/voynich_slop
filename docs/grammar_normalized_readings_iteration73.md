# Normalized candidate readings — iteration 73

**The tested correction fails; retain it as an ablation, not an algorithm addition.** Original-word wins fall from iteration71's207/1273 (16.26%) to189/1273 (14.85%). Normalized shuffled context wins155 (12.18%) and the normalized grammatical prior140 (11.00%). With supplied correct POS, context wins575 (45.17%), shuffled570 (44.78%) and prior573 (45.01%). The primary gate fails; no historical-corruption phase, dictionary search or nuclei were measured.

| Score | Original wins | Wrong candidate wins | Ties |
|---|---:|---:|---:|
| Iteration71 weighted context | 207 | 1,066 | 0 |
| Normalized readings, contextual | 189 | 1,084 | 0 |
| Normalized readings, shuffled context | 155 | 1,118 | 0 |
| Normalized readings, grammatical prior | 140 | 1,133 | 0 |
| Supplied POS + normalized context | 575 | 698 | 0 |
| Supplied POS + normalized shuffle | 570 | 703 | 0 |
| Supplied POS + normalized prior | 573 | 700 | 0 |

## Schema audit

All612 previously flagged cases are the **NOUN reading of `non`**, with raw dictionary `Case=X, Gender=M, Number=X`. Thus those feature values are unresolved inflection, rather than case/number being structurally inapplicable. Its ADV reading has Degree=POS and no Case/Number. These observations justify treating the noun's X values differently from a fully specified inflection; they do not establish a complete missingness schema for every cached reading. The projected cache loses some distinctions, so no general schema repair is claimed.

## Fixed intervention

Keep the1273pairs, source-trained contextual model and iteration71word/POS reading weights unchanged. Collapse dependency-role labels into joint POS/Case/Number profiles. Represent each dictionary reading as the normalized source-prior distribution over joint profiles compatible with it. A specific reading concentrates on its admitted profiles; an unresolved feature distributes probability over source-observed possibilities instead of collecting unrestricted posterior mass. Joint profiles remain intact; no Cartesian product invents feature combinations. Profiles with empty source fields retain those empty fields, including nonapplicable adverb morphology.

Score the overlap between the contextual profile posterior and this candidate reading distribution, weighted by the existing word/POS reading probabilities. Unknown entries and unsupported readings stay zero; candidate word/POS mass is not renormalized. This is one particular normalized overlap score, not a validated likelihood or a complete solution to morphological missingness. It can trade a wildcard preference for a specificity preference; the controls are therefore essential.

The predeclared primary gate requires at least65% strict original wins, ten percentage points above both prior and frequency, and five above shuffled context. It fails. Supplied-POS arms are explicitly privileged diagnostics and cannot authorize recovery. Reference-POS candidate construction and correct surrounding plaintext/sentence boundaries remain supplied as in70–72. Reused and repeated positions provide descriptive development results, not independent confirmation.

## Interpretation

Among the612affected pairs, normalized context prefers the original in53 and the distractor in559. Supplied-POS normalized context prefers the original in451 and the distractor in161. The latter combines normalization with the supplied POS and word/POS weights; it must not be attributed to normalization alone or compared as a pure correction of iteration72's uniform-within-POS arm.

The overall result is worse than71, and supplied-POS contextual gains remain almost absent relative to shuffle/prior. The wildcard mechanism was real, but this replacement does not overcome contextual uncertainty, dictionary coverage and grammatical indistinguishability. It is not evidence that normalized analysis probabilities in general cannot help.

**Next diagnostic:** before changing another candidate score, measure whether the frozen context model predicts reference joint morphology better than its prior or shuffled context, separately for POS prediction and Case/Number conditional on supplied POS. Report unsupported reference profiles and word-type clustering; do not hide dictionary failures. If contextual predictive loss fails to improve, change the context representation/training objective rather than continue candidate-score variants. Require an actual contextual advantage before returning to corruption tests or search.

## Verification

A separate summation over source profile probabilities independently replays all1273predictions; pair identities and evaluation are checked. Audit verifies1508prior manifest input hashes. Five new tests cover normalized unknown-feature mass, specific joint readings, structural adverb absence, unknown/unsupported readings and role-to-profile collapse; all23focused tests pass. The grammar reserve and sealed lexical final test remain unscored.

Artifacts: `experiments/results/grammar-restoration/iteration73/`; runner and independent audit: `benchmarks/grammar_normalized_readings_iteration73*.py`.
