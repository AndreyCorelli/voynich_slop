# Seven-stage out-of-folio context prediction

This follow-up tests whether preceding words improve manuscript prediction beyond a development-trained word-frequency baseline. It measures predictive log scores rather than selecting a generator by matching a few descriptive statistics. No cipher fitting, external downloads or Z3 calls occur.

## Data and frozen scoring

The development set remains the earlier 16 nonoverlapping 64-word blocks from 12 folios. Evaluation uses **ten fresh 64-word blocks on seven previously heldout folios**, excluding every block scored in the previous comparison. All eligible remaining blocks on those folios are included; none is chosen by its outcome. Thus 640 evaluation tokens are fresh, but the folios and some descriptive properties of them were examined previously. This is not a wholly new manuscript holdout.

Folio sets are disjoint. Excluded records and folio boundaries interrupt extraction; model transitions do not cross block boundaries. The first word of each block uses the unigram distribution. Raw lowercase atomic EVA normalization remains unchanged. A suffix is an EVA unit sequence, not an established manuscript glyph or plaintext morpheme.

Each training fold includes words occurring at least twice in its vocabulary. Singletons map to `<UNK>` during training, and unseen evaluation words map to the same class. The unigram has pseudocount 0.5 over this fixed training vocabulary plus `<UNK>`. Every model in a fold predicts the same outcomes; no evaluation words are added to its vocabulary.

Context distributions use the unigram as a Dirichlet backoff prior with strength 10 or 50. Additional mixtures weight this smoothed contextual distribution by 0.25 or 0.5 and the unigram by the remainder. Unseen contexts back off to unigram. The preceding observed word supplies context; the current/future target never does.

Scores are negative log2 probabilities. Lower bits per token is better. Selection averages gains equally over development folios in leave-one-folio-out validation, rather than treating words as independent observations. Vocabulary is refitted in each fold. Known-word log gains are reported separately; scoring an `<UNK>` event is not predicting its exact spelling.

## Seven iterations

1. Freeze data/smoothing and check probability normalization, positive unknown mass and block boundaries.
2. Establish leave-one-folio-out unigram scores.
3. Test preceding-word contexts with prior strengths 10 and 50. Both worsen development prediction.
4. Test preceding length bin, one-unit suffix and two-unit suffix at strength 50. All raw contextual models worsen development prediction; suffix-one is closest to unigram.
5. Test weak mixtures of that development-selected context with unigram at fixed weights 0.25 and 0.5. Both yield positive development gains: 0.0452 and 0.0625 bits per token.
6. Freeze the 0.5 suffix-one mixture as the development winner, retaining unigram as an eligible candidate.
7. Score every frozen model on fresh heldout blocks. The selected model remains selected regardless of heldout results. Evaluate its ordering sensitivity using three predeclared within-block word permutations; independently verify scores and a folio bootstrap.

Base models, pseudocounts, grids and mixture weights were frozen before testing. Stage five chooses its underlying context from development scores only. Source/code hashes and a chain of preceding stage-result hashes preserve the sequence. Heldout predictive scores are first accessed at stage seven.

## Heldout result

Positive gain means improvement over unigram. Overall gain weights each of seven folios equally; known-word gain weights the known-token subset. These columns therefore cannot be algebraically combined to attribute the total gain.

| Model | Overall gain, bits/token | Known-word gain, bits/token |
|---|---:|---:|
| Unigram | 0 | 0 |
| Previous word, strength 10 | -0.1776 | -0.5011 |
| Previous word, strength 50 | -0.0355 | -0.1966 |
| Previous length bin | -0.1706 | -0.4017 |
| Previous one-unit suffix | +0.0315 | -0.0048 |
| Previous two-unit suffix | -0.0203 | -0.0924 |
| Suffix-one mixture, weight 0.25 | +0.0522 | +0.0887 |
| **Selected suffix-one mixture, weight 0.5** | **+0.0751** | **+0.1187** |

The selected model reduces folio-mean log loss from 4.4203 to 4.3451 bits per scored token and improves on all seven folios. A predeclared 2,000-resample folio bootstrap gives a descriptive 95% interval of **0.0450–0.1141 bits/token** for its overall gain. Seven previously examined folios and adaptive development selection limit interpretation; this is not a universal significance claim or a probability of a manuscript hypothesis.

There are **332 unknown tokens out of 640**. The positive known-word gain shows the result is not solely from predicting the unknown class, but the large unknown fraction prevents treating log loss as full-spelling coding performance.

Shuffling the exact word multiset worsens selected-model predictions by an average **0.1142 bits/token** across the fixed permutations. Unigram scores remain unchanged, as independently checked. The gain reflects some order-dependent structure beyond global word frequencies under this protocol.

## Assessment and next step

There is a small transferable contextual signal in the preceding word's final EVA unit. Pure preceding-word lookup overfits this small development set; a strongly regularized suffix model predicts better. These results qualify the earlier weak local-repetition diagnostics: order can carry predictive information even when a few pair-count summaries show little average enrichment.

This does not identify grammar, meaning, a copying process or an encryption mechanism. Line layout, position preferences and source heterogeneity may also generate such dependencies. No generating key or manuscript plaintext has been recovered, and Caesar/German controls were not compared in this loop.

Next: **separate within-line from cross-line transitions and compare against a position-aware frequency baseline**. If position/layout explains the gain, the interpretation changes; if the suffix gain remains within lines after controlling position, it becomes a more useful target for competing text-generation and encoding models. Freeze that test before looking at its outcome rather than adding more suffix lengths or mixture weights.

## Validation and artifacts

Five focused tests pass, including an ordered synthetic positive, a deliberately misordered negative, no cross-block transition, unknown-class behavior, and a hand-computed interpolated probability. All seven stages validate. A separate implementation reconstructs training counts, vocabulary, context probabilities and every saved log score without calling the predictive implementation's fit/probability/score functions. Another check reconstructs shuffled scores and the bootstrap.

Artifacts are under `experiments/results/context-prediction/`: protocol, seven plans/results, `validation.json`, and `assessment.json`.

```sh
.venv/bin/python -m benchmarks.context_prediction --run
.venv/bin/python -m benchmarks.context_prediction_validation
.venv/bin/python -m benchmarks.context_prediction_assessment
.venv/bin/python -m pytest tests/integration/test_context_prediction.py -q
```

Completed runs reuse stored stage results, with frozen code/source checks. Prior text-generation and cipher experiments remain unchanged.
