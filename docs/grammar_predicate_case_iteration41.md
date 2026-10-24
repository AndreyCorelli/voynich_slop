# Iteration 41: does predicate context resolve the case after *in*?

**There is a useful predicate signal, but the evidence is narrow and lexical coverage is the immediate limitation.** On reused Caesar queries, a source-trained predicate model improves binary case accuracy from 41.5% to 58.5%. On Jerome it improves from 35.3% to 47.1%, with substantial uncertainty. Nearest-verb context captures most of the benefit; these results do not establish that recovering the exact predicate link is the primary bottleneck.

## Frozen diagnostic

Reuse iteration40's source and target IDs and its simple, contiguous preposition–nominal constructions. Restrict to *in* with accusative or ablative. Source: 171 examples in 149 of the original 767 Jerome/Palladius sentences, with 55 accusative and 116 ablative labels. Targets: 17 examples in the reused 100-sentence Jerome query slice and 41 in the reused 100-sentence Caesar slice. Caesar is an unseen source author, but these are inspected development queries, not fresh confirmation.

The oracle predicate is the first VERB/AUX ancestor of the nominal head. Record whether it is the direct head or an indirect ancestor. This is a dependency-based proxy for the governing predicate, not an assured semantic relation. The nearest-verb control uses the nearest VERB/AUX to the preposition, with earlier token winning distance ties, and requires no dependency links.

Inputs are privileged: plaintext preposition identity, reference eligibility/boundaries, oracle POS, and predicate lemma; oracle linkage additionally uses reference dependency ancestry. Head case supplies source training and target evaluation labels. The prediction function accepts only a fitted model and a predicate identifier: no target case, head morphology, or reference role can enter its calculation. This tests the value of predicate context, not its extraction from anonymous ciphertext.

Before predictions, freeze a binary estimator:

- Preposition-only baseline: add-half source accusative frequency, `(55+.5)/(171+1)`, about 32.3%. Thus it always predicts ablative at the fixed 0.5 decision threshold.
- Predicate model: `(source_Acc_for_predicate + 4 * baseline)/(source_count_for_predicate + 4)`.
- Missing and source-unseen predicates back off exactly to baseline.
- Primary shrinkage mass is 4. Sensitivities 1 and 16 are declared beforehand and reported without selecting a winner.
- Train nearest-verb context separately as a matched control. Also apply the oracle-trained model to nearest-verb identities to isolate replacing the link at inference.
- Fit 100 shuffled-source controls: permute predicate identifiers among source records, preserving case frequencies, predicate counts, and missing-context counts. Target predicate identities are unchanged.

Freeze source models and declarations before prediction, and predictions before evaluation. No target threshold, lemma mapping, or hyperparameter is fitted. The reserved 200 sentences are excluded before token annotations are parsed; iteration39 queries are not used.

## Primary results

| Author | Examples | Accusative labels | Preposition-only accuracy | Oracle-predicate accuracy | Nearest verb, matched training | Oracle model with nearest link |
|---|---:|---:|---:|---:|---:|---:|
| Jerome | 17 | 11 | 35.3% | **47.1%** | 52.9% | 52.9% |
| Caesar | 41 | 24 | 41.5% | **58.5%** | 56.1% | 56.1% |

At primary mass4, oracle context corrects 3 Jerome predictions while spoiling 1, and corrects 7 Caesar predictions with no spoils. Balanced accuracy improves from 50% to 55.3% Jerome and 64.6% Caesar. Target case proportions differ substantially from the source, so raw accuracy alone is insufficient.

Log loss improves from 0.8694 to 0.7371 on Jerome and 0.8237 to 0.7238 on Caesar. Brier scores improve from 0.3336 to 0.2710 and 0.3117 to 0.2625 respectively.

Ten thousand paired sentence-cluster draws, conditional on the fitted source model, give accuracy-gain intervals of **[-11.1, +35.7] points Jerome** and **[+5.0, +31.6] points Caesar**. Log-loss reduction intervals are [-0.0061, +0.2950] and [+0.0149, +0.1964]. These are small, reused, construction-selected samples; intervals are not independent confirmation.

Primary oracle log loss is better than all 100 source-shuffled controls for each author. The controls' mean accuracies are 34.9% Jerome and 42.3% Caesar; their mean log losses are 0.8896 and 0.8410. This supports a nonrandom source predicate–case association. It does not establish semantic understanding or remove source/target selection biases. Descriptive shuffle percentiles are recorded without interpreting multiple metrics as independent tests.

## Coverage and what the gains depend on

| Author | Reference verbal ancestor | Direct verbal head | Source-seen predicate lemma | Missing predicate | Nonmissing unseen lemma | Nearest token equals reference ancestor |
|---|---:|---:|---:|---:|---:|---:|
| Jerome | 15/17 | 12/17 | **6/17** | 2 | 9 | 12/15 linked |
| Caesar | 40/41 | 35/41 | **11/41** | 1 | 29 | 33/40 linked |

Among seen predicates, accuracy changes from 2/6 to 4/6 Jerome and from 1/11 to 8/11 Caesar. Every unseen or missing predicate prediction remains the baseline by design. The apparent generalization to another author therefore transfers associations for familiar lemmas; it is not generalization to unfamiliar predicate identities.

All 10 corrected predictions involve only three lemmas: *mitto* (5), *uenio* (4), and *abeo* (1). The spoiled Jerome prediction involves *assumo*. Its source evidence is just two accusative examples; its target use is ablative. Predicate identity is informative but does not uniquely determine the case.

On the direct-head subset, oracle accuracy rises from 16.7% to 41.7% Jerome (12 examples) and from 40.0% to 57.1% Caesar (35 examples). The signal is not solely an artifact of indirect ancestor traversal.

The nearest-verb results do **not** show that reference attachment accuracy is essential here. Oracle-trained nearest inference loses only one correct prediction against oracle inference on Caesar and improves Jerome by one. Different contexts can share the same lemma, so link agreement and predictive accuracy are distinct measurements. Both nearest variants still use oracle verbal POS and lemmas.

## Sensitivity, not model selection

With shrinkage mass1, oracle accuracy is 52.9% Jerome / 61.0% Caesar; with mass16 it returns to baseline accuracy, though probability losses still improve. The fixed primary mass4 remains the reported estimator. The discrete decision is sensitive to a few source counts crossing the threshold.

A post-primary source-only bootstrap resamples the 149 source sentences containing eligible examples, refits the fixed mass4 model and its baseline 2,000 times, and holds target queries fixed. Its accuracy-gain ranges are [0, 23.5] points Jerome and [2.4, 19.5] Caesar; log-loss reduction ranges are [0.0585, 0.1826] and [0.0391, 0.1413]. These measure source-sample sensitivity separately from the target bootstrap, not combined uncertainty. They do not justify choosing a different mass.

## Updated hypothesis and next step

Retain the hypothesis that predicate context helps resolve locally ambiguous case. Narrow the stronger claim: the current evidence does not make exact predicate-link recovery the leading bottleneck. **Sparse predicate coverage and variation within a predicate are more immediate obstacles.** Sixty-five percent of Jerome and 73% of Caesar examples have no source-seen oracle predicate, while the observed corrections concentrate on three familiar lemmas.

The next useful challenge is to increase source support while keeping target authors/IDs and the reserve excluded, and then test case prediction separately for seen and unseen predicate lemmas. A transfer model must share evidence between predicates using source-derived contextual or construction profiles; simply collecting more counts for the same few lemmas would not demonstrate that ability. Compare it against the strong nearest-verb control and preserve a leave-predicate-out evaluation. Do not promote any hand-built motion grouping chosen from these failures as independent evidence.

These results justify pursuing predicate-conditioned construction scores. They do not yet justify a large joint decoder or claim restored grammatical structure.

## Verification and artifacts

The validator reconstructs all six source models and replays 6,148 probabilities, including the 100 source permutations. It checks identical baseline under permutation, exact fallback for unseen predicates, oracle/nearest target alignment, disjoint source/target IDs, input hashes, and reserve exclusion. Tests cover shrinkage, unseen/missing backoff, cycles in ancestor traversal, indirect links, nearest/oracle disagreement, and the scorer's refusal to accept target case as a prediction argument.

Code: `src/voynich_smt/predicate_case.py`. Run `python -m benchmarks.grammar_predicate_case_iteration41` (refuses overwrite), then `python -m benchmarks.grammar_predicate_case_iteration41_validate`; source sensitivity is `python -m benchmarks.grammar_predicate_case_iteration41_source_bootstrap`. Artifacts under `experiments/results/grammar-restoration/iteration41/` include declarations, source models, explicit oracle records, frozen probabilities, shuffle controls, evaluation, per-case audit, source bootstrap, and validation. Prior artifacts and the shared todo remain unchanged; reserved200 remain unscored.
