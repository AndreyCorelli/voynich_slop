# Direct contextual morphology prediction — iteration 74

**Preserve this positive diagnostic: the frozen model contains contextual grammatical signal, despite the failed lexical scores.** On1,273previously explored content positions, context improves both POS prediction and Case/Number prediction conditional on supplied correct POS, relative to source prior and shuffled context. This localizes a remaining problem to how that signal is converted into candidate-word compatibility, alongside imperfect predictions, dictionary coverage and ambiguity. It does not establish additional restored nuclei.

| Prediction | Context accuracy | Prior accuracy | Shuffle accuracy | Context NLL | Prior NLL | Shuffle NLL |
|---|---:|---:|---:|---:|---:|---:|
| Coarse POS | 52.47% | 31.81% | 41.40% | 1.0851 | 1.2586 | 1.2531 |
| Exact joint POS/Case/Number | 19.48% | 10.21% | 12.73% | 2.8574 | 3.1228 | 3.2141 |
| Exact Case/Number given correct POS | 35.51% | 32.21% | 30.40% | 1.7723 | 1.8642 | 1.9611 |

NLL is mean negative natural log probability; lower is better. Missing reference feature values are exact categorical empty fields in this direct prediction audit, not wildcard matches. All reference joint profiles occur in model support, so no probability flooring or unsupported-profile exclusion affects these results.

## Method and controls

Keep the iteration70model fixed and evaluate the same1,273positions from100previously declared Caesar sentences. Marginalize dependency roles into joint POS/Case/Number profiles. Measure POS marginals, exact joint profiles and exact morphology conditional on reference POS, using the saved contextual features, saved shuffled features and unconditional source prior. This audit does not use candidate dictionary compatibility, distractor scores or candidate weights. No refitting or parameter selection occurs.

The conditional morphology arm explicitly supplies reference POS. Content-position selection, correct surrounding plaintext and sentence boundaries remain supplied; this is neither blind parsing nor restoration. The shuffled arm uses the saved single permutation per sentence, not an exhaustive permutation test. Model predictions range over content labels, so POS accuracy is restricted to the content-position task, not all words.

The predeclared diagnostic condition—both POS and conditional morphology NLL beat both controls—passes. It is not a search or recovery gate.

## Coverage and repeated-word controls

There are844word types. Giving each type equal weight preserves the direction: POS accuracy52.96% versus37.32%prior/41.55%shuffle, conditional morphology33.91% versus31.40%/29.27%. Thus the gain is not solely a few repeated words.

On the1,069positions with a nonempty reference Case or Number, conditional morphology accuracy is29.00%context,26.19%prior and23.39%shuffle; corresponding NLL2.0055,2.0905,2.2058. The gain therefore persists after excluding feature-empty targets. Supported-profile subsets equal the full corresponding subsets because unsupported count is zero.

A1,000-replicate sentence-cluster bootstrap gives the following descriptive95%percentile ranges for context-minus-control NLL:

| Task/control | Mean difference | Descriptive interval |
|---|---:|---:|
| POS/prior | −0.1735 | [−0.2006, −0.1446] |
| POS/shuffle | −0.1679 | [−0.1976, −0.1364] |
| Conditional morphology/prior | −0.0919 | [−0.1216, −0.0619] |
| Conditional morphology/shuffle | −0.1887 | [−0.2383, −0.1389] |

These are reused development sentences, and word types can recur across sentences. The ranges summarize sensitivity to sentence composition; they are not fresh confirmatory confidence claims.

## Implication and next test

The earlier near-equality of contextual and shuffled **candidate rankings** did not imply that context lacked predictive information. Direct prediction shows otherwise. Still,52%POS and29%conditional morphology accuracy on feature-bearing targets are far from an oracle, and grammatical compatibility alone cannot distinguish words sharing the measured analysis.

The next bounded test is a **context likelihood ratio**: compare posterior profile probability with its source prior before integrating over each candidate's joint analysis distribution. This asks how much the observed context favors an analysis rather than how common that analysis is overall. Keep candidate word/POS priors separate and visible, retain unknown/unsupported readings, use the same fixed pairs and matching prior/shuffle controls, and do not tune combination weights on these results. A score must pass the pair diagnostic and historical first-corruption test before any search. This is a proposed modification, not an adopted algorithm or nucleus claim.

## Verification

An independent summation replays all1,273POS/joint/conditional probabilities; evaluation and identity checks pass. Audit verifies1,519prior input hashes. Three new tests cover role marginalization, unsupported profiles and the probability chain rule; all26focused tests pass. An initial JSON serialization failure was repaired by casting a NumPy count to a Python integer; the original design/prediction freezes are preserved, and the audit reconstructs the original source hash to verify that sole change. No model or metric definition changed.

The grammar reserve and sealed lexical final test remain unscored. Artifacts: `experiments/results/grammar-restoration/iteration74/`; code: `benchmarks/grammar_context_prediction_iteration74*.py`.
