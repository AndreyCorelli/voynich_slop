# Iteration 26: inducing grammatical classes from repeated cipher words

The fixed-transition HMM does **not** recover useful grammatical structure in this experiment. Pooled-source word emissions yield 27.52% / 13.64% balanced eight-class accuracy on fresh Jerome / Caesar queries. Anonymous ending sharing gives 28.45% / 13.13%; randomly reassigned endings do slightly better. Even reporting the best class permutation leaves weak clusters. Oracle supervised emissions reach 98.61% / 97.19%, separating representational capacity from successful unsupervised induction. All primary fits stop at the preregistered iteration cap; a development-only continuation reaches convergence without improving class accuracy.

## Frozen design and information boundary

The eight classes are noun/proper noun, adjective, pronoun/determiner, verb/auxiliary, adverb, adposition, conjunction, and other. This tests POS induction, not case/number induction or full parsing. Source training reuses iteration24's 767 labeled sentences (8,106 tokens; Jerome and Palladius). Start, transition, and termination probabilities are fitted once with pseudocount .5 and stay fixed. Target adaptation estimates only emissions with batched forward–backward EM. Sentence boundaries are supplied.

Fresh material comprises 100 query sentences per author (913 Jerome / 1,514 Caesar tokens), plus 100 separate unlabeled background sentences per author (848 / 1,673 tokens). All 400 IDs are disjoint from prior manifest/truth declarations and the 200-sentence reserve. The old iteration24 calibration 40/background 200 corpus is deliberately reused for development. The reserve remains unparsed for this experiment and unscored.

Cipher words have anonymous consistent bodies and a consistently substituted two-character ending, as in iteration23. The learner receives only first-occurrence word IDs, ending-group IDs, and sentence sequences; it receives no Latin spelling, dictionary, target POS, dependency labels, or cipher key. Repeated words and ending memberships are identical under a second key after canonicalization. Emissions are fitted transductively on background **and query** observations; this is not a model that generalizes to unseen target vocabulary without adaptation.

Word-only emissions have a corpus-frequency prior of mass 1 per state. Ending sharing factorizes `p(word|state) = p(ending|state) × p(word|ending,state)`, avoiding double-counting spelling evidence. Ending probabilities have prior mass 1 per state; conditional word probabilities have mass .2 per ending group. This changes regularization, not emission-table capacity. The shuffled-ending control permutes group assignments across word types, preserving group type counts but not token-weighted group masses.

Every arm uses seeds 2601–2605, at most 80 EM updates, and relative objective tolerance1e-7. Selection maximizes the regularized unlabeled objective **within the arm**, never class accuracy; objectives with different priors are not compared across arms. Context shuffling permutes tokens within each training sentence, retaining sentence lengths and counts, then decodes original query order. Genre controls refit word emissions with Jerome-only or Palladius-only fixed transitions, using the same five starts. Configuration/source models are frozen before fitting, and downstream thresholds are frozen before fresh target fitting/scoring.

## Class induction results

Percentages below refer to fresh query tokens. Balanced accuracy averages recall over the eight reference classes (a uniform random assignment has expectation12.5%). The permutation score is a reporting-only, gold-selected one-to-one reassignment that maximizes balanced accuracy; it never changes predictions or seed selection.

| Arm | Jerome balanced | Caesar balanced | Jerome best permutation | Caesar best permutation |
|---|---:|---:|---:|---:|
| Word | 27.52 | 13.64 | 33.03 | 25.21 |
| Ending sharing | 28.45 | 13.13 | 31.25 | 26.86 |
| Shuffled context | 9.29 | 11.30 | 30.24 | 28.45 |
| Shuffled endings | 29.10 | 15.35 | 34.09 | 27.87 |
| Word, Jerome transitions | 21.96 | 9.95 | 29.44 | 25.74 |
| Word, Palladius transitions | 10.48 | 17.47 | 32.42 | 23.42 |
| Oracle supervised emissions | 98.61 | 97.19 | 98.61 | 97.19 |
| Oracle token classes | 100 | 100 | 100 | 100 |

Ordinary token accuracy for word / ending is 33.41 / 34.61% on Jerome and 19.62 / 18.96% on Caesar. Word-only balanced accuracy across all five seeds ranges16.50–27.52% on Jerome and13.37–15.00% on Caesar; ending ranges16.18–28.45% and13.13–14.70%. These ranges are initialization sensitivity, not confidence intervals. The unlabeled objective does not reliably choose the best grammatical labeling. Single-author transition templates change the result substantially; there is no consistently successful domain choice.

There is no simple collapse into one state: every arm uses all eight hard states on both tests. Word / ending hard-state effective counts are6.72 / 6.65 on Jerome and6.68 / 6.69 on Caesar. Nevertheless, posterior confidence is badly misleading. Word posteriors exceed .95 on83.2% of Jerome tokens with only35.4% accuracy, and83.3% of Caesar tokens with20.3% accuracy. Ending sharing similarly gives39.5% / 20.8% accuracy among tokens above .95. Concentrated posteriors are not reliable grammatical evidence.

Oracle emissions use gold POS **from the same background and query corpus** to estimate the word/state table, followed by ordinary HMM decoding. They are a privileged in-sample capacity check, not a deployable or held-out supervised model. Their high scores show that the emission representation and decoder can express nearly correct classes; they do not establish that unlabeled likelihood identifies them.

## Dependency check

A source-only relation table estimates label probabilities from child class, parent class, and signed distance (absolute distance capped at 6; candidates within 12 tokens). It covers subject, object (including indirect object), nominal modifier, and coordination. Posterior class products marginalize this table. Each child makes at most one claim; tied candidates abstain, and confidence-ordered cycle rejection yields a partial forest. It is a deliberately limited attachment probe, not a full grammar.

Each arm's threshold maximizes labeled-edge F1 on the old 40-sentence calibration set over the frozen grid .01/.03/.05/.1/.2/.35/.5/.7/.9. Word selects .01, ending .05, shuffled context .5, shuffled endings .01; both oracle arms select .2. No fresh-test threshold selection occurs. Recall includes reference links outside the candidate radius.

| Arm | Jerome precision / recall / F1 | Caesar precision / recall / F1 |
|---|---:|---:|
| Word | 4.50 / 9.40 / 6.08 | 2.09 / 4.34 / 2.82 |
| Ending sharing | 4.74 / 8.65 / 6.13 | 2.34 / 4.14 / 2.99 |
| Shuffled context | 1.72 / 0.38 / 0.62 | 4.41 / 0.59 / 1.04 |
| Shuffled endings | 4.80 / 10.15 / 6.52 | 2.41 / 4.93 / 3.24 |
| Oracle emissions | 44.95 / 33.46 / 38.36 | 30.16 / 18.74 / 23.11 |
| Oracle token classes | 44.95 / 33.46 / 38.36 | 30.25 / 18.74 / 23.14 |

Word / ending dependent-token coverage is60.9 / 53.1% on Jerome and69.6 / 59.3% on Caesar, with extremely low precision. No anonymous arm recovers a correct shared-head subject–predicate–object fragment. Oracle classes recover5/18 Jerome fragments but0/23 Caesar fragments. All predicted graphs are acyclic. Acyclicity alone does not imply grammatical recovery.

The ending-minus-word F1 differences are +0.04 and+0.17 percentage points. Paired sentence-bootstrap95% intervals (1,000 replicates) are [−1.48,+1.74] and[−1.13,+1.50] points. There is no convincing ending improvement. Previous iterations use different fresh slices and decoders, so their scores are not direct controlled comparisons.

## Iteration cap and diagnostic continuation

All 90 primary/calibration fits hit 80 iterations without meeting tolerance, so this is a bounded optimization result, not an assertion about the global optimum. After inspecting the primary results, a separately recorded **development-only** diagnostic continues the selected pooled word and ending fits for up to 400 more updates. Word converges after 365 extra updates (445 total), with objective gain 12.64 but balanced accuracy falling 15.39→14.56%. Ending converges after 290 extra updates (370 total), gain 6.29, and accuracy 14.91→14.85%. This weakens the simple explanation that a few more iterations would fix development induction; other initializations, objectives, and fresh-target convergence remain untested. Fresh fits, thresholds, and reported primary scores are unchanged.

## Interpretation and next step

Order carries some information on Jerome, but classes remain poor after an oracle permutation, the ending control does not support linguistic sharing, and emission confidence is uncalibrated. The failure therefore includes class induction, not just anonymous-class alignment. At the same time, oracle classes leave substantial attachment error, especially on Caesar: class recovery would not by itself restore syntax.

The next inexpensive diagnostic is to initialize this HMM from the supervised emission oracle **on existing development material**, then track unlabeled objective and class accuracy during EM, including the first accuracy-losing update. Compare that trajectory to random starts. This would distinguish a poor basin from an objective that actively moves away from grammatical classes; the present runs do not settle that distinction. Avoid adding a richer parser until the class channel becomes reliable.

## Reproduction and verification

Run with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`:

```
.venv/bin/python -m benchmarks.grammar_latent_classes_iteration26
.venv/bin/python -m benchmarks.grammar_latent_classes_iteration26_evaluate
.venv/bin/python -m benchmarks.grammar_latent_classes_iteration26_continuation
.venv/bin/python -m benchmarks.grammar_latent_classes_iteration26_validate
```

Runners preserve existing outputs. Artifacts are in `experiments/results/grammar-restoration/iteration26/`. The validator checks frozen hashes and split exclusion, rekeys, all 90 final objectives, all 90 deterministic full-fit replays, selected seeds, fresh class confusion matrices, exact dependency predictions, independently counted link metrics, and acyclicity. Six new mechanism tests include independent enumeration of all HMM paths for variable-length sentences, emission normalization, monotonic EM, fixed transitions, rekey/metadata invariance, shuffle counts, ties, and cycle removal. The combined relevant suite passes 292 tests. The 200 reserved sentences remain unscored.
