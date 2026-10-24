# Iteration 50: uncertainty for proper-name number

Preserving both number alternatives for proper names with no fit-set number labels recovers both newly lost links from iteration 49, while preserving all 30 unique correct links. It changes mean remaining token links only from 12.598 to 12.632. This is a positive diagnostic for a conservative fallback, not fresh confirmation: the proposal was motivated by inspected errors on these same development folds.

## Fixed experiment

Reuse the frozen expanded-total99 predictions, models, source partitions and 326 constructions from iteration 49. No fitting, recalibration, word-specific exceptions or new data scoring occurs. Inference uses word, supplied POS and the number-label count for that word/POS in the fit portion of its own outer fold. Calibration/test number labels do not affect the gate.

For a qualifying PROPN, add the alternative number to each accepted positive state. Preserve OTHER, person and nominative eligibility; a token without a positive state does not gain one. The three fixed expansion arms are: zero fit number labels (`proper_unseen`), fewer than five (`proper_sparse5`), and every PROPN (`proper_all`). Five follows the existing estimator's minimum-support convention; it was not fitted to held-out results. Here “unseen” means no usable fit number labels for the exact word/POS, not necessarily that the spelling never occurs in training.

## Results

| Policy | Exact morphology retained | Reference links retained | Unique correct | Unique wrong | Mean links |
|---|---:|---:|---:|---:|---:|
| Old joint set99 (iteration 48) | 321 | 323 | 19 | 0 | 19.132 |
| Expanded total99 (iteration 49) | 320 | 322 | 30 | 0 | 12.598 |
| Proper names: no fit number labels | 323 | 324 | 30 | 0 | 12.632 |
| Proper names: fewer than five labels | 323 | 324 | 30 | 0 | 12.647 |
| All proper names | 323 | 324 | 30 | 0 | 12.650 |

All rows concern the same 326 reference constructions. Expansion produces no empty domains and loses no reference links. The two rescued reference links are those involving *osaces* and *salamis*. Exact morphology survival rises by three, while token-link survival rises by two. No unique correct links are added or removed relative to iteration 49. The no-label arm increases mean links by 0.27%; broader arms supply no additional coverage in this sample.

On 2,059 joint-scorable PROPN tokens, the no-label arm expands 99 token occurrences. Gold joint-state coverage rises from 2,042/2,059 (99.17%) to 2,052/2,059 (99.66%); mean set size rises from 2.155 to 2.203. Sparse-five and all-PROPN arms expand 275 and 453 occurrences, respectively, with the same observed coverage. Existing eligibility exclusions remain possible.

In the 270-construction originally ambiguous cohort, reference-link retention improves from 266 to 268, but unique correct links remain three. Thus this repairs coverage rather than resolving the main remaining structural ambiguity. Expansion is monotone: it cannot remove a reference candidate, but it can generally destroy unique outcomes or introduce ambiguity; the preserved unique count here is empirical.

## Decision and next work

Keep feature sharing with the no-fit-number-label proper-name fallback as an experimental configuration. It has better observed retention and discrimination than the old joint set99 baseline, but it still relies on readable Latin, supplied POS and supplied construction selection. Zero observed unique wrong links is not a guarantee.

Before adopting it as the default, freeze the combined configuration and evaluate on genuinely fresh annotations. Separate proper-name calibration remains a proposed alternative, with no evidence yet that it improves on this simple fallback. The next substantive bottleneck is discrimination among the many surviving links, rather than the two repaired number errors.

## Artifacts and checks

Code: `src/voynich_smt/proper_name_uncertainty.py` and `benchmarks/grammar_proper_uncertainty_iteration50.py`. Run with `python -m benchmarks.grammar_proper_uncertainty_iteration50`; an existing output directory is rejected. Results and the pre-evaluation proposal snapshot live in `experiments/results/grammar-restoration/iteration50/`.

The run verifies all 22 iteration-49 manifest inputs, reproduces all 326 baseline reference summaries, checks nested sets for every word type, and compares 2,608 compact-support decodes with explicit candidate lattices. It checks held-out annotation mutation invariance and baseline-lattice inclusion for every arm. Seven new tests cover support boundaries, POS/eligibility preservation, nonmutation and invalid policy handling; 31 relevant tests pass. Only experiment packaging changed during a second run, to preserve a frozen design snapshot while allowing the proposal tracker to remain editable; numerical results were unchanged.

The 200-sentence reserve remains unscored, no prior target queries were scored, and previous frozen files remain intact.
