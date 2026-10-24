# Learned Latin reconstruction scorer: bounded diagnostic

The learned context scorer distinguishes intact Latin from the existing optimized wrong reconstructions on two authors excluded from scorer training. It does **not** establish better recovery: it still prefers optimized wrong reconstructions to approximately half-correct ones, and reranking the existing candidates selects poor dictionaries. Decoder defaults remain unchanged.

## Frozen experiment

Driver: `benchmarks/scalable_latin_reconstruction_scorer.py`.
Artifacts: `experiments/results/scalable-latin-reconstruction-scorer/v1/`.

The design was written before fitting; both models were fitted and their hashes saved before opening test references and outputs. Fixed pairwise logistic preference learning, L2=1, 65,536 signed hash bins, maximum 200 optimizer iterations. No parameter selection on test results.

Training uses two 256-token windows from up to six admitted source files per author, augmented with windows from Apuleius, Curtius and Suetonius. Correct windows are paired with consistent injective type-permutation corruptions at 10%, 50% and 100% selected types. Actual solver-produced negatives come from the three previously completed Apuleius smoke methods (surface, shuffle contrast, regularized contrast). There are 1,260 training pairs. Optimized negative diversity is therefore limited to one author, not three.

The lexical control learns unigram features. The context model additionally learns word pairs at distances one and two, adjacent word triples, and pairs of two/three-letter endings at distances one, two, four and eight. These add sequence information and weak grammatical proxies; there is no explicit morphological analysis or semantic model. Both models use length-normalized features and average scores over fixed disjoint 256-word windows. No sentence boundaries, cipher IDs, topics, target vocabulary restrictions or guessed anchors are supplied. Scores are uncalibrated preferences, not confidence probabilities.

Gellius I and Livy I are excluded authors from both the source language model and scorer training. They were previously inspected recovery benchmarks, so this is a held-out scorer diagnostic, **not** fresh project-wide confirmation. Ammianus and Quintilian remain sealed. Source training passages overlap the existing language-model training corpus; that does not contaminate these excluded-author tests, but limits claims about in-source performance.

## Results

Each work contributes six optimized outputs: three original bigram chains and three trigram chains, with identical cipher/inventory identities checked before decoding their assignments into words.

| Diagnostic | Gellius | Livy |
|---|---:|---:|
| Original above optimized wrong outputs, unigram control | 2/6 | 2/6 |
| Original above optimized wrong outputs, context scorer | 6/6 | 6/6 |
| Correct accuracy ordering among synthetic corruptions, context | 95.38% | 98.48% |
| Approximately half-correct reconstruction above optimized wrong output | **0/18** | **0/18** |
| Recovery of context-selected optimized output | **7.48%** | **0%** |
| Best recovery available among those six outputs | 10.90% | 1.91% |

Corruption ordering uses all unequal-accuracy pairs among 12 synthetic reconstructions per work. These are highly related samples, not independent statistical trials. Type-permutation proportions are not exact token corruption proportions. The same synthetic corruption recipe is used in training and testing, so that diagnostic is easier than generalizing to optimized wrong dictionaries.

The predeclared discrimination gate passes: on each work, the intact reference beats all optimized outputs and corruption pair ordering exceeds 75%. The additional partial-recovery and reranking diagnostics expose why this gate is insufficient. Wrong optimized outputs retain high-frequency, plausible-looking sequences and score above every 50%-correct sample. The model therefore still rewards the wrong solutions in the region where current search operates. A successful intact-reference comparison does not imply a useful search gradient.

The run took about 13 seconds, excluding tests. Unigram fitting converged in 13 iterations and context fitting in 15. Saved weights are about 0.5 MB each. No new decoder run, model integration or word-confidence calibration was performed. Existing recovery results are unchanged.

## Interpretation and next decision

This is evidence that learned context adds discrimination beyond learned word frequency. It is **not evidence of a recovery improvement**, a trustworthy frequent-word nucleus, or semantic reconstruction.

The most direct follow-up would be harder training examples: many independently optimized wrong dictionaries across multiple training authors, plus partially correct dictionaries whose accuracy is directly compared with optimized wrong keys. Before decoder integration, require those partial reconstructions to outrank optimized wrong outputs on excluded authors. Adversarial optimization against the learned scorer would then test whether search immediately discovers new scoring loopholes. Neither step is claimed completed here.

## Reproduction and validation

```
.venv/bin/python -m benchmarks.scalable_latin_reconstruction_scorer
.venv/bin/python -m pytest tests/unit/test_scalable_reconstruction_scorer.py -q
```

The driver refuses to overwrite the versioned experiment directory; preserve it before an intentional rerun. Training records, design, frozen model hashes, weights and detailed test scores are retained. Tests cover order sensitivity beyond unigrams, preference optimization and weight round-trip, empty-input rejection, and consistent injective corruption.
