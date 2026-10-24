# Supplied-POS attribution — iteration 72

**Correct POS helps substantially; the current contextual morphology score adds almost nothing beyond it.** On the 1,273 frozen pairs, supplied reference POS raises weighted contextual original-word wins from 207 (16.26%) to 590 (46.35%). But shuffled context gives 586 (46.03%), and the grammatical prior gives 587 (46.11%). This is an oracle diagnostic, not a restoration gain or a deployable addition. No dictionary search or nuclei were measured.

| Evidence | Original wins | Wrong candidate wins | Ties |
|---|---:|---:|---:|
| Iteration71 weighted context | 207 | 1,066 | 0 |
| Supplied POS + weighted context | 590 | 683 | 0 |
| Supplied POS + weighted shuffled context | 586 | 687 | 0 |
| Supplied POS + weighted grammatical prior | 587 | 686 | 0 |
| Supplied POS + candidate word/POS weight only | 570 | 703 | 0 |
| Supplied POS + uniform within-POS readings, context | 123 | 912 | 238 |
| Supplied POS + uniform within-POS readings, prior | 121 | 914 | 238 |
| Supplied reference POS/Case/Number compatibility | 203 | 218 | 852 |

## Intervention and scope

Reuse iteration71's pairs, candidate weights and frozen iteration70 contextual model. Condition its joint role/POS/Case/Number posterior on the reference coarse POS by zeroing other POS labels and normalizing; an unsupported POS stays zero. No fitting or threshold selection occurs. Evaluate weighted contextual, shuffled and prior compatibility, plus union controls. Uniform within-POS reading weights remove candidate word/POS probability, exposing the remaining Case/Number evidence. A POS-only word-weight control sums candidate reading weights of the supplied POS without contextual morphology.

Reference POS is explicitly privileged. Correct surrounding plaintext, sentence boundaries and reference-POS candidate sampling remain supplied as in70/71. These repeated development positions do not provide independent confirmation. All 1,273 positions remain in the primary table, including missing dictionary readings. No oracle outcome authorizes search.

Among the 1,015 positions whose original dictionary reading admits the reference profile, weighted oracle-POS context wins586 (57.73%), shuffled582 (57.34%), prior583 (57.44%) and POS-only word weight566 (55.76%). Restricting to this favorable subset therefore does not reveal a substantial contextual gain. The full reference-morphology check ties812/1015: many alternatives share the measured grammatical features.

## A concrete scoring defect to investigate next

A post-result specificity audit finds742 distractors with a reading of the correct POS but **unspecified Case and Number**. In612 of these pairs, the original reference actually has Case or Number specified. The uniform within-POS contextual score loses **all612**.

This follows a problematic scoring convention: missing candidate features are treated as unrestricted wildcards, so an underspecified reading can collect posterior mass across every case/number combination, whereas a specific original reading collects only its compatible combinations. This is a mechanism consistent with the observed failures, not proof that correcting it will restore words. Some empty fields represent genuine nonapplicability rather than missing annotation; these must be distinguished before changing the likelihood.

Next, audit these612 comparisons by candidate POS and morphology schema. Then test a normalized observation model that distinguishes known features, unavailable features and nonapplicable features, holding pairs/model fixed and retaining all unknowns. Compare against the existing wildcard score, word/POS prior and shuffled context. Do not simply reject empty fields or remove the difficult pairs. A useful correction must first survive these controls and then the historical first-corruption test before dictionary search.

## Verification

All 1,273 oracle predictions replay; evaluation and the unchanged pair identities are checked. Audit verifies1,498 prior manifest input hashes. Four new tests check conditional normalization, unsupported POS, joint-reading preservation and absent-POS handling; all18 focused tests pass. The grammar reserve and sealed lexical final test remain unscored.

Artifacts: `experiments/results/grammar-restoration/iteration72/`; runner/audit: `benchmarks/grammar_pos_oracle_iteration72*.py`.
