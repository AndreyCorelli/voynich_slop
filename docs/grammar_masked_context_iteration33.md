# Iteration 33: oracle versus inferred neighboring classes

**The bottleneck is mixed: lexical suppression, weak first-order disambiguation, and propagation errors.** With the target token's lexical evidence removed, true immediate neighbors recover about 38–40% of excluded query tags. Inferred neighbors retain most of that at 10% deletion but only 24–26% at 50%. Restoring the original target emission nearly eliminates recovery even with true neighbors at the primary .01 fallback. Thus there is recoverable contextual information that the emission score suppresses, but perfect neighboring tags alone would still leave most excluded tags unresolved.

## Frozen diagnostic and masking boundary

This experiment does not train another model. It reuses iteration32's objective-selected random fits, the same 240 development sentences (2,052 tokens; 473 query tokens), the same five candidate-perturbation seeds, and the oracle development eight-class chain. Deletion rates are 10/50% of word types; fallback epsilon .01 remains primary and .30 is a sensitivity condition. Both word and ending arms are included: 40 frozen-model probes. No new targets, parsing, parameter selection, or reserved-sentence scoring occurs.

For each target position, immediate oracle neighboring classes are the reference tags at the preceding and following tokens of the same sentence. Missing neighbors use start/termination factors. With flat target evidence, the normalized local score is:

`p(c | left, right) ∝ T(left,c) × T(c,right)`

At the sentence beginning replace the first transition by `start(c)`; at the end replace the second by `stop(c)`. There is no extra unigram factor. The target's own tag is used only for scoring the prediction, never in this conditional distribution. True-neighbor input is privileged; this is not a practical decoder or universal accuracy upper bound.

For inferred neighbors, remove the target's emission evidence **before** inferring either neighboring marginal. Exact prefix/suffix messages compute this masked inference separately for every target; their MAP neighbor states then feed the same local conditional. The original unmasked target cannot leak through those neighbor states. Each token is masked separately; the experiment does not simultaneously remove all missing-word evidence.

Emission parameters remain the frozen, transductively fitted parameters from iteration32, which saw the observed corpus. This is target masking at decode time, not leave-one-out training or held-out generalization. The chain itself was fitted from this corpus's reference classes, so oracle-context results are in-sample structural diagnostics.

## Six compared signals

- **Oracle context:** true immediate neighbor states, flat target evidence, all eight target classes available.
- **Masked inferred neighbors:** MAP neighbor states inferred after masking the target; same flat-target local conditional.
- **Masked HMM:** exact target posterior after masking its emission, retaining all other observed-token evidence and uncertainty rather than plugging in neighbor MAP states.
- **Oracle context plus emission:** true neighbors, but multiply their local score by the original target word's full mixture emission.
- **Ordinary HMM:** unchanged iteration32 decoding with all target evidence present.
- **Class frequency:** oracle corpus class-frequency distribution, independent of neighbors and target word.

Target masking removes candidate restrictions as well as lexical identity evidence. A flat target emission is a diagnostic change of evidence, not the learned fallback channel of iteration32. The masked HMM therefore can consider excluded classes much more freely.

## Excluded-query results

The table reports the **word arm, primary epsilon .01**, averaged equally over five perturbation seeds on each seed's excluded-token cohort. At10% deletion there are 23–63 excluded query tokens per seed (mean 42); at 50%,203–251 (mean 231.6). Repeated/coincident tokens across seeds are not independent test examples.

| Signal | 10% deletion accuracy | 50% deletion accuracy |
|---|---:|---:|
| Class frequency | 22.61% | 22.78% |
| Oracle context, flat target | **39.84%** | **38.43%** |
| Masked inferred neighbors | 37.70% | 24.32% |
| Exact masked HMM | 37.16% | 25.53% |
| Oracle context plus original emission | 0.00% | 0.08% |
| Ordinary HMM | 0.00% | 0.00% |

Oracle-context accuracy ranges 31.25–47.83% across the low-deletion cohorts and 35.27–41.87% across the high-deletion cohorts. These are perturbation ranges, not population confidence intervals. Balanced accuracy averages recall over reference classes present in each cohort: oracle context 30.22/28.29%, inferred neighbors 29.31/16.36%, and masked HMM 29.03/17.14% at10/50%. A frequency-only classifier cannot substitute for the context signal, but the context signal is far from reliable tagging.

The ending arm gives the same oracle-context result, as expected. Its masked-neighbor accuracy is 38.12/24.22%, and masked-HMM accuracy 38.24/25.52%; the interpretation is unchanged. Oracle-context probabilities are exactly invariant across all 40 probes because the reference neighbors and chain are fixed; only the scored deletion cohorts change.

## How much contextual information survives?

For oracle context on excluded queries, word-arm top2 accuracy is 62.71/60.43%, and top3 is 74.38/72.52% at10/50% deletion. Mean probability assigned to the correct class is .270/.260. The model often puts the reference among a broad set of plausible classes without identifying a single reliable winner. These numbers are ranking diagnostics, not evidence that an oracle top3 proposal would restore the correct analysis.

With inferred neighbors at primary .01, top2/top3 drop to 54.77/64.84% at 10% deletion and 43.95/57.38% at 50%. Exact masked HMM inference gives 54.35/63.94% and 44.96/57.83%, respectively. Keeping uncertainty rather than using neighbor MAP states helps little here; weak or corrupted context remains.

The result is not that all contextual models are incapable of recovery. It concerns this fixed first-order eight-class chain, supplied true immediate tags or these frozen inferred contexts. Higher-order sequences, morphology, longer constructions, or word-specific evidence could contain additional information.

## Propagation versus insufficient oracle context

For the word arm at .01, **all available immediate neighbor tags are correct** after masking on 46.03% of excluded query cases at 10% deletion, but only 14.49% at 50%. Ending figures are 47.60/14.30%. Sentence boundaries count only existing neighbors. This statistic concerns the target-specific masked neighbor estimates, not the original unmasked tags.

When inferred neighbor states equal the reference neighbor states, their plugged-in conditional exactly matches oracle context; validation checks this identity. On the remaining high-deletion cases, word-arm oracle-context accuracy is 38.38% but inferred-neighbor accuracy 21.95% on the **same tokens**. Paired high-deletion counts average 51.4 oracle-only correct decisions versus 18.8 inferred-only correct decisions per perturbation: net 32.6 losses from substituting inferred neighbors. At low deletion the corresponding counts are 5.2 versus 4.0, so the net loss is much smaller.

Not every changed neighbor makes the target prediction worse; some inferred-neighbor predictions are correct where the oracle-chain local argmax is wrong. Oracle neighbor tags are not an accuracy bound for every individual token. The paired analysis and matching subsets avoid attributing differences solely to a changing mixture of easy/hard cases.

Even on cases with correct neighbors, accuracy remains limited. At high deletion it is about 38.56% for both the oracle and inferred-neighbor plug-in prediction. Thus improved propagation would recover some performance, but cannot by itself make this first-order conditional a reliable full tagger.

## The target emission suppresses useful context

At primary epsilon .01, true neighbors plus a flat target recover 39.84/38.43% of excluded tags; retaining the target emission reduces those scores to 0.00/0.08%. The mixture's positive fallback floor technically permits the correct class, but its emission score is too small relative to supplied candidate classes to win on almost all of these cases—even when neighbors are supplied correctly.

This directly separates emission suppression from neighbor corruption. It is not evidence that lexical evidence should be discarded universally. On **all 473 query tokens**, oracle context alone has 37.63% accuracy, versus 70.32/35.39% for true context plus emission under10/50% deletion. The emission remains useful on many covered words. Blindly replacing it with flat evidence would destroy correct tags.

## Sensitivity: epsilon .30

The stronger fallback from iteration32 does not change the oracle-context-only score. For excluded word-arm queries:

| Signal | 10% deletion | 50% deletion |
|---|---:|---:|
| Oracle context | 39.84% | 38.43% |
| Masked inferred neighbors | 38.97% | 25.25% |
| Exact masked HMM | 37.95% | 25.87% |
| Oracle context plus emission | 9.02% | 9.55% |
| Ordinary HMM | 5.45% | 2.99% |

True neighbors can now recover more missing tags when emissions remain present, but still much less than context alone. The ordinary decoder also loses information through inferred context. Ending results are similar: ordinary recovery 6.19/3.16%, true-neighbor-plus-emission 9.02/9.66%. No epsilon or model is selected by these diagnostic scores.

## Implication and next useful check

The experiment identifies three distinct limitations: candidate-biased target evidence blocks some available context; inferred neighbors deteriorate when many candidates are wrong; and even true immediate tags only support weak first-order disambiguation. A blanket emission override or a simple improvement to neighbor tags would not solve all three.

Before overriding target emissions, test whether **context–candidate disagreement can identify unreliable candidate evidence without oracle neighbors or knowledge of which tokens lost their class**. Score detection on covered versus excluded tokens and report the false-positive cost on already-correct covered tags. Then evaluate a frozen selective override, if any region offers useful precision/coverage. The current probe has not shown such a region, and its context-only gains on excluded tokens must not be presented as deployable recovery. Richer contextual modeling is a separate option if the detection signal proves too weak.

## Reproduction and verification

Artifacts under `experiments/results/grammar-restoration/iteration33/` include the frozen diagnostic manifest, 40 per-model probability/token records, cohort and paired neighbor audits, summary, and independent validation report. Earlier frozen artifacts are unchanged.

```
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_masked_context_iteration33
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_masked_context_iteration33_summarize
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m benchmarks.grammar_masked_context_iteration33_validate
```

Runners preserve outputs. Four new tests independently enumerate every state path for tiny target-masked sequences, verify both target and neighbor posteriors, prove invariance to the target's own emission changes, check boundaries/single-token sentences, and validate stable ties/empty-cohort metrics. Validation explicitly replaces target evidence with ones and invokes the original HMM inference for 9,600 target/sentence pairs, checking the new prefix/suffix calculation independently. It checks 82,080 token rows, 3,360 mode/cohort metrics, invariant oracle-context probabilities, true-neighbor identities, original ordinary predictions, and all prior hashes. The combined relevant suite passes 313 tests. The 200 reserved sentences remain unscored.
